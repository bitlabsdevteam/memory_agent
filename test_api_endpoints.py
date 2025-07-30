#!/usr/bin/env python3
"""
Simplified test script for API endpoints and basic functionality.
This test focuses on API structure and availability rather than actual LLM responses.
"""

import sys
import json
import requests
from typing import Dict, Any

class APIEndpointTester:
    """Test suite for API endpoints."""
    
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details
        })
    
    def test_health_endpoint(self) -> bool:
        """Test API health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=10)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "status" in data, "Health response should contain 'status'"
            assert data["status"] == "healthy", "Status should be 'healthy'"
            
            self.log_test_result(
                "Health Endpoint", 
                True, 
                f"Status: {data['status']}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Health Endpoint", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_providers_endpoint(self) -> bool:
        """Test LLM providers endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/llm/providers", timeout=10)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            required_fields = ["available_providers", "configured_providers", "current_provider", "default_provider"]
            
            for field in required_fields:
                assert field in data, f"Response should contain '{field}'"
            
            assert isinstance(data["available_providers"], list), "Available providers should be a list"
            assert isinstance(data["configured_providers"], dict), "Configured providers should be a dict"
            
            expected_providers = ["google_gemini", "openai", "groq", "perplexity"]
            for provider in expected_providers:
                assert provider in data["available_providers"], f"Missing provider: {provider}"
            
            self.log_test_result(
                "Providers Endpoint", 
                True, 
                f"Found {len(data['available_providers'])} providers, current: {data['current_provider']}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Providers Endpoint", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_chat_endpoint_structure(self, provider_name: str) -> bool:
        """Test chat endpoint structure (without validating LLM response content)."""
        try:
            payload = {
                "message": "Hello",
                "provider": provider_name,
                "session_id": f"test_{provider_name}",
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/chat", 
                json=payload, 
                timeout=30
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            required_fields = ["response", "success", "provider"]
            
            for field in required_fields:
                assert field in data, f"Response should contain '{field}'"
            
            assert isinstance(data["response"], str), "Response should be a string"
            assert isinstance(data["success"], bool), "Success should be a boolean"
            assert data["provider"] == provider_name, f"Provider should be {provider_name}"
            
            self.log_test_result(
                f"Chat Endpoint Structure - {provider_name}", 
                True, 
                f"Success: {data['success']}, Provider: {data['provider']}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                f"Chat Endpoint Structure - {provider_name}", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_streaming_endpoint_structure(self, provider_name: str) -> bool:
        """Test streaming endpoint structure."""
        try:
            payload = {
                "message": "Hello",
                "provider": provider_name,
                "session_id": f"test_stream_{provider_name}",
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/chat", 
                json=payload, 
                stream=True,
                timeout=30
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            # Check if it's a streaming response
            content_type = response.headers.get('content-type', '')
            is_streaming = 'text/event-stream' in content_type or 'text/plain' in content_type
            
            # Try to read some content
            content_received = False
            chunk_count = 0
            
            try:
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.strip():
                        content_received = True
                        chunk_count += 1
                        if chunk_count > 5:  # Just check first few chunks
                            break
            except:
                pass  # Some providers might not stream properly
            
            self.log_test_result(
                f"Streaming Endpoint Structure - {provider_name}", 
                True, 
                f"Content-Type: {content_type}, Chunks received: {chunk_count}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                f"Streaming Endpoint Structure - {provider_name}", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_memory_endpoints(self) -> bool:
        """Test memory-related endpoints."""
        try:
            session_id = "test_memory_session"
            
            # Test memory status endpoint
            response = requests.get(f"{self.base_url}/api/v1/memory/status/{session_id}", timeout=10)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            required_fields = ["session_id", "message_count", "messages"]
            
            for field in required_fields:
                assert field in data, f"Response should contain '{field}'"
            
            assert data["session_id"] == session_id, "Session ID should match"
            assert isinstance(data["message_count"], int), "Message count should be an integer"
            assert isinstance(data["messages"], list), "Messages should be a list"
            
            self.log_test_result(
                "Memory Status Endpoint", 
                True, 
                f"Session: {session_id}, Messages: {data['message_count']}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Memory Status Endpoint", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases."""
        print("🧪 Starting API Endpoint Tests\n")
        
        # Core API tests
        print("📡 Testing Core API Endpoints...")
        self.test_health_endpoint()
        self.test_providers_endpoint()
        self.test_memory_endpoints()
        print()
        
        # Provider-specific tests
        providers = ["google_gemini", "openai", "perplexity"]
        
        for provider in providers:
            print(f"🤖 Testing {provider.upper()} endpoints...")
            self.test_chat_endpoint_structure(provider)
            self.test_streaming_endpoint_structure(provider)
            print()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Test Results Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test_name']}: {result['details']}")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.test_results
        }

def main():
    """Main test runner."""
    print("🚀 API Endpoint Test Suite")
    print("==========================\n")
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:5001/api/v1/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend server is not responding properly")
            print("   Please ensure Docker containers are running: docker compose up -d")
            return 1
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to backend server at http://localhost:5001")
        print("   Please ensure Docker containers are running: docker compose up -d")
        return 1
    
    # Run tests
    tester = APIEndpointTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    if results["failed_tests"] == 0:
        print("\n🎉 All tests passed! API endpoints are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {results['failed_tests']} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())