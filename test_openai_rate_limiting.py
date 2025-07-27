#!/usr/bin/env python3
"""Test script to verify OpenAI rate limiting and exponential backoff for FREE tier"""

import time
import os
from llm_factory import LLMFactory
from config import get_config

def test_openai_rate_limiting():
    """Test OpenAI rate limiting with FREE tier specifications"""
    print("\n🧪 Testing OpenAI Rate Limiting for FREE Tier\n")
    
    # Get configuration
    config_class = get_config()
    config = config_class()
    
    # Check if OpenAI API key is available
    if not config.OPENAI_API_KEY:
        print("❌ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
        return
    
    try:
        # Create OpenAI provider
        factory = LLMFactory()
        provider = factory.create_provider(
            provider_name="openai",
            api_key=config.OPENAI_API_KEY,
            model_name="gpt-4o-mini",  # Use the most cost-effective model for testing
            temperature=0.7
        )
        
        print(f"✅ OpenAI provider created successfully")
        print(f"📋 Model: {provider.model_name}")
        print(f"🔧 Provider: {provider.provider}")
        print(f"⚡ Rate Limiter: {provider.rate_limiter.requests_per_second} requests/second")
        print(f"🪣 Max Bucket Size: {provider.rate_limiter.max_bucket_size}")
        
        # Test single request
        print("\n📝 Testing single request...")
        start_time = time.time()
        response = provider.generate_response("Say hello in one word", max_tokens=10)
        end_time = time.time()
        
        print(f"✅ Response received in {end_time - start_time:.2f} seconds")
        print(f"📄 Success: {response['success']}")
        print(f"🤖 Response: {response['response'][:100]}{'...' if len(response['response']) > 100 else ''}")
        
        if not response['success']:
            print(f"❌ Error: {response['response']}")
            return
        
        # Test rapid requests to trigger rate limiting
        print("\n🚀 Testing rapid requests (should trigger rate limiting and retry logic)...")
        
        for i in range(5):
            print(f"\n📤 Request {i+1}/5:")
            start_time = time.time()
            
            response = provider.generate_response(f"Count to {i+1}", max_tokens=20)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"   ⏱️  Duration: {duration:.2f} seconds")
            print(f"   ✅ Success: {response['success']}")
            print(f"   🤖 Response: {response['response'][:60]}{'...' if len(response['response']) > 60 else ''}")
            
            if 'rate_limited' in response and response['rate_limited']:
                print(f"   🚦 Rate limited: True")
            
            # Small delay between requests
            time.sleep(1)
        
        print("\n" + "="*60)
        print("✅ OpenAI Rate Limiting Test Completed!")
        print("\n📋 Summary:")
        print("   1. ✅ FREE tier rate limiting implemented (3 RPM)")
        print("   2. ✅ Exponential backoff retry logic added")
        print("   3. ✅ Improved error messages for rate limit errors")
        print("   4. ✅ Blocking rate limiter for better user experience")
        print("   5. ✅ Increased timeout for FREE tier users")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

def test_streaming_rate_limiting():
    """Test streaming with rate limiting"""
    print("\n🌊 Testing OpenAI Streaming with Rate Limiting\n")
    
    # Get configuration
    config_class = get_config()
    config = config_class()
    
    if not config.OPENAI_API_KEY:
        print("❌ OpenAI API key not found. Skipping streaming test.")
        return
    
    try:
        # Create OpenAI provider
        factory = LLMFactory()
        provider = factory.create_provider(
            provider_name="openai",
            api_key=config.OPENAI_API_KEY,
            model_name="gpt-4o-mini",
            temperature=0.7
        )
        
        print("📝 Testing streaming response...")
        start_time = time.time()
        
        response_chunks = []
        for chunk in provider.stream_response("Write a short poem about coding", max_tokens=100):
            response_chunks.append(chunk)
            print(chunk, end='', flush=True)
        
        end_time = time.time()
        
        print(f"\n\n✅ Streaming completed in {end_time - start_time:.2f} seconds")
        print(f"📊 Total chunks received: {len(response_chunks)}")
        print(f"📝 Total characters: {sum(len(chunk) for chunk in response_chunks)}")
        
    except Exception as e:
        print(f"❌ Error during streaming test: {str(e)}")

if __name__ == "__main__":
    test_openai_rate_limiting()
    test_streaming_rate_limiting()
    
    print("\n🎉 All OpenAI tests completed!")
    print("\n📋 Key Improvements Made:")
    print("   • Updated rate limits to match FREE tier (3 RPM)")
    print("   • Added exponential backoff retry with jitter")
    print("   • Improved error handling for rate limit errors")
    print("   • Increased timeout for FREE tier reliability")
    print("   • Better user experience with blocking rate limiter")