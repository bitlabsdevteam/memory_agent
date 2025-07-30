"""OpenAI-specific streaming handler for enhanced OpenAI response processing."""

import json
import time
from typing import Dict, Any, Generator, Optional
from openai_output_parser import OpenAIOutputParser, OpenAIParsedToken, OpenAITokenType
from output_parser import ParsedToken, TokenType
from config import Config

class OpenAIStreamingHandler:
    """OpenAI-specific streaming handler with enhanced error handling and response processing."""
    
    def __init__(self, enable_terminal_logging: bool = True):
        """Initialize the OpenAI streaming handler with specialized parsing capabilities.
        
        This constructor sets up the OpenAI-specific streaming handler with an integrated
        OpenAI output parser for processing OpenAI-formatted responses. It provides
        enhanced error handling, logging, and response processing specifically tailored
        for OpenAI's streaming API format.
        
        Features:
        - Specialized OpenAI response parsing and formatting
        - Enhanced error handling for OpenAI-specific issues
        - Optional terminal logging for debugging and monitoring
        - Integration with OpenAI output parser for consistency
        
        Args:
            enable_terminal_logging (bool, optional): Whether to enable terminal logging
                                                     for debugging and monitoring.
                                                     Defaults to True
                                                     
        Notes:
        - Creates an OpenAIOutputParser instance for specialized parsing
        - Configures logging preferences for development and production use
        - Provides foundation for OpenAI-specific streaming operations
        """
        self.openai_parser = OpenAIOutputParser(enable_terminal_logging)
        self.enable_logging = enable_terminal_logging
        
    def log_openai_event(self, event_type: str, content: str = ""):
        """Log OpenAI-specific events to terminal with color-coded output.
        
        This method provides specialized logging for OpenAI streaming events with
        color-coded terminal output for better visibility and debugging. It categorizes
        different types of OpenAI events and formats them appropriately.
        
        Event Types:
        - openai_start: Stream initialization events (Cyan)
        - openai_thinking: Thinking/reasoning phase events (Yellow)
        - openai_response: Response generation events (Green)
        - openai_function: Function/tool call events (Magenta)
        - openai_error: Error and exception events (Red)
        - openai_complete: Stream completion events (Blue)
        
        Content Handling:
        - Truncates long content to 100 characters for readability
        - Adds ellipsis (...) for truncated content
        - Handles empty content gracefully
        
        Args:
            event_type (str): The type of OpenAI event to log (determines color)
            content (str, optional): The content/message to log with the event.
                                   Defaults to empty string
                                   
        Notes:
        - Only logs when enable_logging is True
        - Uses ANSI color codes for terminal formatting
        - Provides consistent logging format across OpenAI operations
        """
        if not self.enable_logging:
            return
            
        colors = {
            "openai_start": "\033[96m",  # Cyan
            "openai_thinking": "\033[93m",  # Yellow
            "openai_response": "\033[92m",  # Green
            "openai_function": "\033[95m",  # Magenta
            "openai_error": "\033[91m",  # Red
            "openai_complete": "\033[94m",  # Blue
            "reset": "\033[0m"
        }
        
        color = colors.get(event_type, colors["reset"])
        reset = colors["reset"]
        
        if content:
            print(f"{color}[OpenAI-{event_type.upper()}]{reset} {content[:100]}{'...' if len(content) > 100 else ''}")
        else:
            print(f"{color}[OpenAI-{event_type.upper()}]{reset}")
    
    def process_openai_streaming_response(
        self, 
        openai_stream: Generator[str, None, None],
        session_id: str = "default"
    ) -> Generator[str, None, None]:
        """Process OpenAI streaming response with enhanced parsing and error handling.
        
        This method provides comprehensive processing of OpenAI streaming responses,
        converting raw token streams into properly formatted OpenAI chunks, parsing
        them with specialized OpenAI logic, and yielding Server-Sent Events (SSE)
        formatted data for real-time streaming.
        
        Processing Pipeline:
        1. Converts raw tokens to OpenAI-compatible chunk format
        2. Parses chunks using specialized OpenAI parser
        3. Logs OpenAI-specific events for monitoring
        4. Formats tokens for SSE streaming
        5. Applies appropriate streaming delays
        6. Handles errors with proper recovery
        
        Error Handling:
        - Catches and logs streaming exceptions
        - Yields error tokens in OpenAI format
        - Provides graceful error recovery with completion tokens
        - Maintains streaming format even during errors
        
        Args:
            openai_stream (Generator[str, None, None]): Raw token stream from OpenAI provider
            session_id (str, optional): Session identifier for tracking and logging.
                                       Defaults to "default"
            
        Yields:
            str: Server-Sent Events (SSE) formatted data containing OpenAI-specific
                token information and metadata
                
        Notes:
        - Uses OpenAI-specific parsing logic for better accuracy
        - Applies streaming delays for improved user experience
        - Provides comprehensive logging for debugging
        - Maintains OpenAI response format consistency
        """
        
        self.log_openai_event("openai_start", f"Starting OpenAI stream processing for session {session_id}")
        
        try:
            # Convert raw token stream to OpenAI chunk format
            openai_chunks = self._convert_tokens_to_openai_chunks(openai_stream)
            
            # Parse OpenAI chunks using the specialized parser
            parsed_stream = self.openai_parser.parse_openai_stream(openai_chunks)
            
            # Process and yield formatted tokens
            for openai_token in parsed_stream:
                # Log OpenAI-specific events
                self._log_openai_token_event(openai_token)
                
                # Format for SSE with OpenAI-specific data
                sse_data = self.openai_parser.format_openai_for_sse(openai_token)
                yield sse_data
                
                # Add streaming delay for non-control tokens
                if self._should_add_delay(openai_token):
                    time.sleep(Config.STREAMING_DELAY)
            
            self.log_openai_event("openai_complete", "OpenAI stream processing completed successfully")
            
        except Exception as e:
            self.log_openai_event("openai_error", f"Error in OpenAI streaming: {str(e)}")
            
            # Yield error token in OpenAI format
            error_token = OpenAIParsedToken(
                content=f"OpenAI streaming error: {str(e)}",
                token_type=OpenAITokenType.OPENAI_ERROR,
                metadata={"error_type": "openai_streaming_error", "session_id": session_id}
            )
            
            yield self.openai_parser.format_openai_for_sse(error_token)
            
            # Yield completion token
            complete_token = OpenAIParsedToken(
                content="",
                token_type=OpenAITokenType.OPENAI_COMPLETE,
                metadata={"error_recovery": True, "session_id": session_id}
            )
            
            yield self.openai_parser.format_openai_for_sse(complete_token)
    
    def _convert_tokens_to_openai_chunks(self, token_stream: Generator[str, None, None]) -> Generator[Dict[str, Any], None, None]:
        """Convert raw token stream to OpenAI chunk format for processing.
        
        This method transforms a raw token stream into OpenAI's standard chunk format,
        enabling consistent processing through OpenAI-specific parsers. It creates
        properly structured chunks with delta format and appropriate metadata.
        
        Chunk Structure:
        - choices: Array containing delta content and metadata
        - delta: Contains the actual token content
        - object: Identifies as chat completion chunk
        - model: Model identifier (updated by actual provider)
        - created: Unix timestamp for the chunk
        - finish_reason: Completion status (null for ongoing, 'stop' for final)
        
        Processing Flow:
        1. Accumulates content for tracking purposes
        2. Creates OpenAI-style chunks for each token
        3. Yields chunks with delta format
        4. Provides final chunk with finish_reason
        
        Args:
            token_stream (Generator[str, None, None]): Raw token stream to convert
            
        Yields:
            Dict[str, Any]: OpenAI-formatted chunks with proper structure and metadata
            
        Notes:
        - Maintains OpenAI API compatibility
        - Handles empty tokens gracefully
        - Provides proper stream termination with final chunk
        - Uses current timestamp for chunk creation
        """
        
        accumulated_content = ""
        
        for token in token_stream:
            if not token:
                continue
                
            accumulated_content += token
            
            # Create OpenAI-style chunk with delta format
            chunk = {
                "choices": [{
                    "delta": {
                        "content": token
                    },
                    "index": 0,
                    "finish_reason": None
                }],
                "object": "chat.completion.chunk",
                "model": "openai-model",  # This will be updated by the actual provider
                "created": int(time.time())
            }
            
            yield chunk
        
        # Yield final chunk with finish_reason
        final_chunk = {
            "choices": [{
                "delta": {},
                "index": 0,
                "finish_reason": "stop"
            }],
            "object": "chat.completion.chunk",
            "model": "openai-model",
            "created": int(time.time())
        }
        
        yield final_chunk
    
    def _log_openai_token_event(self, token: OpenAIParsedToken):
        """Log OpenAI token events with appropriate categorization.
        
        This method provides specialized logging for different types of OpenAI tokens,
        categorizing them appropriately and logging with relevant context. It helps
        with debugging and monitoring of OpenAI streaming processes.
        
        Token Type Categorization:
        - OPENAI_THINKING_START/END: Thinking mode transitions
        - OPENAI_THINKING: Reasoning content during thinking phase
        - OPENAI_RESPONSE: Main response content generation
        - OPENAI_FUNCTION_CALL/TOOL_CALL: Function and tool execution
        - OPENAI_ERROR: Error conditions and exceptions
        - OPENAI_COMPLETE: Stream completion events
        
        Logging Features:
        - Type-specific event categorization
        - Content extraction and formatting
        - Contextual information for debugging
        - Consistent logging format
        
        Args:
            token (OpenAIParsedToken): The OpenAI token to log with type and content
            
        Notes:
        - Uses token type for appropriate event categorization
        - Extracts relevant content for logging context
        - Provides debugging information for OpenAI operations
        - Maintains consistent logging across token types
        """
        
        if token.token_type == OpenAITokenType.OPENAI_THINKING_START:
            self.log_openai_event("openai_thinking", "Entering thinking mode")
        elif token.token_type == OpenAITokenType.OPENAI_THINKING:
            self.log_openai_event("openai_thinking", token.content)
        elif token.token_type == OpenAITokenType.OPENAI_THINKING_END:
            self.log_openai_event("openai_thinking", "Exiting thinking mode")
        elif token.token_type == OpenAITokenType.OPENAI_RESPONSE:
            self.log_openai_event("openai_response", token.content)
        elif token.token_type in [OpenAITokenType.OPENAI_FUNCTION_CALL, OpenAITokenType.OPENAI_TOOL_CALL]:
            self.log_openai_event("openai_function", f"Function call: {token.content}")
        elif token.token_type == OpenAITokenType.OPENAI_ERROR:
            self.log_openai_event("openai_error", token.content)
        elif token.token_type == OpenAITokenType.OPENAI_COMPLETE:
            self.log_openai_event("openai_complete", "Stream completed")
    
    def _should_add_delay(self, token: OpenAIParsedToken) -> bool:
        """Determine if streaming delay should be added for this token type.
        
        This method evaluates whether a streaming delay should be applied based on
        the OpenAI token type. Control tokens (like thinking markers and completion
        signals) are processed immediately, while content tokens receive delays
        for better user experience.
        
        Control Token Types (No Delay):
        - OPENAI_THINKING_START: Start of thinking phase
        - OPENAI_THINKING_END: End of thinking phase
        - OPENAI_COMPLETE: Stream completion marker
        
        Content Token Types (With Delay):
        - OPENAI_THINKING: Thinking content
        - OPENAI_RESPONSE: Response content
        - OPENAI_FUNCTION_CALL: Function calls
        - OPENAI_ERROR: Error messages
        
        Args:
            token (OpenAIParsedToken): The OpenAI token to evaluate for delay
            
        Returns:
            bool: True if streaming delay should be added, False for control tokens
            
        Notes:
        - Improves user experience by controlling streaming speed
        - Excludes control tokens for immediate processing
        - Maintains responsive feel for structural elements
        - Applies delays only to visible content
        """
        
        control_types = {
            OpenAITokenType.OPENAI_THINKING_START,
            OpenAITokenType.OPENAI_THINKING_END,
            OpenAITokenType.OPENAI_COMPLETE
        }
        
        return token.token_type not in control_types
    
    def process_openai_non_streaming_response(
        self, 
        openai_response: Dict[str, Any],
        session_id: str = "default"
    ) -> Dict[str, Any]:
        """Process OpenAI non-streaming response with enhanced validation.
        
        This method processes complete OpenAI responses (non-streaming) with
        comprehensive validation, content extraction, and standardization. It
        ensures consistent response format and integrates with OpenAI-specific
        parsing logic for optimal results.
        
        Processing Steps:
        1. Validates OpenAI response structure
        2. Extracts content from choices array
        3. Processes through OpenAI parser for consistency
        4. Cleans and formats the response
        5. Creates standardized response structure
        6. Includes OpenAI-specific metadata
        
        Response Structure:
        - response: Cleaned and processed content
        - success: Processing success status
        - provider: Provider identification (openai)
        - model: Model name from response
        - session_id: Session tracking identifier
        - openai_metadata: OpenAI-specific response metadata
        
        Error Handling:
        - Validates response structure before processing
        - Handles missing or malformed content gracefully
        - Provides detailed error information
        - Maintains consistent error response format
        
        Args:
            openai_response (Dict[str, Any]): Complete OpenAI API response
            session_id (str, optional): Session identifier for tracking.
                                       Defaults to "default"
            
        Returns:
            Dict[str, Any]: Standardized response with OpenAI metadata and
                          processed content
                          
        Notes:
        - Uses OpenAI parser for consistent content processing
        - Preserves OpenAI-specific metadata for debugging
        - Provides comprehensive error handling
        - Maintains response format consistency
        """
        
        self.log_openai_event("openai_start", f"Processing OpenAI non-streaming response for session {session_id}")
        
        try:
            # Extract content from OpenAI response format
            if 'choices' in openai_response and openai_response['choices']:
                choice = openai_response['choices'][0]
                
                if 'message' in choice and 'content' in choice['message']:
                    content = choice['message']['content']
                    
                    # Process through OpenAI parser for consistency
                    self.openai_parser.reset_openai_state()
                    self.openai_parser.accumulated_response = content
                    
                    # Extract final response using OpenAI-specific cleaning
                    clean_response = self.openai_parser.extract_final_response()
                    
                    # Create standardized response
                    standardized_response = {
                        "response": clean_response,
                        "success": True,
                        "provider": "openai",
                        "model": openai_response.get('model', 'unknown'),
                        "session_id": session_id,
                        "openai_metadata": {
                            "finish_reason": choice.get('finish_reason'),
                            "usage": openai_response.get('usage', {}),
                            "created": openai_response.get('created'),
                            "object": openai_response.get('object')
                        }
                    }
                    
                    self.log_openai_event("openai_complete", f"Non-streaming response processed: {len(clean_response)} chars")
                    return standardized_response
            
            # Handle error case
            error_response = {
                "response": "Invalid OpenAI response format",
                "success": False,
                "provider": "openai",
                "model": openai_response.get('model', 'unknown'),
                "session_id": session_id,
                "error": "Invalid response structure"
            }
            
            self.log_openai_event("openai_error", "Invalid OpenAI response format")
            return error_response
            
        except Exception as e:
            self.log_openai_event("openai_error", f"Error processing OpenAI response: {str(e)}")
            
            return {
                "response": f"Error processing OpenAI response: {str(e)}",
                "success": False,
                "provider": "openai",
                "model": openai_response.get('model', 'unknown') if isinstance(openai_response, dict) else 'unknown',
                "session_id": session_id,
                "error": str(e)
            }
    
    def create_compatibility_stream(
        self, 
        openai_stream: Generator[str, None, None],
        session_id: str = "default"
    ) -> Generator[str, None, None]:
        """Create a compatibility stream that converts OpenAI tokens to standard format.
        
        This method creates a compatibility layer that processes OpenAI streaming responses
        and converts them to a standardized format that can be consumed by components
        expecting standard token formats. It bridges OpenAI-specific processing with
        universal token handling.
        
        Processing Flow:
        1. Processes OpenAI stream through specialized handler
        2. Parses Server-Sent Events (SSE) data from OpenAI processing
        3. Converts OpenAI tokens to standard token format
        4. Re-formats as standard SSE for universal consumption
        5. Handles conversion errors gracefully
        
        Conversion Features:
        - OpenAI token type to standard token type mapping
        - Metadata preservation during conversion
        - Error handling with fallback to standard format
        - SSE format consistency maintenance
        
        Error Handling:
        - Catches JSON parsing errors in SSE data
        - Handles conversion failures gracefully
        - Provides error tokens in standard format
        - Maintains streaming continuity during errors
        
        Args:
            openai_stream (Generator[str, None, None]): Raw OpenAI token stream
            session_id (str, optional): Session identifier for tracking.
                                       Defaults to "default"
            
        Yields:
            str: Standard format SSE data compatible with universal token consumers
            
        Notes:
        - Enables OpenAI responses to work with standard processing pipelines
        - Preserves OpenAI-specific metadata during conversion
        - Maintains streaming performance and responsiveness
        - Provides seamless integration between OpenAI and standard formats
        """
        
        try:
            # Process through OpenAI handler
            openai_sse_stream = self.process_openai_streaming_response(openai_stream, session_id)
            
            for sse_data in openai_sse_stream:
                # Parse the SSE data to extract the token
                if sse_data.startswith('data: '):
                    try:
                        data = json.loads(sse_data[6:])
                        
                        # Convert OpenAI token to standard token
                        openai_token = OpenAIParsedToken(
                            content=data.get('token', ''),
                            token_type=OpenAITokenType(data.get('type', 'openai_response')),
                            metadata=data
                        )
                        
                        # Convert to standard format
                        standard_token = self.openai_parser.convert_to_standard_token(openai_token)
                        
                        # Format as standard SSE
                        standard_sse = self.openai_parser.format_for_sse(standard_token)
                        yield standard_sse
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        self.log_openai_event("openai_error", f"Error parsing SSE data: {str(e)}")
                        continue
                else:
                    # Pass through non-data lines
                    yield sse_data
                    
        except Exception as e:
            self.log_openai_event("openai_error", f"Error in compatibility stream: {str(e)}")
            
            # Yield error in standard format
            error_token = ParsedToken(
                content=f"OpenAI compatibility error: {str(e)}",
                token_type=TokenType.ERROR,
                metadata={"error_type": "openai_compatibility_error"}
            )
            
            yield self.openai_parser.format_for_sse(error_token)
    
    def get_openai_response_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of the OpenAI response processing.
        
        This method provides a detailed summary of the OpenAI response processing
        session, including extracted content, metadata, and processing statistics.
        It aggregates information from the OpenAI parser to provide insights into
        the response generation and processing.
        
        Summary Components:
        - final_response: The cleaned and processed final response content
        - thinking_content: Any thinking/reasoning content that was processed
        - had_thinking: Boolean indicating if thinking phase was present
        - response_length: Character count of the final response
        - thinking_length: Character count of thinking content
        - function_calls: Any function/tool calls that were processed
        - openai_metadata: OpenAI-specific processing metadata
        
        OpenAI Metadata:
        - function_name: Name of any function calls detected
        - function_arguments: Arguments for function calls
        - content_buffer: Size of internal content buffer
        
        Use Cases:
        - Response quality analysis and debugging
        - Processing performance monitoring
        - Content extraction and validation
        - Session tracking and logging
        
        Returns:
            Dict[str, Any]: Comprehensive summary containing response content,
                          processing statistics, and OpenAI-specific metadata
                          
        Notes:
        - Aggregates data from the internal OpenAI parser
        - Provides both content and metadata for analysis
        - Useful for debugging and monitoring OpenAI processing
        - Includes processing statistics for performance analysis
        """
        
        return {
            "final_response": self.openai_parser.extract_final_response(),
            "thinking_content": self.openai_parser.accumulated_thinking,
            "had_thinking": self.openai_parser.thinking_started,
            "response_length": len(self.openai_parser.final_response),
            "thinking_length": len(self.openai_parser.accumulated_thinking),
            "function_calls": self.openai_parser.accumulated_tool_calls,
            "openai_metadata": {
                "function_name": self.openai_parser.openai_function_name,
                "function_arguments": self.openai_parser.openai_function_arguments,
                "content_buffer": len(self.openai_parser.openai_content_buffer)
            }
        }