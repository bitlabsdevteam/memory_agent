import os
import json
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import google.generativeai as genai
import time
import threading
from typing import Dict, Any, Optional
import requests
from datetime import datetime, timezone, timedelta
from config import get_config
from llm_factory import LLMFactory, BaseLLMProvider

# Get configuration
config_class = get_config()
config = config_class()

# Validate configuration
errors = config.validate()
if errors:
    print("❌ Configuration errors:")
    for error in errors:
        print(f"   - {error}")
    exit(1)

# Print configuration
config.print_config()

app = Flask(__name__)
CORS(app, origins=config.CORS_ORIGINS)

# Global memory store for different sessions
session_histories: Dict[str, list] = {}
session_lock = threading.Lock()

class TripAgent:
    def __init__(self):
        # Initialize LLM provider using factory
        self.llm_provider = self._initialize_llm_provider()
        
        # Define tools for the City Information Assistant
        self.tools = self._create_tools()
        
        # Create system prompt for the assistant
        self.system_prompt = self._create_system_prompt()
    
    def _initialize_llm_provider(self) -> BaseLLMProvider:
        """Initialize LLM provider using factory pattern"""
        try:
            # Try to create provider from default configuration
            return LLMFactory.create_from_config(config.DEFAULT_LLM_PROVIDER)
        except Exception as e:
            print(f"Error initializing {config.DEFAULT_LLM_PROVIDER} provider: {e}")
            
            # Fallback to Google Gemini if available
            if config.GOOGLE_API_KEY and config.DEFAULT_LLM_PROVIDER != "google_gemini":
                print("Falling back to Google Gemini provider")
                return LLMFactory.create_from_config("google_gemini")
            
            # If no fallback is available, re-raise the exception
            raise
    
    def _create_tools(self):
        """Create tools for the City Information Assistant"""
        
        def weather_tool(city: str) -> str:
            """Get current weather for a city using OpenWeatherMap API"""
            try:
                # Mock weather data for demonstration
                # In production, you would use: api.openweathermap.org/data/2.5/weather
                weather_data = {
                    "paris": {"temp": 23, "condition": "clear skies", "humidity": 65},
                    "london": {"temp": 18, "condition": "partly cloudy", "humidity": 72},
                    "tokyo": {"temp": 28, "condition": "sunny", "humidity": 58},
                    "new york": {"temp": 25, "condition": "overcast", "humidity": 68},
                    "sydney": {"temp": 22, "condition": "light rain", "humidity": 75}
                }
                
                city_lower = city.lower()
                if city_lower in weather_data:
                    data = weather_data[city_lower]
                    return f"Current weather in {city}: {data['temp']}°C, {data['condition']}, humidity {data['humidity']}%"
                else:
                    return f"Weather data for {city}: 20°C, partly cloudy (mock data)"
            except Exception as e:
                return f"Error getting weather for {city}: {str(e)}"
        
        def time_tool(city: str) -> str:
            """Get current time in a city using timezone offsets"""
            try:
                # City to timezone offset mapping (hours from UTC)
                city_offsets = {
                    "paris": 1,      # CET/CEST
                    "london": 0,     # GMT/BST
                    "tokyo": 9,      # JST
                    "new york": -5,  # EST/EDT
                    "sydney": 10,    # AEST/AEDT
                    "los angeles": -8, # PST/PDT
                    "berlin": 1,     # CET/CEST
                    "moscow": 3,     # MSK
                    "beijing": 8,    # CST
                    "mumbai": 5.5    # IST
                }
                
                city_lower = city.lower()
                offset_hours = city_offsets.get(city_lower, 0)
                
                # Create timezone with offset
                tz = timezone(timedelta(hours=offset_hours))
                current_time = datetime.now(tz)
                formatted_time = current_time.strftime("%H:%M %p")
                
                return f"Current time in {city}: {formatted_time}"
            except Exception as e:
                return f"Error getting time for {city}: {str(e)}"
        
        def city_facts_tool(city: str) -> str:
            """Get basic facts about a city"""
            try:
                # Mock city facts data
                city_facts = {
                    "paris": {
                        "country": "France",
                        "population": "2.1 million",
                        "description": "Paris is the capital of France. It's known for the Eiffel Tower, Louvre Museum, and its romantic atmosphere."
                    },
                    "london": {
                        "country": "United Kingdom",
                        "population": "9 million",
                        "description": "London is the capital of England and the UK. Famous for Big Ben, Tower Bridge, and rich history."
                    },
                    "tokyo": {
                        "country": "Japan",
                        "population": "14 million",
                        "description": "Tokyo is Japan's capital and largest city. Known for modern technology, anime culture, and traditional temples."
                    },
                    "new york": {
                        "country": "United States",
                        "population": "8.3 million",
                        "description": "New York City is the most populous city in the US. Famous for Times Square, Central Park, and the Statue of Liberty."
                    },
                    "sydney": {
                        "country": "Australia",
                        "population": "5.3 million",
                        "description": "Sydney is Australia's largest city. Known for the Sydney Opera House, Harbour Bridge, and beautiful beaches."
                    }
                }
                
                city_lower = city.lower()
                if city_lower in city_facts:
                    facts = city_facts[city_lower]
                    return f"{city} is located in {facts['country']} with a population of {facts['population']}. {facts['description']}"
                else:
                    return f"Basic facts about {city}: A city with rich culture and history (mock data - in production would use GeoDB Cities API or Wikipedia API)"
            except Exception as e:
                return f"Error getting facts for {city}: {str(e)}"
        
        def plan_city_visit_tool(city: str) -> str:
            """Composite tool that uses multiple tools to plan a city visit"""
            try:
                # Get city facts
                facts = city_facts_tool(city)
                
                # Get current weather
                weather = weather_tool(city)
                
                # Get current time
                current_time = time_tool(city)
                
                # Create thinking process
                thinking = f"To help you plan your visit to {city}, I'll first get some facts, then fetch the current weather and time."
                
                # Combine all information
                response = {
                    "thinking": thinking,
                    "function_calls": [
                        {"tool": "CityFactsTool", "parameters": {"city": city}},
                        {"tool": "WeatherTool", "parameters": {"city": city}},
                        {"tool": "TimeTool", "parameters": {"city": city}}
                    ],
                    "response": f"{facts} {weather} {current_time} What would you like to do in {city}?"
                }
                
                return json.dumps(response, indent=2)
            except Exception as e:
                return f"Error planning visit to {city}: {str(e)}"
        
        return {
            "WeatherTool": weather_tool,
            "TimeTool": time_tool,
            "CityFactsTool": city_facts_tool,
            "PlanMyCityVisitTool": plan_city_visit_tool
        }
    
    def _create_system_prompt(self):
        """Create the system prompt for City Information Assistant"""
        return """You are a City Information Assistant that helps users gather factual information about cities around the world. You specialize in providing weather information, current local time, and basic city facts.

You have access to the following tools:
- WeatherTool: Get current weather for a city
- TimeTool: Get current time in a city
- CityFactsTool: Get basic facts about a city (country, population, description)
- PlanMyCityVisitTool: Plan a city visit by getting facts, weather, and time information

When a user asks about a city, you should:
1. Think carefully about what information they need
2. Use the appropriate tools to gather that information
3. Provide a comprehensive and helpful response
4. For complex requests, consider using PlanMyCityVisitTool which orchestrates multiple tools

Always think through your approach step by step. Be conversational and helpful."""
    
    def _get_session_history(self, session_id: str) -> list:
        """Get or create session history for a given session ID"""
        with session_lock:
            if session_id not in session_histories:
                session_histories[session_id] = []
            return session_histories[session_id]
    
    def _format_conversation_history(self, session_id: str) -> str:
        """Format the conversation history for context"""
        history = self._get_session_history(session_id)
        if not history:
            return "No previous conversation."
        
        formatted_messages = []
        for message in history[-10:]:  # Keep last 10 messages
            role = message.get('role', 'user')
            content = message.get('content', '')
            formatted_messages.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted_messages)
    
    def _generate_response(self, message: str, session_id: str) -> dict:
        """Generate response using the current LLM provider"""
        try:
            # Get conversation history
            conversation_context = self._format_conversation_history(session_id)
            
            # Prepare the full prompt with context
            full_prompt = f"""{self.system_prompt}

Conversation History:
{conversation_context}

User: {message}"""
            
            # Generate response using the LLM provider
            result = self.llm_provider.generate_response(
                prompt=full_prompt,
                max_tokens=2048
            )
            
            return result
            
        except Exception as e:
            return {
                "response": f"Error generating response: {str(e)}",
                "success": False
            }
    
    def _optimize_memory(self, session_id: str, max_messages: int = None):
        """Optimize memory by keeping only recent messages"""
        if max_messages is None:
            max_messages = config.MEMORY_MAX_MESSAGES
            
        with session_lock:
            if session_id in session_histories:
                history = session_histories[session_id]
                if len(history) > max_messages:
                    # Keep only the most recent messages
                    session_histories[session_id] = history[-max_messages:]
    
    def query(self, message: str, session_id: str = "default") -> dict:
        """Process a query and generate response"""
        try:
            # Optimize memory before processing
            self._optimize_memory(session_id)
            
            # Generate response
            result = self._generate_response(message, session_id)
            
            # Add to conversation history
            history = self._get_session_history(session_id)
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": result["response"]})
            
            return result
            
        except Exception as e:
            print(f"Error in query processing: {e}")
            return {
                "response": f"I encountered an error while processing your request: {str(e)}",
                "success": False
            }
    
    def stream_response(self, message: str, session_id: str = "default"):
        """Stream response from the agent"""
        try:
            # Optimize memory before processing
            self._optimize_memory(session_id)
            
            # Get conversation history
            conversation_context = self._format_conversation_history(session_id)
            
            # Prepare the full prompt with context
            full_prompt = f"""{self.system_prompt}

Conversation History:
{conversation_context}

User: {message}"""
            
            # Stream response using the LLM provider
            response_text = ""
            for token in self.llm_provider.stream_response(full_prompt, max_tokens=2048):
                response_text += token
                yield f"data: {json.dumps({'token': token, 'type': 'response'})}\n\n"
                time.sleep(config.STREAMING_DELAY)
            
            # Add to conversation history
            history = self._get_session_history(session_id)
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response_text})
            
            # Send completion signal
            yield f"data: {json.dumps({'token': '', 'type': 'complete'})}\n\n"
            
        except Exception as e:
            print(f"Error in streaming: {e}")
            error_msg = f"I encountered an error while processing your request: {str(e)}"
            for char in error_msg:
                yield f"data: {json.dumps({'token': char, 'type': 'error'})}\n\n"
                time.sleep(config.STREAMING_DELAY)
            yield f"data: {json.dumps({'token': '', 'type': 'complete'})}\n\n"

