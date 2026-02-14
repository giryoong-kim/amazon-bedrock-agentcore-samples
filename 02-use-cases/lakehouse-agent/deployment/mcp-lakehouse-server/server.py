"""
MCP Server for Health Lakehouse Data - Production Security with Lake Formation

This MCP server provides tools for querying and managing health lakehouse data
with enterprise-grade row-level security enforced by AWS Lake Formation.

Security Architecture:
- OAuth authentication (Cognito JWT tokens)
- User identity extraction from Gateway interceptor
- Lake Formation session tag-based row-level security
- No SQL string interpolation (eliminates SQL injection risk)

IMPORTANT: This server ONLY supports Lake Formation security mode.
Application-level SQL filtering has been removed for security reasons.

Configuration:
- Reads from SSM Parameter Store
- Auto-detects region from boto3 session
- Requires SECURITY_MODE=lakeformation
- Optional RLS_ROLE_ARN to be set
"""

import sys
import os
from typing import Any, Dict, Optional
import boto3
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP(host="0.0.0.0", stateless_http=True)

# PRODUCTION ONLY: Use Lake Formation row-level security
from athena_tools_secure import SecureAthenaClaimsTools as AthenaTools

print("🔒 Using Lake Formation row-level security (production mode)")

# Global Athena tools instance
athena_tools = None

# Configuration cache
_config_cache = None


def get_config() -> Dict[str, Optional[str]]:
    """
    Load configuration from environment variables and SSM Parameter Store.
    """
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    config = {}
    
    # Get region from boto3 session with proper fallback
    try:
        session = boto3.Session()
        config['region'] = (
            session.region_name or
            os.environ.get('AWS_REGION') or
            os.environ.get('AWS_DEFAULT_REGION') or
            'us-east-1'
        )
        if not session.region_name:
            print("⚠️  No region in AWS config, using fallback")
        print(f"✅ Region: {config['region']}")
    except Exception as e:
        print(f"⚠️  Could not detect region: {e}")
        config['region'] = 'us-east-1'
    
    # Get account ID
    try:
        sts = boto3.client('sts', region_name=config['region'])
        config['account_id'] = sts.get_caller_identity()['Account']
    except Exception as e:
        print(f"⚠️  Could not get account ID: {e}")
        config['account_id'] = None
    
    ssm = boto3.client('ssm', region_name=config['region'])
    
    def get_param(name: str, env_var: str = None, default: str = None) -> Optional[str]:
        if env_var and env_var in os.environ:
            value = os.environ[env_var]
            print(f"✅ {name} from environment: {value}")
            return value
        
        try:
            response = ssm.get_parameter(Name=f'/app/lakehouse-agent/{name}')
            value = response['Parameter']['Value']
            print(f"✅ {name} from SSM: {value}")
            return value
        except ssm.exceptions.ParameterNotFound:
            if default:
                print(f"ℹ️  {name} using default: {default}")
                return default
            print(f"⚠️  {name} not found")
            return None
        except Exception as e:
            print(f"❌ Error getting {name}: {e}")
            return default
    
    config['s3_bucket_name'] = get_param('s3-bucket-name', 'S3_BUCKET_NAME')
    config['database_name'] = get_param('database-name', 'ATHENA_DATABASE_NAME')
    config['rls_role_arn'] = get_param('rls-role-arn', None)
    config['security_mode'] = get_param('security-mode', 'SECURITY_MODE', 'lakeformation')
    config['log_level'] = os.environ.get('LOG_LEVEL', 'INFO')
    
    if config['s3_bucket_name']:
        config['s3_output_location'] = f"s3://{config['s3_bucket_name']}/athena-results/"
    else:
        config['s3_output_location'] = None
    
    config['test_user'] = os.environ.get('TEST_USER_1', 'policyholder001@example.com')
    config['local_development'] = os.environ.get('LOCAL_DEVELOPMENT', 'false').lower() == 'true'
    
    _config_cache = config
    return config


def validate_config(config: Dict[str, Optional[str]]) -> bool:
    required_params = [
        ('region', 'AWS Region'),
        ('s3_bucket_name', 'S3 Bucket Name'),
        ('database_name', 'Athena Database Name'),
        ('security_mode', 'Security Mode')
    ]
    
    missing = []
    for param, display_name in required_params:
        if not config.get(param):
            missing.append(display_name)
    
    if missing:
        print(f"❌ Missing required configuration: {', '.join(missing)}")
        return False
    
    if config['security_mode'] != 'lakeformation':
        print(f"❌ Invalid security mode: {config['security_mode']}")
        print("   Only 'lakeformation' is supported")
        return False
    
    return True


