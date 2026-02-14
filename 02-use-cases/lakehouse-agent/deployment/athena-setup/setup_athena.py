#!/usr/bin/env python3
"""
Athena Setup Script for Health Lakehouse Data Processing System

This script:
1. Creates an S3 bucket for Athena data and query results
2. Uploads sample claims data to S3
3. Creates Athena database and tables
4. Verifies the setup by running test queries

Usage:
    python setup_athena.py --bucket-name BUCKET_NAME
    python setup_athena.py  # Reads bucket name from SSM

Arguments:
    --bucket-name: (Optional) Base name for S3 bucket. Will be prefixed with {account_id}-{region_name}-
                   If not provided, reads from SSM parameter /app/lakehouse-agent/s3-bucket-name
                   Example: --bucket-name my-lakehouse creates bucket XXXXXXXXXXXX-us-east-1-my-lakehouse
"""

import boto3
import csv
import io
import time
import sys
import argparse
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any

class AthenaSetup:
    def __init__(self, bucket_base_name: str):
        """
        Initialize Athena setup with AWS region and S3 bucket name.
        
        Region is obtained from the boto3 session.
        Bucket name is constructed as: {account_id}-{region}-{bucket_base_name}
        
        Args:
            bucket_base_name: Base name for S3 bucket (will be prefixed with account_id and region)
        """
        # Get region from boto3 session
        session = boto3.Session()
        self.region = session.region_name
        
        # Get account ID from STS
        sts_client = boto3.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        
        # Construct bucket name with prefix
        self.bucket_name = f"{account_id}-{self.region}-{bucket_base_name}"
        
        self.database_name = 'lakehouse_db'

        # Initialize AWS clients
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.athena_client = boto3.client('athena', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)

        # S3 locations
        self.claims_prefix = 'lakehouse-data/claims/'
        self.users_prefix = 'lakehouse-data/users/'
        self.query_results_prefix = 'athena-results/'

    def create_s3_bucket(self):
        """Create S3 bucket if it doesn't exist."""
        print(f"\n📦 Checking S3 bucket: {self.bucket_name}")

        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Bucket {self.bucket_name} already exists")
        except:
            # Bucket doesn't exist, create it
            try:
                if self.region == 'us-east-1':
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                else:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.region}
                    )
                print(f"✅ Created S3 bucket: {self.bucket_name}")
            except Exception as e:
                print(f"❌ Error creating bucket: {e}")
                sys.exit(1)

    def cleanup_s3_data(self):
        """Delete existing data from S3 bucket to allow rerun."""
        print(f"\n🧹 Cleaning up existing S3 data...")
        
        prefixes_to_clean = [self.claims_prefix, self.users_prefix]
        
        for prefix in prefixes_to_clean:
            try:
                # List and delete objects with this prefix
                paginator = self.s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
                
                objects_to_delete = []
                for page in pages:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            objects_to_delete.append({'Key': obj['Key']})
                
                if objects_to_delete:
                    self.s3_client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={'Objects': objects_to_delete}
                    )
                    print(f"✅ Deleted {len(objects_to_delete)} objects from {prefix}")
                else:
                    print(f"ℹ️  No existing objects found in {prefix}")
                    
            except self.s3_client.exceptions.NoSuchBucket:
                print(f"ℹ️  Bucket does not exist yet, skipping cleanup for {prefix}")
            except Exception as e:
                print(f"⚠️  Warning cleaning up {prefix}: {e}")

    def drop_existing_tables(self):
        """Drop existing Athena tables to allow recreation."""
        print(f"\n🗑️  Dropping existing tables...")
        
        tables_to_drop = ['claims', 'users']
        
        for table in tables_to_drop:
            try:
                drop_query = f"DROP TABLE IF EXISTS {self.database_name}.{table}"
                self.run_athena_query(drop_query)
                print(f"✅ Dropped table: {table}")
            except Exception as e:
                print(f"⚠️  Warning dropping table {table}: {e}")

    def get_sample_claims_data(self) -> List[Dict[str, Any]]:
        """Generate sample claims data with assigned adjusters."""
        claims = [
            # Claims for policyholder001@example.com (John Doe)
            {
                'claim_id': 'CLM-2024-001',
                'user_id': 'policyholder001@example.com',
                'policyholder_name': 'John Doe',
                'policyholder_dob': '1985-03-15',
                'claim_date': '2024-01-10',
                'claim_amount': '1250.00',
                'claim_type': 'medical',
                'claim_status': 'approved',
                'provider_name': 'City Medical Center',
                'provider_npi': '1234567890',
                'diagnosis_code': 'J06.9',
                'procedure_code': '99213',
                'submitted_date': '2024-01-11 09:30:00',
                'processed_date': '2024-01-15 14:20:00',
                'approved_amount': '1000.00',
                'denial_reason': '',
                'notes': 'Annual physical examination and lab work',
                'created_by': 'policyholder001@example.com',
                'last_modified_by': 'adjuster001@example.com',
                'last_modified_date': '2024-01-15 14:20:00',
                'adjuster_user_id': 'adjuster001@example.com'
            },
            {
                'claim_id': 'CLM-2024-002',
                'user_id': 'policyholder001@example.com',
                'policyholder_name': 'John Doe',
                'policyholder_dob': '1985-03-15',
                'claim_date': '2024-02-05',
                'claim_amount': '85.50',
                'claim_type': 'prescription',
                'claim_status': 'approved',
                'provider_name': 'CVS Pharmacy',
                'provider_npi': '9876543210',
                'diagnosis_code': 'E11.9',
                'procedure_code': '90670',
                'submitted_date': '2024-02-05 16:45:00',
                'processed_date': '2024-02-06 10:15:00',
                'approved_amount': '85.50',
                'denial_reason': '',
                'notes': 'Diabetes medication - monthly refill',
                'created_by': 'policyholder001@example.com',
                'last_modified_by': 'adjuster001@example.com',
                'last_modified_date': '2024-02-06 10:15:00',
                'adjuster_user_id': 'adjuster001@example.com'
            },
            {
                'claim_id': 'CLM-2024-003',
                'user_id': 'policyholder001@example.com',
                'policyholder_name': 'John Doe',
                'policyholder_dob': '1985-03-15',
                'claim_date': '2024-02-20',
                'claim_amount': '3500.00',
                'claim_type': 'hospital',
                'claim_status': 'in_review',
                'provider_name': 'General Hospital',
                'provider_npi': '1122334455',
                'diagnosis_code': 'M54.5',
                'procedure_code': '22612',
                'submitted_date': '2024-02-21 08:00:00',
                'processed_date': '',
                'approved_amount': '',
                'denial_reason': '',
                'notes': 'Emergency room visit for back pain including X-rays',
                'created_by': 'policyholder001@example.com',
                'last_modified_by': 'adjuster002@example.com',
                'last_modified_date': '2024-02-21 08:00:00',
                'adjuster_user_id': 'adjuster002@example.com'
            },
            {
                'claim_id': 'CLM-2024-004',
                'user_id': 'policyholder001@example.com',
                'policyholder_name': 'John Doe',
                'policyholder_dob': '1985-03-15',
                'claim_date': '2024-03-10',
                'claim_amount': '450.00',
                'claim_type': 'medical',
                'claim_status': 'pending',
                'provider_name': 'Downtown Dental Clinic',
                'provider_npi': '2233445566',
                'diagnosis_code': 'K02.9',
                'procedure_code': 'D0150',
                'submitted_date': '2024-03-11 11:20:00',
                'processed_date': '',
                'approved_amount': '',
                'denial_reason': '',
                'notes': 'Dental examination and cleaning',
                'created_by': 'policyholder001@example.com',
                'last_modified_by': 'adjuster001@example.com',
                'last_modified_date': '2024-03-11 11:20:00',
                'adjuster_user_id': 'adjuster001@example.com'
            },
            # Claims for policyholder002@example.com (Jane Smith)
            {
                'claim_id': 'CLM-2024-005',
                'user_id': 'policyholder002@example.com',
                'policyholder_name': 'Jane Smith',
                'policyholder_dob': '1990-07-22',
                'claim_date': '2024-01-15',
                'claim_amount': '850.00',
                'claim_type': 'medical',
                'claim_status': 'approved',
                'provider_name': 'Womens Health Center',
                'provider_npi': '5544332211',
                'diagnosis_code': 'Z00.00',
                'procedure_code': '99395',
                'submitted_date': '2024-01-16 10:00:00',
                'processed_date': '2024-01-18 15:30:00',
                'approved_amount': '680.00',
                'denial_reason': '',
                'notes': 'Annual gynecological exam and preventive care',
                'created_by': 'policyholder002@example.com',
                'last_modified_by': 'adjuster002@example.com',
                'last_modified_date': '2024-01-18 15:30:00',
                'adjuster_user_id': 'adjuster002@example.com'
            },
            {
                'claim_id': 'CLM-2024-006',
                'user_id': 'policyholder002@example.com',
                'policyholder_name': 'Jane Smith',
                'policyholder_dob': '1990-07-22',
                'claim_date': '2024-02-10',
                'claim_amount': '125.00',
                'claim_type': 'prescription',
                'claim_status': 'approved',
                'provider_name': 'Walgreens Pharmacy',
                'provider_npi': '6655443322',
                'diagnosis_code': 'H10.9',
                'procedure_code': '90680',
                'submitted_date': '2024-02-10 13:15:00',
                'processed_date': '2024-02-11 09:00:00',
                'approved_amount': '125.00',
                'denial_reason': '',
                'notes': 'Antibiotic prescription for eye infection',
                'created_by': 'policyholder002@example.com',
                'last_modified_by': 'adjuster001@example.com',
                'last_modified_date': '2024-02-11 09:00:00',
                'adjuster_user_id': 'adjuster001@example.com'
            },
            {
                'claim_id': 'CLM-2024-007',
                'user_id': 'policyholder002@example.com',
                'policyholder_name': 'Jane Smith',
                'policyholder_dob': '1990-07-22',
                'claim_date': '2024-02-25',
                'claim_amount': '12500.00',
                'claim_type': 'hospital',
                'claim_status': 'approved',
                'provider_name': 'St. Marys Hospital',
                'provider_npi': '7766554433',
                'diagnosis_code': 'O80',
                'procedure_code': '59400',
                'submitted_date': '2024-02-26 07:30:00',
                'processed_date': '2024-03-05 16:00:00',
                'approved_amount': '10000.00',
                'denial_reason': '',
                'notes': 'Childbirth and postpartum care',
                'created_by': 'policyholder002@example.com',
                'last_modified_by': 'adjuster002@example.com',
                'last_modified_date': '2024-03-05 16:00:00',
                'adjuster_user_id': 'adjuster002@example.com'
            },
            {
                'claim_id': 'CLM-2024-008',
                'user_id': 'policyholder002@example.com',
                'policyholder_name': 'Jane Smith',
                'policyholder_dob': '1990-07-22',
                'claim_date': '2024-03-15',
                'claim_amount': '200.00',
                'claim_type': 'medical',
                'claim_status': 'denied',
                'provider_name': 'Cosmetic Surgery Center',
                'provider_npi': '8877665544',
                'diagnosis_code': 'Z41.1',
                'procedure_code': '15780',
                'submitted_date': '2024-03-16 14:00:00',
                'processed_date': '2024-03-20 11:00:00',
                'approved_amount': '0.00',
                'denial_reason': 'Cosmetic procedures not covered by policy',
                'notes': 'Facial cosmetic procedure',
                'created_by': 'policyholder002@example.com',
                'last_modified_by': 'adjuster001@example.com',
                'last_modified_date': '2024-03-20 11:00:00',
                'adjuster_user_id': 'adjuster001@example.com'
            },
            {
                'claim_id': 'CLM-2024-009',
                'user_id': 'policyholder002@example.com',
                'policyholder_name': 'Jane Smith',
                'policyholder_dob': '1990-07-22',
                'claim_date': '2024-03-25',
                'claim_amount': '75.00',
                'claim_type': 'prescription',
                'claim_status': 'pending',
                'provider_name': 'Target Pharmacy',
                'provider_npi': '9988776655',
                'diagnosis_code': 'Z79.890',
                'procedure_code': '90715',
                'submitted_date': '2024-03-26 09:45:00',
                'processed_date': '',
                'approved_amount': '',
                'denial_reason': '',
                'notes': 'Vitamin supplements and prenatal care',
                'created_by': 'policyholder002@example.com',
                'last_modified_by': 'adjuster002@example.com',
                'last_modified_date': '2024-03-26 09:45:00',
                'adjuster_user_id': 'adjuster002@example.com'
            }
        ]
        
        return claims

    def get_sample_users_data(self) -> List[Dict[str, Any]]:
        """Generate sample users data."""
        return [
            {
                'user_id': 'policyholder001@example.com',
                'user_name': 'John Doe',
                'user_role': 'policyholder',
                'department': 'Individual',
                'created_date': '2023-01-15 00:00:00'
            },
            {
                'user_id': 'policyholder002@example.com',
                'user_name': 'Jane Smith',
                'user_role': 'policyholder',
                'department': 'Individual',
                'created_date': '2023-02-20 00:00:00'
            },
            {
                'user_id': 'adjuster001@example.com',
                'user_name': 'Michael Johnson',
                'user_role': 'adjuster',
                'department': 'Claims Department',
                'created_date': '2022-06-01 00:00:00'
            },
            {
                'user_id': 'adjuster002@example.com',
                'user_name': 'Sarah Williams',
                'user_role': 'adjuster',
                'department': 'Claims Department',
                'created_date': '2022-08-15 00:00:00'
            },
            {
                'user_id': 'admin@example.com',
                'user_name': 'Admin User',
                'user_role': 'admin',
                'department': 'IT Department',
                'created_date': '2022-01-01 00:00:00'
            }
        ]

    def upload_csv_to_s3(self, data: List[Dict[str, Any]], s3_key: str):
        """Upload data as CSV to S3."""
        if not data:
            print(f"⚠️  No data to upload for {s3_key}")
            return

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=output.getvalue().encode('utf-8')
            )
            print(f"✅ Uploaded {s3_key} to S3")
        except Exception as e:
            print(f"❌ Error uploading {s3_key}: {e}")
            raise

    def run_athena_query(self, query: str, wait_for_results: bool = True) -> str:
        """
        Execute an Athena query and optionally wait for results.

        Args:
            query: SQL query to execute
            wait_for_results: Whether to wait for query completion

        Returns:
            Query execution ID
        """
        try:
            # Prepare query execution parameters
            query_params = {
                'QueryString': query,
                'ResultConfiguration': {
                    'OutputLocation': f's3://{self.bucket_name}/{self.query_results_prefix}'
                }
            }

            # Only add Database context if not creating a database
            if 'CREATE DATABASE' not in query.upper():
                query_params['QueryExecutionContext'] = {'Database': self.database_name}

            response = self.athena_client.start_query_execution(**query_params)

            query_execution_id = response['QueryExecutionId']

            if wait_for_results:
                # Wait for query to complete
                while True:
                    status_response = self.athena_client.get_query_execution(
                        QueryExecutionId=query_execution_id
                    )
                    status = status_response['QueryExecution']['Status']['State']

                    if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                        if status == 'SUCCEEDED':
                            return query_execution_id
                        else:
                            error = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                            raise Exception(f"Query failed: {error}")

                    time.sleep(1)

            return query_execution_id

        except Exception as e:
            print(f"❌ Error executing query: {e}")
            raise

    def store_parameters_in_ssm(self):
        """Store S3 bucket name and database name in SSM Parameter Store."""
        print("\n💾 Storing configuration in SSM Parameter Store...")
        
        parameters = [
            {
                'name': '/app/lakehouse-agent/s3-bucket-name',
                'value': self.bucket_name,
                'description': 'S3 bucket name for lakehouse data storage'
            },
            {
                'name': '/app/lakehouse-agent/database-name',
                'value': self.database_name,
                'description': 'Athena/Glue database name for lakehouse'
            }
        ]
        
        for param in parameters:
            try:
                self.ssm_client.put_parameter(
                    Name=param['name'],
                    Value=param['value'],
                    Description=param['description'],
                    Type='String',
                    Overwrite=True
                )
                print(f"✅ Stored parameter: {param['name']} = {param['value']}")
            except Exception as e:
                print(f"❌ Error storing parameter {param['name']}: {e}")
                raise

    def setup(self):
        """Run the complete Athena setup."""
        print("\n🚀 Starting Athena Setup for Health Lakehouse Data Processing")
        print(f"   Region: {self.region}")
        print(f"   S3 Bucket: {self.bucket_name}")

        # Step 1: Create S3 bucket
        self.create_s3_bucket()

        # Step 2: Cleanup existing data (for rerunnable deployments)
        self.cleanup_s3_data()

        # Step 3: Drop existing tables (for rerunnable deployments)
        # First ensure database exists for drop queries
        print("\n🗄️  Ensuring Athena database exists...")
        create_db_query = f"CREATE DATABASE IF NOT EXISTS {self.database_name}"
        try:
            self.run_athena_query(create_db_query)
            print(f"✅ Database {self.database_name} ready")
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            return

        self.drop_existing_tables()

        # Step 4: Upload sample data
        print("\n📤 Uploading sample data to S3...")
        claims_data = self.get_sample_claims_data()
        users_data = self.get_sample_users_data()

        self.upload_csv_to_s3(claims_data, f'{self.claims_prefix}claims.csv')
        self.upload_csv_to_s3(users_data, f'{self.users_prefix}users.csv')

        # Step 5: Create claims table
        print("\n📊 Creating claims table...")
        create_claims_table_query = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS {self.database_name}.claims (
            claim_id STRING,
            user_id STRING,
            policyholder_name STRING,
            policyholder_dob STRING,
            claim_date STRING,
            claim_amount STRING,
            claim_type STRING,
            claim_status STRING,
            provider_name STRING,
            provider_npi STRING,
            diagnosis_code STRING,
            procedure_code STRING,
            submitted_date STRING,
            processed_date STRING,
            approved_amount STRING,
            denial_reason STRING,
            notes STRING,
            created_by STRING,
            last_modified_by STRING,
            last_modified_date STRING,
            adjuster_user_id STRING
        )
        ROW FORMAT DELIMITED
        FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        LOCATION 's3://{self.bucket_name}/{self.claims_prefix}'
        TBLPROPERTIES ('skip.header.line.count'='1')
        """
        try:
            self.run_athena_query(create_claims_table_query)
            print("✅ Claims table created")
        except Exception as e:
            print(f"❌ Error creating claims table: {e}")
            return

        # Step 6: Create users table
        print("\n👥 Creating users table...")
        create_users_table_query = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS {self.database_name}.users (
            user_id STRING,
            user_name STRING,
            user_role STRING,
            department STRING,
            created_date STRING
        )
        ROW FORMAT DELIMITED
        FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        LOCATION 's3://{self.bucket_name}/{self.users_prefix}'
        TBLPROPERTIES ('skip.header.line.count'='1')
        """
        try:
            self.run_athena_query(create_users_table_query)
            print("✅ Users table created")
        except Exception as e:
            print(f"❌ Error creating users table: {e}")
            return

        # Step 7: Verify setup with test query
        print("\n🔍 Verifying setup with test queries...")
        try:
            # Count claims
            count_query = f"SELECT COUNT(*) as total_claims FROM {self.database_name}.claims"
            self.run_athena_query(count_query)
            print("✅ Claims table verification successful")

            # Query claims for policyholder001
            user_query = f"SELECT claim_id, claim_type, claim_status FROM {self.database_name}.claims WHERE user_id = 'policyholder001@example.com' LIMIT 5"
            self.run_athena_query(user_query)
            print("✅ User-specific query successful")

        except Exception as e:
            print(f"⚠️  Verification query failed: {e}")

        # Step 8: Store configuration in SSM Parameter Store
        self.store_parameters_in_ssm()

        print("\n✨ Athena setup completed successfully!")
        print(f"\n📋 Database name: {self.database_name}")
        print(f"📁 S3 bucket: s3://{self.bucket_name}")
        print(f"📊 Tables created: claims, users")
        print(f"💾 SSM Parameters:")
        print(f"   - /app/lakehouse-agent/s3-bucket-name")
        print(f"   - /app/lakehouse-agent/database-name")
        print(f"\n🔐 Row-level access control ready:")
        print(f"   - policyholder001@example.com: {len([c for c in claims_data if c['user_id'] == 'policyholder001@example.com'])} claims")
        print(f"   - policyholder002@example.com: {len([c for c in claims_data if c['user_id'] == 'policyholder002@example.com'])} claims")
        print(f"   - adjuster001@example.com: {len([c for c in claims_data if c['user_id'] == 'adjuster001@example.com'])} claims")
        print(f"\n👤 Adjuster assignments:")
        print(f"   - adjuster001@example.com: {len([c for c in claims_data if c['adjuster_user_id'] == 'adjuster001@example.com'])} claims assigned")
        print(f"   - adjuster002@example.com: {len([c for c in claims_data if c['adjuster_user_id'] == 'adjuster002@example.com'])} claims assigned")

