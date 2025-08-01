import os
import json
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource, fields, Namespace
import google.generativeai as genai
import time
import threading
from typing import Dict, Any, Optional
# Standard LangSmith imports for tracing
from langsmith import traceable
import requests
from datetime import datetime, timezone, timedelta
from config import get_config
from llm_factory import LLMFactory, BaseLLMProvider
from output_parser import OutputParser, TokenType

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

# Set up LangSmith environment variables for tracing
if config.LANGSMITH_TRACING:
    os.environ["LANGSMITH_TRACING"] = "true"
    if config.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = config.LANGSMITH_API_KEY
    if config.LANGSMITH_PROJECT:
        os.environ["LANGSMITH_PROJECT"] = config.LANGSMITH_PROJECT
    if config.LANGSMITH_ENDPOINT:
        os.environ["LANGSMITH_ENDPOINT"] = config.LANGSMITH_ENDPOINT

# Print configuration
config.print_config()

app = Flask(__name__)
CORS(app, origins=config.CORS_ORIGINS)

# Initialize Flask-RESTX API
api = Api(
    app,
    version='1.0',
    title='Trip Advisor - AI Agent API',
    description='A Trip Advisor AI Agent API with LLM capabilities',
    doc='/docs/',
    prefix='/api/v1'
)

# Create namespaces
chat_ns = Namespace('chat', description='Chat operations')
memory_ns = Namespace('memory', description='Memory management operations')
llm_ns = Namespace('llm', description='LLM provider operations')
health_ns = Namespace('health', description='Health check operations')

# Add namespaces to API
api.add_namespace(chat_ns)
api.add_namespace(memory_ns)
api.add_namespace(llm_ns)
api.add_namespace(health_ns)

# Define API models for documentation
chat_request = api.model('ChatRequest', {
    'message': fields.String(required=True, description='The user message'),
    'session_id': fields.String(required=False, default='default', description='Session identifier'),
    'provider': fields.String(required=False, description='LLM provider to use (openai, google_gemini, groq)'),
    'stream': fields.Boolean(required=False, default=True, description='Whether to stream the response')
})

chat_response = api.model('ChatResponse', {
    'response': fields.String(description='The assistant response'),
    'success': fields.Boolean(description='Whether the request was successful'),
    'provider': fields.String(description='The LLM provider used'),
    'model': fields.String(description='The model used'),
    'rate_limited': fields.Boolean(description='Whether the response was rate limited')
})

memory_status_response = api.model('MemoryStatusResponse', {
    'session_id': fields.String(description='Session identifier'),
    'message_count': fields.Integer(description='Number of messages in session'),
    'messages': fields.List(fields.Raw, description='Recent messages in session')
})

llm_providers_response = api.model('LLMProvidersResponse', {
    'available_providers': fields.List(fields.String, description='List of available providers'),
    'configured_providers': fields.Raw(description='Configuration status of providers'),
    'current_provider': fields.String(description='Currently active provider'),
    'default_provider': fields.String(description='Default provider')
})

llm_switch_request = api.model('LLMSwitchRequest', {
    'provider': fields.String(required=True, description='Provider to switch to')
})

health_response = api.model('HealthResponse', {
    'status': fields.String(description='Health status'),
    'message': fields.String(description='Health message')
})

error_response = api.model('ErrorResponse', {
    'error': fields.String(description='Error message')
})

# Global memory store for different sessions
session_histories: Dict[str, list] = {}
session_lock = threading.Lock()

