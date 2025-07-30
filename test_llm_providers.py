#!/usr/bin/env python3
"""Comprehensive test script for GEMINI, OpenAI, and Perplexity LLM providers.

This script tests:
1. LLM provider initialization and functionality
2. API endpoint responses for all three models
3. Error handling and edge cases
4. Streaming functionality
"""

import sys
import json
import time
import requests
from typing import Dict, Any, List
from config import Config
from llm_factory import LLMFactory
from agents.trip_agent import TripAgent
from output_parser import OutputParser

class LLMProviderTester:
    """Test suite for LLM providers and API endpoints."""
    
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_results = []
        self.output_parser = OutputParser(enable_terminal_logging=False)
        
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
    
    def test_llm_provider_initialization(self, provider_name: str) -> bool:
        """Test LLM provider initialization."""
        try:
            llm_provider = LLMFactory.create_from_config(provider_name, [])
            if llm_provider is None:
                self.log_test_result(
                    f"LLM Provider Init - {provider_name}", 
                    False, 
                    "Provider returned None (likely missing API key)"
                )
                return False
            
            # Test basic attributes
            assert hasattr(llm_provider, 'provider'), "Missing provider attribute"
            assert hasattr(llm_provider, 'model_name'), "Missing model_name attribute"
            
            self.log_test_result(
                f"LLM Provider Init - {provider_name}", 
                True, 
                f"Provider: {llm_provider.provider}, Model: {llm_provider.model_name}"
            )
            return True
            
        except ValueError as e:
            if "API key not found" in str(e):
                self.log_test_result(
                    f"LLM Provider Init - {provider_name}", 
                    False, 
                    "API key not configured (expected for testing)"
                )
                return False
            else:
                self.log_test_result(
                    f"LLM Provider Init - {provider_name}", 
                    False, 
                    f"ValueError: {str(e)}"
                )
                return False
        except Exception as e:
            self.log_test_result(
                f"LLM Provider Init - {provider_name}", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_llm_provider_response(self, provider_name: str) -> bool:
        """Test LLM provider response generation."""
        try:
            llm_provider = LLMFactory.create_from_config(provider_name, [])
            if llm_provider is None:
                self.log_test_result(
                    f"LLM Response - {provider_name}", 
                    False, 
                    "Provider not available (missing API key)"
                )
                return False
            
            # Test simple response
            test_prompt = "Say 'Hello, this is a test response' and nothing else."
            response = llm_provider.generate_response(test_prompt, max_tokens=50)
            
            # Response should be a dict with 'response' key
            assert isinstance(response, dict), "Response should be a dictionary"
            assert "response" in response, "Response should contain 'response' key"
            assert "success" in response, "Response should contain 'success' key"
            
            response_text = response["response"]
            assert isinstance(response_text, str), "Response text should be a string"
            assert len(response_text.strip()) > 0, "Response should not be empty"
            
            self.log_test_result(
                f"LLM Response - {provider_name}", 
                True, 
                f"Success: {response['success']}, Response length: {len(response_text)} chars"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                f"LLM Response - {provider_name}", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_llm_provider_streaming(self, provider_name: str) -> bool:
        """Test LLM provider streaming functionality."""
        try:
            llm_provider = LLMFactory.create_from_config(provider_name, [])
            if llm_provider is None:
                self.log_test_result(
                    f"LLM Streaming - {provider_name}", 
                    False, 
                    "Provider not available (missing API key)"
                )
                return False
            
            # Test streaming response
            test_prompt = "Count from 1 to 5, each number on a new line."
            token_count = 0
            
            for token in llm_provider.stream_response(test_prompt, max_tokens=50):
                assert isinstance(token, str), "Token should be a string"
                token_count += 1
                if token_count > 100:  # Prevent infinite loops
                    break
            
            assert token_count > 0, "Should receive at least one token"
            
            self.log_test_result(
                f"LLM Streaming - {provider_name}", 
                True, 
                f"Received {token_count} tokens"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                f"LLM Streaming - {provider_name}", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_api_health_endpoint(self) -> bool:
        """Test API health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=10)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "status" in data, "Health response should contain 'status'"
            assert data["status"] == "healthy", "Status should be 'healthy'"
            
            self.log_test_result(
                "API Health Endpoint", 
                True, 
                f"Status: {data['status']}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "API Health Endpoint", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_api_providers_endpoint(self) -> bool:
        """Test API providers endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/llm/providers", timeout=10)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "available_providers" in data, "Response should contain 'available_providers'"
            assert "configured_providers" in data, "Response should contain 'configured_providers'"
            assert "current_provider" in data, "Response should contain 'current_provider'"
            assert "default_provider" in data, "Response should contain 'default_provider'"
            
            assert isinstance(data["available_providers"], list), "Available providers should be a list"
            assert isinstance(data["configured_providers"], dict), "Configured providers should be a dict"
            
            expected_providers = ["google_gemini", "openai", "groq", "perplexity"]
            for provider in expected_providers:
                assert provider in data["available_providers"], f"Missing provider: {provider}"
            
            self.log_test_result(
                "API Providers Endpoint", 
                True, 
                f"Found {len(data['available_providers'])} providers, current: {data['current_provider']}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "API Providers Endpoint", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_api_chat_endpoint(self, provider_name: str) -> bool:
        """Test API chat endpoint with specific provider."""
        try:
            payload = {
                "message": "Hello, please respond with 'Test successful' and nothing else.",
                "provider": provider_name,
                "session_id": f"test_session_{provider_name}",
                "stream": False  # Explicitly request non-streaming
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/chat", 
                json=payload, 
                timeout=30
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response should contain 'response'"
            assert "success" in data, "Response should contain 'success'"
            assert data["success"] is True, "Success should be True"
            assert "provider" in data, "Response should contain 'provider'"
            
            response_text = data["response"]
            assert isinstance(response_text, str), "Response should be a string"
            assert len(response_text.strip()) > 0, "Response should not be empty"
            
            self.log_test_result(
                f"API Chat Endpoint - {provider_name}", 
                True, 
                f"Provider: {data.get('provider')}, Response length: {len(response_text)}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                f"API Chat Endpoint - {provider_name}", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_api_stream_endpoint(self, provider_name: str) -> bool:
        """Test API streaming endpoint with specific provider."""
        try:
            payload = {
                "message": "Count from 1 to 3, each number on a new line.",
                "provider": provider_name,
                "session_id": f"test_stream_{provider_name}",
                "stream": True  # Explicitly request streaming
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/chat", 
                json=payload, 
                stream=True,
                timeout=30
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert response.headers.get('content-type') == 'text/event-stream', "Should be event stream"
            
            chunk_count = 0
            content_received = False
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    # Check for any content in the stream
                    if line_str.strip():
                        chunk_count += 1
                        content_received = True
                        if chunk_count > 100:  # Prevent infinite loops
                            break
            
            assert content_received, "Should receive at least some content"
            
            self.log_test_result(
                f"API Stream Endpoint - {provider_name}", 
                True, 
                f"Received {chunk_count} chunks"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                f"API Stream Endpoint - {provider_name}", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_agent_integration(self, provider_name: str) -> bool:
        """Test agent integration with specific provider."""
        try:
            llm_provider = LLMFactory.create_from_config(provider_name, [])
            if llm_provider is None:
                self.log_test_result(
                    f"Agent Integration - {provider_name}", 
                    False, 
                    "Provider not available (missing API key)"
                )
                return False
            
            # Create agent
            agent = TripAgent(llm_provider, self.output_parser)
            
            # Test agent response
            test_message = "What's the weather like in Paris?"
            session_id = f"test_agent_{provider_name}"
            
            result = agent.process_message(test_message, session_id)
            
            assert isinstance(result, dict), "Result should be a dictionary"
            assert "response" in result, "Result should contain 'response'"
            assert "success" in result, "Result should contain 'success'"
            assert result["success"] is True, "Success should be True"
            
            response_text = result["response"]
            assert isinstance(response_text, str), "Response should be a string"
            assert len(response_text.strip()) > 0, "Response should not be empty"
            
            self.log_test_result(
                f"Agent Integration - {provider_name}", 
                True, 
                f"Response length: {len(response_text)} chars"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                f"Agent Integration - {provider_name}", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases."""
        print("🧪 Starting comprehensive LLM provider and API tests\n")
        
        # Test providers
        providers = ["google_gemini", "openai", "perplexity"]
        
        # API endpoint tests (provider-independent)
        print("📡 Testing API Endpoints...")
        self.test_api_health_endpoint()
        self.test_api_providers_endpoint()
        print()
        
        # Provider-specific tests
        for provider in providers:
            print(f"🤖 Testing {provider.upper()}...")
            
            # LLM provider tests
            self.test_llm_provider_initialization(provider)
            self.test_llm_provider_response(provider)
            self.test_llm_provider_streaming(provider)
            
            # API endpoint tests with provider
            self.test_api_chat_endpoint(provider)
            self.test_api_stream_endpoint(provider)
            
            # Agent integration tests
            self.test_agent_integration(provider)
            
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
    print("🚀 LLM Provider and API Test Suite")
    print("===================================\n")
    
    # Check if Docker containers are running
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
    tester = LLMProviderTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    if results["failed_tests"] == 0:
        print("\n🎉 All tests passed! LLM providers and API endpoints are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {results['failed_tests']} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())