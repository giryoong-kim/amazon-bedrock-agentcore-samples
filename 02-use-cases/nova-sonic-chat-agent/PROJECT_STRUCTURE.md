# Nova Sonic Chat Agent - Project Structure

## Overview

This document describes the complete project structure for the Nova Sonic 2 Chat Agent implementation.

## Directory Structure

```
nova-sonic-chat-agent/
├── README.md                          # Main project documentation
├── QUICKSTART.md                      # Quick start guide (10-minute setup)
├── PROJECT_STRUCTURE.md              # This file
├── .gitignore                        # Git ignore rules
├── requirements.txt                  # Python dependencies
├── config.yaml                       # Agent configuration
├── setup.sh                          # Environment setup script
├── chat_agent.py                     # Main agent implementation ⭐
│
├── deployment/                       # Deployment configuration
│   ├── iam-policy.json              # IAM permissions policy
│   ├── trust-policy.json            # IAM trust relationship
│   ├── setup-iam.sh                 # IAM setup script
│   ├── deploy.sh                    # Deployment script ⭐
│   ├── cleanup.sh                   # Cleanup/removal script
│   └── agentcore_config.py          # Python deployment utilities
│
├── tests/                           # Testing suite
│   ├── test_local.py               # Local testing (pre-deployment)
│   └── test_deployed.py            # Deployed agent testing
│
├── examples/                        # Usage examples
│   └── basic_usage.py              # Integration examples
│
└── docs/                            # Additional documentation
    ├── DEPLOYMENT_GUIDE.md         # Detailed deployment instructions
    └── CUSTOMIZATION_GUIDE.md      # Customization examples
```

## File Descriptions

### Core Files

#### `chat_agent.py` ⭐
**Purpose**: Main agent implementation  
**Key Components**:
- System prompt definition for conversational AI
- Strands Agent initialization with tools
- AgentCore integration with streaming support
- Asynchronous and synchronous handlers
- Session and context management

**Usage**:
```bash
# Deploy this file to AgentCore
agentcore configure --entrypoint chat_agent.py
```

#### `requirements.txt`
**Purpose**: Python package dependencies  
**Includes**:
- strands-agents (core framework)
- strands-agents-tools (calculator, web search)
- bedrock-agentcore (runtime SDK)
- bedrock-agentcore-starter-toolkit (CLI tools)
- aws-opentelemetry-distro (observability)
- boto3 (AWS SDK)

#### `config.yaml`
**Purpose**: Centralized configuration  
**Sections**:
- Agent settings (name, runtime, model)
- AWS configuration (region, IAM, monitoring)
- Deployment settings (environment, scaling)
- Development and testing configuration

### Deployment Files

#### `deployment/setup-iam.sh` ⭐
**Purpose**: Create AWS IAM resources  
**Actions**:
- Creates IAM role for agent execution
- Creates IAM policy with Bedrock permissions
- Attaches policy to role
- Saves role ARN for deployment

**Usage**:
```bash
./deployment/setup-iam.sh
```

#### `deployment/deploy.sh` ⭐
**Purpose**: Deploy agent to AgentCore  
**Actions**:
- Validates prerequisites
- Configures agent with AgentCore CLI
- Launches agent to runtime
- Displays deployment status

**Usage**:
```bash
./deployment/deploy.sh
```

#### `deployment/iam-policy.json`
**Purpose**: IAM permissions definition  
**Permissions**:
- Bedrock model invocation
- AgentCore runtime access
- CloudWatch logging and metrics
- X-Ray tracing

#### `deployment/trust-policy.json`
**Purpose**: IAM role trust relationship  
**Allows**: Bedrock and Lambda services to assume the role

#### `deployment/cleanup.sh`
**Purpose**: Remove all deployed resources  
**Actions**:
- Deletes AgentCore instance
- Removes IAM role and policy
- Cleans up local configuration files

#### `deployment/agentcore_config.py`
**Purpose**: Programmatic deployment configuration  
**Features**:
- Python-based IAM resource creation
- Configuration management
- Can be imported by other scripts

### Testing Files

#### `tests/test_local.py`
**Purpose**: Local testing before deployment  
**Test Suites**:
- Basic conversation flow
- Context-aware conversations
- Error handling
- Interactive chat mode

**Usage**:
```bash
# Run all tests
python tests/test_local.py

# Interactive mode
python tests/test_local.py --interactive

# Specific test
python tests/test_local.py --test basic
```

#### `tests/test_deployed.py`
**Purpose**: Test deployed agent on AgentCore  
**Test Suites**:
- Basic responses
- Calculation capabilities
- Conversation context
- Performance benchmarking

**Usage**:
```bash
python tests/test_deployed.py --agent-id YOUR_AGENT_ID --region us-east-1
```

### Documentation Files

#### `README.md` ⭐
**Purpose**: Comprehensive project documentation  
**Sections**:
- Overview and architecture
- Features and capabilities
- Prerequisites and installation
- Configuration and deployment
- Usage examples and testing
- Monitoring and troubleshooting
- Customization guidelines
- Best practices

#### `QUICKSTART.md`
**Purpose**: 10-minute quick start guide  
**Contents**:
- Rapid setup instructions
- Essential commands
- Common troubleshooting

#### `docs/DEPLOYMENT_GUIDE.md`
**Purpose**: Detailed deployment instructions  
**Topics**:
- Pre-deployment checklist
- Multiple deployment methods
- Step-by-step procedures
- Troubleshooting deployment issues
- Rollback procedures
- Multi-environment setup

