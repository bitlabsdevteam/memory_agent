#!/usr/bin/env python3
"""
Example usage script for Memory Agentic system
This script demonstrates various features and capabilities
"""

import requests
import json
import time
from typing import Generator

class MemoryAgenticClient:
    """Client for interacting with the Memory Agentic API"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session_id = "example_session"
    
    def health_check(self) -> bool:
        """Check if the server is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
    
    def chat_stream(self, message: str, session_id: str = None) -> Generator[dict, None, None]:
        """Send a message and stream the response"""
        if session_id is None:
            session_id = self.session_id
            
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={"message": message, "session_id": session_id},
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            yield data
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield {"type": "error", "error": str(e)}
    
    def get_memory_status(self, session_id: str = None) -> dict:
        """Get memory status for a session"""
        if session_id is None:
            session_id = self.session_id
            
        try:
            response = requests.get(f"{self.base_url}/memory/status/{session_id}")
            return response.json() if response.status_code == 200 else {}
        except:
            return {}
    
    def clear_memory(self, session_id: str = None) -> dict:
        """Clear memory for a session"""
        if session_id is None:
            session_id = self.session_id
            
        try:
            response = requests.delete(f"{self.base_url}/memory/clear/{session_id}")
            return response.json() if response.status_code == 200 else {}
        except:
            return {}

def print_stream_response(client: MemoryAgenticClient, message: str):
    """Print streaming response in a formatted way"""
    print(f"\n👤 User: {message}")
    print("🤖 Assistant: ", end="", flush=True)
    
    full_response = ""
    for chunk in client.chat_stream(message):
        if chunk.get('type') == 'content':
            token = chunk.get('token', '')
            print(token, end="", flush=True)
            full_response += token
        elif chunk.get('type') == 'action':
            print(f"\n   🔧 {chunk.get('token', '').strip()}")
        elif chunk.get('type') == 'observation':
            print(f"   👁️  {chunk.get('token', '').strip()}")
        elif chunk.get('type') == 'error':
            print(f"\n   ❌ Error: {chunk.get('error')}")
            return
        elif chunk.get('type') == 'end':
            break
    
    print()  # New line after response
    return full_response

def demonstrate_basic_conversation(client: MemoryAgenticClient):
    """Demonstrate basic conversation capabilities"""
    print("\n" + "="*60)
    print("🗣️  BASIC CONVERSATION DEMONSTRATION")
    print("="*60)
    
    messages = [
        "Hello! What's your name and what can you do?",
        "Can you tell me a bit about LangChain and React agents?",
        "What tools do you have access to?"
    ]
    
    for message in messages:
        print_stream_response(client, message)
        time.sleep(1)

def demonstrate_memory_persistence(client: MemoryAgenticClient):
    """Demonstrate memory persistence across messages"""
    print("\n" + "="*60)
    print("🧠 MEMORY PERSISTENCE DEMONSTRATION")
    print("="*60)
    
    # Set up some context
    print_stream_response(client, "My name is Alice, I'm 25 years old, and I work as a data scientist in San Francisco.")
    time.sleep(1)
    
    print_stream_response(client, "I love hiking and photography in my free time.")
    time.sleep(1)
    
    # Test memory recall
    print_stream_response(client, "What do you remember about me?")
    time.sleep(1)
    
    print_stream_response(client, "What's my profession and where do I work?")
    time.sleep(1)

def demonstrate_tool_usage(client: MemoryAgenticClient):
    """Demonstrate various tool capabilities"""
    print("\n" + "="*60)
    print("🛠️  TOOL USAGE DEMONSTRATION")
    print("="*60)
    
    # Calculator tool
    print_stream_response(client, "Can you calculate 15 * 23 + 47 - 12?")
    time.sleep(1)
    
    # Search tool
    print_stream_response(client, "Search for information about machine learning algorithms")
    time.sleep(1)
    
    # Memory info tool
    print_stream_response(client, "How many messages do we have in our conversation history?")
    time.sleep(1)
    
    # Complex calculation
    print_stream_response(client, "What's the square root of 144 plus 25% of 200?")
    time.sleep(1)

