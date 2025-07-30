"""Base agent class for LangGraph integration."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Generator
import threading
from tools import get_all_tools, TOOL_REGISTRY

class BaseAgent(ABC):
    """Base agent class that provides common functionality for all agents.
    
    This class is designed to be compatible with LangGraph integration
    and provides the foundation for building stateful, tool-enabled agents.
    """
    
    def __init__(self, llm_provider=None, tools: Optional[List] = None):
        """Initialize the base agent.
        
        Args:
            llm_provider: The LLM provider instance
            tools: List of tools available to the agent
        """
        self.llm_provider = llm_provider
        self.tools = tools or get_all_tools()
        self.tool_registry = TOOL_REGISTRY
        self.session_lock = threading.Lock()
        self.session_histories = {}
        
    @abstractmethod
    def create_system_prompt(self) -> str:
        """Create the system prompt for the agent.
        
        Returns:
            str: The system prompt
        """
        pass
    
    @abstractmethod
    def process_message(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """Process a message and return a response.
        
        Args:
            message: The user message
            session_id: Session identifier
            
        Returns:
            Dict containing the response and metadata
        """
        pass
    
    @abstractmethod
    def stream_response(self, message: str, session_id: str = "default") -> Generator[str, None, None]:
        """Stream a response for the given message.
        
        Args:
            message: The user message
            session_id: Session identifier
            
        Yields:
            str: Streaming response chunks
        """
        pass
    
    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation messages
        """
        with self.session_lock:
            return self.session_histories.get(session_id, [])
    
    def add_to_history(self, session_id: str, role: str, content: str):
        """Add a message to session history.
        
        Args:
            session_id: Session identifier
            role: Message role (user/assistant)
            content: Message content
        """
        with self.session_lock:
            if session_id not in self.session_histories:
                self.session_histories[session_id] = []
            self.session_histories[session_id].append({
                "role": role,
                "content": content
            })
    
    def clear_session_history(self, session_id: str):
        """Clear history for a specific session.
        
        Args:
            session_id: Session identifier
        """
        with self.session_lock:
            if session_id in self.session_histories:
                del self.session_histories[session_id]
    
    def optimize_memory(self, session_id: str, max_messages: int = 20):
        """Optimize memory by keeping only recent messages.
        
        Args:
            session_id: Session identifier
            max_messages: Maximum number of messages to keep
        """
        with self.session_lock:
            if session_id in self.session_histories:
                history = self.session_histories[session_id]
                if len(history) > max_messages:
                    # Keep the most recent messages
                    self.session_histories[session_id] = history[-max_messages:]
    
    def format_conversation_history(self, session_id: str, max_messages: int = 10) -> str:
        """Format conversation history for prompt inclusion.
        
        Args:
            session_id: Session identifier
            max_messages: Maximum number of recent messages to include
            
        Returns:
            Formatted conversation history
        """
        history = self.get_session_history(session_id)
        if not history:
            return "No previous conversation."
        
        # Get recent messages
        recent_history = history[-max_messages:] if len(history) > max_messages else history
        
        formatted = []
        for msg in recent_history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role.title()}: {content}")
        
        return "\n".join(formatted)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return list(self.tool_registry.keys())
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name in self.tool_registry:
            tool_func = self.tool_registry[tool_name]
            try:
                return tool_func(**kwargs)
            except Exception as e:
                return f"Error executing {tool_name}: {str(e)}"
        else:
            return f"Tool {tool_name} not found"
    
    # LangGraph compatibility methods
    def get_state_schema(self) -> Dict[str, Any]:
        """Get the state schema for LangGraph integration.
        
        Returns:
            Dictionary defining the agent state schema
        """
        return {
            "messages": List[Dict[str, str]],
            "session_id": str,
            "current_tool": Optional[str],
            "tool_results": Optional[Dict[str, Any]],
            "thinking": Optional[str],
            "final_response": Optional[str]
        }
    
    def create_initial_state(self, session_id: str = "default") -> Dict[str, Any]:
        """Create initial state for LangGraph.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Initial state dictionary
        """
        return {
            "messages": self.get_session_history(session_id),
            "session_id": session_id,
            "current_tool": None,
            "tool_results": None,
            "thinking": None,
            "final_response": None
        }