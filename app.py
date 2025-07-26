import os
import json
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory
import time
import threading
from typing import Dict, Any
from config import get_config

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
session_histories: Dict[str, ChatMessageHistory] = {}
session_lock = threading.Lock()

class MemoryOptimizedAgent:
    def __init__(self):
        # Initialize Google Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model=config.GOOGLE_MODEL,
            google_api_key=config.GOOGLE_API_KEY,
            temperature=config.AGENT_TEMPERATURE,
            streaming=config.STREAMING_ENABLED
        )
        
        # Define tools for the React agent
        self.tools = self._create_tools()
        
        # Create React agent prompt
        self.prompt = self._create_react_prompt()
        
        # Create the React agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor with memory
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=config.AGENT_VERBOSE,
            handle_parsing_errors=True,
            max_iterations=config.AGENT_MAX_ITERATIONS
        )
        
        # Create runnable with message history for memory management
        self.agent_with_memory = RunnableWithMessageHistory(
            self.agent_executor,
            self._get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
    
    def _create_tools(self):
        """Create tools for the React agent"""
        def search_tool(query: str) -> str:
            """A simple search tool that simulates web search"""
            return f"Search results for '{query}': This is a simulated search result. In a real implementation, this would connect to a search API."
        
        def calculator_tool(expression: str) -> str:
            """A calculator tool for mathematical operations"""
            try:
                result = eval(expression)
                return f"The result of {expression} is {result}"
            except Exception as e:
                return f"Error calculating {expression}: {str(e)}"
        
        def memory_info_tool(query: str) -> str:
            """Tool to get information about current conversation memory"""
            session_id = getattr(threading.current_thread(), 'session_id', 'default')
            if session_id in session_histories:
                history = session_histories[session_id]
                message_count = len(history.messages)
                return f"Current session has {message_count} messages in memory."
            return "No conversation history found for this session."
        
        return [
            Tool(
                name="search",
                description="Use this tool to search for information on the internet",
                func=search_tool
            ),
            Tool(
                name="calculator",
                description="Use this tool to perform mathematical calculations",
                func=calculator_tool
            ),
            Tool(
                name="memory_info",
                description="Use this tool to get information about conversation memory",
                func=memory_info_tool
            )
        ]
    
    def _create_react_prompt(self):
        """Create the React agent prompt template"""
        template = """You are a helpful AI assistant with access to tools and conversation memory.
        
You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Previous conversation history:
{chat_history}

Question: {input}
Thought: {agent_scratchpad}"""
        
        return PromptTemplate(
            input_variables=["input", "chat_history", "agent_scratchpad", "tools", "tool_names"],
            template=template
        )
    
    def _get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Get or create session history for memory management"""
        with session_lock:
            if session_id not in session_histories:
                session_histories[session_id] = ChatMessageHistory()
            return session_histories[session_id]
    
    def _optimize_memory(self, session_id: str, max_messages: int = None):
        """Optimize memory by keeping only recent messages"""
        if max_messages is None:
            max_messages = config.MEMORY_MAX_MESSAGES
            
        with session_lock:
            if session_id in session_histories:
                history = session_histories[session_id]
                if len(history.messages) > max_messages:
                    # Keep only the most recent messages
                    history.messages = history.messages[-max_messages:]
    
    def stream_response(self, message: str, session_id: str = "default"):
        """Stream response from the agent with memory"""
        # Set session_id for current thread (for tools to access)
        threading.current_thread().session_id = session_id
        
        try:
            # Optimize memory before processing
            self._optimize_memory(session_id)
            
            # Stream the response
            for chunk in self.agent_with_memory.stream(
                {"input": message},
                config={"configurable": {"session_id": session_id}}
            ):
                if "output" in chunk:
                    # Stream the output token by token
                    output = chunk["output"]
                    for char in output:
                        yield f"data: {json.dumps({'token': char, 'type': 'content'})}\n\n"
                        time.sleep(config.STREAMING_DELAY)  # Configurable delay for streaming effect
                elif "intermediate_steps" in chunk:
                    # Stream intermediate steps (thoughts, actions)
                    steps = chunk["intermediate_steps"]
                    for step in steps:
                        if len(step) >= 2:
                            action, observation = step[0], step[1]
                            yield f"data: {json.dumps({'token': f'Action: {action.tool}\n', 'type': 'action'})}\n\n"
                            yield f"data: {json.dumps({'token': f'Observation: {observation}\n', 'type': 'observation'})}\n\n"
            
            yield f"data: {json.dumps({'token': '', 'type': 'end'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"

# Initialize the agent
agent = MemoryOptimizedAgent()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Memory Agentic API is running"})

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
                    "message_count": len(history.messages),
                    "messages": [
                        {
                            "type": type(msg).__name__,
                            "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                        }
                        for msg in history.messages[-5:]  # Show last 5 messages
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

if __name__ == '__main__':
    print(f"\n🚀 Starting Memory Agentic server on {config.FLASK_HOST}:{config.FLASK_PORT}")
    print(f"📱 Web interface: http://localhost:{config.FLASK_PORT}")
    print(f"🖥️  Open client.html in your browser to interact with the agent")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(
        debug=config.FLASK_DEBUG,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        threaded=True
    )