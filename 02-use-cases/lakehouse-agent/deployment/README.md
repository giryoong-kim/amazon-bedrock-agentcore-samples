# Lakehouse Agent Deployment Guide (DevOps)

This guide provides the deployment sequence for the Lakehouse Agent system using command-line scripts. For a guided notebook-based approach, see the Jupyter notebooks in the parent directory.

## Prerequisites

1. AWS CLI configured with appropriate permissions
2. Python 3.10+ with virtual environment
3. Docker running (for AgentCore Runtime deployments)
4. `bedrock-agentcore-starter-toolkit` installed

```bash
# Setup virtual environment
cd 02-use-cases/lakehouse-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install bedrock-agentcore-starter-toolkit
```

## Deployment Sequence

### Step 1: Deploy S3 Tables Database

Creates S3 Tables bucket, namespace, tables (claims, users), and S3 bucket for query results.

```bash
cd deployment/s3tables-setup
python setup_s3tables.py  # Uses default: lakehouse-{account_id}
# Or specify custom name:
# python setup_s3tables.py --table-bucket-name my-lakehouse
python load_sample_data.py
python setup_lakeformation_permissions.py
```

SSM Parameters created:
- `/app/lakehouse-agent/table-bucket-name`
- `/app/lakehouse-agent/table-bucket-arn`
- `/app/lakehouse-agent/namespace`
- `/app/lakehouse-agent/database-name`
- `/app/lakehouse-agent/s3-bucket-name`

Lake Formation permissions:
- Registers S3 Tables bucket with Lake Formation
- Grants database and table permissions to tenant roles
- Configures column-level access for row-level security

---

### Step 2: Deploy Cognito

Creates User Pool, OAuth clients, groups (policyholders, adjusters, administrators), and test users.
Automatically configures Post-Authentication trigger if Lambda exists.

```bash
cd ../cognito-setup
python setup_cognito.py
```

SSM Parameters created:
- `/app/lakehouse-agent/cognito-user-pool-id`
- `/app/lakehouse-agent/cognito-user-pool-arn`
- `/app/lakehouse-agent/cognito-app-client-id`
- `/app/lakehouse-agent/cognito-app-client-secret` (SecureString)
- `/app/lakehouse-agent/cognito-m2m-client-id`
- `/app/lakehouse-agent/cognito-m2m-client-secret` (SecureString)
- `/app/lakehouse-agent/cognito-domain`
- `/app/lakehouse-agent/cognito-resource-server-id`
- `/app/lakehouse-agent/cognito-region`

Test users created:
- `policyholder001@example.com` → policyholders group
- `policyholder002@example.com` → policyholders group
- `adjuster001@example.com` → adjusters group
- `adjuster002@example.com` → adjusters group
- `admin@example.com` → administrators group

Default password: `TempPass123!`

#### Optional: Enable Login Audit Logging

To enable login audit logging, deploy the Post-Authentication Lambda before running setup_cognito.py:

```bash
# Deploy Lambda and DynamoDB table first
bash deploy_post_auth_lambda.sh

# Then run setup (will automatically configure the trigger)
python setup_cognito.py
```

Or add the trigger to an existing User Pool:

```bash
# Deploy Lambda if not already deployed
bash deploy_post_auth_lambda.sh

# Add trigger to existing pool
python setup_cognito.py --add-post-auth-trigger
```

This creates:
- DynamoDB table: `lakehouse_user_login_audit`
- Lambda function: `lakehouse-cognito-post-auth`
- IAM role: `lakehouse-cognito-post-auth-role`

See [POST_AUTH_SETUP.md](cognito-setup/POST_AUTH_SETUP.md) for details.

---

### Step 3: Deploy IAM Roles for Tenant Groups

Creates IAM roles for users and adjusters groups with Athena/S3 permissions.

```bash
cd ../lakehouse-tenant-roles-setup
python setup_iam_roles.py
```

SSM Parameters created:
- `/app/lakehouse-agent/roles/lakehouse-users-role`
- `/app/lakehouse-agent/roles/lakehouse-adjusters-role`

---

### Step 4: Deploy MCP Server

Deploys the MCP Athena server to AgentCore Runtime.

```bash
cd ../mcp-lakehouse-server
python deploy_runtime.py --yes
```

SSM Parameters created:
- `/app/lakehouse-agent/mcp-server-runtime-arn`

---

### Step 5: Deploy Gateway Interceptor Lambda

