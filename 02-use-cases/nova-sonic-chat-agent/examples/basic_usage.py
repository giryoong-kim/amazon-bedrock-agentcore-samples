"""
Basic usage examples for Nova Sonic Chat Agent

This module demonstrates various ways to interact with the deployed chat agent.
"""

import json
import boto3
from typing import Dict, Any, List


class ChatAgentClient:
    """Client for interacting with deployed Nova Sonic Chat Agent."""
    
    def __init__(self, agent_endpoint: str, region: str = "us-east-1"):
        """
        Initialize chat agent client.
        
        Args:
            agent_endpoint: AgentCore endpoint URL
            region: AWS region
        """
        self.agent_endpoint = agent_endpoint
        self.region = region
        self.session = boto3.Session(region_name=region)
    
    def send_message(
        self,
        message: str,
        session_id: str = "default",
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to the chat agent.
        
        Args:
            message: User message
            session_id: Session identifier for conversation continuity
            conversation_history: Optional list of previous messages
            
        Returns:
            Agent response dictionary
        """
        payload = {
            "prompt": message,
            "session_id": session_id
        }
        
        if conversation_history:
            payload["conversation_history"] = conversation_history
        
        # In actual implementation, this would call the AgentCore endpoint
        # For now, this is a template showing the expected interface
        print(f"Sending to agent: {json.dumps(payload, indent=2)}")
        
        # Simulated response structure
        return {
            "status": "success",
            "response": "This is a simulated response. Replace with actual API call.",
            "session_id": session_id
        }


def example_simple_chat():
    """Example: Simple single-turn chat."""
    print("\n" + "=" * 60)
    print("Example 1: Simple Chat")
    print("=" * 60 + "\n")
    
    # Initialize client
    client = ChatAgentClient(agent_endpoint="your-agent-endpoint-url")
    
    # Send a simple message
    response = client.send_message(
        message="Hello! Tell me about Amazon Nova Sonic.",
        session_id="example-1"
    )
    
    print(f"User: Hello! Tell me about Amazon Nova Sonic.")
    print(f"Agent: {response['response']}")


def example_multi_turn_conversation():
    """Example: Multi-turn conversation with context."""
    print("\n" + "=" * 60)
    print("Example 2: Multi-turn Conversation")
    print("=" * 60 + "\n")
    
    client = ChatAgentClient(agent_endpoint="your-agent-endpoint-url")
    
    # Initialize conversation
    session_id = "example-2"
    conversation_history = []
    
    # Turn 1
    user_msg_1 = "My favorite color is blue."
    response_1 = client.send_message(
        message=user_msg_1,
        session_id=session_id,
        conversation_history=conversation_history
    )
    
    print(f"User: {user_msg_1}")
    print(f"Agent: {response_1['response']}\n")
    
    # Update history
    conversation_history.append({"role": "user", "content": user_msg_1})
    conversation_history.append({"role": "assistant", "content": response_1['response']})
    
    # Turn 2
    user_msg_2 = "What's my favorite color?"
    response_2 = client.send_message(
        message=user_msg_2,
        session_id=session_id,
        conversation_history=conversation_history
    )
    
    print(f"User: {user_msg_2}")
    print(f"Agent: {response_2['response']}")


def example_with_calculations():
    """Example: Using agent for calculations."""
    print("\n" + "=" * 60)
    print("Example 3: Calculations")
    print("=" * 60 + "\n")
    
    client = ChatAgentClient(agent_endpoint="your-agent-endpoint-url")
    
    calculations = [
        "What is 234 multiplied by 567?",
        "If I invest $5000 at 7% annual interest for 10 years, how much will I have?",
        "Calculate the area of a circle with radius 15 meters."
    ]
    
    for calc in calculations:
        response = client.send_message(
            message=calc,
            session_id="calc-example"
        )
        print(f"User: {calc}")
        print(f"Agent: {response['response']}\n")


def example_information_queries():
    """Example: Information and knowledge queries."""
    print("\n" + "=" * 60)
    print("Example 4: Information Queries")
    print("=" * 60 + "\n")
    
    client = ChatAgentClient(agent_endpoint="your-agent-endpoint-url")
    
    queries = [
        "What are the main features of Amazon Bedrock?",
        "Explain how AI agents work in simple terms.",
        "What is the difference between synchronous and asynchronous programming?"
    ]
    
    for query in queries:
        response = client.send_message(
            message=query,
            session_id="info-example"
        )
        print(f"User: {query}")
        print(f"Agent: {response['response']}\n")


def example_customer_support_scenario():
    """Example: Customer support conversation."""
    print("\n" + "=" * 60)
    print("Example 5: Customer Support Scenario")
    print("=" * 60 + "\n")
    
    client = ChatAgentClient(agent_endpoint="your-agent-endpoint-url")
    
    session_id = "support-example"
    conversation_history = []
    
    conversation = [
        "Hi, I need help with my account.",
        "I'm trying to reset my password but I'm not receiving the reset email.",
        "I've checked my spam folder, it's not there.",
        "My email is user@example.com",
        "Thank you for your help!"
    ]
    
    for message in conversation:
        response = client.send_message(
            message=message,
            session_id=session_id,
            conversation_history=conversation_history
        )
        
        print(f"User: {message}")
        print(f"Agent: {response['response']}\n")
        
        # Update history
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": response['response']})


def example_integration_code():
    """Example: Integration code snippet."""
    print("\n" + "=" * 60)
    print("Example 6: Integration Code Template")
    print("=" * 60 + "\n")
    
    integration_code = '''
# Integration with your application

import requests
import json

class NovaSonicChatIntegration:
    """Integrate Nova Sonic Chat Agent into your application."""
    
    def __init__(self, agent_url: str, api_key: str = None):
        self.agent_url = agent_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def chat(self, user_message: str, session_id: str = None):
        """Send a chat message and get response."""
        payload = {
            "prompt": user_message,
            "session_id": session_id or "default"
        }
        
        response = requests.post(
            self.agent_url,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        return response.json()

# Usage
agent = NovaSonicChatIntegration(
    agent_url="https://your-agent-endpoint.execute-api.us-east-1.amazonaws.com/prod/chat"
)

response = agent.chat("Hello, how can you help me?")
print(response)
'''
    
    print(integration_code)


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" " * 15 + "Nova Sonic Chat Agent - Usage Examples")
    print("=" * 70)
    
    examples = [
        ("Simple Chat", example_simple_chat),
        ("Multi-turn Conversation", example_multi_turn_conversation),
        ("Calculations", example_with_calculations),
        ("Information Queries", example_information_queries),
        ("Customer Support", example_customer_support_scenario),
        ("Integration Code", example_integration_code)
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning all examples...\n")
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"Error in {name}: {str(e)}\n")
    
    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)
    print("\nNote: These examples show the interface and patterns.")
    print("Replace 'your-agent-endpoint-url' with your actual AgentCore endpoint.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
