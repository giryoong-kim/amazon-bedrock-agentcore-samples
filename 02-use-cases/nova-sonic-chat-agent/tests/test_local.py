"""
Local testing script for Nova Sonic Chat Agent

This script allows you to test the agent locally before deploying to AgentCore.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import chat_agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from chat_agent import agent, chat_invocation


async def test_basic_conversation():
    """Test basic conversation flow."""
    print("\n" + "=" * 60)
    print("Testing Basic Conversation")
    print("=" * 60 + "\n")
    
    test_messages = [
        "Hello! How are you?",
        "Can you help me with a math problem? What is 15 * 24?",
        "Tell me an interesting fact about AI."
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n[Test {i}] User: {message}")
        print("-" * 60)
        
        payload = {"prompt": message}
        context = {"test": True}
        
        response_parts = []
        async for event in chat_invocation(payload, context):
            if isinstance(event, dict):
                if event.get('type') == 'error':
                    print(f"Error: {event.get('content')}")
                    break
            response_parts.append(str(event))
        
        print(f"Agent: {''.join(response_parts)}")
        print("-" * 60)


async def test_context_awareness():
    """Test conversation with context history."""
    print("\n" + "=" * 60)
    print("Testing Context-Aware Conversation")
    print("=" * 60 + "\n")
    
    conversation_history = [
        {"role": "user", "content": "My name is Alex"},
        {"role": "assistant", "content": "Nice to meet you, Alex! How can I help you today?"}
    ]
    
    payload = {
        "prompt": "What's my name?",
        "conversation_history": conversation_history,
        "session_id": "test-session-123"
    }
    context = {"test": True}
    
    print("User: What's my name?")
    print("(with conversation history)")
    print("-" * 60)
    
    response_parts = []
    async for event in chat_invocation(payload, context):
        if isinstance(event, dict):
            if event.get('type') == 'error':
                print(f"Error: {event.get('content')}")
                break
        response_parts.append(str(event))
    
    print(f"Agent: {''.join(response_parts)}")
    print("-" * 60)


async def test_error_handling():
    """Test error handling with empty/invalid payloads."""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60 + "\n")
    
    # Test with empty payload
    print("[Test 1] Empty payload")
    print("-" * 60)
    
    payload = {}
    context = {"test": True}
    
    response_parts = []
    async for event in chat_invocation(payload, context):
        if isinstance(event, dict):
            if event.get('type') == 'error':
                print(f"Error: {event.get('content')}")
                break
        response_parts.append(str(event))
    
    print(f"Agent: {''.join(response_parts)}")
    print("-" * 60)


async def interactive_mode():
    """Run interactive chat session."""
    print("\n" + "=" * 60)
    print("Interactive Chat Mode")
    print("=" * 60)
    print("Type 'quit' or 'exit' to end the session")
    print("Type 'clear' to clear conversation history\n")
    
    conversation_history = []
    session_id = "interactive-session"
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("\nGoodbye! 👋")
                break
            
            if user_input.lower() == 'clear':
                conversation_history = []
                print("Conversation history cleared.")
                continue
            
            payload = {
                "prompt": user_input,
                "conversation_history": conversation_history,
                "session_id": session_id
            }
            context = {"test": True}
            
            print("Agent: ", end="", flush=True)
            response_parts = []
            
            async for event in chat_invocation(payload, context):
                if isinstance(event, dict):
                    if event.get('type') == 'error':
                        print(f"Error: {event.get('content')}")
                        break
                else:
                    print(event, end="", flush=True)
                    response_parts.append(str(event))
            
            print()  # New line after response
            
            # Update conversation history
            full_response = ''.join(response_parts)
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": full_response})
            
            # Keep only last 5 exchanges (10 messages)
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye! 👋")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")


async def main():
    """Run all tests."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test Nova Sonic Chat Agent locally'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive chat mode'
    )
    parser.add_argument(
        '--test',
        choices=['basic', 'context', 'error', 'all'],
        default='all',
        help='Specific test to run (default: all)'
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        await interactive_mode()
    else:
        print("\n" + "=" * 60)
        print("Nova Sonic Chat Agent - Local Tests")
        print("=" * 60)
        
        if args.test in ['basic', 'all']:
            await test_basic_conversation()
        
        if args.test in ['context', 'all']:
            await test_context_awareness()
        
        if args.test in ['error', 'all']:
            await test_error_handling()
        
        print("\n" + "=" * 60)
        print("All Tests Complete!")
        print("=" * 60)
        print("\nTo run interactive mode, use: python test_local.py --interactive")


if __name__ == "__main__":
    asyncio.run(main())
