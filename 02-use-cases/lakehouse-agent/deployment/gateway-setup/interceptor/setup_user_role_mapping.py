#!/usr/bin/env python3
"""
Setup DynamoDB table for user-to-role mapping

This script creates a DynamoDB table to store mappings between users and their
assigned IAM roles for tenant-based access control.

Table Schema:
- Table Name: lakehouse-user-map
- Partition Key: userId (String)
- Attribute: iamRole (String)

Usage:
    python setup_user_role_mapping.py
    python setup_user_role_mapping.py --table-name custom-table-name
"""

import boto3
import json
import sys
import argparse
from typing import Dict, List
from botocore.exceptions import ClientError

class UserRoleMappingSetup:
    def __init__(self, table_name: str = 'lakehouse-user-map'):
        """
        Initialize DynamoDB setup.
        
        Args:
            table_name: Name of the DynamoDB table
        """
        # Get region from boto3 session
        session = boto3.Session()
        self.region = session.region_name
        
        # Get account ID from STS
        sts_client = boto3.client('sts')
        self.account_id = sts_client.get_caller_identity()['Account']
        
        # Initialize AWS clients
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)
        
        self.table_name = table_name
        
        print(f"✅ Using AWS configuration")
        print(f"   Region: {self.region}")
        print(f"   Account: {self.account_id}")
        print(f"   Table Name: {self.table_name}")
    
    def create_table(self) -> bool:
        """
        Create DynamoDB table for user-role mapping.
        
        Returns:
            True if table was created or already exists
        """
        print(f"\n📦 Creating DynamoDB table: {self.table_name}")
        
        try:
            # Check if table already exists
            existing_tables = self.dynamodb_client.list_tables()['TableNames']
            if self.table_name in existing_tables:
                print(f"✅ Table {self.table_name} already exists")
                
                # Wait for table to be active
                table = self.dynamodb.Table(self.table_name)
                table.wait_until_exists()
                print(f"✅ Table is active")
                return True
            
            # Create table
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'userId',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'userId',
                        'AttributeType': 'S'  # String
                    }
                ],
                BillingMode='PAY_PER_REQUEST',  # On-demand billing
                Tags=[
                    {
                        'Key': 'Application',
                        'Value': 'lakehouse-agent'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'user-role-mapping'
                    }
                ]
            )
            
            print(f"⏳ Waiting for table to be created...")
            table.wait_until_exists()
            
            print(f"✅ Table {self.table_name} created successfully")
            print(f"   Table ARN: {table.table_arn}")
            
            return True
            
        except ClientError as e:
            print(f"❌ Error creating table: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def get_seed_data(self) -> List[Dict[str, str]]:
        """
        Get seed data for user-role mappings.
        
        Returns:
            List of user-role mappings
        """
        return [
            {
                'userId': 'user001@example.com',
                'iamRole': f'arn:aws:iam::{self.account_id}:role/lakehouse-tenant-1',
                'description': 'User 1 - Tenant 1 access',
                'createdAt': '2024-01-01T00:00:00Z'
            },
            {
                'userId': 'user002@example.com',
                'iamRole': f'arn:aws:iam::{self.account_id}:role/lakehouse-tenant-2',
                'description': 'User 2 - Tenant 2 access',
                'createdAt': '2024-01-01T00:00:00Z'
            }
        ]
    
    def populate_seed_data(self) -> bool:
        """
        Populate table with seed data.
        
        Returns:
            True if data was populated successfully
        """
        print(f"\n📝 Populating seed data...")
        
        try:
            table = self.dynamodb.Table(self.table_name)
            seed_data = self.get_seed_data()
            
            for item in seed_data:
                # Check if item already exists
                try:
                    response = table.get_item(Key={'userId': item['userId']})
                    if 'Item' in response:
                        print(f"   ℹ️  User {item['userId']} already exists, skipping")
                        continue
                except:
                    pass
                
                # Put item
                table.put_item(Item=item)
                print(f"   ✅ Added mapping: {item['userId']} → {item['iamRole'].split('/')[-1]}")
            
            print(f"✅ Seed data populated successfully")
            return True
            
        except ClientError as e:
            print(f"❌ Error populating seed data: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def verify_data(self):
        """Verify the data in the table."""
        print(f"\n🔍 Verifying table data...")
        
        try:
            table = self.dynamodb.Table(self.table_name)
            
            # Scan table to get all items
            response = table.scan()
            items = response.get('Items', [])
            
            print(f"✅ Found {len(items)} items in table:")
            for item in items:
                print(f"   - {item['userId']}")
                print(f"     Role: {item['iamRole']}")
                if 'description' in item:
                    print(f"     Description: {item['description']}")
            
        except Exception as e:
            print(f"❌ Error verifying data: {e}")
    
    def store_table_info_in_ssm(self):
        """Store table information in SSM Parameter Store."""
        print(f"\n💾 Storing table information in SSM Parameter Store...")
        
        try:
            table_arn = f"arn:aws:dynamodb:{self.region}:{self.account_id}:table/{self.table_name}"
            
            parameters = [
                {
                    'name': '/app/lakehouse-agent/user-role-mapping-table',
                    'value': self.table_name,
                    'description': 'DynamoDB table name for user-role mapping'
                },
                {
                    'name': '/app/lakehouse-agent/user-role-mapping-table-arn',
                    'value': table_arn,
                    'description': 'DynamoDB table ARN for user-role mapping'
                }
            ]
            
            for param in parameters:
                self.ssm_client.put_parameter(
                    Name=param['name'],
                    Value=param['value'],
                    Description=param['description'],
                    Type='String',
                    Overwrite=True
                )
                print(f"✅ Stored parameter: {param['name']}")
            
        except Exception as e:
            print(f"❌ Error storing SSM parameters: {e}")
    
    def update_lambda_role_permissions(self):
        """Add DynamoDB read permissions to Lambda role."""
        print(f"\n🔑 Updating Lambda role permissions for DynamoDB access...")
        
        try:
            iam = boto3.client('iam', region_name=self.region)
            lambda_role_name = 'InsuranceClaimsGatewayInterceptorRole'
            
            # Create DynamoDB read policy
            dynamodb_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "DynamoDBReadUserRoleMapping",
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:GetItem",
                            "dynamodb:Query",
                            "dynamodb:Scan"
                        ],
                        "Resource": f"arn:aws:dynamodb:{self.region}:{self.account_id}:table/{self.table_name}"
                    }
                ]
            }
            
            # Add policy to Lambda role
            iam.put_role_policy(
                RoleName=lambda_role_name,
                PolicyName='DynamoDBUserRoleMappingPolicy',
                PolicyDocument=json.dumps(dynamodb_policy)
            )
            
            print(f"✅ Added DynamoDB read permissions to Lambda role")
            
        except Exception as e:
            print(f"⚠️  Could not update Lambda role: {e}")
            print(f"   You may need to add DynamoDB permissions manually")
    
    def setup(self):
        """Run the complete setup."""
        print("\n🚀 Starting User-Role Mapping Setup")
        print("=" * 70)
        
        # Create table
        if not self.create_table():
            print("\n❌ Failed to create table")
            sys.exit(1)
        
        # Populate seed data
        if not self.populate_seed_data():
            print("\n❌ Failed to populate seed data")
            sys.exit(1)
        
        # Verify data
        self.verify_data()
        
        # Store table info in SSM
        self.store_table_info_in_ssm()
        
        # Update Lambda role permissions
        self.update_lambda_role_permissions()
        
        print("\n" + "=" * 70)
        print("✨ Setup completed successfully!")
        print("=" * 70)
        print(f"\n📋 Summary:")
        print(f"   Table Name: {self.table_name}")
        print(f"   Region: {self.region}")
        print(f"   Billing Mode: PAY_PER_REQUEST (on-demand)")
        print(f"   Seed Data: 2 users populated")
        print(f"\n💾 SSM Parameters:")
        print(f"   - /app/lakehouse-agent/user-role-mapping-table")
        print(f"   - /app/lakehouse-agent/user-role-mapping-table-arn")
        print(f"\n🔐 Lambda Role:")
        print(f"   - Added DynamoDB read permissions")
        print(f"\n📝 Next Steps:")
        print(f"   1. Update lambda_function.py to read from DynamoDB")
        print(f"   2. Redeploy Lambda function: ./deploy.sh")
        print(f"   3. Test with user001@example.com and user002@example.com")


def main():
    parser = argparse.ArgumentParser(
        description='Setup DynamoDB table for user-role mapping'
    )
    parser.add_argument(
        '--table-name',
        required=False,
        default='lakehouse-user-map',
        help='Name of the DynamoDB table (default: lakehouse-user-map)'
    )
    
    args = parser.parse_args()
    
    # Run setup
    setup = UserRoleMappingSetup(table_name=args.table_name)
    setup.setup()


if __name__ == '__main__':
    main()
