#!/bin/bash

# Setup IAM Role and Policies for Nova Sonic Chat Agent
# This script creates the necessary IAM resources for deploying the agent on AgentCore Runtime

set -e

# Configuration
ROLE_NAME="NovaSonicChatAgentRole"
POLICY_NAME="NovaSonicChatAgentPolicy"
REGION="${AWS_REGION:-us-east-1}"

echo "================================================"
echo "Setting up IAM resources for Nova Sonic Chat Agent"
echo "================================================"
echo "Region: $REGION"
echo "Role Name: $ROLE_NAME"
echo "Policy Name: $POLICY_NAME"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if role already exists
if aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
    echo "✓ IAM Role '$ROLE_NAME' already exists"
else
    echo "Creating IAM Role '$ROLE_NAME'..."
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://"$SCRIPT_DIR"/trust-policy.json \
        --description "IAM role for Nova Sonic Chat Agent on Bedrock AgentCore" \
        --tags Key=Project,Value=NovaSonicChatAgent Key=ManagedBy,Value=AgentCore
    echo "✓ IAM Role created successfully"
fi

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Check if policy already exists
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"
if aws iam get-policy --policy-arn "$POLICY_ARN" 2>/dev/null; then
    echo "✓ IAM Policy '$POLICY_NAME' already exists"
    
    # Update policy with new version
    echo "Updating IAM Policy..."
    aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document file://"$SCRIPT_DIR"/iam-policy.json \
        --set-as-default
    echo "✓ IAM Policy updated successfully"
else
    echo "Creating IAM Policy '$POLICY_NAME'..."
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file://"$SCRIPT_DIR"/iam-policy.json \
        --description "Policy for Nova Sonic Chat Agent to access Bedrock and related services" \
        --tags Key=Project,Value=NovaSonicChatAgent Key=ManagedBy,Value=AgentCore
    echo "✓ IAM Policy created successfully"
fi

# Attach policy to role
echo "Attaching policy to role..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN" 2>/dev/null || echo "Policy already attached"
echo "✓ Policy attached to role"

# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)

echo ""
echo "================================================"
echo "IAM Setup Complete!"
echo "================================================"
echo "Role ARN: $ROLE_ARN"
echo ""
echo "Next steps:"
echo "1. Wait a few seconds for IAM propagation"
echo "2. Run the deployment script: ./deploy.sh"
echo "================================================"

# Save role ARN to file for use by other scripts
echo "$ROLE_ARN" > "$SCRIPT_DIR"/.role-arn
