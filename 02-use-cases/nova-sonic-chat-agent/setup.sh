#!/bin/bash

# Setup script for Nova Sonic Chat Agent
# This script prepares your environment for development and deployment

set -e

echo "================================================"
echo "Nova Sonic Chat Agent - Setup"
echo "================================================"
echo ""

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

echo "Checking Python version..."
if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo "❌ Error: Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi
echo "✓ Python version: $PYTHON_VERSION"
echo ""

# Check AWS CLI
echo "Checking AWS CLI..."
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI not found. Please install it:"
    echo "   pip install awscli"
    exit 1
fi
AWS_VERSION=$(aws --version 2>&1 | awk '{print $1}')
echo "✓ AWS CLI: $AWS_VERSION"
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS credentials not configured. Please run:"
    echo "   aws configure"
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✓ AWS Account: $ACCOUNT_ID"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    
    # Try to use uv first, fall back to venv
    if command -v uv &> /dev/null; then
        echo "Using uv for faster environment setup..."
        uv venv
    else
        echo "Using standard venv..."
        python -m venv .venv
    fi
    
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate || source .venv/Scripts/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv for faster package installation..."
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi
echo "✓ Dependencies installed"
echo ""

# Check if bedrock-agentcore-starter-toolkit is installed
echo "Checking bedrock-agentcore-starter-toolkit..."
if ! command -v agentcore &> /dev/null; then
    echo "⚠ Warning: agentcore CLI not found in PATH"
    echo "  Installing bedrock-agentcore-starter-toolkit..."
    pip install bedrock-agentcore-starter-toolkit
fi
echo "✓ AgentCore toolkit ready"
echo ""

# Verify Bedrock model access
echo "Checking Amazon Bedrock model access..."
if aws bedrock list-foundation-models --region ${AWS_REGION:-us-east-1} &> /dev/null; then
    echo "✓ Bedrock access confirmed"
    
    # Check specific model access
    if aws bedrock list-foundation-models --region ${AWS_REGION:-us-east-1} \
        --query 'modelSummaries[?contains(modelId, `claude-3-5-sonnet`)]' --output text &> /dev/null; then
        echo "✓ Claude 3.5 Sonnet model available"
    else
        echo "⚠ Warning: Claude 3.5 Sonnet model access not confirmed"
        echo "  Please enable model access in Bedrock console"
    fi
else
    echo "⚠ Warning: Could not verify Bedrock access"
    echo "  Please ensure you have access to Amazon Bedrock"
fi
echo ""

# Create necessary directories
echo "Creating project directories..."
mkdir -p logs
mkdir -p tmp
echo "✓ Directories created"
echo ""

# Run a quick test
echo "Running quick validation test..."
python -c "
import sys
try:
    import strands
    import bedrock_agentcore
    import boto3
    print('✓ All required packages imported successfully')
    sys.exit(0)
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
echo ""

echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Review configuration: config.yaml"
echo "2. Test locally: python tests/test_local.py --interactive"
echo "3. Set up IAM: ./deployment/setup-iam.sh"
echo "4. Deploy agent: ./deployment/deploy.sh"
echo ""
echo "For more information, see README.md"
echo "================================================"