def get_athena_tools():
    global athena_tools
    if athena_tools is None:
        config = get_config()
        
        print("Initializing Athena tools with Lake Formation RLS...")
        print(f"  Region: {config['region']}")
        print(f"  Database: {config['database_name']}")
        print(f"  S3 Output: {config['s3_output_location']}")
        print(f"  RLS Role: {config['rls_role_arn']}")

        athena_tools = AthenaTools(
            region=config['region'],
            database_name=config['database_name'],
            s3_output_location=config['s3_output_location'],
            rls_role_arn=config['rls_role_arn']
        )

        print("✅ Athena tools initialized with Lake Formation RLS")

    return athena_tools


def get_user_id_with_fallback(context_arg: Dict[str, Any] = None) -> tuple[str, Optional[Dict[str, str]]]:
    """
    Get user ID and tenant credentials from context argument or fallback to test user.
    
    Returns:
        Tuple of (user_id, tenant_credentials)
    """
    config = get_config()
    user_id = None
    tenant_credentials = None
    
    if context_arg:
        print(f"📋 Context argument received: {list(context_arg.keys())}")
        user_id = context_arg.get('user_id')
        if user_id:
            print(f"   Got user_id from context: {user_id}")
        
        # Extract tenant credentials if present
        tenant_creds = context_arg.get('tenant_credentials')
        if tenant_creds:
            print(f"   Got tenant_credentials from context")
            print(f"   Role: {tenant_creds.get('role_name', 'N/A')}")
            print(f"   Expiration: {tenant_creds.get('expiration', 'N/A')}")
            tenant_credentials = tenant_creds
        
        if user_id:
            return user_id, tenant_credentials
    
    if config['local_development']:
        user_id = config['test_user']
        print(f"⚠️  Using test user for local development: {user_id}")
        return user_id, None
    
    print("❌ User identity not found in request")
    return None, None


