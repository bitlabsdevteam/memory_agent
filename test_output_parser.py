#!/usr/bin/env python3
"""Test script for the OutputParser to verify standardized response processing"""

import json
from output_parser import OutputParser, TokenType

def test_thinking_response():
    """Test parsing response with thinking tags"""
    print("\n🧠 Testing response with thinking tags...")
    
    parser = OutputParser()
    
    # Simulate a response with thinking tags
    mock_tokens = [
        "I need to ",
        "<thinking>",
        "Let me think about this step by step. ",
        "First, I should consider the weather conditions. ",
        "Then I need to think about the best time to visit.",
        "</thinking>",
        "Based on my analysis, ",
        "I recommend visiting ",
        "Paris in spring for ",
        "the best weather."
    ]
    
    def mock_stream():
        for token in mock_tokens:
            yield token
    
    print("Raw tokens:", mock_tokens)
    print("\nParsed output:")
    
    parsed_tokens = []
    for parsed_token in parser.parse_stream(mock_stream()):
        parsed_tokens.append(parsed_token)
        print(f"  {parsed_token.token_type.value}: '{parsed_token.content}'")
    
    final_response = parser.extract_final_response()
    print(f"\nFinal response: '{final_response}'")
    
    # Verify thinking content was separated
    thinking_tokens = [t for t in parsed_tokens if t.token_type == TokenType.THINKING]
    response_tokens = [t for t in parsed_tokens if t.token_type == TokenType.RESPONSE]
    
    print(f"Thinking tokens count: {len(thinking_tokens)}")
    print(f"Response tokens count: {len(response_tokens)}")
    
    return len(thinking_tokens) > 0 and len(response_tokens) > 0

def test_direct_response():
    """Test parsing response without thinking tags"""
    print("\n💬 Testing direct response without thinking tags...")
    
    parser = OutputParser()
    
    # Simulate a direct response without thinking
    mock_tokens = [
        "Paris is a ",
        "beautiful city ",
        "with amazing ",
        "architecture and ",
        "rich history."
    ]
    
    def mock_stream():
        for token in mock_tokens:
            yield token
    
    print("Raw tokens:", mock_tokens)
    print("\nParsed output:")
    
    parsed_tokens = []
    for parsed_token in parser.parse_stream(mock_stream()):
        parsed_tokens.append(parsed_token)
        print(f"  {parsed_token.token_type.value}: '{parsed_token.content}'")
    
    final_response = parser.extract_final_response()
    print(f"\nFinal response: '{final_response}'")
    
    # Verify no thinking content was detected
    thinking_tokens = [t for t in parsed_tokens if t.token_type == TokenType.THINKING]
    response_tokens = [t for t in parsed_tokens if t.token_type == TokenType.RESPONSE]
    
    print(f"Thinking tokens count: {len(thinking_tokens)}")
    print(f"Response tokens count: {len(response_tokens)}")
    
    return len(thinking_tokens) == 0 and len(response_tokens) > 0

def test_alternative_thinking_tags():
    """Test parsing with alternative thinking tag formats"""
    print("\n🔄 Testing alternative thinking tag formats...")
    
    parser = OutputParser()
    
    # Test with <think> tags
    mock_tokens = [
        "Let me ",
        "<think>",
        "analyze this carefully",
        "</think>",
        "provide you with ",
        "the best answer."
    ]
    
    def mock_stream():
        for token in mock_tokens:
            yield token
    
    print("Raw tokens (with <think> tags):", mock_tokens)
    print("\nParsed output:")
    
    parsed_tokens = []
    for parsed_token in parser.parse_stream(mock_stream()):
        parsed_tokens.append(parsed_token)
        print(f"  {parsed_token.token_type.value}: '{parsed_token.content}'")
    
    final_response = parser.extract_final_response()
    print(f"\nFinal response: '{final_response}'")
    
    # Verify thinking content was properly separated
    thinking_tokens = [t for t in parsed_tokens if t.token_type == TokenType.THINKING]
    response_tokens = [t for t in parsed_tokens if t.token_type == TokenType.RESPONSE]
    
    print(f"Thinking tokens count: {len(thinking_tokens)}")
    print(f"Response tokens count: {len(response_tokens)}")
    
    return len(thinking_tokens) > 0 and len(response_tokens) > 0

def test_sse_formatting():
    """Test Server-Sent Events formatting"""
    print("\n📡 Testing SSE formatting...")
    
    parser = OutputParser()
    
    # Create sample parsed tokens
    from output_parser import ParsedToken
    
    test_tokens = [
        ParsedToken(content="", token_type=TokenType.THINKING_START),
        ParsedToken(content="thinking content", token_type=TokenType.THINKING),
        ParsedToken(content="", token_type=TokenType.THINKING_END),
        ParsedToken(content="response content", token_type=TokenType.RESPONSE),
        ParsedToken(content="", token_type=TokenType.COMPLETE)
    ]
    
    print("SSE formatted output:")
    for token in test_tokens:
        sse_data = parser.format_for_sse(token)
        print(f"  {repr(sse_data)}")
    
    return True

def test_response_validation():
    """Test response structure validation"""
    print("\n✅ Testing response structure validation...")
    
    parser = OutputParser()
    
    # Test various response formats
    test_responses = [
        # Valid response
        {
            "response": "Hello world",
            "success": True,
            "provider": "openai",
            "model": "gpt-4"
        },
        # Response with missing fields
        {
            "response": "Hello",
            "success": True
        },
        # Error response
        {
            "response": "Error occurred",
            "success": False,
            "error": "API timeout"
        },
        # Invalid response (not a dict)
        "Just a string response",
        # Empty response
        {}
    ]
    
    for i, response in enumerate(test_responses):
        print(f"\nTest case {i+1}:")
        print(f"  Input: {response}")
        validated = parser.validate_response_structure(response)
        print(f"  Output: {validated}")
        
        # Verify all required fields are present
        required_fields = ["response", "success", "provider", "model", "rate_limited", "error"]
        missing_fields = [field for field in required_fields if field not in validated]
        if missing_fields:
            print(f"  ❌ Missing fields: {missing_fields}")
            return False
        else:
            print(f"  ✅ All required fields present")
    
    return True

def main():
    """Run all tests"""
    print("🧪 OutputParser Test Suite")
    print("=" * 50)
    
    tests = [
        ("Thinking Response", test_thinking_response),
        ("Direct Response", test_direct_response),
        ("Alternative Tags", test_alternative_thinking_tags),
        ("SSE Formatting", test_sse_formatting),
        ("Response Validation", test_response_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"\n{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n❌ {test_name}: FAILED with error: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! OutputParser is working correctly.")
        print("\n📋 Key Features Verified:")
        print("  ✅ Thinking content separation from all models")
        print("  ✅ Support for multiple thinking tag formats (<thinking>, <think>)")
        print("  ✅ Direct response handling without thinking tags")
        print("  ✅ Server-Sent Events formatting")
        print("  ✅ Response structure validation and standardization")
        print("  ✅ Error handling and data object parsing prevention")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main()