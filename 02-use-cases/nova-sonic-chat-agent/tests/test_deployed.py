"""
Test script for deployed Nova Sonic Chat Agent on AgentCore

This script tests the agent after it has been deployed to Bedrock AgentCore Runtime.
"""

import json
import boto3
import time
from typing import Dict, Any


class DeployedAgentTester:
    """Test deployed agent on AgentCore."""
    
    def __init__(self, agent_id: str, region: str = "us-east-1"):
        """
        Initialize tester for deployed agent.
        
        Args:
            agent_id: The AgentCore agent ID
            region: AWS region where agent is deployed
        """
        self.agent_id = agent_id
        self.region = region
        self.bedrock_client = boto3.client('bedrock-agent-runtime', region_name=region)
    
    def invoke_agent(self, prompt: str, session_id: str = None) -> Dict[str, Any]:
        """
        Invoke the deployed agent.
        
        Args:
            prompt: User message
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Agent response
        """
        if not session_id:
            session_id = f"test-{int(time.time())}"
        
        payload = {
            "prompt": prompt,
            "session_id": session_id
        }
        
        try:
            response = self.bedrock_client.invoke_agent(
                agentId=self.agent_id,
                sessionId=session_id,
                inputText=json.dumps(payload)
            )
            
            # Process streaming response
            result_text = ""
            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result_text += chunk['bytes'].decode('utf-8')
            
            return {
                "status": "success",
                "response": result_text,
                "session_id": session_id
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
    
    def test_basic_responses(self):
        """Test basic agent responses."""
        print("\n" + "=" * 60)
        print("Testing Basic Responses")
        print("=" * 60 + "\n")
        
        test_cases = [
            "Hello! How are you?",
            "What can you help me with?",
            "Tell me a fun fact about space."
        ]
        
        session_id = f"basic-test-{int(time.time())}"
        
        for i, prompt in enumerate(test_cases, 1):
            print(f"[Test {i}] Prompt: {prompt}")
            print("-" * 60)
            
            result = self.invoke_agent(prompt, session_id)
            
            if result['status'] == 'success':
                print(f"✓ Response: {result['response'][:200]}...")
            else:
                print(f"✗ Error: {result['error']}")
            
            print("-" * 60 + "\n")
            time.sleep(1)  # Rate limiting
    
    def test_calculation(self):
        """Test calculation capabilities."""
        print("\n" + "=" * 60)
        print("Testing Calculation Capabilities")
        print("=" * 60 + "\n")
        
        test_cases = [
            "What is 157 * 23?",
            "Calculate the square root of 144",
            "If I have $1000 and invest it at 5% annual interest, how much will I have after 3 years?"
        ]
        
        session_id = f"calc-test-{int(time.time())}"
        
        for i, prompt in enumerate(test_cases, 1):
            print(f"[Test {i}] Prompt: {prompt}")
            print("-" * 60)
            
            result = self.invoke_agent(prompt, session_id)
            
            if result['status'] == 'success':
                print(f"✓ Response: {result['response']}")
            else:
                print(f"✗ Error: {result['error']}")
            
            print("-" * 60 + "\n")
            time.sleep(1)
    
    def test_conversation_context(self):
        """Test conversation context maintenance."""
        print("\n" + "=" * 60)
        print("Testing Conversation Context")
        print("=" * 60 + "\n")
        
        conversation = [
            "My name is Sarah and I live in Seattle.",
            "What's my name?",
            "Where do I live?",
            "What did I tell you about myself?"
        ]
        
        session_id = f"context-test-{int(time.time())}"
        
        for i, prompt in enumerate(conversation, 1):
            print(f"[Turn {i}] User: {prompt}")
            print("-" * 60)
            
            result = self.invoke_agent(prompt, session_id)
            
            if result['status'] == 'success':
                print(f"Agent: {result['response']}")
            else:
                print(f"✗ Error: {result['error']}")
            
            print("-" * 60 + "\n")
            time.sleep(1)
    
    def test_performance(self, num_requests: int = 5):
        """Test agent performance with multiple requests."""
        print("\n" + "=" * 60)
        print(f"Testing Performance ({num_requests} requests)")
        print("=" * 60 + "\n")
        
        prompt = "Hello, how are you?"
        session_id = f"perf-test-{int(time.time())}"
        
        response_times = []
        
        for i in range(num_requests):
            print(f"Request {i+1}/{num_requests}...", end=" ")
            
            start_time = time.time()
            result = self.invoke_agent(prompt, session_id)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            if result['status'] == 'success':
                print(f"✓ ({response_time:.2f}s)")
            else:
                print(f"✗ Error: {result['error']}")
            
            time.sleep(0.5)
        
        # Calculate statistics
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            print("\nPerformance Statistics:")
            print(f"  Average: {avg_time:.2f}s")
            print(f"  Min: {min_time:.2f}s")
            print(f"  Max: {max_time:.2f}s")
    
    def run_all_tests(self):
        """Run all test suites."""
        print("\n" + "=" * 60)
        print("Nova Sonic Chat Agent - Deployed Tests")
        print("=" * 60)
        print(f"Agent ID: {self.agent_id}")
        print(f"Region: {self.region}")
        
        try:
            self.test_basic_responses()
            self.test_calculation()
            self.test_conversation_context()
            self.test_performance()
            
            print("\n" + "=" * 60)
            print("All Tests Complete!")
            print("=" * 60 + "\n")
        
        except Exception as e:
            print(f"\n✗ Test suite failed: {str(e)}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test deployed Nova Sonic Chat Agent'
    )
    parser.add_argument(
        '--agent-id',
        required=True,
        help='AgentCore agent ID'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--test',
        choices=['basic', 'calc', 'context', 'perf', 'all'],
        default='all',
        help='Specific test to run (default: all)'
    )
    
    args = parser.parse_args()
    
    tester = DeployedAgentTester(args.agent_id, args.region)
    
    if args.test == 'all':
        tester.run_all_tests()
    elif args.test == 'basic':
        tester.test_basic_responses()
    elif args.test == 'calc':
        tester.test_calculation()
    elif args.test == 'context':
        tester.test_conversation_context()
    elif args.test == 'perf':
        tester.test_performance()


if __name__ == "__main__":
    main()