def main():
    parser = argparse.ArgumentParser(
        description='Setup Athena database and tables for health lakehouse data processing'
    )
    parser.add_argument(
        '--bucket-name',
        required=False,
        default=None,
        help='Base name for S3 bucket (will be prefixed with {account_id}-{region_name}-). '
             'If not provided, reads from SSM parameter /app/lakehouse-agent/s3-bucket-name. '
             'Example: my-lakehouse'
    )

    args = parser.parse_args()

    bucket_name = args.bucket_name
    
    # If bucket name not provided, try to read from SSM
    if not bucket_name:
        print("📋 No --bucket-name provided, reading from SSM Parameter Store...")
        try:
            session = boto3.Session()
            ssm = boto3.client('ssm', region_name=session.region_name)
            response = ssm.get_parameter(Name='/app/lakehouse-agent/s3-bucket-name')
            full_bucket_name = response['Parameter']['Value']
            print(f"✅ Found bucket name in SSM: {full_bucket_name}")
            
            # Extract the base name by removing the account-region prefix
            # Format is: {account_id}-{region}-{base_name}
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            region = session.region_name
            prefix = f"{account_id}-{region}-"
            
            if full_bucket_name.startswith(prefix):
                bucket_name = full_bucket_name[len(prefix):]
                print(f"   Extracted base name: {bucket_name}")
            else:
                # Use the full bucket name as-is (might be a custom name)
                bucket_name = full_bucket_name
                print(f"   Using full bucket name: {bucket_name}")
                
        except Exception as e:
            print(f"❌ Error reading bucket name from SSM: {e}")
            print("   Please provide --bucket-name argument or set SSM parameter /app/lakehouse-agent/s3-bucket-name")
            sys.exit(1)

    # Run setup
    setup = AthenaSetup(bucket_base_name=bucket_name)
    setup.setup()

if __name__ == '__main__':
    main()
