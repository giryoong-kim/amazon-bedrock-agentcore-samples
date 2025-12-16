# Nova Sonic Chat Agent - Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│         (Web, Mobile, Voice Interfaces, APIs)               │
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
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │        System Prompt & Configuration        │    │  │
│  │  └─────────────────────────────────────────────┘    │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │      Conversation Context Manager           │    │  │
│  │  │  - Session tracking                          │    │  │
│  │  │  - History management                        │    │  │
│  │  │  - Context awareness                         │    │  │
│  │  └─────────────────────────────────────────────┘    │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │           Tool Integration Layer            │    │  │
│  │  │  - Calculator                                │    │  │
│  │  │  - Web Search                                │    │  │
│  │  │  - Custom Tools (extensible)                 │    │  │
│  │  └─────────────────────────────────────────────┘    │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │       Streaming Response Handler            │    │  │
│  │  │  - Real-time streaming                       │    │  │
│  │  │  - Event processing                          │    │  │
│  │  └─────────────────────────────────────────────┘    │  │
│  └──────────────────┬───────────────────────────────────┘  │
└─────────────────────┼──────────────────────────────────────┘
                      │
                      │ Bedrock API
                      │
┌─────────────────────▼──────────────────────────────────────┐
│                  Amazon Bedrock                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Foundation Models                                  │    │
│  │  • Claude 3.5 Sonnet (primary)                     │    │
│  │  • Amazon Nova Sonic 2 (voice capabilities)        │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │
        ┌──────────────┴──────────────┬──────────────────┐
        │                             │                  │
┌───────▼──────┐           ┌─────────▼────────┐  ┌──────▼──────┐
│  CloudWatch  │           │    AWS X-Ray      │  │     IAM     │
│   Logs &     │           │    Tracing        │  │   Roles &   │
│   Metrics    │           │                   │  │  Policies   │
└──────────────┘           └──────────────────┘  └─────────────┘
```

## Component Details

### 1. Client Applications Layer

**Purpose**: User-facing applications that interact with the chat agent

**Components**:
- Web applications (React, Vue, Angular)
- Mobile applications (iOS, Android)
- Voice interfaces (Alexa, Google Assistant)
- REST/GraphQL APIs
- Chatbots (Slack, Teams, Discord)

**Integration Methods**:
- Direct API calls to AgentCore endpoint
- WebSocket for streaming responses
- Server-side integration via AWS SDK

### 2. Amazon Bedrock AgentCore Runtime

**Purpose**: Managed serverless runtime for hosting the agent

**Key Features**:
- Automatic scaling based on load
- Built-in load balancing
- High availability (multi-AZ)
- Managed infrastructure
- Pay-per-use pricing

**Responsibilities**:
- Request routing
- Agent lifecycle management
- Environment isolation
- Resource allocation
- Monitoring and logging

### 3. Nova Sonic Chat Agent (Core Application)

#### 3.1 System Prompt & Configuration

**Purpose**: Define agent behavior and personality

```python
SYSTEM_PROMPT = """
You are a helpful and friendly AI assistant...
"""
```

**Configuration Sources**:
- `config.yaml` - Static configuration
- Environment variables - Runtime settings
- Context object - Request-specific data

#### 3.2 Conversation Context Manager

**Purpose**: Maintain conversation state and history

**Features**:
- Session ID tracking
- Message history storage
- Context window management
- Multi-turn conversation support

**Data Flow**:
```
Request → Extract session_id → Load history → 
Augment prompt → Process → Save response
```

#### 3.3 Tool Integration Layer

**Purpose**: Extend agent capabilities with external tools

**Built-in Tools**:
1. **Calculator**: Mathematical computations
2. **Web Search**: Current information retrieval

**Tool Invocation Flow**:
```
User Query → Intent Detection → Tool Selection → 
Tool Execution → Result Integration → Response Generation
```

**Extensibility**:
```python
@tool
def custom_tool(param: str) -> dict:
    """Custom tool implementation"""
    return {"result": "value"}
