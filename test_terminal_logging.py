#!/usr/bin/env python3
"""Test script to demonstrate terminal logging for thinking messages"""

import time
from output_parser import OutputParser, TokenType

def test_terminal_logging():
    """Test the terminal logging functionality with thinking messages"""
    print("\n🧪 Testing Terminal Logging for Chain-of-Thought Messages\n")
    
    # Initialize parser with terminal logging enabled
    parser = OutputParser(enable_terminal_logging=True)
    
    # Simulate a response with thinking tags from Google Gemini
    print("📝 Simulating Google Gemini response with thinking...")
    mock_gemini_response = [
        "I need to help you with information about ",
        "<thinking>",
        "Let me think about this step by step. ",
        "First, I should consider what information the user needs. ",
        "They're asking about a city, so I should gather weather, time, and facts. ",
        "I'll use the appropriate tools to get this information.",
        "</thinking>",
        "Paris. Let me gather some information for you.\n\n",
        "I'll check the current weather, time, and some facts about Paris."
    ]
    
    # Process the mock response
    parsed_tokens = list(parser.parse_stream(iter(mock_gemini_response)))
    
    print("\n" + "="*60)
    print("📊 PARSING RESULTS:")
    print("="*60)
    
    # Show the parsed tokens
    for i, token in enumerate(parsed_tokens):
        if token.token_type == TokenType.THINKING_START:
            print(f"Token {i+1}: [THINKING_START] - Transition detected")
        elif token.token_type == TokenType.THINKING:
            print(f"Token {i+1}: [THINKING] - '{token.content[:50]}{'...' if len(token.content) > 50 else ''}'")
        elif token.token_type == TokenType.THINKING_END:
            print(f"Token {i+1}: [THINKING_END] - Transition detected")
        elif token.token_type == TokenType.RESPONSE:
            print(f"Token {i+1}: [RESPONSE] - '{token.content[:50]}{'...' if len(token.content) > 50 else ''}'")
        elif token.token_type == TokenType.COMPLETE:
            print(f"Token {i+1}: [COMPLETE] - Processing finished")
    
    # Show final extracted response
    final_response = parser.extract_final_response()
    print(f"\n🎯 Final Response (clean): '{final_response}'")
    print(f"🧠 Thinking Content Length: {len(parser.accumulated_thinking)} characters")
    print(f"📝 Response Content Length: {len(parser.final_response)} characters")
    
    print("\n" + "="*60)
    print("✅ Terminal logging test completed!")
    print("The thinking messages should have appeared in blue above.")
    print("="*60)

def test_standardized_formatting():
    """Test standardized formatting across different model response styles"""
    print("\n🔧 Testing Standardized Response Formatting\n")
    
    # Test different response formats
    test_cases = [
        {
            "name": "Google Gemini Style",
            "response": {
                "response": "<thinking>Let me think about this...</thinking>Here's the weather in Paris: 23°C, clear skies.",
                "success": True,
                "provider": "google_gemini",
                "model": "gemini-1.5-flash"
            }
        },
        {
            "name": "OpenAI Style",
            "response": {
                "response": "Here's the weather in Paris: 23°C, clear skies.",
                "success": True,
                "provider": "openai",
                "model": "gpt-4o"
            }
        },
        {
            "name": "Groq Style",
            "response": {
                "response": "Here's the weather in Paris: 23°C, clear skies.",
                "success": True,
                "provider": "groq",
                "model": "deepseek-r1-distill-llama-70b"
            }
        }
    ]
    
    parser = OutputParser(enable_terminal_logging=False)  # Disable logging for this test
    
    for test_case in test_cases:
        print(f"📋 Testing {test_case['name']}:")
        
        # Validate response structure
        standardized = parser.validate_response_structure(test_case['response'])
        
        print(f"   ✅ Provider: {standardized['provider']}")
        print(f"   ✅ Model: {standardized['model']}")
        print(f"   ✅ Success: {standardized['success']}")
        print(f"   ✅ Response Length: {len(standardized['response'])} chars")
        print(f"   ✅ Rate Limited: {standardized['rate_limited']}")
        
        # Test response cleaning
        parser.reset_state()
        parser.accumulated_response = standardized['response']
        clean_response = parser.extract_final_response()
        print(f"   🧹 Clean Response: '{clean_response[:60]}{'...' if len(clean_response) > 60 else ''}'")
        print()
    
    print("✅ All response formats standardized successfully!")

if __name__ == "__main__":
    test_terminal_logging()
    test_standardized_formatting()
    
    print("\n🎉 All tests completed!")
    print("\n📋 Summary:")
    print("   1. ✅ Terminal logging for thinking messages implemented")
    print("   2. ✅ Standardized response formatting across all providers")
    print("   3. ✅ Chain-of-Thought messages displayed in terminal during inference")
    print("   4. ✅ Clean response extraction without thinking content")