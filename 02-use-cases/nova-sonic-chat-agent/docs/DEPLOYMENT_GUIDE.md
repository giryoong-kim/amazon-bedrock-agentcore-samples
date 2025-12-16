# Deployment Guide - Nova Sonic Chat Agent

This guide provides detailed instructions for deploying the Nova Sonic Chat Agent to Amazon Bedrock AgentCore Runtime.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Methods](#deployment-methods)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Troubleshooting Deployment Issues](#troubleshooting-deployment-issues)
6. [Rollback Procedures](#rollback-procedures)
7. [Multi-Environment Deployment](#multi-environment-deployment)

## Pre-Deployment Checklist

Before deploying, ensure you have completed:

### AWS Account Setup
- [ ] AWS account with appropriate permissions
- [ ] AWS CLI installed and configured
- [ ] Correct AWS region selected (e.g., us-east-1)
- [ ] IAM permissions to create roles and policies

### Bedrock Access
- [ ] Amazon Bedrock access enabled in your account
- [ ] Model access enabled for Claude 3.5 Sonnet
- [ ] (Optional) Model access enabled for Amazon Nova Sonic 2
- [ ] Bedrock AgentCore access (if in preview/limited access)

### Development Environment
- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] bedrock-agentcore-starter-toolkit installed

### Testing
- [ ] Local testing completed successfully
- [ ] Configuration reviewed and customized
- [ ] System prompt validated

## Deployment Methods

### Method 1: Automated Script (Recommended)

Fastest and easiest method using provided scripts:

```bash
# 1. Set up IAM resources
./deployment/setup-iam.sh

# 2. Deploy the agent
./deployment/deploy.sh
```

**Pros:**
- Automated and consistent
- Error handling included
- Best for CI/CD integration

**Cons:**
- Less control over individual steps
- May need customization for specific requirements

### Method 2: AgentCore CLI

Direct use of AgentCore CLI for more control:

```bash
# 1. Configure
agentcore configure \
  --entrypoint chat_agent.py \
  --name nova-sonic-chat-agent \
  --region us-east-1

# 2. Launch
agentcore launch \
  --role arn:aws:iam::ACCOUNT_ID:role/NovaSonicChatAgentRole \
  --region us-east-1
```

**Pros:**
- Direct control over configuration
- Easy to customize parameters
- Good for iterative development

**Cons:**
- Requires manual IAM setup first
- More steps to remember

### Method 3: Python SDK

Programmatic deployment for advanced use cases:

```python
from deployment.agentcore_config import AgentCoreConfig

# Set up configuration
config = AgentCoreConfig(region='us-east-1')

# Create IAM resources
resources = config.setup_iam_resources()

# Deploy using AgentCore SDK
# (See agentcore_config.py for full implementation)
```

**Pros:**
- Full programmatic control
- Easy to integrate with existing tools
- Can add custom logic

**Cons:**
- More complex
- Requires understanding of SDK

## Step-by-Step Deployment

### Step 1: Environment Preparation

```bash
# Navigate to project directory
cd /path/to/nova-sonic-chat-agent

# Activate virtual environment
source .venv/bin/activate

# Verify AWS credentials
aws sts get-caller-identity

# Set AWS region (if not already set)
export AWS_REGION=us-east-1
```

### Step 2: IAM Resources Setup

#### Option A: Using Script

```bash
./deployment/setup-iam.sh
```

#### Option B: Manual Setup

```bash
# Create IAM role
aws iam create-role \
  --role-name NovaSonicChatAgentRole \
  --assume-role-policy-document file://deployment/trust-policy.json \
  --description "IAM role for Nova Sonic Chat Agent" \
  --tags Key=Project,Value=NovaSonicChatAgent

# Create IAM policy
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws iam create-policy \
  --policy-name NovaSonicChatAgentPolicy \
  --policy-document file://deployment/iam-policy.json \
  --description "Policy for Nova Sonic Chat Agent"

# Attach policy to role
aws iam attach-role-policy \
  --role-name NovaSonicChatAgentRole \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/NovaSonicChatAgentPolicy

# Get and save role ARN
ROLE_ARN=$(aws iam get-role --role-name NovaSonicChatAgentRole --query 'Role.Arn' --output text)
echo $ROLE_ARN > deployment/.role-arn
```

### Step 3: Agent Configuration

```bash
# Configure agent with AgentCore
agentcore configure \
  --entrypoint chat_agent.py \
  --name nova-sonic-chat-agent \
  --region $AWS_REGION \
  --runtime python3.11 \
  --memory 2048 \
  --timeout 300
```

This creates a configuration file (`.agentcore/config.yaml`) with your settings.

### Step 4: Deploy to AgentCore

```bash
# Load role ARN
ROLE_ARN=$(cat deployment/.role-arn)

# Launch the agent
agentcore launch \
  --role $ROLE_ARN \
  --region $AWS_REGION \
  --environment BYPASS_TOOL_CONSENT=true \
  --environment AWS_REGION=$AWS_REGION

# This will:
# 1. Package your agent code
# 2. Upload to S3
# 3. Create AgentCore runtime instance
# 4. Deploy and start the agent
```

### Step 5: Wait for Deployment

```bash
# Monitor deployment status
agentcore status

# The status will progress through:
# - CREATING
# - DEPLOYING
# - ACTIVE (deployment complete)

# Wait for ACTIVE status
while [[ $(agentcore status | grep "Status:" | awk '{print $2}') != "ACTIVE" ]]; do
  echo "Waiting for deployment to complete..."
  sleep 10
done

echo "Deployment complete!"
```

### Step 6: Get Agent Details

```bash
# View full agent details
agentcore describe

# Output includes:
# - Agent ID
# - Endpoint URL
# - Status
# - Configuration
```

## Post-Deployment Verification

### Basic Functionality Test

```bash
# Test 1: Simple greeting
agentcore invoke '{"prompt": "Hello, how are you?"}'

# Expected: Friendly response from agent

# Test 2: Calculation
agentcore invoke '{"prompt": "What is 123 * 456?"}'

# Expected: Correct calculation result

# Test 3: Context awareness
agentcore invoke '{"prompt": "My name is Alex", "session_id": "test-1"}'
agentcore invoke '{"prompt": "What is my name?", "session_id": "test-1"}'

# Expected: Agent remembers and responds with "Alex"
```

### Run Test Suite

```bash
# Get agent ID
AGENT_ID=$(agentcore describe | grep "Agent ID" | awk '{print $3}')

# Run comprehensive tests
python tests/test_deployed.py --agent-id $AGENT_ID --region $AWS_REGION
```

### Verify Monitoring

```bash
# Check CloudWatch logs
aws logs tail /aws/bedrock/agentcore/nova-sonic-chat-agent --follow

# View metrics in CloudWatch console
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock/AgentCore \
  --metric-name Invocations \
  --dimensions Name=AgentName,Value=nova-sonic-chat-agent \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Performance Baseline

```bash
# Run performance tests to establish baseline
python tests/test_deployed.py --agent-id $AGENT_ID --test perf

# Record baseline metrics:
# - Average response time
# - Token usage
# - Error rate
```

## Troubleshooting Deployment Issues

### Issue 1: IAM Permission Errors

**Symptoms:**
```
Error: Access Denied when creating IAM role
```

**Solutions:**
```bash
# Verify your IAM permissions
aws iam get-user

# Required permissions:
# - iam:CreateRole
# - iam:CreatePolicy
# - iam:AttachRolePolicy

# If using an IAM role, verify trust relationship
aws iam get-role --role-name YourCurrentRole
```

### Issue 2: Model Access Denied

**Symptoms:**
```
Error: Access denied to foundation model
```

**Solutions:**
```bash
# Enable model access in Bedrock console
# OR use CLI:
aws bedrock put-model-invocation-logging-configuration \
  --logging-config cloudWatchConfig={logGroupName=/aws/bedrock/modelinvocations,roleArn=arn:aws:iam::ACCOUNT_ID:role/...}
```

### Issue 3: Deployment Timeout

**Symptoms:**
```
Deployment stuck in CREATING state
```

**Solutions:**
```bash
# Check deployment logs
agentcore logs --tail 100

# Cancel and retry
agentcore delete --name nova-sonic-chat-agent
./deployment/deploy.sh
```

### Issue 4: Agent Fails to Start

**Symptoms:**
```
Status: FAILED
```

**Solutions:**
```bash
# View error logs
agentcore logs --tail 50

# Common causes:
# 1. Syntax error in chat_agent.py
# 2. Missing dependencies
# 3. Import errors

# Fix and redeploy:
agentcore update
```

### Issue 5: Network/VPC Issues

**Symptoms:**
```
Error: Cannot connect to Bedrock service
```

**Solutions:**
```bash
# Ensure VPC configuration is correct (if using VPC)
# Check security groups allow outbound HTTPS
# Verify VPC endpoints for Bedrock exist

# For non-VPC deployment:
# Ensure agent has internet access for Bedrock API calls
```

## Rollback Procedures

### Quick Rollback

```bash
# If deployment fails, rollback to previous version
agentcore rollback

# Or delete and redeploy previous version
agentcore delete --name nova-sonic-chat-agent
git checkout <previous-commit>
./deployment/deploy.sh
```

### Complete Removal

```bash
# Use cleanup script
./deployment/cleanup.sh

# This removes:
# - AgentCore instance
# - IAM role and policy
# - Configuration files
```

### Gradual Rollback

For production environments:

```bash
# Deploy new version alongside old version
agentcore configure --name nova-sonic-chat-agent-v2 --entrypoint chat_agent.py
agentcore launch --name nova-sonic-chat-agent-v2 --role $ROLE_ARN

# Test new version
agentcore invoke --name nova-sonic-chat-agent-v2 '{"prompt": "test"}'

# Switch traffic gradually
# (Implement traffic routing at load balancer level)

# Once validated, remove old version
agentcore delete --name nova-sonic-chat-agent
```

## Multi-Environment Deployment

### Setup Multiple Environments

```bash
# Development environment
export AWS_REGION=us-east-1
export ENVIRONMENT=dev
./deployment/deploy.sh

# Staging environment
export AWS_REGION=us-east-1
export ENVIRONMENT=staging
./deployment/deploy.sh

# Production environment
export AWS_REGION=us-east-1
export ENVIRONMENT=production
./deployment/deploy.sh
```

### Environment-Specific Configuration

```yaml
# config.dev.yaml
agent:
  name: nova-sonic-chat-agent-dev
  runtime:
    memory_mb: 1024

# config.production.yaml
agent:
  name: nova-sonic-chat-agent-prod
  runtime:
    memory_mb: 4096
  monitoring:
    cloudwatch_logs:
      retention_days: 30
```

### CI/CD Pipeline Example

```yaml
# .github/workflows/deploy.yml
name: Deploy Agent

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy to AgentCore
        run: |
          ./deployment/setup-iam.sh
          ./deployment/deploy.sh
      
      - name: Run tests
        run: |
          python tests/test_deployed.py --agent-id ${{ steps.deploy.outputs.agent-id }}
```

## Best Practices

1. **Version Control**: Tag releases before deployment
2. **Testing**: Always test in dev/staging before production
3. **Monitoring**: Set up alarms before deploying to production
4. **Documentation**: Keep deployment notes for each release
5. **Backups**: Save configuration and IAM policies
6. **Gradual Rollout**: Use canary deployments for production
7. **Rollback Plan**: Always have a rollback strategy ready

## Next Steps

After successful deployment:

1. [Configure monitoring and alerts](./MONITORING.md)
2. [Set up logging and observability](./OBSERVABILITY.md)
3. [Integrate with your application](./INTEGRATION_GUIDE.md)
4. [Optimize performance](./PERFORMANCE_TUNING.md)

---

For questions or issues, refer to the [main README](../README.md) or open an issue in the repository.
