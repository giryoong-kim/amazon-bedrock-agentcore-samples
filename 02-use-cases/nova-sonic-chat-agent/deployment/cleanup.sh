#!/bin/bash

# Cleanup script for Nova Sonic Chat Agent
# This script removes the deployed agent and associated IAM resources

set -e

# Configuration
AGENT_NAME="nova-sonic-chat-agent"
ROLE_NAME="NovaSonicChatAgentRole"
POLICY_NAME="NovaSonicChatAgentPolicy"
REGION="${AWS_REGION:-us-east-1}"

echo "================================================"
echo "Cleaning up Nova Sonic Chat Agent Resources"
echo "================================================"
echo ""

read -p "Are you sure you want to delete all resources? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Get the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Step 1: Delete the agent from AgentCore
if command -v agentcore &> /dev/null; then
    echo "Step 1: Deleting agent from AgentCore Runtime..."
    agentcore delete --name "$AGENT_NAME" --region "$REGION" 2>/dev/null || echo "Agent not found or already deleted"
    echo "✓ Agent deleted"
else
    echo "⚠ agentcore CLI not found, skipping agent deletion"
fi
echo ""

# Step 2: Detach and delete IAM policy
echo "Step 2: Cleaning up IAM resources..."

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

# Detach policy from role
echo "Detaching policy from role..."
aws iam detach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN" 2>/dev/null || echo "Policy not attached"

# Delete all non-default policy versions
echo "Deleting policy versions..."
for version in $(aws iam list-policy-versions --policy-arn "$POLICY_ARN" --query 'Versions[?!IsDefaultVersion].VersionId' --output text 2>/dev/null); do
    aws iam delete-policy-version --policy-arn "$POLICY_ARN" --version-id "$version" 2>/dev/null || true
done

# Delete policy
echo "Deleting IAM policy..."
aws iam delete-policy --policy-arn "$POLICY_ARN" 2>/dev/null || echo "Policy not found"

# Delete role
echo "Deleting IAM role..."
aws iam delete-role --role-name "$ROLE_NAME" 2>/dev/null || echo "Role not found"

echo "✓ IAM resources cleaned up"
echo ""

# Step 3: Clean up local files
echo "Step 3: Cleaning up local configuration files..."
rm -f "$SCRIPT_DIR/.role-arn"
rm -rf "$PROJECT_DIR/.agentcore"
echo "✓ Local files cleaned up"
echo ""

echo "================================================"
echo "Cleanup Complete!"
echo "================================================"
echo "All Nova Sonic Chat Agent resources have been removed."
echo "================================================"
