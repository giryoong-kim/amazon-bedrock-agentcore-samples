# Customization Guide - Nova Sonic Chat Agent

This guide explains how to customize the Nova Sonic Chat Agent for your specific use case.

## Table of Contents

1. [System Prompt Customization](#system-prompt-customization)
2. [Adding Custom Tools](#adding-custom-tools)
3. [Model Configuration](#model-configuration)
4. [Response Formatting](#response-formatting)
5. [Backend Integration](#backend-integration)
6. [Conversation Management](#conversation-management)
7. [Advanced Customizations](#advanced-customizations)

## System Prompt Customization

The system prompt defines your agent's personality, capabilities, and behavior.

### Basic Customization

Edit `chat_agent.py` to modify the `SYSTEM_PROMPT`:

```python
SYSTEM_PROMPT = """You are a specialized customer support agent for Acme Corporation.

Your role:
- Answer questions about Acme products
- Help troubleshoot technical issues
- Escalate complex cases to human agents

Your personality:
- Professional yet friendly
- Patient and empathetic
- Solution-oriented

Guidelines:
- Always verify customer identity before sharing account details
- Use clear, jargon-free language
- Provide step-by-step instructions when helpful
- Acknowledge customer frustrations with empathy
"""
```

### Industry-Specific Examples

#### Healthcare Assistant
```python
SYSTEM_PROMPT = """You are a healthcare information assistant.

Important disclaimers:
- You provide general health information only
- You are NOT a replacement for professional medical advice
- Always recommend consulting healthcare providers for medical decisions

Your capabilities:
- Explain common health conditions
- Provide wellness tips
- Help understand medical terminology
- Schedule appointment assistance

NEVER:
- Diagnose conditions
- Prescribe medications
- Provide emergency medical advice
"""
```

#### Financial Advisor
```python
SYSTEM_PROMPT = """You are a personal finance assistant.

Your expertise:
- Budgeting and saving strategies
- Investment basics and portfolio diversification
- Retirement planning
- Debt management

Guidelines:
- Provide educational information, not financial advice
- Encourage consultation with licensed financial advisors
- Use examples to illustrate concepts
- Be conservative with risk assessments

Disclaimers:
- Past performance doesn't guarantee future results
- Investment decisions should consider individual circumstances
"""
```

## Adding Custom Tools

### Creating a Simple Tool

```python
from strands_tools import tool
from typing import Dict, Any

@tool
def check_inventory(product_id: str) -> Dict[str, Any]:
    """
    Check product inventory status.
    
    Args:
        product_id: The unique product identifier
        
    Returns:
        Dictionary with inventory information
    """
    # Your implementation here
    # This could call your inventory API
    
    return {
        "product_id": product_id,
        "in_stock": True,
        "quantity": 42,
        "location": "Warehouse A"
    }

# Add to agent initialization
agent = Agent(
    tools=[calculator, web_search, check_inventory],
    system_prompt=SYSTEM_PROMPT
)
```

### Tool with External API Integration

```python
import requests
from strands_tools import tool

@tool
async def get_weather(city: str) -> Dict[str, Any]:
    """
    Get current weather for a city.
    
    Args:
        city: City name
        
    Returns:
        Weather information
    """
    api_key = os.environ.get("WEATHER_API_KEY")
    
    try:
        response = requests.get(
            f"https://api.weather.com/v1/current",
            params={
                "city": city,
                "apikey": api_key
            },
            timeout=5
        )
        response.raise_for_status()
        
        data = response.json()
        return {
            "city": city,
            "temperature": data["temp"],
            "conditions": data["conditions"],
            "humidity": data["humidity"]
        }
    except Exception as e:
        return {
            "error": f"Could not fetch weather: {str(e)}"
        }
```

### Tool with Database Access

```python
import boto3
from strands_tools import tool

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('CustomerOrders')

@tool
def get_order_status(order_id: str) -> Dict[str, Any]:
    """
    Retrieve order status from database.
    
    Args:
        order_id: Order identifier
        
    Returns:
        Order details and status
    """
    try:
        response = table.get_item(Key={'order_id': order_id})
        
        if 'Item' not in response:
            return {"error": "Order not found"}
        
        order = response['Item']
        return {
            "order_id": order_id,
            "status": order['status'],
            "items": order['items'],
            "total": order['total'],
            "estimated_delivery": order['delivery_date']
        }
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}
```

## Model Configuration

### Changing the Model

```python
# Use different Claude model
agent = Agent(
    model="anthropic.claude-3-haiku-20240307-v1:0",  # Faster, cheaper
    tools=[calculator],
    system_prompt=SYSTEM_PROMPT
)

# Or use Claude Opus for better quality
agent = Agent(
    model="anthropic.claude-3-opus-20240229-v1:0",  # Highest quality
    tools=[calculator],
    system_prompt=SYSTEM_PROMPT
)
```

### Adjusting Model Parameters

```python
from strands import Agent, ModelConfig

model_config = ModelConfig(
    temperature=0.7,        # Creativity (0.0-1.0)
    max_tokens=2048,        # Response length
    top_p=0.9,             # Nucleus sampling
    top_k=50               # Token sampling
)

agent = Agent(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    model_config=model_config,
    tools=[calculator],
    system_prompt=SYSTEM_PROMPT
)
```

## Response Formatting

### Adding Structured Output

```python
from pydantic import BaseModel

class AgentResponse(BaseModel):
    message: str
    intent: str
    confidence: float
    suggested_actions: list[str]

@app.entrypoint
async def chat_invocation(payload: Dict[str, Any], context: Any):
    user_message = payload.get("prompt")
    
    # Get agent response
    result = await agent.run_async(user_message)
    
    # Format as structured response
    response = AgentResponse(
        message=result.message,
        intent=result.metadata.get("intent", "general"),
        confidence=result.metadata.get("confidence", 0.8),
        suggested_actions=result.metadata.get("actions", [])
    )
    
    yield response.dict()
```

### Adding Metadata

```python
@app.entrypoint
async def chat_invocation(payload: Dict[str, Any], context: Any):
    user_message = payload.get("prompt")
    session_id = payload.get("session_id", "default")
    
    start_time = time.time()
    
    async for event in agent.stream_async(user_message):
        # Add metadata to each event
        enriched_event = {
            "content": event,
            "session_id": session_id,
            "timestamp": time.time(),
            "agent_version": "1.0.0"
        }
        yield enriched_event
    
    # Log performance metrics
    duration = time.time() - start_time
    print(f"Response completed in {duration:.2f}s")
```

### Custom Formatting for Different Channels

```python
def format_for_channel(content: str, channel: str) -> str:
    """Format response based on channel."""
    
    if channel == "sms":
        # SMS: Short, no markdown
        return content[:160]
    
    elif channel == "web":
        # Web: Full markdown, links
        return content
    
    elif channel == "voice":
        # Voice: Remove markdown, add pauses
        import re
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        text = text.replace('\n', '. ')
        return text
    
    return content

@app.entrypoint
async def chat_invocation(payload: Dict[str, Any], context: Any):
    user_message = payload.get("prompt")
    channel = payload.get("channel", "web")
    
    result = agent(user_message)
    formatted_response = format_for_channel(result.message, channel)
    
    yield {"response": formatted_response}
```

## Backend Integration

### Integrating with REST APIs

```python
import httpx
from typing import Optional

class BackendClient:
    """Client for backend API integration."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Fetch user profile from backend."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{user_id}",
                headers=self.headers,
                timeout=5.0
            )
            
            if response.status_code == 200:
                return response.json()
            return None

# Initialize backend client
backend = BackendClient(
    base_url=os.environ.get("BACKEND_URL"),
    api_key=os.environ.get("BACKEND_API_KEY")
)

@tool
async def get_user_info(user_id: str) -> Dict[str, Any]:
    """Get user information from backend."""
    profile = await backend.get_user_profile(user_id)
    
    if not profile:
        return {"error": "User not found"}
    
    return {
        "user_id": user_id,
        "name": profile["name"],
        "email": profile["email"],
        "membership": profile["membership_tier"]
    }
```

### Database Integration with Connection Pool

```python
import asyncpg
from typing import Optional

class DatabaseClient:
    """Async PostgreSQL client with connection pooling."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def init_pool(self):
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(
            host=os.environ.get("DB_HOST"),
            port=int(os.environ.get("DB_PORT", 5432)),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME"),
            min_size=2,
            max_size=10
        )
    
    async def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Fetch customer data."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM customers WHERE id = $1",
                customer_id
            )
            return dict(row) if row else None

# Initialize database client
db = DatabaseClient()

@app.on_startup
async def startup():
    """Initialize resources on startup."""
    await db.init_pool()

@tool
async def lookup_customer(customer_id: str) -> Dict[str, Any]:
    """Look up customer in database."""
    customer = await db.get_customer(customer_id)
    
    if not customer:
        return {"error": "Customer not found"}
    
    return customer
```

## Conversation Management

### Custom Session Storage

```python
from typing import Dict, List
import boto3
from datetime import datetime, timedelta

class ConversationManager:
    """Manage conversation sessions with DynamoDB."""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('ChatSessions')
    
    def save_message(
        self,
        session_id: str,
        role: str,
        content: str
    ):
        """Save message to session history."""
        self.table.put_item(
            Item={
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'role': role,
                'content': content,
                'ttl': int((datetime.utcnow() + timedelta(days=30)).timestamp())
            }
        )
    
    def get_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Retrieve conversation history."""
        response = self.table.query(
            KeyConditionExpression='session_id = :sid',
            ExpressionAttributeValues={':sid': session_id},
            Limit=limit,
            ScanIndexForward=False  # Most recent first
        )
        
        messages = response.get('Items', [])
        messages.reverse()  # Chronological order
        
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

# Initialize conversation manager
conv_manager = ConversationManager()

@app.entrypoint
async def chat_invocation(payload: Dict[str, Any], context: Any):
    session_id = payload.get("session_id", "default")
    user_message = payload.get("prompt")
    
    # Get conversation history
    history = conv_manager.get_history(session_id)
    
    # Build context-aware message
    full_context = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in history
    ])
    full_context += f"\nuser: {user_message}"
    
    # Get agent response
    async for event in agent.stream_async(full_context):
        yield event
    
    # Save to history
    conv_manager.save_message(session_id, "user", user_message)
    conv_manager.save_message(session_id, "assistant", event)
```

## Advanced Customizations

### Multi-Agent Orchestration

```python
from strands import Agent

# Specialized agents
triage_agent = Agent(
    system_prompt="You classify user requests into categories...",
    model="anthropic.claude-3-haiku-20240307-v1:0"
)

support_agent = Agent(
    system_prompt="You handle technical support questions...",
    tools=[check_system_status, restart_service],
    model="anthropic.claude-3-5-sonnet-20241022-v2:0"
)

sales_agent = Agent(
    system_prompt="You handle sales inquiries...",
    tools=[check_inventory, calculate_pricing],
    model="anthropic.claude-3-5-sonnet-20241022-v2:0"
)

@app.entrypoint
async def chat_invocation(payload: Dict[str, Any], context: Any):
    user_message = payload.get("prompt")
    
    # Step 1: Triage
    triage_result = triage_agent(
        f"Classify this request: {user_message}\n"
        f"Categories: support, sales, general"
    )
    
    category = triage_result.message.lower()
    
    # Step 2: Route to appropriate agent
    if "support" in category:
        agent_stream = support_agent.stream_async(user_message)
    elif "sales" in category:
        agent_stream = sales_agent.stream_async(user_message)
    else:
        agent_stream = agent.stream_async(user_message)
    
    # Step 3: Stream response
    async for event in agent_stream:
        yield event
```

### Adding Authentication and Authorization

```python
from functools import wraps

def require_auth(func):
    """Decorator to require authentication."""
    @wraps(func)
    async def wrapper(payload: Dict[str, Any], context: Any):
        # Verify JWT token
        token = payload.get("auth_token")
        
        if not verify_token(token):
            yield {"error": "Unauthorized", "status": 401}
            return
        
        # Extract user info
        user_info = decode_token(token)
        payload["user_info"] = user_info
        
        # Call original function
        async for event in func(payload, context):
            yield event
    
    return wrapper

@app.entrypoint
@require_auth
async def chat_invocation(payload: Dict[str, Any], context: Any):
    user_info = payload.get("user_info", {})
    user_message = payload.get("prompt")
    
    # Personalize based on user
    personalized_prompt = f"""
    User: {user_info.get('name', 'Guest')}
    Membership: {user_info.get('tier', 'standard')}
    
    Message: {user_message}
    """
    
    async for event in agent.stream_async(personalized_prompt):
        yield event
```

## Testing Custom Implementations

Always test your customizations:

```python
# tests/test_custom.py
import pytest
from chat_agent import agent, check_inventory

@pytest.mark.asyncio
async def test_custom_tool():
    """Test custom inventory tool."""
    result = check_inventory("PROD-123")
    
    assert result["product_id"] == "PROD-123"
    assert "in_stock" in result
    assert isinstance(result["quantity"], int)

@pytest.mark.asyncio
async def test_custom_system_prompt():
    """Test agent with custom prompt."""
    result = agent("Hello")
    
    # Verify response matches expected behavior
    assert len(result.message) > 0
    assert "ACME" in result.message  # If customized for ACME corp
```

## Next Steps

- Review [Deployment Guide](./DEPLOYMENT_GUIDE.md) for deploying customizations
- Check [Performance Tuning](../README.md#best-practices) for optimization
- See [examples/](../examples/) for more code samples

---

For questions, open an issue or refer to the [main README](../README.md).