class TripAgent:
    def __init__(self):
        # Define tools for the Trip Advisor - AI Agent first
        self.tools = self._create_tools()
        
        # Initialize LLM provider using factory (now tools are available)
        self.llm_provider = self._initialize_llm_provider()
        
        # Initialize output parser for standardized response processing with terminal logging
        self.output_parser = OutputParser(enable_terminal_logging=True)
        
        # Create system prompt for the assistant
        self.system_prompt = self._create_system_prompt()
        
        # Agent initialization complete
        print(f"✅ TripAgent initialized with {config.DEFAULT_LLM_PROVIDER} provider and {len(self.tools)} tools")
    
    def _initialize_llm_provider(self) -> BaseLLMProvider:
        """Initialize LLM provider using factory pattern"""
        try:
            # Try to create provider from default configuration with tools
            return LLMFactory.create_from_config(config.DEFAULT_LLM_PROVIDER, self.tools)
        except Exception as e:
            print(f"Error initializing {config.DEFAULT_LLM_PROVIDER} provider: {e}")
            
            # Fallback to Google Gemini if available
            if config.GOOGLE_API_KEY and config.DEFAULT_LLM_PROVIDER != "google_gemini":
                print("Falling back to Google Gemini provider")
                return LLMFactory.create_from_config("google_gemini", self.tools)
            
            # If no fallback is available, re-raise the exception
            raise
    
    def _create_tools(self):
        """Create tools for the Trip Advisor - AI Agent"""
        from tools import WeatherTool, TimeTool, CityFactsTool, PlanCityVisitTool
        
        # Initialize tool instances
        weather_tool_instance = WeatherTool()
        time_tool_instance = TimeTool()
        city_facts_tool_instance = CityFactsTool()
        plan_visit_tool_instance = PlanCityVisitTool()
        
        return {
            "WeatherTool": weather_tool_instance.get_weather,
            "TimeTool": time_tool_instance.get_time,
            "CityFactsTool": city_facts_tool_instance.get_city_facts,
            "PlanMyCityVisitTool": plan_visit_tool_instance.plan_visit
        }
    
    def _create_system_prompt(self):
        """Create the system prompt for Trip Advisor - AI Agent"""
        return """You are a Trip Advisor - AI Agent that helps users gather factual information about cities around the world. You specialize in providing weather information, current local time, and basic city facts.

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
    
    def _create_thinking_prompt(self):
        """Create a prompt that encourages transparent thinking"""
        return """Before providing your final response, please show your thinking process by following this format:

<thinking>
[Your step-by-step reasoning process here. Think about:
- What the user is asking for
- What information you need to gather
- Which tools you should use
- How to structure your response
- Any considerations or edge cases]
</thinking>

[Your final response here]

This thinking process helps users understand how you approach their questions and builds trust in your responses."""
    
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
    
    @traceable(name="trip_agent_generate_response")
    def _generate_response(self, message: str, session_id: str) -> dict:
        """Generate response using the current LLM provider"""
        try:
            # Get conversation history
            conversation_context = self._format_conversation_history(session_id)
            
            # Prepare the full prompt with context and thinking instructions
            full_prompt = f"""{self.system_prompt}

{self._create_thinking_prompt()}

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
    
    @traceable(name="trip_agent_query")
    def query(self, message: str, session_id: str = "default") -> dict:
        """Process a query and generate response with standardized output parsing"""
        try:
            # Optimize memory before processing
            self._optimize_memory(session_id)
            
            # Generate response
            result = self._generate_response(message, session_id)
            
            # Validate and standardize the response structure
            standardized_result = self.output_parser.validate_response_structure(result)
            
            # Add to conversation history
            history = self._get_session_history(session_id)
            history.append({"role": "user", "content": message})
            
            # Clean the response using the output parser
            response_text = standardized_result.get("response", "")
            
            # Reset parser state and process the full response to extract clean content
            self.output_parser.reset_state()
            self.output_parser.accumulated_response = response_text
            clean_response = self.output_parser.extract_final_response()
            
            history.append({"role": "assistant", "content": clean_response})
            
            # Update the result with cleaned response
            standardized_result["response"] = clean_response
            
            return standardized_result
            
        except Exception as e:
            print(f"Error in query processing: {e}")
            # Use parser to standardize error response
            error_response = {
                "response": f"I encountered an error while processing your request: {str(e)}",
                "success": False,
                "provider": getattr(self.llm_provider, "provider", "unknown"),
                "model": getattr(self.llm_provider, "model_name", "unknown"),
                "error": str(e)
            }
            return self.output_parser.validate_response_structure(error_response)
    
    @traceable(name="trip_agent_stream")
    def stream_response(self, message: str, session_id: str = "default"):
        """Stream response from the agent with standardized output parsing"""
        try:
            # Optimize memory before processing
            self._optimize_memory(session_id)
            
            # Get conversation history
            conversation_context = self._format_conversation_history(session_id)
            
            # Prepare the full prompt with context and thinking instructions
            full_prompt = f"""{self.system_prompt}

{self._create_thinking_prompt()}

Conversation History:
{conversation_context}

User: {message}"""
            
            # Get token stream from LLM provider
            token_stream = self.llm_provider.stream_response(full_prompt, max_tokens=2048)
            
            # Use OutputParser to standardize the response processing
            parsed_stream = self.output_parser.parse_stream(token_stream)
            
            # Stream parsed tokens with proper formatting
            for parsed_token in parsed_stream:
                # Format for Server-Sent Events
                sse_data = self.output_parser.format_for_sse(parsed_token)
                yield sse_data
                
                # Add streaming delay except for control tokens
                if parsed_token.token_type not in [
                    TokenType.THINKING_START, TokenType.THINKING_END, 
                    TokenType.TOOL_CALL_START, TokenType.TOOL_CALL_END,
                    TokenType.TOOL_RESULT_START, TokenType.TOOL_RESULT_END,
                    TokenType.COMPLETE
                ]:
                    time.sleep(config.STREAMING_DELAY)
            
            # Add to conversation history (store only the final response, not thinking)
            history = self._get_session_history(session_id)
            history.append({"role": "user", "content": message})
            
            # Extract final response using the parser
            final_response_clean = self.output_parser.extract_final_response()
            history.append({"role": "assistant", "content": final_response_clean})
            
        except Exception as e:
            print(f"Error in streaming: {e}")
            # Use parser to handle error formatting
            error_msg = f"I encountered an error while processing your request: {str(e)}"
            for char in error_msg:
                yield f"data: {json.dumps({'token': char, 'type': 'error'})}\n\n"
                time.sleep(config.STREAMING_DELAY)
            yield f"data: {json.dumps({'token': '', 'type': 'complete'})}\n\n"

