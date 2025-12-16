# Quick Start Guide - Nova Sonic Chat Agent

Get your Nova Sonic Chat Agent up and running in 10 minutes!

## Prerequisites

- AWS account with Bedrock access
- Python 3.10+
- AWS CLI configured

## 5-Minute Setup

### 1. Navigate to Project

```bash
cd /path/to/amazon-bedrock-agentcore-samples/02-use-cases/nova-sonic-chat-agent
```

### 2. Run Setup Script

```bash
./setup.sh
```

This will:
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Verify AWS credentials
- ✅ Check Bedrock access

### 3. Deploy to AgentCore

```bash
# Set up IAM resources (one-time)
./deployment/setup-iam.sh

# Deploy the agent
./deployment/deploy.sh
```

### 4. Test Your Agent

```bash
# Simple test
agentcore invoke '{"prompt": "Hello, how are you?"}'

# With context
agentcore invoke '{"prompt": "My name is Alex", "session_id": "test-1"}'
agentcore invoke '{"prompt": "What is my name?", "session_id": "test-1"}'
```

## What You Get

✅ **Production-ready chat agent** deployed on AWS  
✅ **Streaming responses** for real-time interaction  
✅ **Built-in tools** (calculator, web search)  
✅ **Session management** for multi-turn conversations  
✅ **Full observability** with CloudWatch logs & metrics  

## Next Steps

### Customize Your Agent

Edit `chat_agent.py` to change the system prompt:

```python
SYSTEM_PROMPT = """You are a helpful assistant for [YOUR COMPANY].
Your role is to...
"""
```

Then redeploy:

```bash
./deployment/deploy.sh
```

### Test Locally First

Before deploying, test locally:

```bash
python tests/test_local.py --interactive
```

### View Logs

```bash
agentcore logs --follow
```

### Check Status

```bash
agentcore status
```

## Common Commands

```bash
# Invoke agent
agentcore invoke '{"prompt": "YOUR_MESSAGE"}'

# View logs
agentcore logs --tail 50

# Check status
agentcore status

# Update agent
agentcore update

# Delete agent
agentcore delete --name nova-sonic-chat-agent
```

## Troubleshooting

### "Command 'agentcore' not found"

```bash
pip install bedrock-agentcore-starter-toolkit
```

### "Access Denied" errors

Enable model access in Amazon Bedrock console:
1. Go to Bedrock console
2. Click "Model access"
3. Enable Claude 3.5 Sonnet

### Agent not responding

```bash
# Check logs
agentcore logs --tail 100

# Verify status
agentcore status
```

## Learn More

- 📖 [Full Documentation](./README.md)
- 🚀 [Deployment Guide](./docs/DEPLOYMENT_GUIDE.md)
- 🛠️ [Customization Guide](./docs/CUSTOMIZATION_GUIDE.md)
- 💡 [Usage Examples](./examples/basic_usage.py)

## Get Help

- Open an issue in the repository
- Check [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- Contact AWS Support

---

**Ready to go?** Start with `./setup.sh` and follow the prompts!