```

#### 3.4 Streaming Response Handler

**Purpose**: Real-time response streaming for better UX

**Event Types**:
- Text chunks (partial responses)
- Tool invocation events
- Completion events
- Error events

**Streaming Flow**:
```
Request → Agent Processing → Stream Events → 
Client Receives → Display Updates → Complete
```

### 4. Amazon Bedrock (Model Layer)

**Purpose**: AI model inference

**Models Used**:

1. **Claude 3.5 Sonnet** (Primary)
   - Model ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
   - Use case: General conversation, reasoning
   - Strengths: High quality, tool use, reasoning

2. **Amazon Nova Sonic 2** (Voice)
   - Model ID: `us.amazon.nova-sonic-v2:0`
   - Use case: Voice conversations, real-time interaction
   - Strengths: Speech-to-speech, low latency

**Model Selection Logic**:
```
Voice Input → Nova Sonic 2
Text Input → Claude 3.5 Sonnet
```

### 5. Observability Layer

#### CloudWatch Logs
- Request/response logging
- Error tracking
- Debug information
- Performance metrics

#### CloudWatch Metrics
- Invocation count
- Duration
- Token usage
- Error rate

#### AWS X-Ray
- Distributed tracing
- Performance bottlenecks
- Service dependencies
- Request flow visualization

### 6. Security Layer (IAM)

**Components**:

1. **Execution Role**: `NovaSonicChatAgentRole`
   - Allows AgentCore to execute agent code
   - Trust relationship with Bedrock service

2. **Permission Policy**: `NovaSonicChatAgentPolicy`
   - Bedrock model invocation
   - CloudWatch logging
   - X-Ray tracing
   - (Optional) DynamoDB, S3, etc.

## Data Flow

### Request Processing Flow

```
1. Client Request
   ├─ Payload: {"prompt": "...", "session_id": "..."}
   └─ Protocol: HTTPS/WebSocket
   
2. AgentCore Runtime
   ├─ Authentication & Authorization (IAM)
   ├─ Request validation
   └─ Agent invocation
   
3. Chat Agent Entrypoint
   ├─ Extract user message
   ├─ Load conversation history
   └─ Build context
   
4. Strands Agent Processing
   ├─ System prompt application
   ├─ Tool availability check
   └─ Model invocation preparation
   
5. Bedrock Model Inference
   ├─ Request to Bedrock API
   ├─ Model processes input
   └─ Generates response (streaming)
   
6. Tool Execution (if needed)
   ├─ Tool identified by model
   ├─ Tool invoked with parameters
   ├─ Result returned to model
   └─ Final response generated
   
7. Response Streaming
   ├─ Chunks sent to client
   ├─ Real-time display updates
   └─ Completion event
   
8. Session Management
   ├─ Save message history
   ├─ Update session state
   └─ Cleanup (if needed)
   
9. Observability
   ├─ Log to CloudWatch
   ├─ Record metrics
   └─ Trace to X-Ray
```

### Session Management Flow

```
┌─────────────────────────────────────────┐
│         User Starts Conversation        │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│      Generate/Receive Session ID       │
│         (e.g., "user-123-abc")          │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│     First Message Processing            │
│  - No history, fresh context            │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│   Save Message to Session Store        │
│  - User message                         │
│  - Agent response                       │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│    Subsequent Messages                  │
│  - Load history from session store      │
│  - Append to context                    │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│   Context Window Management             │
│  - Keep last N messages (e.g., 10)     │
│  - Trim older messages                  │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│      Session Timeout/Cleanup            │
│  - TTL-based expiration (e.g., 30 days) │
│  - Manual session end                   │
└─────────────────────────────────────────┘
```

## Deployment Architecture

### Development Environment

```
Local Machine
├─ Python virtual environment
├─ Local testing with test_local.py
├─ Mock Bedrock responses (optional)
└─ Direct code editing and debugging
```

### Staging Environment

```
AWS Account (Staging)
├─ AgentCore Runtime (staging config)
├─ Reduced resource allocation
├─ Limited model access
└─ Test data and scenarios
```

### Production Environment

```
AWS Account (Production)
├─ AgentCore Runtime (production config)
│  ├─ Auto-scaling enabled
│  ├─ High memory allocation (2048-4096 MB)
│  └─ Enhanced monitoring
├─ CloudWatch Alarms configured
├─ X-Ray sampling at 100%
└─ Production IAM roles and policies
```

## Scalability

### Horizontal Scaling

**AgentCore Automatic Scaling**:
- Min instances: 1 (config: `scaling.min_instances`)
- Max instances: 10 (config: `scaling.max_instances`)
- Scaling trigger: CPU utilization > 70%
- Scale-up time: ~1 minute
- Scale-down time: ~5 minutes

### Vertical Scaling

**Resource Allocation**:
```yaml
# config.yaml
agent:
  runtime:
    memory_mb: 2048    # Can increase to 4096 or more
    timeout_seconds: 300
