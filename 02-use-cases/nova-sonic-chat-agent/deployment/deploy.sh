#!/bin/bash

# Deploy Nova Sonic Chat Agent to Amazon Bedrock AgentCore
# This script uses the bedrock-agentcore-starter-toolkit to deploy the agent

set -e

# Configuration
AGENT_NAME="nova-sonic-chat-agent"
REGION="${AWS_REGION:-us-east-1}"

echo "================================================"
echo "Deploying Nova Sonic Chat Agent to AgentCore"
echo "================================================"
echo "Agent Name: $AGENT_NAME"
echo "Region: $REGION"
echo ""

# Get the project root directory (parent of deployment directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Check if IAM role has been created
if [ ! -f "$SCRIPT_DIR/.role-arn" ]; then
    echo "❌ Error: IAM role not found. Please run setup-iam.sh first."
    exit 1
fi

ROLE_ARN=$(cat "$SCRIPT_DIR/.role-arn")
echo "Using IAM Role: $ROLE_ARN"
echo ""

# Check if agentcore CLI is installed
if ! command -v agentcore &> /dev/null; then
    echo "❌ Error: agentcore CLI not found. Please install it with:"
    echo "   pip install bedrock-agentcore-starter-toolkit"
    exit 1
fi

# Step 1: Configure the agent
echo "Step 1: Configuring agent..."
agentcore configure \
    --entrypoint chat_agent.py \
    --name "$AGENT_NAME" \
    --region "$REGION"

echo "✓ Agent configured"
echo ""

# Step 2: Launch the agent
echo "Step 2: Launching agent to AgentCore Runtime..."
agentcore launch \
    --role "$ROLE_ARN" \
    --region "$REGION"

echo ""
echo "================================================"
echo "Deployment Complete!"
echo "================================================"
echo ""
echo "Your Nova Sonic Chat Agent has been deployed to AgentCore Runtime."
echo ""
echo "To test your agent, run:"
echo "  agentcore invoke '{\"prompt\": \"Hello, how are you?\"}'"
echo ""
echo "To check agent status:"
echo "  agentcore status"
echo ""
echo "To view agent logs:"
echo "  agentcore logs"
echo "================================================"
