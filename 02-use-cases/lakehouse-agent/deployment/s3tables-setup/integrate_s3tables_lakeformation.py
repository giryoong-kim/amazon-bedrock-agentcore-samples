#!/usr/bin/env python3
"""
Integrate Amazon S3 Tables with Data Catalog and Lake Formation

This script performs the integration steps required to enable Lake Formation
permissions on S3 Tables:
1. Creates IAM role for Lake Formation data access
2. Registers S3 Tables bucket with Lake Formation
3. Creates federated catalog for S3 Tables

Reference: https://docs.aws.amazon.com/lake-formation/latest/dg/enable-s3-tables-catalog-integration.html

Usage:
    python integrate_s3tables_lakeformation.py
"""

import boto3
import json
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from utils.aws_session_utils import get_aws_session


class S3TablesLakeFormationIntegration:
    def __init__(self):
        """Initialize the integration setup."""
        session, self.region, self.account_id = get_aws_session()
        
        self.iam = boto3.client('iam')
        self.lakeformation = boto3.client('lakeformation', region_name=self.region)
        self.glue = boto3.client('glue', region_name=self.region)
        self.ssm = boto3.client('ssm', region_name=self.region)
        
        # Role name for Lake Formation data access
        self.lf_role_name = 'LakeFormationS3TablesDataAccessRole'
        
    def _get_ssm_param(self, name: str) -> str:
        """Get parameter from SSM."""
        try:
            response = self.ssm.get_parameter(Name=f'/app/lakehouse-agent/{name}')
            return response['Parameter']['Value']
        except Exception as e:
            raise Exception(f"Failed to get SSM parameter /app/lakehouse-agent/{name}: {e}")
    
    def create_lakeformation_role(self):
        """Create IAM role for Lake Formation to access S3 Tables."""
        print(f"\n🔐 Creating Lake Formation data access role...")
        
        # Trust policy for Lake Formation
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lakeformation.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Permissions policy for S3 Tables access
        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "S3TablesAccess",
                    "Effect": "Allow",
                    "Action": [
                        "s3tables:GetTableBucket",
                        "s3tables:GetTable",
                        "s3tables:GetTableMetadata",
                        "s3tables:GetTableMetadataLocation",
                        "s3tables:GetNamespace",
                        "s3tables:ListTables",
                        "s3tables:ListNamespaces",
                        "s3tables:GetTableMaintenanceConfiguration"
                    ],
                    "Resource": [
                        f"arn:aws:s3tables:{self.region}:{self.account_id}:bucket/*"
                    ]
                },
                {
                    "Sid": "S3Access",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket",
                        "s3:GetBucketLocation"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            # Check if role exists
            try:
                role = self.iam.get_role(RoleName=self.lf_role_name)
                role_arn = role['Role']['Arn']
                print(f"✅ Role already exists: {role_arn}")
            except self.iam.exceptions.NoSuchEntityException:
                # Create role
                response = self.iam.create_role(
                    RoleName=self.lf_role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description='Lake Formation role for S3 Tables data access',
                    Tags=[
                        {'Key': 'Application', 'Value': 'lakehouse-agent'},
                        {'Key': 'Purpose', 'Value': 'LakeFormation-S3Tables'}
                    ]
                )
                role_arn = response['Role']['Arn']
                print(f"✅ Created role: {role_arn}")
                
                # Wait for role to be available
                time.sleep(10)
            
            # Attach inline policy
            self.iam.put_role_policy(
                RoleName=self.lf_role_name,
                PolicyName='S3TablesDataAccess',
                PolicyDocument=json.dumps(permissions_policy)
            )
            print(f"✅ Attached permissions policy")
            
            return role_arn
            
        except Exception as e:
            print(f"❌ Error creating role: {e}")
            raise
    
    def register_s3tables_with_lakeformation(self, role_arn: str):
        """Register S3 Tables bucket with Lake Formation."""
        print(f"\n📋 Registering S3 Tables with Lake Formation...")
        
        # Use wildcard to register all S3 Tables buckets
        resource_arn = f"arn:aws:s3tables:{self.region}:{self.account_id}:bucket/*"
        
        try:
            self.lakeformation.register_resource(
                ResourceArn=resource_arn,
                RoleArn=role_arn,
                WithFederation=True
            )
            print(f"✅ Registered S3 Tables: {resource_arn}")
            print(f"   With federation enabled")
            
        except self.lakeformation.exceptions.AlreadyExistsException:
            print(f"✅ S3 Tables already registered")
        except Exception as e:
            print(f"⚠️  Registration note: {e}")
            # Continue even if already registered
    
    def create_federated_catalog(self):
        """Create federated catalog for S3 Tables."""
        print(f"\n📚 Creating federated catalog for S3 Tables...")
        
        catalog_name = 's3tablescatalog'
        
        catalog_input = {
            "Name": catalog_name,
            "CatalogInput": {
                "FederatedCatalog": {
                    "Identifier": f"arn:aws:s3tables:{self.region}:{self.account_id}:bucket/*",
                    "ConnectionName": "aws:s3tables"
                },
                "CreateDatabaseDefaultPermissions": [],
                "CreateTableDefaultPermissions": []
            }
        }
        
        try:
            response = self.glue.create_catalog(**catalog_input)
            print(f"✅ Created federated catalog: {catalog_name}")
            return catalog_name
            
        except self.glue.exceptions.AlreadyExistsException:
            print(f"✅ Federated catalog already exists: {catalog_name}")
            return catalog_name
        except Exception as e:
            print(f"❌ Error creating catalog: {e}")
            raise
    
    def store_configuration(self, role_arn: str, catalog_name: str):
        """Store configuration in SSM."""
        print(f"\n💾 Storing configuration in SSM...")
        
        params = {
            '/app/lakehouse-agent/lakeformation-role-arn': role_arn,
            '/app/lakehouse-agent/s3tables-catalog-name': catalog_name
        }
        
        for name, value in params.items():
            try:
                self.ssm.put_parameter(
                    Name=name,
                    Value=value,
                    Description=f'S3 Tables Lake Formation integration parameter',
                    Type='String',
                    Overwrite=True
                )
                print(f"✅ {name}")
            except Exception as e:
                print(f"⚠️  Error storing {name}: {e}")
    
    def run(self):
        """Run the complete integration process."""
        print(f"\n🚀 S3 Tables Lake Formation Integration")
        print(f"   Region: {self.region}")
        print(f"   Account: {self.account_id}")
        
        # Step 1: Create Lake Formation role
        role_arn = self.create_lakeformation_role()
        
        # Step 2: Register S3 Tables with Lake Formation
        self.register_s3tables_with_lakeformation(role_arn)
        
        # Step 3: Create federated catalog
        catalog_name = self.create_federated_catalog()
        
        # Step 4: Store configuration
        self.store_configuration(role_arn, catalog_name)
        
        print(f"\n✨ Integration complete!")
        print(f"\n📋 Summary:")
        print(f"   Lake Formation Role: {role_arn}")
        print(f"   Federated Catalog: {catalog_name}")
        print(f"   S3 Tables Resource: arn:aws:s3tables:{self.region}:{self.account_id}:bucket/*")
        
        print(f"\n📋 Next steps:")
        print(f"   1. Run: python setup_s3tables.py")
        print(f"   2. Run: python load_sample_data.py")
        print(f"   3. Run: python setup_lakeformation_permissions.py")


def main():
    integration = S3TablesLakeFormationIntegration()
    integration.run()


if __name__ == '__main__':
    main()