```

### Performance Optimization

1. **Streaming**: Reduces perceived latency
2. **Context Caching**: Reuse conversation context
3. **Model Selection**: Use faster models for simple queries
4. **Tool Caching**: Cache tool results when appropriate
5. **Async Processing**: Non-blocking I/O operations

## Security Architecture

### Authentication

```
Client → API Gateway (with Auth) → AgentCore
   │
   ├─ API Keys
   ├─ JWT Tokens
   ├─ AWS SigV4
   └─ OAuth 2.0
```

### Authorization

```
IAM Role (NovaSonicChatAgentRole)
├─ Bedrock Model Access
│  └─ Specific model ARNs only
├─ CloudWatch Logs
│  └─ Specific log group only
├─ X-Ray Tracing
│  └─ No sensitive data in traces
└─ Principle of Least Privilege
```

### Data Protection

1. **In Transit**: TLS 1.2+ for all communications
2. **At Rest**: AWS managed encryption (KMS)
3. **Conversation History**: Optional encryption
4. **PII Handling**: Configurable data retention

## Integration Patterns

### Pattern 1: Synchronous Request-Response

```python
response = client.invoke_agent(
    agentId=agent_id,
    sessionId=session_id,
    inputText=user_message
)
```

**Use Cases**: Simple Q&A, fact retrieval

### Pattern 2: Asynchronous Streaming

```python
async for event in agent.stream_async(message):
    # Process event in real-time
    display_update(event)
```

**Use Cases**: Long responses, conversational UI

### Pattern 3: Multi-Agent Orchestration

```python
# Triage → Route → Execute
category = triage_agent(message)
specialist = route_to_specialist(category)
response = specialist.process(message)
```

**Use Cases**: Complex workflows, specialized tasks

## Monitoring Architecture

### Metrics Collection

```
Agent Execution
    ↓
OpenTelemetry SDK
    ↓
CloudWatch + X-Ray
    ↓
Dashboards & Alarms
```

### Key Metrics

1. **Performance**:
   - Request duration (p50, p95, p99)
   - Token usage per request
   - Tool invocation time

2. **Reliability**:
   - Success rate
   - Error rate by type
   - Timeout rate

3. **Business**:
   - Daily active sessions
   - Messages per session
   - Popular queries

## Cost Architecture

### Cost Components

1. **Bedrock Model Inference**:
   - Input tokens: $X per 1K tokens
   - Output tokens: $Y per 1K tokens
   - Streaming: No additional cost

2. **AgentCore Runtime**:
   - Compute time: $ per second
   - Memory allocation: $ per GB-second

3. **Storage & Observability**:
   - CloudWatch Logs: $ per GB stored
   - CloudWatch Metrics: $ per metric
   - X-Ray traces: $ per trace

### Cost Optimization

1. Use appropriate model (Haiku for simple queries)
2. Implement caching for repeated queries
3. Set reasonable timeout values
4. Configure log retention policies
5. Use sampling for X-Ray in production

---

For implementation details, see:
- [README.md](./README.md) - Complete documentation
- [DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md) - Deployment details
- [CUSTOMIZATION_GUIDE.md](./docs/CUSTOMIZATION_GUIDE.md) - Customization examples
