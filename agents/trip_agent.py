"""Trip Agent implementation."""

import json
import time
from typing import Dict, Any, Generator
from langsmith import traceable

from .base_agent import BaseAgent
from tools import get_all_tools
from config import Config
from output_parser import OutputParser, TokenType
from openai_streaming_handler import OpenAIStreamingHandler

class TripAgent(BaseAgent):
    """Trip planning agent with tool capabilities.
    
    This agent specializes in travel planning and provides weather,
    time, city facts, and visit planning capabilities.
    """
    
    def __init__(self, llm_provider=None, output_parser=None):
        """
        Initialize the Trip Agent with LLM provider and specialized handlers.
        
        Sets up the trip planning agent with all necessary components for
        travel-related conversations, including tool integration, output parsing,
        and provider-specific streaming handlers.
        
        Args:
            llm_provider: The LLM provider instance (OpenAI, Gemini, etc.)
                         If None, must be set before using the agent
            output_parser: Output parser for response processing and token handling
                          If None, creates default OutputParser instance
        
        Initialization Process:
            1. Calls parent BaseAgent constructor with travel tools
            2. Sets up output parser for response processing
            3. Creates OpenAI-specific streaming handler with logging
            4. Generates system prompt for travel planning context
        
        Components Created:
            - output_parser: Handles token parsing and response formatting
            - openai_handler: Specialized handler for OpenAI streaming responses
            - system_prompt: Travel-focused instructions for the LLM
        
        Available Tools:
            - weather_tool: Current weather information
            - time_tool: Time zone and current time queries
            - city_facts_tool: City information and facts
            - plan_city_visit_tool: Detailed travel planning
        
        Note:
            - Inherits conversation history and memory management from BaseAgent
            - OpenAI handler enables terminal logging for debugging
            - Tools are automatically loaded from the tools module
        """
        super().__init__(llm_provider, get_all_tools())
        self.output_parser = output_parser or OutputParser()
        self.openai_handler = OpenAIStreamingHandler(enable_terminal_logging=True)
        self.system_prompt = self.create_system_prompt()
    
    def create_system_prompt(self) -> str:
        """
        Create the comprehensive system prompt for the trip planning agent.
        
        Generates a detailed system prompt that defines the agent's role as a
        travel planning assistant, lists available tools, and provides guidelines
        for helpful travel advice. The prompt ensures consistent, informative
        responses focused on travel planning needs.
        
        Returns:
            str: Complete system prompt with role definition, tool descriptions,
                 and travel planning guidelines
        
        Prompt Components:
            1. Role Definition: Travel planning assistant identity
            2. Tool Descriptions: Detailed list of available travel tools
            3. Usage Guidelines: When and how to use tools effectively
            4. Response Style: Friendly, informative, and helpful tone
            5. Planning Factors: Key considerations for travel advice
        
        Available Tools Described:
            - weather_tool: Real-time weather data for any location
            - time_tool: Current time and timezone information
            - city_facts_tool: Cultural and practical city information
            - plan_city_visit_tool: Comprehensive travel itinerary creation
        
        Travel Planning Focus:
            - Weather-appropriate recommendations
            - Time zone awareness for scheduling
            - Cultural attractions and local experiences
            - Dining and cuisine suggestions
            - Transportation logistics
            - Optimal timing for visits
        
        Note:
            - Emphasizes tool usage for accurate information
            - Encourages practical, actionable advice
            - Maintains consistent helpful and friendly tone
        """
        return f"""You are a helpful travel planning assistant. You have access to the following tools:

1. **weather_tool(location)** - Get current weather information for any location
2. **time_tool(timezone)** - Get current time, optionally for a specific timezone
3. **city_facts_tool(city)** - Get interesting facts and information about cities
4. **plan_city_visit_tool(city, days, interests)** - Create detailed travel plans for city visits

When users ask about travel, weather, time, or city information, use the appropriate tools to provide accurate and helpful responses.

Always be friendly, informative, and helpful. If you need to use a tool, clearly indicate what information you're looking up.

For travel planning, consider factors like:
- Weather conditions
- Local time zones
- Popular attractions and cultural sites
- Local cuisine and dining recommendations
- Transportation options
- Best times to visit

Provide practical, actionable advice that helps users plan amazing trips!"""
    
    def create_thinking_prompt(self) -> str:
        """
        Create structured thinking prompt to guide the agent's reasoning process.
        
        Generates instructions that encourage the agent to think through its
        approach before responding, ensuring more thoughtful and well-structured
        responses. The thinking process helps the agent plan tool usage and
        response strategy.
        
        Returns:
            str: Thinking prompt with structured reasoning guidelines
        
        Thinking Structure:
            1. Information Analysis: What does the user need?
            2. Tool Selection: Which tools are most appropriate?
            3. Response Planning: How to provide maximum value?
        
        Benefits:
            - Encourages systematic approach to problem-solving
            - Improves tool selection and usage
            - Results in more comprehensive and helpful responses
            - Provides transparency in the agent's reasoning process
        
        Usage:
            - Inserted into prompts before user queries
            - Guides the LLM to think before acting
            - Helps maintain consistency in response quality
        
        Note:
            - Uses XML-style tags for clear structure
            - Focuses on travel-specific considerations
            - Encourages proactive tool usage
        """
        return """Before responding, think through your approach:

<thinking>
- What information does the user need?
- Which tools should I use to get this information?
- How can I provide the most helpful response?
</thinking>

Then provide your response."""
    
    @traceable(name="trip_agent_query")
    def process_message(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Process a user message and return a complete response with provider-specific handling.
        
        Handles the complete flow of processing a user message, from conversation
        context preparation to response generation and history management. Uses
        provider-specific handlers to ensure optimal processing for different LLM
        providers (OpenAI vs others).
        
        Args:
            message (str): The user's travel-related question or request
            session_id (str): Unique identifier for the conversation session
                             Used for conversation history and memory management
        
        Returns:
            Dict[str, Any]: Standardized response dictionary containing:
                - response (str): The agent's complete response
                - success (bool): Whether processing was successful
                - provider (str): LLM provider used (openai, gemini, etc.)
                - model (str): Specific model name used
                - session_id (str): Session identifier
                - error (str, optional): Error details if success=False
        
        Processing Flow:
            1. Memory Optimization: Clears old conversation data if needed
            2. Context Preparation: Formats conversation history
            3. Prompt Construction: Combines system prompt, thinking prompt, and context
            4. LLM Response: Gets response from configured provider
            5. Provider-Specific Processing: Uses specialized handlers
            6. History Management: Adds messages to conversation history
            7. Response Validation: Ensures proper response structure
        
        Provider-Specific Handling:
            - OpenAI: Uses OpenAIStreamingHandler for specialized processing
            - Others: Uses standard OutputParser for response processing
        
        Error Handling:
            - Catches all exceptions and returns standardized error response
            - Maintains conversation state even on errors
            - Provides user-friendly error messages
        
        Note:
            - Decorated with @traceable for LangSmith monitoring
            - Automatically manages conversation history
            - Optimizes memory usage for long conversations
        """
        try:
            # Optimize memory before processing
            self.optimize_memory(session_id)
            
            # Get conversation history
            conversation_context = self.format_conversation_history(session_id)
            
            # Prepare the full prompt
            full_prompt = f"""{self.system_prompt}

{self.create_thinking_prompt()}

Conversation History:
{conversation_context}

User: {message}"""
            
            # Get response from LLM provider
            response = self.llm_provider.generate_response(full_prompt, max_tokens=2048)
            
            # Check if this is an OpenAI provider and use specialized handler
            provider_name = getattr(self.llm_provider, "provider", "unknown").lower()
            
            if provider_name == "openai":
                # Use OpenAI-specific non-streaming handler
                print(f"🔄 Using OpenAI-specific non-streaming handler for session {session_id}")
                
                # Process through OpenAI handler
                if isinstance(response, dict):
                    # Response is already in OpenAI format
                    standardized_result = self.openai_handler.process_openai_non_streaming_response(response, session_id)
                else:
                    # Response is a string, convert to OpenAI format
                    openai_response = {
                        "choices": [{
                            "message": {
                                "content": response
                            },
                            "finish_reason": "stop"
                        }],
                        "model": getattr(self.llm_provider, "model_name", "unknown"),
                        "object": "chat.completion",
                        "created": int(time.time())
                    }
                    standardized_result = self.openai_handler.process_openai_non_streaming_response(openai_response, session_id)
                
                clean_response = standardized_result.get("response", "")
                
            else:
                # Use standard OutputParser for other providers
                print(f"🔄 Using standard non-streaming handler for provider: {provider_name}")
                
                # Process response through output parser
                self.output_parser.accumulated_response = response
                clean_response = self.output_parser.extract_final_response()
                
                # Create standardized result
                standardized_result = {
                    "response": clean_response,
                    "success": True,
                    "provider": getattr(self.llm_provider, "provider", "unknown"),
                    "model": getattr(self.llm_provider, "model_name", "unknown"),
                    "session_id": session_id
                }
            
            # Add to conversation history
            self.add_to_history(session_id, "user", message)
            self.add_to_history(session_id, "assistant", clean_response)
            
            return self.output_parser.validate_response_structure(standardized_result)
            
        except Exception as e:
            print(f"Error in query processing: {e}")
            error_response = {
                "response": f"I encountered an error while processing your request: {str(e)}",
                "success": False,
                "provider": getattr(self.llm_provider, "provider", "unknown"),
                "model": getattr(self.llm_provider, "model_name", "unknown"),
                "error": str(e),
                "session_id": session_id
            }
            return self.output_parser.validate_response_structure(error_response)
    
    @traceable(name="trip_agent_stream")
    def stream_response(self, message: str, session_id: str = "default") -> Generator[str, None, None]:
        """Stream response from the agent with provider-specific handling.
        
        This method provides real-time streaming of AI responses with different handling
        strategies based on the LLM provider. It optimizes memory usage, formats conversation
        context, and routes to appropriate streaming handlers for different providers.
        
        Processing Flow:
        1. Optimizes memory and formats conversation history
        2. Constructs full prompt with system instructions and thinking prompts
        3. Obtains token stream from the LLM provider
        4. Routes to provider-specific streaming handler:
           - OpenAI: Uses specialized OpenAI streaming handler with compatibility layer
           - Others: Uses standard OutputParser with token-by-token processing
        5. Yields Server-Sent Events (SSE) formatted data for real-time streaming
        6. Adds final response to conversation history
        
        Provider-Specific Handling:
        - OpenAI: Leverages openai_handler for specialized processing and compatibility
        - Gemini/Perplexity/Groq: Uses standard output_parser with token classification
        
        Error Handling:
        - Catches streaming exceptions and yields error messages in SSE format
        - Maintains streaming format even during error conditions
        
        Args:
            message (str): The user message to process and respond to
            session_id (str, optional): Session identifier for conversation tracking.
                                      Defaults to "default"
            
        Yields:
            str: Streaming response chunks in Server-Sent Events (SSE) format.
                Each chunk contains JSON data with token and type information
                
        Notes:
        - Applies streaming delays between tokens for better UX (except control tokens)
        - Stores only final response in conversation history, not thinking process
        - Uses different parsers based on provider capabilities
        - Maintains session-based conversation context
        """
        try:
            # Optimize memory before processing
            self.optimize_memory(session_id)
            
            # Get conversation history
            conversation_context = self.format_conversation_history(session_id)
            
            # Prepare the full prompt with context and thinking instructions
            full_prompt = f"""{self.system_prompt}

{self.create_thinking_prompt()}

Conversation History:
{conversation_context}

User: {message}"""
            
            # Get token stream from LLM provider
            token_stream = self.llm_provider.stream_response(full_prompt, max_tokens=2048)
            
            # Check if this is an OpenAI provider and use specialized handler
            provider_name = getattr(self.llm_provider, "provider", "unknown").lower()
            
            if provider_name == "openai":
                # Use OpenAI-specific streaming handler
                print(f"🔄 Using OpenAI-specific streaming handler for session {session_id}")
                
                # Process through OpenAI handler and convert to compatibility format
                openai_stream = self.openai_handler.create_compatibility_stream(token_stream, session_id)
                
                for sse_data in openai_stream:
                    yield sse_data
                
                # Get final response from OpenAI handler
                response_summary = self.openai_handler.get_openai_response_summary()
                final_response_clean = response_summary.get("final_response", "")
                
            else:
                # Use standard OutputParser for other providers
                print(f"🔄 Using standard streaming handler for provider: {provider_name}")
                
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
                        time.sleep(Config.STREAMING_DELAY)
                
                # Extract final response using the standard parser
                final_response_clean = self.output_parser.extract_final_response()
            
            # Add to conversation history (store only the final response, not thinking)
            self.add_to_history(session_id, "user", message)
            self.add_to_history(session_id, "assistant", final_response_clean)
            
        except Exception as e:
            print(f"Error in streaming: {e}")
            # Use parser to handle error formatting
            error_msg = f"I encountered an error while processing your request: {str(e)}"
            for char in error_msg:
                yield f"data: {json.dumps({'token': char, 'type': 'error'})}\n\n"
                time.sleep(Config.STREAMING_DELAY)
            yield f"data: {json.dumps({'token': '', 'type': 'complete'})}\n\n"
    
    # LangGraph-specific methods
    def create_graph_nodes(self) -> Dict[str, Any]:
        """Create node definitions for LangGraph integration.
        
        This method defines the computational nodes that can be used in a LangGraph
        workflow for more complex, graph-based AI agent orchestration. Each node
        represents a specific stage in the agent's processing pipeline.
        
        Node Definitions:
        - process_input: Handles initial input processing and validation
        - think: Manages the thinking/reasoning phase of the agent
        - use_tool: Executes tool calls and external integrations
        - generate_response: Handles response generation from the LLM
        - format_output: Formats and structures the final output
        
        Returns:
            Dict[str, Any]: Dictionary mapping node names to their corresponding
                          method references for LangGraph execution
                          
        Notes:
        - Currently provides placeholder implementations for future LangGraph integration
        - Enables modular, graph-based agent workflow design
        - Supports complex multi-step reasoning and tool usage patterns
        """
        return {
            "process_input": self._process_input_node,
            "think": self._thinking_node,
            "use_tool": self._tool_execution_node,
            "generate_response": self._response_generation_node,
            "format_output": self._output_formatting_node
        }
    
    def _process_input_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process input node for LangGraph workflow.
        
        This node handles the initial processing of user input within a LangGraph
        workflow. It would typically validate input, extract relevant information,
        and prepare the state for subsequent processing nodes.
        
        Typical Processing:
        - Input validation and sanitization
        - Context extraction and preparation
        - State initialization for downstream nodes
        - Session management and tracking
        
        Args:
            state (Dict[str, Any]): Current graph state containing input data,
                                  session information, and workflow context
            
        Returns:
            Dict[str, Any]: Updated state with processed input and prepared context
                          for subsequent nodes in the workflow
                          
        Notes:
        - Currently a placeholder for future LangGraph integration
        - Would implement input preprocessing logic when LangGraph is integrated
        - Maintains state consistency across the workflow
        """
        # This would be implemented when integrating with LangGraph
        # For now, it's a placeholder that maintains compatibility
        return state
    
    def _thinking_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Thinking node for LangGraph workflow.
        
        This node manages the reasoning and thinking phase of the agent within
        a LangGraph workflow. It would handle complex reasoning, planning, and
        decision-making processes before generating responses.
        
        Typical Processing:
        - Analyzes the current context and user request
        - Performs reasoning and planning steps
        - Determines appropriate response strategies
        - Evaluates need for tool usage or additional information
        
        Args:
            state (Dict[str, Any]): Current graph state containing processed input,
                                  context, and any previous reasoning results
            
        Returns:
            Dict[str, Any]: Updated state with reasoning results, plans, and
                          decisions for subsequent processing nodes
                          
        Notes:
        - Currently a placeholder for future LangGraph integration
        - Would implement sophisticated reasoning logic when LangGraph is integrated
        - Enables complex multi-step thinking processes
        """
        # This would be implemented when integrating with LangGraph
        return state
    
    def _tool_execution_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool execution node for LangGraph workflow.
        
        This node handles the execution of external tools and integrations within
        a LangGraph workflow. It would manage tool calls, API integrations, and
        external service interactions based on the agent's reasoning.
        
        Typical Processing:
        - Identifies required tools based on reasoning results
        - Executes tool calls with appropriate parameters
        - Handles tool responses and error conditions
        - Integrates tool results back into the workflow state
        
        Args:
            state (Dict[str, Any]): Current graph state containing reasoning results,
                                  tool requirements, and execution context
            
        Returns:
            Dict[str, Any]: Updated state with tool execution results and
                          integrated external data for response generation
                          
        Notes:
        - Currently a placeholder for future LangGraph integration
        - Would implement tool orchestration logic when LangGraph is integrated
        - Supports complex tool chaining and error handling
        """
        # This would be implemented when integrating with LangGraph
        return state
    
    def _response_generation_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Response generation node for LangGraph workflow.
        
        This node handles the generation of the final response within a LangGraph
        workflow. It would use the LLM provider to generate responses based on
        all previous processing, reasoning, and tool execution results.
        
        Typical Processing:
        - Constructs final prompt from all workflow context
        - Calls the LLM provider for response generation
        - Handles streaming or non-streaming response modes
        - Manages provider-specific response processing
        
        Args:
            state (Dict[str, Any]): Current graph state containing all processed
                                  context, reasoning, and tool results
            
        Returns:
            Dict[str, Any]: Updated state with generated response and
                          completion metadata for final formatting
                          
        Notes:
        - Currently a placeholder for future LangGraph integration
        - Would implement LLM integration logic when LangGraph is integrated
        - Supports both streaming and non-streaming response generation
        """
        # This would be implemented when integrating with LangGraph
        return state
    
    def _output_formatting_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Output formatting node for LangGraph workflow.
        
        This node handles the final formatting and structuring of the agent's
        response within a LangGraph workflow. It would ensure consistent output
        format, apply any necessary post-processing, and prepare the final result.
        
        Typical Processing:
        - Formats the generated response for consistency
        - Applies output validation and quality checks
        - Structures response metadata and session information
        - Prepares final result for client consumption
        
        Args:
            state (Dict[str, Any]): Current graph state containing generated response
                                  and all workflow context and metadata
            
        Returns:
            Dict[str, Any]: Updated state with formatted final response and
                          completion status for workflow conclusion
                          
        Notes:
        - Currently a placeholder for future LangGraph integration
        - Would implement output formatting logic when LangGraph is integrated
        - Ensures consistent response structure and quality
            Updated state
        """
        # This would be implemented when integrating with LangGraph
        return state