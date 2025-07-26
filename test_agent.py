#!/usr/bin/env python3
"""
Test script for the Memory Agentic system
This script demonstrates the agent's capabilities and memory management
"""

import os
import sys
import time
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AgentTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session_id = "test_session"
    
    def test_health(self):
        """Test the health endpoint"""
        print("🔍 Testing health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data['message']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Make sure the Flask app is running.")
            return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_memory_status(self):
        """Test memory status endpoint"""
        print(f"\n🧠 Testing memory status for session '{self.session_id}'...")
        try:
            response = requests.get(f"{self.base_url}/memory/status/{self.session_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Memory status retrieved:")
                print(f"   Session ID: {data['session_id']}")
                print(f"   Message count: {data['message_count']}")
                print(f"   Recent messages: {len(data['messages'])}")
                return True
            else:
                print(f"❌ Memory status failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Memory status error: {e}")
            return False
    
    def test_chat_simple(self, message):
        """Test simple chat without streaming"""
        print(f"\n💬 Testing simple chat: '{message}'")
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "message": message,
                    "session_id": self.session_id
                },
                stream=True
            )
            
            if response.status_code == 200:
                print("✅ Chat response received (streaming):")
                full_response = ""
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if data.get('type') == 'content':
                                    full_response += data.get('token', '')
                                elif data.get('type') == 'action':
                                    print(f"   🔧 {data.get('token', '').strip()}")
                                elif data.get('type') == 'observation':
                                    print(f"   👁️ {data.get('token', '').strip()}")
                                elif data.get('type') == 'end':
                                    break
                                elif data.get('type') == 'error':
                                    print(f"   ❌ Error: {data.get('error')}")
                                    return False
                            except json.JSONDecodeError:
                                continue
                
                print(f"   🤖 Final response: {full_response.strip()}")
                return True
            else:
                print(f"❌ Chat failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return False
    
    def test_memory_persistence(self):
        """Test memory persistence across multiple messages"""
        print("\n🔄 Testing memory persistence...")
        
        # First message
        success1 = self.test_chat_simple("My name is Alice and I like pizza.")
        if not success1:
            return False
        
        time.sleep(2)
        
        # Second message that should remember the first
        success2 = self.test_chat_simple("What's my name and what do I like?")
        if not success2:
            return False
        
        return True
    
    def test_tools(self):
        """Test the agent's tools"""
        print("\n🛠️ Testing agent tools...")
        
        # Test calculator tool
        calc_success = self.test_chat_simple("Calculate 15 * 7 + 23")
        if not calc_success:
            return False
        
        time.sleep(2)
        
        # Test memory info tool
        memory_success = self.test_chat_simple("How many messages are in our conversation memory?")
        if not memory_success:
            return False
        
        time.sleep(2)
        
        # Test search tool
        search_success = self.test_chat_simple("Search for information about Python programming")
        if not search_success:
            return False
        
        return True
    
    def test_clear_memory(self):
        """Test memory clearing"""
        print(f"\n🗑️ Testing memory clearing for session '{self.session_id}'...")
        try:
            response = requests.delete(f"{self.base_url}/memory/clear/{self.session_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Memory cleared: {data['message']}")
                return True
            else:
                print(f"❌ Memory clear failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Memory clear error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Memory Agentic Test Suite")
        print("=" * 50)
        
        # Check if API key is set
        if not os.getenv("GOOGLE_API_KEY"):
            print("❌ GOOGLE_API_KEY not found in environment variables")
            print("Please set up your .env file with a valid Google API key")
            return False
        
        tests = [
            ("Health Check", self.test_health),
            ("Memory Status", self.test_memory_status),
            ("Simple Chat", lambda: self.test_chat_simple("Hello! Can you introduce yourself?")),
            ("Memory Persistence", self.test_memory_persistence),
            ("Tool Testing", self.test_tools),
            ("Memory Status After Chat", self.test_memory_status),
            ("Clear Memory", self.test_clear_memory),
            ("Memory Status After Clear", self.test_memory_status),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"❌ {test_name} ERROR: {e}")
            
            time.sleep(1)  # Small delay between tests
        
        print("\n" + "=" * 50)
        print(f"🏁 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your Memory Agentic system is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
        
        return passed == total

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Memory Agentic Test Script")
            print("Usage: python test_agent.py [--help]")
            print("")
            print("Make sure to:")
            print("1. Start the Flask server: python app.py")
            print("2. Set up your .env file with GOOGLE_API_KEY")
            print("3. Run this test script")
            return
    
    tester = AgentTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()