# Initialize the agent
agent = TripAgent()

# Health check endpoint
@health_ns.route('')
class HealthCheck(Resource):
    @health_ns.doc('health_check')
    @health_ns.marshal_with(health_response)
    def get(self):
        """Health check endpoint"""
        return {"status": "healthy", "message": "Trip Advisor - AI Agent API is running"}

# Chat endpoint
@chat_ns.route('')
class Chat(Resource):
    @chat_ns.doc('chat')
    @chat_ns.expect(chat_request)
    @chat_ns.response(200, 'Success', chat_response)
    @chat_ns.response(400, 'Bad Request', error_response)
    @chat_ns.response(500, 'Internal Server Error', error_response)
    def post(self):
        """Main chat endpoint with optional streaming"""
        try:
            data = request.get_json()
            message = data.get('message', '')
            session_id = data.get('session_id', 'default')
            provider = data.get('provider')  # Optional provider override
            stream = data.get('stream', True)  # Default to streaming
            
            if not message:
                return {"error": "Message is required"}, 400
            
            # Switch provider if specified
            if provider and provider != getattr(agent.llm_provider, "provider", config.DEFAULT_LLM_PROVIDER):
                try:
                    agent.llm_provider = LLMFactory.create_from_config(provider, agent.tools)
                except Exception as e:
                    return {"error": f"Failed to switch to {provider}: {str(e)}"}, 500
            
            if stream:
                # For streaming, we need to bypass Flask-RESTX marshalling
                # and return a Flask Response directly
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
            else:
                # Non-streaming response
                result = agent.query(message, session_id)
                return result
        
        except Exception as e:
            return {"error": str(e)}, 500

# Memory status endpoint
@memory_ns.route('/status/<string:session_id>')
class MemoryStatus(Resource):
    @memory_ns.doc('get_memory_status')
    @memory_ns.marshal_with(memory_status_response)
    @memory_ns.response(500, 'Internal Server Error', error_response)
    def get(self, session_id):
        """Get memory status for a session"""
        try:
            with session_lock:
                if session_id in session_histories:
                    history = session_histories[session_id]
                    return {
                        "session_id": session_id,
                        "message_count": len(history),
                        "messages": [
                            {
                                "role": msg.get("role", "unknown"),
                                "content": msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
                            }
                            for msg in history[-5:]  # Show last 5 messages
                        ]
                    }
                else:
                    return {
                        "session_id": session_id,
                        "message_count": 0,
                        "messages": []
                    }
        except Exception as e:
            return {"error": str(e)}, 500