def demonstrate_memory_management(client: MemoryAgenticClient):
    """Demonstrate memory management features"""
    print("\n" + "="*60)
    print("💾 MEMORY MANAGEMENT DEMONSTRATION")
    print("="*60)
    
    # Check current memory status
    memory_status = client.get_memory_status()
    print(f"📊 Current memory status:")
    print(f"   Session ID: {memory_status.get('session_id', 'N/A')}")
    print(f"   Message count: {memory_status.get('message_count', 0)}")
    print(f"   Recent messages: {len(memory_status.get('messages', []))}")
    
    # Add more messages to test memory optimization
    for i in range(3):
        print_stream_response(client, f"This is test message number {i+1} to fill up memory.")
        time.sleep(0.5)
    
    # Check memory status again
    memory_status = client.get_memory_status()
    print(f"\n📊 Updated memory status:")
    print(f"   Message count: {memory_status.get('message_count', 0)}")
    
    # Clear memory
    print("\n🗑️  Clearing memory...")
    clear_result = client.clear_memory()
    print(f"   Result: {clear_result.get('message', 'Unknown')}")
    
    # Check memory status after clearing
    memory_status = client.get_memory_status()
    print(f"\n📊 Memory status after clearing:")
    print(f"   Message count: {memory_status.get('message_count', 0)}")

def demonstrate_multi_session(client: MemoryAgenticClient):
    """Demonstrate multiple session handling"""
    print("\n" + "="*60)
    print("👥 MULTI-SESSION DEMONSTRATION")
    print("="*60)
    
    # Session 1
    print("\n🔵 Session 1 (Alice):")
    client.session_id = "alice_session"
    print_stream_response(client, "Hi, I'm Alice and I love cats.")
    
    # Session 2
    print("\n🟢 Session 2 (Bob):")
    client.session_id = "bob_session"
    print_stream_response(client, "Hello, I'm Bob and I prefer dogs.")
    
    # Back to Session 1
    print("\n🔵 Back to Session 1 (Alice):")
    client.session_id = "alice_session"
    print_stream_response(client, "What do you remember about my pet preference?")
    
    # Back to Session 2
    print("\n🟢 Back to Session 2 (Bob):")
    client.session_id = "bob_session"
    print_stream_response(client, "What do you remember about my pet preference?")
    
    # Show memory status for both sessions
    print("\n📊 Memory status comparison:")
    alice_memory = client.get_memory_status("alice_session")
    bob_memory = client.get_memory_status("bob_session")
    
    print(f"   Alice's session: {alice_memory.get('message_count', 0)} messages")
    print(f"   Bob's session: {bob_memory.get('message_count', 0)} messages")

def main():
    """Main demonstration function"""
    print("🚀 Memory Agentic - Comprehensive Feature Demonstration")
    print("=" * 70)
    
    # Initialize client
    client = MemoryAgenticClient()
    
    # Health check
    print("🔍 Checking server health...")
    if not client.health_check():
        print("❌ Server is not running. Please start the Flask app first:")
        print("   python app.py")
        return
    
    print("✅ Server is healthy!")
    
    try:
        # Run demonstrations
        demonstrate_basic_conversation(client)
        demonstrate_memory_persistence(client)
        demonstrate_tool_usage(client)
        demonstrate_memory_management(client)
        demonstrate_multi_session(client)
        
        print("\n" + "="*70)
        print("🎉 DEMONSTRATION COMPLETE!")
        print("="*70)
        print("\n💡 Key features demonstrated:")
        print("   ✅ Real-time streaming responses")
        print("   ✅ Persistent conversation memory")
        print("   ✅ Tool integration (calculator, search, memory info)")
        print("   ✅ Memory optimization and management")
        print("   ✅ Multi-session isolation")
        print("   ✅ React agent reasoning pattern")
        print("\n🌐 Try the web interface by opening client.html in your browser!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during demonstration: {e}")

if __name__ == "__main__":
    main()