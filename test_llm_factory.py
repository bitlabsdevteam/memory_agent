#!/usr/bin/env python3
"""Test script for LLM Factory functionality"""

import os
import sys
from dotenv import load_dotenv
from llm_factory import LLMFactory
from config import get_config

# Load environment variables
load_dotenv()

def test_provider(provider_name: str):
    """Test a specific LLM provider"""
    print(f"\n🧪 Testing {provider_name} provider...")
    
    try:
        # Create provider from config
        provider = LLMFactory.create_from_config(provider_name)
        print(f"✅ Successfully initialized {provider_name}")
        
        # Test simple generation
        test_prompt = "Hello! Please respond with a brief greeting and tell me what LLM you are."
        print(f"📝 Test prompt: {test_prompt}")
        
        result = provider.generate_response(test_prompt, max_tokens=100)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            print(f"📊 Provider: {result.get('provider', 'unknown')}")
            print(f"🤖 Model: {result.get('model', 'unknown')}")
        else:
            print(f"❌ Failed: {result['response']}")
            
        # Test streaming
        print(f"\n🌊 Testing streaming for {provider_name}...")
        stream_response = ""
        for token in provider.stream_response("Count from 1 to 5, one number per response.", max_tokens=50):
            stream_response += token
            print(token, end="", flush=True)
        print(f"\n✅ Streaming completed. Full response: {stream_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing {provider_name}: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 LLM Factory Test Suite")
    print("=" * 50)
    
    # Get configuration
    config_class = get_config()
    config = config_class()
    
    # Print configuration
    config.print_config()
    
    # Get available providers
    available_providers = LLMFactory.get_available_providers()
    print(f"\n📋 Available providers: {available_providers}")
    
    # Test each provider that has an API key configured
    successful_providers = []
    failed_providers = []
    
    for provider in available_providers:
        if test_provider(provider):
            successful_providers.append(provider)
        else:
            failed_providers.append(provider)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"✅ Successful providers: {successful_providers}")
    print(f"❌ Failed providers: {failed_providers}")
    
    if successful_providers:
        print(f"\n🎉 {len(successful_providers)} provider(s) are working correctly!")
    else:
        print("\n⚠️  No providers are working. Please check your API keys in the .env file.")
        print("\n💡 Make sure you have at least one of these API keys configured:")
        print("   - GOOGLE_API_KEY (for Google Gemini)")
        print("   - OPENAI_API_KEY (for OpenAI)")
        print("   - GROQ_API_KEY (for Groq/DeepSeek)")

if __name__ == "__main__":
    main()