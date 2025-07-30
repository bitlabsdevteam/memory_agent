#!/usr/bin/env python3
"""Test script to verify the restructured application works correctly."""

import sys
import traceback

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    try:
        # Test tool imports
        from tools import get_all_tools, TOOL_REGISTRY, get_tool_names
        from tools.weather_tool import weather_tool
        from tools.time_tool import time_tool
        from tools.city_facts_tool import city_facts_tool
        from tools.plan_city_visit_tool import plan_city_visit_tool
        
        # Test agent imports
        from agents import BaseAgent, TripAgent
        
        # Test other imports
        from llm_factory import LLMFactory
        from output_parser import OutputParser
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_tools():
    """Test that tools work correctly."""
    print("\nTesting tools...")
    try:
        # Test tool registry
        tools = get_all_tools()
        tool_names = get_tool_names()
        
        print(f"Available tools: {len(tools)}")
        print(f"Tool names: {tool_names}")
        
        # Test individual tools
        weather_result = weather_tool("Paris")
        print(f"Weather tool result: {weather_result[:50]}...")
        
        time_result = time_tool("UTC")
        print(f"Time tool result: {time_result[:50]}...")
        
        facts_result = city_facts_tool("Tokyo")
        print(f"City facts result: {facts_result[:50]}...")
        
        plan_result = plan_city_visit_tool("London", 2)
        print(f"Plan visit result: {plan_result[:50]}...")
        
        print("✅ All tools working correctly")
        return True
    except Exception as e:
        print(f"❌ Tool test failed: {e}")
        traceback.print_exc()
        return False

def test_agent_creation():
    """Test that agent can be created."""
    print("\nTesting agent creation...")
    try:
        from llm_factory import LLMFactory
        from output_parser import OutputParser
        from agents import TripAgent
        import config
        
        # Create components
        output_parser = OutputParser(enable_terminal_logging=False)
        
        # Try to create LLM provider (this might fail if no API keys)
        try:
            llm_provider = LLMFactory.create_from_config(config.DEFAULT_LLM_PROVIDER, [])
            print(f"✅ LLM provider created: {config.DEFAULT_LLM_PROVIDER}")
        except Exception as e:
            print(f"⚠️  LLM provider creation failed (expected if no API keys): {e}")
            llm_provider = None
        
        # Create agent
        agent = TripAgent(llm_provider, output_parser)
        
        # Test agent methods
        tools = agent.get_available_tools()
        print(f"Agent tools: {tools}")
        
        # Test session management
        history = agent.get_session_history("test_session")
        print(f"Initial history length: {len(history)}")
        
        agent.add_to_history("test_session", "user", "Hello")
        agent.add_to_history("test_session", "assistant", "Hi there!")
        
        history = agent.get_session_history("test_session")
        print(f"History after adding messages: {len(history)}")
        
        agent.clear_session_history("test_session")
        history = agent.get_session_history("test_session")
        print(f"History after clearing: {len(history)}")
        
        print("✅ Agent creation and basic functionality working")
        return True
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        traceback.print_exc()
        return False

def test_app_import():
    """Test that the Flask app can be imported."""
    print("\nTesting Flask app import...")
    try:
        import app
        print("✅ Flask app imported successfully")
        print(f"Agent initialized: {hasattr(app, 'agent')}")
        return True
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 Testing restructured Trip Agent application\n")
    
    tests = [
        test_imports,
        test_tools,
        test_agent_creation,
        test_app_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The restructuring was successful.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())