# Initialize the agent
agent = TripAgent()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Trip Agent API is running"})

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint with streaming"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        def generate():
            yield from agent.stream_response(message, session_id)
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/memory/status/<session_id>', methods=['GET'])
def get_memory_status(session_id):
    """Get memory status for a session"""
    try:
        with session_lock:
            if session_id in session_histories:
                history = session_histories[session_id]
                return jsonify({
                    "session_id": session_id,
                    "message_count": len(history),
                    "messages": [
                        {
                            "role": msg.get("role", "unknown"),
                            "content": msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
                        }
                        for msg in history[-5:]  # Show last 5 messages
                    ]
                })
            else:
                return jsonify({
                    "session_id": session_id,
                    "message_count": 0,
                    "messages": []
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/memory/clear/<session_id>', methods=['DELETE'])
def clear_memory(session_id):
    """Clear memory for a specific session"""
    try:
        with session_lock:
            if session_id in session_histories:
                del session_histories[session_id]
                return jsonify({"message": f"Memory cleared for session {session_id}"})
            else:
                return jsonify({"message": f"No memory found for session {session_id}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/llm/providers', methods=['GET'])
def get_llm_providers():
    """Get available LLM providers and their configuration status"""
    try:
        providers = LLMFactory.get_available_providers()
        provider_status = {
            "google_gemini": config.GOOGLE_API_KEY is not None,
            "openai": config.OPENAI_API_KEY is not None,
            "groq": config.GROQ_API_KEY is not None
        }
        
        current_provider = getattr(agent.llm_provider, "provider", config.DEFAULT_LLM_PROVIDER)
        
        return jsonify({
            "available_providers": providers,
            "configured_providers": provider_status,
            "current_provider": current_provider,
            "default_provider": config.DEFAULT_LLM_PROVIDER
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/llm/switch', methods=['POST'])
def switch_llm_provider():
    """Switch the active LLM provider"""
    try:
        data = request.get_json()
        provider = data.get('provider')
        
        if not provider:
            return jsonify({"error": "Provider name is required"}), 400
        
        if provider not in LLMFactory.get_available_providers():
            return jsonify({"error": f"Unsupported provider: {provider}"}), 400
        
        # Check if provider is configured
        if provider == "google_gemini" and not config.GOOGLE_API_KEY:
            return jsonify({"error": "Google Gemini API key is not configured"}), 400
        elif provider == "openai" and not config.OPENAI_API_KEY:
            return jsonify({"error": "OpenAI API key is not configured"}), 400
        elif provider == "groq" and not config.GROQ_API_KEY:
            return jsonify({"error": "Groq API key is not configured"}), 400
        
        # Create new provider
        try:
            agent.llm_provider = LLMFactory.create_from_config(provider)
            return jsonify({
                "message": f"Switched to {provider} provider",
                "provider": provider
            })
        except Exception as e:
            return jsonify({"error": f"Failed to initialize {provider} provider: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"\n🚀 Starting Trip Agent server on {config.FLASK_HOST}:{config.FLASK_PORT}")
    print(f"📱 Web interface: http://localhost:{config.FLASK_PORT}")
    print(f"🖥️  Open client.html in your browser to interact with the agent")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(
        debug=config.FLASK_DEBUG,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        threaded=True
    )