#### `docs/CUSTOMIZATION_GUIDE.md`
**Purpose**: Customization examples and patterns  
**Topics**:
- System prompt customization
- Adding custom tools
- Model configuration
- Response formatting
- Backend integration
- Conversation management
- Advanced patterns

### Example Files

#### `examples/basic_usage.py`
**Purpose**: Integration and usage examples  
**Examples**:
- Simple chat
- Multi-turn conversations
- Calculations
- Information queries
- Customer support scenario
- Integration code templates

### Setup Files

#### `setup.sh`
**Purpose**: One-command environment setup  
**Actions**:
- Checks Python version
- Verifies AWS CLI and credentials
- Creates virtual environment
- Installs dependencies
- Validates Bedrock access
- Runs quick validation test

**Usage**:
```bash
./setup.sh
```

#### `.gitignore`
**Purpose**: Git ignore patterns  
**Excludes**:
- Python cache files
- Virtual environments
- IDE configurations
- Environment variables
- AWS configuration
- Logs and temporary files

## Component Relationships

```
┌─────────────────────────────────────────────────────────┐
│                     setup.sh                            │
│              (Initial environment setup)                │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              deployment/setup-iam.sh                    │
│           (Create AWS IAM resources)                    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│               deployment/deploy.sh                      │
│         (Deploy agent to AgentCore)                     │
│                                                         │
│   Uses: chat_agent.py + config.yaml                    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│            Amazon Bedrock AgentCore                     │
│              (Running chat_agent.py)                    │
└─────────────────────────────────────────────────────────┘
```

## Key Integration Points

### 1. Strands Agents Framework
- **File**: `chat_agent.py`
- **Purpose**: Agent orchestration and tool management
- **Components**: Agent, tools, system prompt

### 2. Amazon Bedrock
- **Access**: Via boto3 and bedrock-agentcore SDK
- **Models**: Claude 3.5 Sonnet, Nova Sonic 2
- **Purpose**: LLM inference for conversations

### 3. AgentCore Runtime
- **Configuration**: `config.yaml`, agentcore CLI
- **Deployment**: Serverless, auto-scaling
- **Monitoring**: CloudWatch Logs, Metrics, X-Ray

### 4. AWS Services
- **IAM**: Role and policy for permissions
- **CloudWatch**: Logs and metrics
- **X-Ray**: Distributed tracing
- **S3**: Agent package storage (managed by AgentCore)

## Development Workflow

```
1. Clone/Setup
   └─> ./setup.sh

2. Local Development
   ├─> Edit chat_agent.py
   ├─> Modify config.yaml
   └─> Test: python tests/test_local.py --interactive

3. Deploy
   ├─> ./deployment/setup-iam.sh (one-time)
   └─> ./deployment/deploy.sh

4. Test Deployed
   └─> python tests/test_deployed.py --agent-id ID

5. Monitor
   ├─> agentcore logs --follow
   └─> CloudWatch console

6. Iterate
   ├─> Update code
   ├─> Test locally
   └─> Redeploy: ./deployment/deploy.sh

7. Cleanup (when done)
   └─> ./deployment/cleanup.sh
```

## Configuration Hierarchy

```
config.yaml (base configuration)
    │
    ├─> Environment variables (override)
    │   └─> AWS_REGION, BYPASS_TOOL_CONSENT, etc.
    │
    ├─> AgentCore CLI flags (deployment time)
    │   └─> --memory, --timeout, --env, etc.
    │
    └─> Runtime context (execution time)
        └─> Session ID, user info, etc.
```

## Extension Points

### Adding New Tools
**File**: `chat_agent.py`
```python
from strands_tools import tool

@tool
def my_custom_tool(param: str) -> dict:
    """Your tool implementation."""
    return {"result": "value"}

agent = Agent(tools=[calculator, web_search, my_custom_tool])
```

### Custom Backend Integration
**File**: `chat_agent.py`
```python
import requests

@tool
def fetch_from_backend(query: str) -> dict:
    response = requests.get(f"https://api.example.com?q={query}")
    return response.json()
```

### Environment-Specific Configuration
**New File**: `config.production.yaml`
```yaml
agent:
  runtime:
    memory_mb: 4096
  monitoring:
    retention_days: 30
```

## Best Practices

1. **Development**: Always test locally first with `test_local.py`
2. **Deployment**: Use automated scripts for consistency
3. **Monitoring**: Set up CloudWatch alarms before production
4. **Security**: Never commit credentials or secrets
5. **Documentation**: Update README when adding features
6. **Testing**: Add test cases for new tools/features
7. **Version Control**: Tag releases before deploying

## Quick Reference

### Essential Commands
```bash
# Setup
./setup.sh

# Deploy
./deployment/setup-iam.sh
./deployment/deploy.sh

# Test
agentcore invoke '{"prompt": "Hello"}'

# Monitor
agentcore logs --follow

# Update
agentcore update

# Cleanup
./deployment/cleanup.sh
```

### Key Files to Edit
- `chat_agent.py` - Agent behavior and tools
- `config.yaml` - Configuration settings
- `deployment/iam-policy.json` - Permissions

### Documentation Hierarchy
1. `QUICKSTART.md` - Start here (5-10 minutes)
2. `README.md` - Complete reference (20-30 minutes)
3. `docs/DEPLOYMENT_GUIDE.md` - Deployment details
4. `docs/CUSTOMIZATION_GUIDE.md` - Advanced customization

---

**Last Updated**: December 2025  
**Version**: 1.0.0  
**Maintainer**: AWS Bedrock AgentCore Samples Team