Deploys the JWT validation Lambda and creates the tenant role mapping table.

```bash
cd ../gateway-setup/interceptor
./deploy.sh
```

This script:
1. Packages Lambda function with dependencies
2. Creates Lambda execution role
3. Deploys Lambda function
4. Creates DynamoDB table `lakehouse_tenant_role_map`
5. Seeds tenant-to-role mappings

SSM Parameters created:
- `/app/lakehouse-agent/interceptor-lambda-arn`
- `/app/lakehouse-agent/interceptor-lambda-role-arn`
- `/app/lakehouse-agent/tenant-role-mapping-table`

---

### Step 6: Deploy AgentCore Gateway

Creates the Gateway connecting to MCP server with JWT interceptor.

```bash
cd ..
python create_gateway.py --yes
```

SSM Parameters created:
- `/app/lakehouse-agent/gateway-arn`

---

### Step 7: Deploy Lakehouse Agent

Deploys the conversational AI agent to AgentCore Runtime.

```bash
cd ../lakehouse-agent
python deploy_lakehouse_agent.py --yes
```

SSM Parameters created:
- `/app/lakehouse-agent/agent-runtime-arn`

---

### Step 8: Run Streamlit UI (Optional)

```bash
cd ../../streamlit-ui
streamlit run streamlit_app.py
```

Access at: http://localhost:8501

---

## Quick Reference

| Step | Directory | Command |
|------|-----------|---------|
| 1 | `s3tables-setup` | `python setup_s3tables.py` then `python load_sample_data.py` |
| 2 | `cognito-setup` | `python setup_cognito.py` |
| 3 | `lakehouse-tenant-roles-setup` | `python setup_iam_roles.py` |
| 4 | `mcp-lakehouse-server` | `python deploy_runtime.py --yes` |
| 5 | `gateway-setup/interceptor` | `./deploy.sh` |
| 6 | `gateway-setup` | `python create_gateway.py --yes` |
| 7 | `lakehouse-agent` | `python deploy_lakehouse_agent.py --yes` |
| 8 | `streamlit-ui` | `streamlit run streamlit_app.py` |

---

## Directory Structure

```
deployment/
├── s3tables-setup/                  # Step 1
│   ├── setup_s3tables.py
│   └── load_sample_data.py
├── cognito-setup/                   # Step 2
│   └── setup_cognito.py
├── lakehouse-tenant-roles-setup/    # Step 3
│   └── setup_iam_roles.py
├── mcp-lakehouse-server/            # Step 4
│   └── deploy_runtime.py
├── gateway-setup/                   # Steps 5-6
│   ├── interceptor/
│   │   ├── deploy.sh
│   │   ├── lambda_function.py
│   │   ├── token_exchange.py
│   │   └── setup_dynamodb_tenant_role_maps.py
│   └── create_gateway.py
└── lakehouse-agent/                 # Step 7
    └── deploy_lakehouse_agent.py
```

---

## Verify Deployment

Check all SSM parameters:

```bash
aws ssm get-parameters-by-path \
  --path /app/lakehouse-agent/ \
  --recursive \
  --query 'Parameters[*].[Name,Value]' \
  --output table
```

---

## Cleanup

Run the cleanup notebook or delete resources manually:

```bash
# Delete AgentCore resources
aws bedrock-agent delete-agent-runtime --runtime-id <agent-runtime-id>
aws bedrock-agent delete-agent-runtime --runtime-id <mcp-runtime-id>
aws bedrock-agent delete-gateway --gateway-id <gateway-id>

# Delete Lambda
aws lambda delete-function --function-name lakehouse-gateway-interceptor

# Delete DynamoDB table
aws dynamodb delete-table --table-name lakehouse_tenant_role_map

# Delete IAM roles
aws iam delete-role-policy --role-name lakehouse-users-role --policy-name lakehouse-users-role-athena-s3-access
aws iam delete-role --role-name lakehouse-users-role
aws iam delete-role-policy --role-name lakehouse-adjusters-role --policy-name lakehouse-adjusters-role-athena-s3-access
aws iam delete-role --role-name lakehouse-adjusters-role

# Delete Cognito
aws cognito-idp delete-user-pool --user-pool-id <pool-id>

# Delete SSM parameters
aws ssm delete-parameters --names $(aws ssm get-parameters-by-path \
  --path /app/lakehouse-agent/ --recursive \
  --query 'Parameters[*].Name' --output text)
```