# Memory clear endpoint
@memory_ns.route('/clear/<string:session_id>')
class MemoryClear(Resource):
    @memory_ns.doc('clear_memory')
    @memory_ns.response(200, 'Success')
    @memory_ns.response(500, 'Internal Server Error', error_response)
    def delete(self, session_id):
        """Clear memory for a specific session"""
        try:
            with session_lock:
                if session_id in session_histories:
                    del session_histories[session_id]
                    return {"message": f"Memory cleared for session {session_id}"}
                else:
                    return {"message": f"No memory found for session {session_id}"}
        except Exception as e:
            return {"error": str(e)}, 500

# LLM providers endpoint
@llm_ns.route('/providers')
class LLMProviders(Resource):
    @llm_ns.doc('get_llm_providers')
    @llm_ns.marshal_with(llm_providers_response)
    @llm_ns.response(500, 'Internal Server Error', error_response)
    def get(self):
        """Get available LLM providers and their configuration status"""
        try:
            providers = LLMFactory.get_available_providers()
            provider_status = {
                "google_gemini": config.GOOGLE_API_KEY is not None,
                "openai": config.OPENAI_API_KEY is not None,
                "groq": config.GROQ_API_KEY is not None,
                "perplexity": config.PERPLEXITY_API_KEY is not None
            }
            
            current_provider = getattr(agent.llm_provider, "provider", config.DEFAULT_LLM_PROVIDER)
            
            return {
                "available_providers": providers,
                "configured_providers": provider_status,
                "current_provider": current_provider,
                "default_provider": config.DEFAULT_LLM_PROVIDER
            }
        except Exception as e:
            return {"error": str(e)}, 500

# LLM switch endpoint
@llm_ns.route('/switch')
class LLMSwitch(Resource):
    @llm_ns.doc('switch_llm_provider')
    @llm_ns.expect(llm_switch_request)
    @llm_ns.response(200, 'Success')
    @llm_ns.response(400, 'Bad Request', error_response)
    @llm_ns.response(500, 'Internal Server Error', error_response)
    def post(self):
        """Switch the active LLM provider"""
        try:
            data = request.get_json()
            provider = data.get('provider')
            
            if not provider:
                return {"error": "Provider name is required"}, 400
            
            if provider not in LLMFactory.get_available_providers():
                return {"error": f"Unsupported provider: {provider}"}, 400
            
            # Check if provider is configured
            if provider == "google_gemini" and not config.GOOGLE_API_KEY:
                return {"error": "Google Gemini API key is not configured"}, 400
            elif provider == "openai" and not config.OPENAI_API_KEY:
                return {"error": "OpenAI API key is not configured"}, 400
            elif provider == "groq" and not config.GROQ_API_KEY:
                return {"error": "Groq API key is not configured"}, 400
            elif provider == "perplexity" and not config.PERPLEXITY_API_KEY:
                return {"error": "Perplexity API key is not configured"}, 400
            
            # Create new provider
            try:
                agent.llm_provider = LLMFactory.create_from_config(provider, agent.tools)
                return {
                    "message": f"Switched to {provider} provider",
                    "provider": provider
                }
            except Exception as e:
                return {"error": f"Failed to initialize {provider} provider: {str(e)}"}, 500
            
        except Exception as e:
             return {"error": str(e)}, 500

# Backward compatibility routes (legacy endpoints)
@app.route('/health', methods=['GET'])
def health_check_legacy():
    """Legacy health check endpoint for backward compatibility"""
    return jsonify({"status": "healthy", "message": "Trip Advisor - AI Agent API is running"})

@app.route('/chat', methods=['POST'])
def chat_legacy():
    """Legacy chat endpoint for backward compatibility"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        provider = data.get('provider')  # Optional provider override
        stream = data.get('stream', True)  # Default to streaming
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Switch provider if specified
        if provider and provider != getattr(agent.llm_provider, "provider", config.DEFAULT_LLM_PROVIDER):
            try:
                agent.llm_provider = LLMFactory.create_from_config(provider, agent.tools)
            except Exception as e:
                return jsonify({"error": f"Failed to switch to {provider}: {str(e)}"}), 500
        
        if stream:
            # Streaming response
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
        else:
            # Non-streaming response
            result = agent.query(message, session_id)
            return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"\n🚀 Starting Trip Advisor - AI Agent server on {config.FLASK_HOST}:{config.FLASK_PORT}")
    print(f"📱 Web interface: http://localhost:{config.FLASK_PORT}")
    print(f"🖥️  Open client.html in your browser to interact with the agent")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(
        debug=config.FLASK_DEBUG,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        threaded=True
    )