import os
import json
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource, fields, Namespace
import time
import threading
from typing import Any, Optional
# Standard LangSmith imports for tracing
from langsmith import traceable
from config import get_config
from llm_factory import LLMFactory, BaseLLMProvider
from output_parser import OutputParser, TokenType
from agents import TripAgent

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

# Session management is now handled by the agent

# Initialize the agent
output_parser = OutputParser(enable_terminal_logging=True)
llm_provider = LLMFactory.create_from_config(config.DEFAULT_LLM_PROVIDER, [])
agent = TripAgent(llm_provider, output_parser)

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
                result = agent.process_message(message, session_id)
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
            history = agent.get_session_history(session_id)
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
            agent.clear_session_history(session_id)
            return {"message": f"Memory cleared for session {session_id}"}
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
            result = agent.process_message(message, session_id)
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