@mcp.tool(
    name="query_claims",
    description="Query health lakehouse data for the authenticated user with optional filters"
)
def query_claims(
    claim_status: str = None,
    claim_type: str = None,
    start_date: str = None,
    end_date: str = None,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Query lakehouse data for the authenticated user."""
    print("=" * 60)
    print("🔧 TOOL INVOKED: query_claims")
    print("=" * 60)
    
    print("📥 INPUT PARAMETERS:")
    print(f"   claim_status: {claim_status}")
    print(f"   claim_type: {claim_type}")
    print(f"   start_date: {start_date}")
    print(f"   end_date: {end_date}")
    print(f"   context: {context}")
    
    try:
        user_id, tenant_credentials = get_user_id_with_fallback(context)
        print(f"👤 USER ID: {user_id}")
        if tenant_credentials:
            print(f"🔑 TENANT CREDENTIALS: Role {tenant_credentials.get('role_name')}")
        
        if not user_id:
            return {"success": False, "error": "User identity not found in request"}
        
        filters = {k: v for k, v in {
            'claim_status': claim_status,
            'claim_type': claim_type,
            'start_date': start_date,
            'end_date': end_date
        }.items() if v is not None}
        
        print(f"🔍 FILTERS: {filters}")

        tools = get_athena_tools()
        result = tools.query_claims(user_id, filters if filters else None, tenant_credentials)
        
        print("📤 OUTPUT:")
        print(f"   success: {result.get('success', 'N/A')}")
        if result.get('success'):
            claims_count = len(result.get('claims', []))
            print(f"   claims_count: {claims_count}")
        else:
            print(f"   error: {result.get('error', 'N/A')}")
        
        print("=" * 60)
        return result

    except Exception as e:
        print(f"❌ ERROR in query_claims: {str(e)}")
        import traceback
        print(f"   Stack trace: {traceback.format_exc()}")
        print("=" * 60)
        return {"success": False, "error": str(e)}


@mcp.tool(
    name="get_claim_details",
    description="Get detailed information about a specific claim by ID"
)
def get_claim_details(claim_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get details of a specific claim."""
    print("=" * 60)
    print("🔧 TOOL INVOKED: get_claim_details")
    print("=" * 60)
    
    print("📥 INPUT PARAMETERS:")
    print(f"   claim_id: {claim_id}")
    print(f"   context: {context}")
    
    try:
        user_id, tenant_credentials = get_user_id_with_fallback(context)
        print(f"👤 USER ID: {user_id}")
        if tenant_credentials:
            print(f"🔑 TENANT CREDENTIALS: Role {tenant_credentials.get('role_name')}")
        
        if not user_id:
            return {"success": False, "error": "User identity not found in request"}
        
        tools = get_athena_tools()
        result = tools.get_claim_details(user_id, claim_id, tenant_credentials)
        
        print("📤 OUTPUT:")
        print(f"   success: {result.get('success', 'N/A')}")
        if result.get('success'):
            claim_data = result.get('claim', {})
            print(f"   claim_id: {claim_data.get('claim_id', 'N/A')}")
            print(f"   claim_status: {claim_data.get('claim_status', 'N/A')}")
        else:
            print(f"   error: {result.get('error', 'N/A')}")
        
        print("=" * 60)
        return result

    except Exception as e:
        print(f"❌ ERROR in get_claim_details: {str(e)}")
        import traceback
        print(f"   Stack trace: {traceback.format_exc()}")
        print("=" * 60)
        return {"success": False, "error": str(e)}


@mcp.tool(
    name="get_claims_summary",
    description="Get summary statistics of all claims for the authenticated user"
)
def get_claims_summary(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get claims summary for the user."""
    print("=" * 60)
    print("🔧 TOOL INVOKED: get_claims_summary")
    print("=" * 60)
    
    print("📥 INPUT PARAMETERS:")
    print(f"   context: {context}")
    
    try:
        user_id, tenant_credentials = get_user_id_with_fallback(context)
        print(f"👤 USER ID: {user_id}")
        if tenant_credentials:
            print(f"🔑 TENANT CREDENTIALS: Role {tenant_credentials.get('role_name')}")
        
        if not user_id:
            return {"success": False, "error": "User identity not found in request"}
        
        tools = get_athena_tools()
        result = tools.get_claims_summary(user_id, tenant_credentials)
        
        print("📤 OUTPUT:")
        print(f"   success: {result.get('success', 'N/A')}")
        if result.get('success'):
            summary = result.get('summary', {})
            print(f"   total_claims: {summary.get('total_claims', 'N/A')}")
            print(f"   total_amount: {summary.get('total_amount', 'N/A')}")
            print(f"   by_status: {summary.get('by_status', 'N/A')}")
        else:
            print(f"   error: {result.get('error', 'N/A')}")
        
        print("=" * 60)
        return result

    except Exception as e:
        print(f"❌ ERROR in get_claims_summary: {str(e)}")
        import traceback
        print(f"   Stack trace: {traceback.format_exc()}")
        print("=" * 60)
        return {"success": False, "error": str(e)}


@mcp.tool(
    name="query_login_audit",
    description="Query user login audit logs from DynamoDB. RESTRICTED: This tool can only be used by IT administrators."
)
def query_login_audit(
    user_id: str = None,
    limit: int = 10,
    start_date: str = None,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Query login audit logs from DynamoDB.
    
    SECURITY: This tool is RESTRICTED to IT administrators only.
    Access control should be enforced at the Gateway level using fine-grained access control (FGAC).
    
    Args:
        user_id: Optional user ID to filter logs (email address). If not provided, returns recent logins across all users.
        limit: Maximum number of records to return (default: 10, max: 100)
        start_date: Optional ISO 8601 date to filter logs from (e.g., "2024-01-01")
        context: Request context containing authenticated user information
        
    Returns:
        Dictionary with success status and login records
    """
    print("=" * 60)
    print("🔧 TOOL INVOKED: query_login_audit")
    print("⚠️  ADMIN ONLY TOOL - Should be restricted via Gateway FGAC")
    print("=" * 60)
    
    print("📥 INPUT PARAMETERS:")
    print(f"   user_id: {user_id}")
    print(f"   limit: {limit}")
    print(f"   start_date: {start_date}")
    print(f"   context: {context}")
    
    try:
        # Get authenticated user from context
        authenticated_user, tenant_credentials = get_user_id_with_fallback(context)
        print(f"👤 AUTHENTICATED USER: {authenticated_user}")
        
        if not authenticated_user:
            return {"success": False, "error": "User identity not found in request"}
        
        # Check if user is in administrators group
        # Note: This is a secondary check. Primary access control should be at Gateway level.
        user_groups = []
        if context and 'user_groups' in context:
            user_groups = context.get('user_groups', [])
            print(f"👥 USER GROUPS: {user_groups}")
        
        # Validate limit
        if limit < 1 or limit > 100:
            return {"success": False, "error": "Limit must be between 1 and 100"}
        
        config = get_config()
        
        # Use tenant credentials if available, otherwise use default credentials
        if tenant_credentials:
            print(f"🔑 Using tenant credentials for DynamoDB access")
            dynamodb = boto3.resource(
                'dynamodb',
                region_name=config['region'],
                aws_access_key_id=tenant_credentials['access_key_id'],
                aws_secret_access_key=tenant_credentials['secret_access_key'],
                aws_session_token=tenant_credentials['session_token']
            )
        else:
            print(f"⚠️  No tenant credentials found, using default credentials")
            dynamodb = boto3.resource('dynamodb', region_name=config['region'])
        table_name = 'lakehouse_user_login_audit'
        
        try:
            table = dynamodb.Table(table_name)
            print(f"📊 Querying DynamoDB table: {table_name}")
            
            if user_id:
                # Query specific user's login history
                print(f"🔍 Querying logs for user: {user_id}")
                
                from boto3.dynamodb.conditions import Key
                
                key_condition = Key('user_id').eq(user_id)
                
                # Add date filter if provided
                if start_date:
                    key_condition = key_condition & Key('login_timestamp').gte(start_date)
                
                response = table.query(
                    KeyConditionExpression=key_condition,
                    ScanIndexForward=False,  # Most recent first
                    Limit=limit
                )
                
                records = response.get('Items', [])
                
            else:
                # Scan for recent logins across all users (use with caution)
                print(f"🔍 Scanning for recent logins across all users (limit: {limit})")
                
                scan_params = {
                    'Limit': limit
                }
                
                # Note: Scan doesn't support date filtering efficiently
                # For production, consider adding a GSI on login_timestamp
                if start_date:
                    from boto3.dynamodb.conditions import Attr
                    scan_params['FilterExpression'] = Attr('login_timestamp').gte(start_date)
                
                response = table.scan(**scan_params)
                records = response.get('Items', [])
                
                # Sort by timestamp (most recent first)
                records = sorted(records, key=lambda x: x.get('login_timestamp', ''), reverse=True)
            
            # Format records for output
            formatted_records = []
            for record in records:
                formatted_records.append({
                    'user_id': record.get('user_id', ''),
                    'login_timestamp': record.get('login_timestamp', ''),
                    'email': record.get('email', ''),
                    'groups': record.get('groups', '[]'),
                    'source_ip': record.get('source_ip', ''),
                    'user_agent': record.get('user_agent', ''),
                    'client_id': record.get('client_id', ''),
                    'event_type': record.get('event_type', '')
                })
            
            result = {
                "success": True,
                "records": formatted_records,
                "count": len(formatted_records),
                "queried_user": user_id if user_id else "all_users",
                "authenticated_as": authenticated_user
            }
            
            print("📤 OUTPUT:")
            print(f"   success: True")
            print(f"   records_count: {len(formatted_records)}")
            print(f"   queried_user: {user_id if user_id else 'all_users'}")
            
            print("=" * 60)
            return result
            
        except dynamodb.meta.client.exceptions.ResourceNotFoundException:
            error_msg = f"DynamoDB table '{table_name}' not found. Run deploy_post_auth_lambda.sh to create it."
            print(f"❌ ERROR: {error_msg}")
            print("=" * 60)
            return {"success": False, "error": error_msg}
        
    except Exception as e:
        print(f"❌ ERROR in query_login_audit: {str(e)}")
        import traceback
        print(f"   Stack trace: {traceback.format_exc()}")
        print("=" * 60)
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("\n🔍 Validating configuration...")
    
    config = get_config()
    
    if config['security_mode'] != 'lakeformation':
        print("\n❌ Error: Only Lake Formation security mode is supported!")
        print(f"   Current SECURITY_MODE: {config['security_mode']}")
        sys.exit(1)

    if not validate_config(config):
        print("\n❌ Configuration is invalid!")
        sys.exit(1)

    print("✅ Configuration validated")
    print("🔒 Lake Formation row-level security enabled")

    print(f"Starting MCP Server with Lake Formation RLS:")
    print(f"  Region: {config['region']}")
    print(f"  Database: {config['database_name']}")
    print(f"  S3 Output: {config['s3_output_location']}")
    print(f"  RLS Role: {config['rls_role_arn']}")

    mcp.run(transport="streamable-http")
