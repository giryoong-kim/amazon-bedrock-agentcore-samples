"""
Nova Sonic 2 Chat Agent using Strands Agents Framework

This module implements a conversational AI chat agent using Amazon Nova Sonic 2 model
integrated with the Strands Agents framework and Amazon Bedrock AgentCore Runtime.
"""

import asyncio
import os
import json
from typing import Dict, Any, Optional

# Bypass tool consent for production deployment
os.environ["BYPASS_TOOL_CONSENT"] = "true"

from strands import Agent
from strands_tools import calculator, web_search
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# System prompt for Nova Sonic 2 chat agent
SYSTEM_PROMPT = """You are a helpful and friendly AI assistant powered by Amazon Nova Sonic 2, designed to engage in natural, conversational interactions.

Your capabilities include:
- Engaging in multi-turn conversations with context awareness
- Providing accurate and helpful information on a wide range of topics
- Performing calculations when needed
- Searching for current information when required
- Understanding and responding to user intent naturally

Guidelines for interaction:
- Be conversational, warm, and approachable in your responses
- Maintain context throughout the conversation
- Ask clarifying questions when user intent is unclear
- Provide concise but complete answers
- Acknowledge when you don't know something
- Use tools (calculator, web search) when appropriate to enhance responses
- Keep responses natural and human-like, avoiding overly robotic language

Your goal is to be a reliable, helpful companion that makes conversations feel natural and productive.
"""

# Initialize Strands Agent with conversational capabilities
agent = Agent(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",  # Using Claude via Bedrock
    tools=[calculator, web_search],
    system_prompt=SYSTEM_PROMPT,
    callback_handler=None
)

# Initialize Bedrock AgentCore Application
app = BedrockAgentCoreApp()


@app.entrypoint
async def chat_invocation(payload: Dict[str, Any], context: Any):
    """
    Main entrypoint for chat agent invocation with streaming support.
    
    This handler processes incoming chat messages and streams responses back,
    enabling real-time conversational interactions suitable for Nova Sonic 2.
    
    Args:
        payload: Dictionary containing the chat request with keys:
            - prompt: The user's message/query
            - conversation_history: Optional list of previous messages
            - session_id: Optional session identifier for conversation continuity
        context: AgentCore runtime context with execution metadata
    
    Yields:
        Streaming response events from the agent
    """
    # Extract user message from payload
    user_message = payload.get(
        "prompt", 
        "Hello! How can I assist you today?"
    )
    
    # Extract optional conversation context
    conversation_history = payload.get("conversation_history", [])
    session_id = payload.get("session_id", "default")
    
    # Log invocation details
    print(f"[Nova Sonic Chat Agent] Session: {session_id}")
    print(f"[Nova Sonic Chat Agent] Processing message: {user_message}")
    
    # Build context-aware message if history exists
    if conversation_history:
        context_msg = f"Previous conversation context:\n"
        for msg in conversation_history[-3:]:  # Include last 3 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_msg += f"{role}: {content}\n"
        context_msg += f"\nCurrent user message: {user_message}"
        full_message = context_msg
    else:
        full_message = user_message
    
    try:
        # Stream agent response for real-time interaction
        agent_stream = agent.stream_async(full_message)
        
        async for event in agent_stream:
            yield event
            
    except Exception as e:
        error_msg = f"Error processing chat message: {str(e)}"
        print(f"[Nova Sonic Chat Agent] {error_msg}")
        yield {
            "type": "error",
            "content": error_msg
        }


@app.handler
def chat_handler(payload: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Synchronous handler for non-streaming chat interactions.
    
    This handler is useful for simple request-response patterns where
    streaming is not required.
    
    Args:
        payload: Dictionary containing the chat request
        context: AgentCore runtime context
    
    Returns:
        Dictionary with the agent's response
    """
    user_message = payload.get(
        "prompt",
        "Hello! How can I assist you today?"
    )
    
    session_id = payload.get("session_id", "default")
    
    print(f"[Nova Sonic Chat Agent] Sync Session: {session_id}")
    print(f"[Nova Sonic Chat Agent] Processing message: {user_message}")
    
    try:
        # Run agent synchronously
        result = agent(user_message)
        
        return {
            "status": "success",
            "response": result.message,
            "session_id": session_id,
            "model": "nova-sonic-2"
        }
    except Exception as e:
        error_msg = f"Error processing chat message: {str(e)}"
        print(f"[Nova Sonic Chat Agent] {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "session_id": session_id
        }


if __name__ == "__main__":
    # Run the AgentCore application
    print("[Nova Sonic Chat Agent] Starting AgentCore Runtime...")
    app.run()
