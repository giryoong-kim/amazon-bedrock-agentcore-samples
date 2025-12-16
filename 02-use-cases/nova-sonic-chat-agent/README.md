# Nova Sonic 2 Chat Agent

A production-ready conversational AI chat agent built with [Strands Agents framework](https://github.com/strands-ai/strands-agents) and deployed on [Amazon Bedrock AgentCore Runtime](https://aws.amazon.com/bedrock/agentcore/). This agent leverages the Amazon Nova Sonic 2 model to deliver natural, context-aware conversational experiences.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Usage](#usage)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

The Nova Sonic 2 Chat Agent is designed to provide intelligent, conversational AI capabilities through Amazon Bedrock AgentCore's serverless runtime. It combines the power of:

- **Amazon Nova Sonic 2**: Advanced conversational AI model with natural language understanding
- **Strands Agents Framework**: Flexible agent orchestration with tool integration
- **Amazon Bedrock AgentCore**: Managed, serverless deployment platform for AI agents

### Key Capabilities

- ✅ Natural, multi-turn conversations with context awareness
- ✅ Real-time streaming responses for better user experience
- ✅ Built-in tools (calculator, web search) for enhanced functionality
- ✅ Session management for conversation continuity
- ✅ Production-ready deployment with observability
- ✅ Automatic scaling and high availability

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Application                       │
│                  (Web, Mobile, Voice, etc.)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTPS/WebSocket
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Amazon Bedrock AgentCore                        │
│                  (Serverless Runtime)                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Nova Sonic Chat Agent (Strands)              │  │
│  │                                                       │  │
│  │  ├─ System Prompt & Configuration                    │  │
│  │  ├─ Conversation Context Manager                     │  │
│  │  ├─ Tool Integration (Calculator, Web Search)        │  │
│  │  └─ Streaming Response Handler                       │  │
│  └──────────────────┬───────────────────────────────────┘  │
└─────────────────────┼──────────────────────────────────────┘
                      │
                      │ Bedrock API
                      │
┌─────────────────────▼──────────────────────────────────────┐
│                  Amazon Bedrock                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Claude 3.5 Sonnet (via Bedrock)                   │    │
│  │  or Nova Sonic 2 Model                             │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                      │
                      │
        ┌─────────────┴──────────────┐
        │                            │
┌───────▼──────┐           ┌─────────▼────────┐
│  CloudWatch  │           │    AWS X-Ray      │
│   Logs &     │           │    Tracing        │
│   Metrics    │           │                   │
└──────────────┘           └──────────────────┘
```

### Component Interaction Flow

1. **Client Request**: User sends a message through the client application
2. **AgentCore Runtime**: Receives request and invokes the chat agent
3. **Strands Agent**: Processes message with context and system prompt
4. **Tool Execution**: Invokes tools (calculator, web search) if needed
5. **Model Inference**: Calls Bedrock model (Claude 3.5 or Nova Sonic 2)
6. **Streaming Response**: Returns response chunks in real-time
7. **Observability**: Logs and metrics sent to CloudWatch and X-Ray

## Features

### Conversational AI
- **Multi-turn Conversations**: Maintains context across conversation turns
- **Intent Understanding**: Accurately interprets user intent and queries
- **Natural Responses**: Human-like, conversational response generation
- **Clarification**: Asks follow-up questions when needed

### Tool Integration
- **Calculator**: Performs mathematical calculations and financial computations
- **Web Search**: Retrieves current information from the web (when enabled)
- **Extensible**: Easy to add custom tools for your use case

### Production-Ready
- **Streaming Support**: Real-time response streaming for better UX
- **Session Management**: Tracks conversations across multiple turns
- **Error Handling**: Graceful error handling with informative messages
- **Observability**: Built-in CloudWatch Logs, Metrics, and X-Ray tracing
- **Security**: IAM-based authentication and authorization

### Deployment
- **Serverless**: Fully managed by AgentCore Runtime
- **Auto-scaling**: Automatically scales based on demand
- **High Availability**: Multi-AZ deployment for reliability
- **Easy Updates**: Simple deployment updates with version control

## Prerequisites

Before deploying the Nova Sonic Chat Agent, ensure you have:

### AWS Account Requirements
- AWS account with appropriate permissions
- Access to Amazon Bedrock
- Access to Amazon Bedrock AgentCore (preview/GA)
- IAM permissions to create roles and policies

### Model Access
Enable model access in Amazon Bedrock console:
1. Navigate to Amazon Bedrock console
2. Go to "Model access" section
3. Enable access for:
   - `Anthropic Claude 3.5 Sonnet` (for development)
   - `Amazon Nova Sonic 2` (for voice capabilities)

### Development Environment
- **Python 3.10+** installed on your machine
- **AWS CLI** configured with appropriate credentials
- **pip** or **uv** for Python package management
- **Git** for version control

### Required Tools
```bash
# Install AWS CLI
pip install awscli

# Install bedrock-agentcore-starter-toolkit
pip install bedrock-agentcore-starter-toolkit

# Verify installations
aws --version
agentcore --version
```

## Installation

### 1. Clone the Repository

```bash
cd /path/to/amazon-bedrock-agentcore-samples
cd 02-use-cases/nova-sonic-chat-agent
```

### 2. Create Virtual Environment

Using `venv`:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Or using `uv` (recommended):
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using uv (faster)
uv pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "import strands; import bedrock_agentcore; print('✓ Installation successful')"
```

## Configuration

### 1. Review Configuration File

The `config.yaml` file contains all configurable parameters:

```yaml
agent:
  name: nova-sonic-chat-agent
  model:
    model_id: "anthropic.claude-3-5-sonnet-20241022-v2:0"
    temperature: 0.7
    max_tokens: 4096
```

### 2. Customize System Prompt (Optional)

Edit `chat_agent.py` to customize the system prompt:

```python
SYSTEM_PROMPT = """You are a helpful and friendly AI assistant..."""
```

### 3. Configure AWS Region

Set your preferred AWS region:

```bash
export AWS_REGION=us-east-1
# Or edit config.yaml
```

### 4. Environment Variables

Create a `.env` file (optional):

```env
AWS_REGION=us-east-1
AWS_PROFILE=default
BYPASS_TOOL_CONSENT=true
LOG_LEVEL=INFO
```

## Deployment

### Quick Deployment (Recommended)

Use the automated deployment scripts:

```bash
# Step 1: Set up IAM resources
./deployment/setup-iam.sh

# Step 2: Deploy the agent
./deployment/deploy.sh
```

### Manual Deployment

#### Step 1: Create IAM Resources

```bash
# Create IAM role
aws iam create-role \
  --role-name NovaSonicChatAgentRole \
  --assume-role-policy-document file://deployment/trust-policy.json

# Create IAM policy
aws iam create-policy \
  --policy-name NovaSonicChatAgentPolicy \
  --policy-document file://deployment/iam-policy.json

# Attach policy to role
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws iam attach-role-policy \
  --role-name NovaSonicChatAgentRole \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/NovaSonicChatAgentPolicy
```

#### Step 2: Configure Agent

```bash
agentcore configure \
  --entrypoint chat_agent.py \
  --name nova-sonic-chat-agent \
  --region us-east-1
```

#### Step 3: Launch Agent

```bash
# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name NovaSonicChatAgentRole --query 'Role.Arn' --output text)

# Launch agent
agentcore launch \
  --role $ROLE_ARN \
  --region us-east-1
```

#### Step 4: Verify Deployment

```bash
# Check agent status
agentcore status

# View agent details
agentcore describe
```

### Python-based Deployment

Alternatively, use the Python configuration script:

```bash
# Set up IAM resources
python deployment/agentcore_config.py --region us-east-1

# Then deploy with agentcore CLI
./deployment/deploy.sh
```

## Usage

### Quick Start

Test your deployed agent:

```bash
# Simple test
agentcore invoke '{"prompt": "Hello, how are you?"}'

# With session ID
agentcore invoke '{"prompt": "My name is Alex", "session_id": "user-123"}'

# Follow-up message (same session)
agentcore invoke '{"prompt": "What is my name?", "session_id": "user-123"}'
```

### Using the Agent in Your Application

#### Python Integration

```python
import boto3
import json

# Initialize Bedrock Agent Runtime client
client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# Send a message
response = client.invoke_agent(
    agentId='your-agent-id',
    sessionId='user-session-123',
    inputText=json.dumps({
        "prompt": "Hello, how can you help me?",
        "session_id": "user-session-123"
    })
)

# Process streaming response
for event in response['completion']:
    if 'chunk' in event:
        chunk = event['chunk']
        if 'bytes' in chunk:
            print(chunk['bytes'].decode('utf-8'), end='', flush=True)
```

#### REST API Integration

```javascript
// JavaScript/TypeScript example
const invokeAgent = async (message, sessionId) => {
  const response = await fetch('https://your-agent-endpoint.execute-api.us-east-1.amazonaws.com/prod/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_TOKEN'
    },
    body: JSON.stringify({
      prompt: message,
      session_id: sessionId
    })
  });
  
  return await response.json();
};

// Usage
const result = await invokeAgent('Hello!', 'session-123');
console.log(result.response);
```

#### cURL Example

```bash
curl -X POST https://your-agent-endpoint.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "prompt": "What can you help me with?",
    "session_id": "test-session"
  }'
```

### Payload Format

#### Request Payload

```json
{
  "prompt": "User message here",
  "session_id": "unique-session-id",
  "conversation_history": [
    {
      "role": "user",
      "content": "Previous user message"
    },
    {
      "role": "assistant",
      "content": "Previous assistant response"
    }
  ]
}
```

#### Response Format

```json
{
  "status": "success",
  "response": "Agent response message",
  "session_id": "unique-session-id",
  "model": "nova-sonic-2"
}
```

### Example Conversations

See `examples/basic_usage.py` for comprehensive usage examples:

```bash
python examples/basic_usage.py
```

## Testing

### Local Testing

Test the agent locally before deployment:

```bash
# Run all local tests
python tests/test_local.py

# Run specific test
python tests/test_local.py --test basic

# Interactive mode
python tests/test_local.py --interactive
```

### Testing Deployed Agent

Test the agent after deployment:

```bash
# Get your agent ID
AGENT_ID=$(agentcore describe | grep "Agent ID" | awk '{print $3}')

# Run deployment tests
python tests/test_deployed.py --agent-id $AGENT_ID --region us-east-1

# Run specific test suite
python tests/test_deployed.py --agent-id $AGENT_ID --test basic
```

### AgentCore CLI Testing

```bash
# Basic invocation
agentcore invoke '{"prompt": "Hello!"}'

# Test calculation
agentcore invoke '{"prompt": "What is 234 * 567?"}'

# Test context awareness
agentcore invoke '{"prompt": "My name is Sarah", "session_id": "test-1"}'
agentcore invoke '{"prompt": "What is my name?", "session_id": "test-1"}'

# View logs
agentcore logs --tail 50
```

### Load Testing

For production readiness, conduct load testing:

```bash
# Using Apache Bench
ab -n 1000 -c 10 -p payload.json -T application/json \
  https://your-agent-endpoint.execute-api.us-east-1.amazonaws.com/prod/chat

# Using Locust
locust -f tests/load_test.py --host=https://your-agent-endpoint
```

## Monitoring

### CloudWatch Logs

View agent logs in CloudWatch:

```bash
# Using AWS CLI
aws logs tail /aws/bedrock/agentcore/nova-sonic-chat-agent --follow

# Or use AgentCore CLI
agentcore logs --follow
```

### CloudWatch Metrics

Monitor agent performance:

- **Invocation Count**: Number of agent invocations
- **Invocation Duration**: Time taken to process requests
- **Error Count**: Number of failed invocations
- **Token Usage**: Bedrock API token consumption

Access metrics in CloudWatch console:
1. Navigate to CloudWatch
2. Select "Metrics"
3. Choose namespace: `AWS/Bedrock/AgentCore`

### X-Ray Tracing

View distributed traces:

```bash
# AWS Console
1. Navigate to AWS X-Ray console
2. View Service Map
3. Analyze traces for nova-sonic-chat-agent
```

### Custom Dashboards

Create CloudWatch dashboards:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name NovaSonicChatAgentDashboard \
  --dashboard-body file://monitoring/dashboard.json
```

### Alarms

Set up CloudWatch alarms for critical metrics:

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name nova-sonic-high-error-rate \
  --alarm-description "Alert when error rate exceeds threshold" \
  --metric-name Errors \
  --namespace AWS/Bedrock/AgentCore \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

## Customization

### Adding Custom Tools

Create custom tools for your use case:

```python
# In chat_agent.py

from strands_tools import tool

@tool
def get_user_data(user_id: str) -> dict:
    """Retrieve user data from your database."""
    # Your custom logic here
    return {"user_id": user_id, "name": "Example User"}

# Add to agent initialization
agent = Agent(
    tools=[calculator, web_search, get_user_data],
    system_prompt=SYSTEM_PROMPT
)
```

### Modifying System Prompt

Customize the agent's behavior by editing the system prompt:

```python
SYSTEM_PROMPT = """You are a specialized customer support assistant for ACME Corp.

Your responsibilities:
- Answer questions about ACME products
- Help troubleshoot common issues
- Escalate complex cases to human agents

Guidelines:
- Always be professional and courteous
- Use the customer's name when known
- Provide step-by-step instructions
"""
```

### Integrating with Your Backend

Connect the agent to your backend services:

```python
import requests

@tool
async def check_order_status(order_id: str) -> dict:
    """Check order status from backend API."""
    response = requests.get(
        f"https://api.yourcompany.com/orders/{order_id}",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    return response.json()
```

### Custom Response Formatting

Add custom response formatting:

```python
@app.entrypoint
async def chat_invocation(payload: Dict[str, Any], context: Any):
    # ... existing code ...
    
    async for event in agent_stream:
        # Add custom formatting
        formatted_event = {
            "content": event,
            "timestamp": time.time(),
            "agent_version": "1.0.0"
        }
        yield formatted_event
```

### Environment-Specific Configuration

Use different configurations for dev/staging/prod:

```bash
# Load configuration based on environment
export ENVIRONMENT=production
python deployment/deploy.sh --config config.${ENVIRONMENT}.yaml
```

## Troubleshooting

### Common Issues

#### 1. Agent Not Responding

**Symptoms**: Agent invocations timeout or return no response

**Solutions**:
```bash
# Check agent status
agentcore status

# View recent logs
agentcore logs --tail 100

# Verify IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn $(aws iam get-role --role-name NovaSonicChatAgentRole --query 'Role.Arn' --output text) \
  --action-names bedrock:InvokeModel
```

#### 2. Model Access Denied

**Symptoms**: Error: "Access denied to model"

**Solutions**:
1. Verify model access in Bedrock console
2. Check IAM policy includes model ARN
3. Ensure model is available in your region

```bash
# List available models
aws bedrock list-foundation-models --region us-east-1
```

#### 3. High Latency

**Symptoms**: Responses take too long

**Solutions**:
- Enable streaming for faster perceived response time
- Reduce model max_tokens parameter
- Check CloudWatch metrics for bottlenecks
- Consider caching frequent queries

#### 4. Memory Errors

**Symptoms**: "Out of memory" errors in logs

**Solutions**:
```yaml
# Increase memory in config.yaml
agent:
  runtime:
    memory_mb: 4096  # Increase from 2048
```

#### 5. Tool Execution Failures

**Symptoms**: Tools not being invoked or failing

**Solutions**:
```bash
# Check tool permissions
# Verify BYPASS_TOOL_CONSENT is set
echo $BYPASS_TOOL_CONSENT

# Test tool locally
python -c "from strands_tools import calculator; print(calculator('2 + 2'))"
```

### Debugging

Enable debug logging:

```python
# In chat_agent.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

View detailed traces:

```bash
# Enable X-Ray debugging
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --filter-expression 'service(name: "nova-sonic-chat-agent")'
```

### Getting Help

- **AWS Support**: Contact AWS Support for infrastructure issues
- **Bedrock Documentation**: [Amazon Bedrock Docs](https://docs.aws.amazon.com/bedrock/)
- **Strands GitHub**: [Strands Agents Issues](https://github.com/strands-ai/strands-agents/issues)
- **Community**: AWS Developer Forums

## Best Practices

### Security
- ✅ Use IAM roles with least privilege principle
- ✅ Enable encryption at rest and in transit
- ✅ Rotate credentials regularly
- ✅ Implement request throttling and rate limiting
- ✅ Validate and sanitize user inputs

### Performance
- ✅ Enable streaming for better user experience
- ✅ Implement caching for frequent queries
- ✅ Monitor and optimize token usage
- ✅ Use appropriate model size for your use case
- ✅ Set reasonable timeout values

### Cost Optimization
- ✅ Set appropriate max_tokens to avoid unnecessary costs
- ✅ Use model that fits your needs (don't over-provision)
- ✅ Implement request caching
- ✅ Monitor usage with CloudWatch metrics
- ✅ Set up billing alarms

### Reliability
- ✅ Implement retry logic with exponential backoff
- ✅ Set up CloudWatch alarms for critical metrics
- ✅ Use multiple availability zones
- ✅ Implement circuit breakers for external dependencies
- ✅ Regular backup and disaster recovery testing

## Cleanup

To remove all deployed resources:

```bash
# Using cleanup script
./deployment/cleanup.sh

# Manual cleanup
agentcore delete --name nova-sonic-chat-agent
aws iam detach-role-policy --role-name NovaSonicChatAgentRole --policy-arn $(aws iam list-attached-role-policies --role-name NovaSonicChatAgentRole --query 'AttachedPolicies[0].PolicyArn' --output text)
aws iam delete-policy --policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/NovaSonicChatAgentPolicy
aws iam delete-role --role-name NovaSonicChatAgentRole
```

## Contributing

Contributions are welcome! Please see the main repository [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT-0 License. See the [LICENSE](../../LICENSE) file for details.

## Additional Resources

- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Strands Agents Framework](https://github.com/strands-ai/strands-agents)
- [Amazon Nova Models](https://aws.amazon.com/ai/generative-ai/nova/)
- [Bedrock AgentCore Samples Repository](https://github.com/aws-samples/amazon-bedrock-agentcore-samples)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## Support

For issues and questions:
- Open an issue in the repository
- Contact AWS Support for infrastructure issues
- Check AWS Developer Forums for community support

---

**Note**: This is a sample implementation demonstrating the integration patterns. Adapt the code and configuration to your specific use case and security requirements.
