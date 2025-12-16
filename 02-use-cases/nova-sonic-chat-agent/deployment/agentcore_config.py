"""
AgentCore Configuration for Nova Sonic Chat Agent

This module provides programmatic configuration and deployment utilities
for the Nova Sonic Chat Agent on Amazon Bedrock AgentCore Runtime.
"""

import os
import json
import boto3
from typing import Dict, Any, Optional
from pathlib import Path


class AgentCoreConfig:
    """Configuration manager for AgentCore deployment."""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize AgentCore configuration.
        
        Args:
            region: AWS region for deployment (default: us-east-1)
        """
        self.region = region
        self.iam_client = boto3.client('iam', region_name=region)
        self.bedrock_client = boto3.client('bedrock', region_name=region)
        self.sts_client = boto3.client('sts', region_name=region)
        
        # Get project paths
        self.deployment_dir = Path(__file__).parent
        self.project_dir = self.deployment_dir.parent
        
    def get_account_id(self) -> str:
        """Get AWS account ID."""
        return self.sts_client.get_caller_identity()['Account']
    
    def create_iam_role(self, role_name: str = "NovaSonicChatAgentRole") -> str:
        """
        Create IAM role for the agent.
        
        Args:
            role_name: Name for the IAM role
            
        Returns:
            Role ARN
        """
        trust_policy_path = self.deployment_dir / "trust-policy.json"
        with open(trust_policy_path, 'r') as f:
            trust_policy = json.load(f)
        
        try:
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="IAM role for Nova Sonic Chat Agent on Bedrock AgentCore",
                Tags=[
                    {'Key': 'Project', 'Value': 'NovaSonicChatAgent'},
                    {'Key': 'ManagedBy', 'Value': 'AgentCore'}
                ]
            )
            print(f"✓ Created IAM role: {role_name}")
            return response['Role']['Arn']
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            response = self.iam_client.get_role(RoleName=role_name)
            print(f"✓ IAM role already exists: {role_name}")
            return response['Role']['Arn']
    
    def create_iam_policy(self, policy_name: str = "NovaSonicChatAgentPolicy") -> str:
        """
        Create IAM policy for the agent.
        
        Args:
            policy_name: Name for the IAM policy
            
        Returns:
            Policy ARN
        """
        policy_path = self.deployment_dir / "iam-policy.json"
        with open(policy_path, 'r') as f:
            policy_document = json.load(f)
        
        account_id = self.get_account_id()
        policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
        
        try:
            response = self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description="Policy for Nova Sonic Chat Agent to access Bedrock and related services",
                Tags=[
                    {'Key': 'Project', 'Value': 'NovaSonicChatAgent'},
                    {'Key': 'ManagedBy', 'Value': 'AgentCore'}
                ]
            )
            print(f"✓ Created IAM policy: {policy_name}")
            return response['Policy']['Arn']
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            print(f"✓ IAM policy already exists: {policy_name}")
            return policy_arn
    
    def attach_policy_to_role(
        self,
        role_name: str = "NovaSonicChatAgentRole",
        policy_arn: Optional[str] = None
    ):
        """
        Attach IAM policy to role.
        
        Args:
            role_name: Name of the IAM role
            policy_arn: ARN of the policy to attach
        """
        if not policy_arn:
            account_id = self.get_account_id()
            policy_arn = f"arn:aws:iam::{account_id}:policy/NovaSonicChatAgentPolicy"
        
        try:
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"✓ Attached policy to role")
        except Exception as e:
            if "already attached" in str(e).lower():
                print(f"✓ Policy already attached to role")
            else:
                raise
    
    def setup_iam_resources(self) -> Dict[str, str]:
        """
        Set up all IAM resources needed for the agent.
        
        Returns:
            Dictionary with role_arn and policy_arn
        """
        print("Setting up IAM resources...")
        
        role_arn = self.create_iam_role()
        policy_arn = self.create_iam_policy()
        self.attach_policy_to_role(policy_arn=policy_arn)
        
        # Save role ARN for use by shell scripts
        role_arn_file = self.deployment_dir / ".role-arn"
        with open(role_arn_file, 'w') as f:
            f.write(role_arn)
        
        print("\n✓ IAM setup complete")
        return {
            'role_arn': role_arn,
            'policy_arn': policy_arn
        }
    
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get agent configuration for deployment.
        
        Returns:
            Agent configuration dictionary
        """
        return {
            'name': 'nova-sonic-chat-agent',
            'entrypoint': 'chat_agent.py',
            'runtime': 'python3.11',
            'region': self.region,
            'environment': {
                'BYPASS_TOOL_CONSENT': 'true',
                'AWS_REGION': self.region
            },
            'memory_size': 2048,
            'timeout': 300
        }


def main():
    """Main entry point for configuration script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Configure IAM resources for Nova Sonic Chat Agent'
    )
    parser.add_argument(
        '--region',
        default=os.environ.get('AWS_REGION', 'us-east-1'),
        help='AWS region (default: us-east-1)'
    )
    
    args = parser.parse_args()
    
    # Setup configuration
    config = AgentCoreConfig(region=args.region)
    
    print("=" * 50)
    print("Nova Sonic Chat Agent - IAM Configuration")
    print("=" * 50)
    print(f"Region: {args.region}\n")
    
    # Setup IAM resources
    resources = config.setup_iam_resources()
    
    print("\n" + "=" * 50)
    print("Configuration Complete!")
    print("=" * 50)
    print(f"Role ARN: {resources['role_arn']}")
    print(f"Policy ARN: {resources['policy_arn']}")
    print("\nNext steps:")
    print("1. Run: ./deploy.sh")
    print("   or")
    print("2. Use agentcore CLI: agentcore configure -e ../chat_agent.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
