"""OpenAI-specific output parser for handling OpenAI streaming responses."""

import json
import re
from typing import Dict, Any, Generator, Tuple
from enum import Enum
from dataclasses import dataclass
from output_parser import OutputParser, ParsedToken, TokenType

class OpenAITokenType(Enum):
    """OpenAI-specific token types for enhanced parsing"""
    OPENAI_THINKING_START = "openai_thinking_start"
    OPENAI_THINKING = "openai_thinking"
    OPENAI_THINKING_END = "openai_thinking_end"
    OPENAI_RESPONSE = "openai_response"
    OPENAI_TOOL_CALL = "openai_tool_call"
    OPENAI_ERROR = "openai_error"
    OPENAI_COMPLETE = "openai_complete"
    OPENAI_DELTA = "openai_delta"  # For OpenAI's delta format
    OPENAI_FUNCTION_CALL = "openai_function_call"  # For function calling
    OPENAI_CONTENT = "openai_content"  # For content tokens

@dataclass
class OpenAIParsedToken:
    """OpenAI-specific parsed token with enhanced metadata"""
    content: str
    token_type: OpenAITokenType
    metadata: Dict[str, Any]
    raw_delta: Dict[str, Any] = None  # Store raw OpenAI delta
    finish_reason: str = None  # OpenAI finish reason
    function_call: Dict[str, Any] = None  # Function call data

class OpenAIOutputParser(OutputParser):
    """OpenAI-specific output parser with enhanced OpenAI response handling."""
    
    def __init__(self, enable_terminal_logging: bool = False):
        """Initialize the OpenAI-specific output parser with enhanced OpenAI capabilities.
        
        This constructor extends the base OutputParser with OpenAI-specific parsing
        capabilities, including specialized pattern recognition for OpenAI's unique
        response formats, delta processing, and function call handling.
        
        OpenAI-Specific Features:
        - Enhanced thinking pattern recognition for OpenAI responses
        - Delta format processing for streaming responses
        - Function call and tool call parsing
        - OpenAI-specific state management
        - Specialized content buffering and tracking
        
        Pattern Recognition:
        - Multiple thinking tag formats (<thinking>, <think>, **thinking**, [thinking])
        - Corresponding end patterns for proper thinking section detection
        - Case-insensitive and multiline pattern matching
        - Regex compilation for performance optimization
        
        State Management:
        - Delta buffer for accumulating OpenAI delta responses
        - Function call buffer for tracking function execution
        - Content buffer for OpenAI-specific content handling
        - Function call state tracking
        
        Args:
            enable_terminal_logging (bool, optional): Whether to enable terminal logging
                                                     for debugging and monitoring.
                                                     Defaults to False
                                                     
        Notes:
        - Inherits base functionality from OutputParser
        - Adds OpenAI-specific regex patterns and state variables
        - Optimizes pattern matching with compiled regex
        - Provides foundation for OpenAI delta and function call processing
        """
        super().__init__(enable_terminal_logging)
        
        # OpenAI-specific patterns
        self.openai_thinking_patterns = [
            r'<thinking>',
            r'<think>',
            r'\*\*thinking\*\*',
            r'\[thinking\]'
        ]
        
        self.openai_thinking_end_patterns = [
            r'</thinking>',
            r'</think>',
            r'\*\*/thinking\*\*',
            r'\[/thinking\]'
        ]
        
        # OpenAI-specific regex patterns
        self.openai_thinking_start_regex = re.compile(
            '|'.join(self.openai_thinking_patterns), 
            re.IGNORECASE | re.MULTILINE
        )
        
        self.openai_thinking_end_regex = re.compile(
            '|'.join(self.openai_thinking_end_patterns), 
            re.IGNORECASE | re.MULTILINE
        )
        
        # OpenAI delta tracking
        self.openai_delta_buffer = ""
        self.openai_function_call_buffer = {}
        self.openai_content_buffer = ""
        
        # OpenAI-specific state
        self.openai_in_function_call = False
        self.openai_function_name = None
        self.openai_function_arguments = ""
        
    def reset_openai_state(self):
        """Reset OpenAI-specific parsing state to initial conditions.
        
        This method resets all OpenAI-specific state variables to their initial
        values, preparing the parser for processing a new OpenAI response. It
        extends the base reset functionality with OpenAI-specific state management.
        
        Reset Components:
        - Base parser state (via parent reset_state call)
        - OpenAI delta buffer for accumulating delta responses
        - Function call buffer for tracking function data
        - Content buffer for OpenAI-specific content
        - Function call state flags and tracking variables
        - Function name and arguments accumulation
        
        State Variables Reset:
        - openai_delta_buffer: Cleared to empty string
        - openai_function_call_buffer: Reset to empty dictionary
        - openai_content_buffer: Cleared to empty string
        - openai_in_function_call: Set to False
        - openai_function_name: Reset to None
        - openai_function_arguments: Cleared to empty string
        
        Use Cases:
        - Preparing for new OpenAI response processing
        - Cleaning up after completed response processing
        - Error recovery and state consistency maintenance
        - Session boundary management
        
        Notes:
        - Calls parent reset_state() to maintain inheritance consistency
        - Ensures clean state for accurate OpenAI response parsing
        - Prevents state leakage between different responses
        - Essential for proper multi-response processing
        """
        self.reset_state()  # Call parent reset
        self.openai_delta_buffer = ""
        self.openai_function_call_buffer = {}
        self.openai_content_buffer = ""
        self.openai_in_function_call = False
        self.openai_function_name = None
        self.openai_function_arguments = ""
    
    def parse_openai_delta(self, delta: Dict[str, Any]) -> Generator[OpenAIParsedToken, None, None]:
        """Parse OpenAI delta format with comprehensive content and function call handling.
        
        This method processes OpenAI's delta format responses, which provide incremental
        updates to the response content. It handles content deltas, function calls, and
        tool calls while maintaining proper state tracking and thinking section detection.
        
        Delta Processing Features:
        - Content delta accumulation and processing
        - Thinking pattern detection within delta content
        - Function call parsing and state management
        - Tool call handling for newer OpenAI formats
        - Proper state transitions and metadata tracking
        
        Content Handling:
        - Accumulates content in openai_content_buffer
        - Detects thinking start/end patterns in real-time
        - Manages thinking vs response content classification
        - Cleans content of thinking markers
        - Tracks content length and processing state
        
        Function Call Processing:
        - Detects function call initiation and name extraction
        - Accumulates function arguments incrementally
        - Provides stage-based function call tracking
        - Handles both legacy and modern function call formats
        
        Tool Call Support:
        - Processes tool_calls array from newer OpenAI responses
        - Extracts tool call IDs and function information
        - Provides comprehensive tool call metadata
        
        Args:
            delta (Dict[str, Any]): OpenAI delta object containing incremental updates
            
        Yields:
            OpenAIParsedToken: Parsed tokens with OpenAI-specific type classification,
                             content, metadata, and raw delta information
                             
        Notes:
        - Handles empty or None deltas gracefully
        - Maintains proper thinking state transitions
        - Provides comprehensive metadata for debugging
        - Supports both content and function call processing simultaneously
        """
        if not delta:
            return
            
        # Handle content deltas
        if 'content' in delta and delta['content']:
            content = delta['content']
            self.openai_content_buffer += content
            
            # Check for thinking patterns in content
            if self.openai_thinking_start_regex.search(content) and not self.in_thinking:
                self.in_thinking = True
                self.thinking_started = True
                yield OpenAIParsedToken(
                    content="",
                    token_type=OpenAITokenType.OPENAI_THINKING_START,
                    metadata={"transition": "entering_openai_thinking"},
                    raw_delta=delta
                )
                # Clean content and continue
                content = self.clean_openai_token(content)
            
            if self.openai_thinking_end_regex.search(content) and self.in_thinking:
                self.in_thinking = False
                self.thinking_ended = True
                yield OpenAIParsedToken(
                    content="",
                    token_type=OpenAITokenType.OPENAI_THINKING_END,
                    metadata={"transition": "exiting_openai_thinking"},
                    raw_delta=delta
                )
                # Clean content and continue
                content = self.clean_openai_token(content)
            
            # Yield appropriate content based on state
            if content:
                if self.in_thinking:
                    self.accumulated_thinking += content
                    yield OpenAIParsedToken(
                        content=content,
                        token_type=OpenAITokenType.OPENAI_THINKING,
                        metadata={"thinking_length": len(self.accumulated_thinking)},
                        raw_delta=delta
                    )
                else:
                    self.final_response += content
                    yield OpenAIParsedToken(
                        content=content,
                        token_type=OpenAITokenType.OPENAI_RESPONSE,
                        metadata={"response_length": len(self.final_response)},
                        raw_delta=delta
                    )
        
        # Handle function calls
        if 'function_call' in delta:
            function_call = delta['function_call']
            
            if 'name' in function_call:
                self.openai_in_function_call = True
                self.openai_function_name = function_call['name']
                yield OpenAIParsedToken(
                    content="",
                    token_type=OpenAITokenType.OPENAI_FUNCTION_CALL,
                    metadata={"function_name": self.openai_function_name, "stage": "start"},
                    raw_delta=delta,
                    function_call=function_call
                )
            
            if 'arguments' in function_call:
                self.openai_function_arguments += function_call['arguments']
                yield OpenAIParsedToken(
                    content=function_call['arguments'],
                    token_type=OpenAITokenType.OPENAI_FUNCTION_CALL,
                    metadata={
                        "function_name": self.openai_function_name,
                        "stage": "arguments",
                        "arguments_length": len(self.openai_function_arguments)
                    },
                    raw_delta=delta,
                    function_call=function_call
                )
        
        # Handle tool calls (newer OpenAI format)
        if 'tool_calls' in delta:
            for tool_call in delta['tool_calls']:
                if 'function' in tool_call:
                    function = tool_call['function']
                    yield OpenAIParsedToken(
                        content=json.dumps(function),
                        token_type=OpenAITokenType.OPENAI_TOOL_CALL,
                        metadata={
                            "tool_call_id": tool_call.get('id'),
                            "function_name": function.get('name'),
                            "stage": "tool_call"
                        },
                        raw_delta=delta,
                        function_call=function
                    )
    
    def clean_openai_token(self, token: str) -> str:
        """Clean OpenAI-specific tokens by removing thinking markers and formatting.
        
        This method removes OpenAI-specific thinking markers and formatting from
        token content, ensuring clean output for final response generation. It
        processes multiple thinking tag formats and handles case-insensitive matching.
        
        Cleaning Operations:
        - Removes thinking start markers (<thinking>, <think>, **thinking**, [thinking])
        - Removes thinking end markers (</thinking>, </think>, **/thinking**, [/thinking])
        - Handles case-insensitive pattern matching
        - Preserves content while removing only formatting markers
        
        Supported Thinking Formats:
        - XML-style tags: <thinking>, <think>
        - Markdown-style: **thinking**
        - Bracket-style: [thinking]
        - Corresponding end tags for each format
        
        Processing Features:
        - Case-insensitive pattern matching
        - Multiple pattern format support
        - Preserves original content structure
        - Handles partial marker matches
        
        Args:
            token (str): The token content to clean of OpenAI-specific markers
            
        Returns:
            str: Cleaned token content with thinking markers removed
            
        Notes:
        - Returns original token if None or empty
        - Uses regex substitution for efficient cleaning
        - Maintains content integrity while removing formatting
        - Essential for generating clean final responses
        """
        if not token:
            return token
        
        # Remove OpenAI thinking tags
        for pattern in self.openai_thinking_patterns:
            token = re.sub(pattern, '', token, flags=re.IGNORECASE)
        
        for pattern in self.openai_thinking_end_patterns:
            token = re.sub(pattern, '', token, flags=re.IGNORECASE)
        
        return token
    
    def parse_openai_stream(self, openai_stream: Generator[Dict[str, Any], None, None]) -> Generator[OpenAIParsedToken, None, None]:
        """Parse OpenAI streaming response format with comprehensive chunk processing.
        
        This method processes a stream of OpenAI response chunks, extracting deltas
        and handling various OpenAI response formats including content, function calls,
        and completion signals. It provides the main entry point for OpenAI stream processing.
        
        Processing Pipeline:
        1. Iterates through OpenAI response chunks
        2. Extracts choices array from each chunk
        3. Processes delta content through specialized delta parser
        4. Handles finish_reason for completion detection
        5. Yields completion tokens when stream ends
        6. Provides error handling for malformed chunks
        
        Chunk Structure Handling:
        - Validates chunk structure and choices array
        - Extracts delta content from choices[0]
        - Processes finish_reason for completion detection
        - Handles multiple choice scenarios (uses first choice)
        
        Completion Detection:
        - Monitors finish_reason for stream completion
        - Yields OPENAI_COMPLETE token when stream ends
        - Provides completion metadata and statistics
        
        Error Handling:
        - Gracefully handles malformed chunks
        - Continues processing despite individual chunk errors
        - Provides error logging and recovery
        
        Args:
            openai_stream (Generator[Dict[str, Any], None, None]): Stream of OpenAI
                                                                  response chunks
            
        Yields:
            OpenAIParsedToken: Parsed tokens from OpenAI deltas with proper
                             type classification and metadata
                             
        Notes:
        - Main entry point for OpenAI streaming response processing
        - Handles various OpenAI response formats and edge cases
        - Provides comprehensive completion detection and signaling
        - Integrates with delta parser for detailed content processing
        """
        self.reset_openai_state()
        
        try:
            for chunk in openai_stream:
                # Handle OpenAI chunk format
                if 'choices' in chunk and chunk['choices']:
                    choice = chunk['choices'][0]
                    
                    # Handle delta format
                    if 'delta' in choice:
                        yield from self.parse_openai_delta(choice['delta'])
                    
                    # Handle finish reason
                    if 'finish_reason' in choice and choice['finish_reason']:
                        yield OpenAIParsedToken(
                            content="",
                            token_type=OpenAITokenType.OPENAI_COMPLETE,
                            metadata={
                                "finish_reason": choice['finish_reason'],
                                "final_response_length": len(self.final_response),
                                "thinking_length": len(self.accumulated_thinking),
                                "had_thinking": self.thinking_started
                            },
                            finish_reason=choice['finish_reason']
                        )
                        break
                
                # Handle error in chunk
                if 'error' in chunk:
                    yield OpenAIParsedToken(
                        content=f"OpenAI Error: {chunk['error']}",
                        token_type=OpenAITokenType.OPENAI_ERROR,
                        metadata={"error_type": "openai_api_error"},
                        raw_delta=chunk
                    )
        
        except Exception as e:
            yield OpenAIParsedToken(
                content=f"Error parsing OpenAI stream: {str(e)}",
                token_type=OpenAITokenType.OPENAI_ERROR,
                metadata={"error_type": "openai_parsing_error"}
            )
        
        finally:
            # Always yield completion if not already done
            if not any(True for _ in []):
                yield OpenAIParsedToken(
                    content="",
                    token_type=OpenAITokenType.OPENAI_COMPLETE,
                    metadata={
                        "final_response_length": len(self.final_response),
                        "thinking_length": len(self.accumulated_thinking),
                        "had_thinking": self.thinking_started
                    }
                )
    
    def format_openai_for_sse(self, parsed_token: OpenAIParsedToken) -> str:
        """Format OpenAI ParsedToken for Server-Sent Events with comprehensive metadata.
        
        This method converts an OpenAI-specific parsed token into a properly formatted
        Server-Sent Events (SSE) data string, preserving all OpenAI-specific metadata
        and ensuring compatibility with web streaming protocols.
        
        SSE Formatting Features:
        - Converts token content and type to JSON format
        - Preserves OpenAI-specific metadata and fields
        - Includes function call information when present
        - Maintains raw delta data for debugging
        - Follows SSE protocol with proper data prefix
        
        Data Structure:
        - Base fields: token content and type
        - Metadata: All available metadata from parsed token
        - OpenAI-specific: finish_reason, function_call, raw_delta
        - JSON serialization for web compatibility
        
        OpenAI-Specific Fields:
        - finish_reason: Completion status from OpenAI
        - function_call: Function call data and arguments
        - raw_delta: Original delta object for debugging
        - Metadata: Processing statistics and state information
        
        Args:
            parsed_token (OpenAIParsedToken): OpenAI-specific parsed token with
                                            content, type, and metadata
                                            
        Returns:
            str: SSE-formatted string ready for web streaming with proper
                 data prefix and JSON payload
                 
        Notes:
        - Follows SSE protocol with 'data: ' prefix and double newline
        - Preserves all OpenAI-specific information for client processing
        - Ensures JSON serialization compatibility
        - Maintains debugging information through raw_delta inclusion
        """
        data = {
            'token': parsed_token.content,
            'type': parsed_token.token_type.value
        }
        
        # Add metadata if present
        if parsed_token.metadata:
            data.update(parsed_token.metadata)
        
        # Add OpenAI-specific fields
        if parsed_token.finish_reason:
            data['finish_reason'] = parsed_token.finish_reason
        
        if parsed_token.function_call:
            data['function_call'] = parsed_token.function_call
        
        if parsed_token.raw_delta:
            data['raw_delta'] = parsed_token.raw_delta
        
        return f"data: {json.dumps(data)}\n\n"
    
    def convert_to_standard_token(self, openai_token: OpenAIParsedToken) -> ParsedToken:
        """Convert OpenAI token to standard ParsedToken for cross-provider compatibility.
        
        This method provides a compatibility layer by converting OpenAI-specific
        parsed tokens into standard ParsedToken format, enabling consistent
        processing across different LLM providers while preserving essential information.
        
        Conversion Features:
        - Maps OpenAI-specific token types to standard types
        - Preserves content and metadata information
        - Provides fallback mapping for unknown types
        - Maintains compatibility with base OutputParser
        
        Type Mapping:
        - OPENAI_THINKING_START → THINKING_START
        - OPENAI_THINKING → THINKING
        - OPENAI_THINKING_END → THINKING_END
        - OPENAI_RESPONSE → RESPONSE
        - OPENAI_TOOL_CALL → TOOL_CALL
        - OPENAI_FUNCTION_CALL → TOOL_CALL
        - OPENAI_ERROR → ERROR
        - OPENAI_COMPLETE → COMPLETE
        - OPENAI_DELTA → RESPONSE
        - OPENAI_CONTENT → RESPONSE
        
        Compatibility Benefits:
        - Enables use of standard processing pipelines
        - Allows provider-agnostic token handling
        - Maintains essential token information
        - Provides consistent interface across providers
        
        Args:
            openai_token (OpenAIParsedToken): OpenAI-specific token to convert
            
        Returns:
            ParsedToken: Standard token format compatible with base OutputParser
            
        Notes:
        - Uses type mapping dictionary for efficient conversion
        - Defaults to RESPONSE type for unmapped types
        - Preserves all metadata from original token
        - Essential for provider-agnostic processing
        """
        # Map OpenAI token types to standard types
        type_mapping = {
            OpenAITokenType.OPENAI_THINKING_START: TokenType.THINKING_START,
            OpenAITokenType.OPENAI_THINKING: TokenType.THINKING,
            OpenAITokenType.OPENAI_THINKING_END: TokenType.THINKING_END,
            OpenAITokenType.OPENAI_RESPONSE: TokenType.RESPONSE,
            OpenAITokenType.OPENAI_TOOL_CALL: TokenType.TOOL_CALL,
            OpenAITokenType.OPENAI_ERROR: TokenType.ERROR,
            OpenAITokenType.OPENAI_COMPLETE: TokenType.COMPLETE,
            OpenAITokenType.OPENAI_DELTA: TokenType.RESPONSE,
            OpenAITokenType.OPENAI_FUNCTION_CALL: TokenType.TOOL_CALL,
            OpenAITokenType.OPENAI_CONTENT: TokenType.RESPONSE
        }
        
        standard_type = type_mapping.get(openai_token.token_type, TokenType.RESPONSE)
        
        return ParsedToken(
            content=openai_token.content,
            token_type=standard_type,
            metadata=openai_token.metadata or {}
        )
    
    def format_for_sse(self, parsed_token: ParsedToken) -> str:
        """Format a ParsedToken for Server-Sent Events using inherited base functionality.
        
        This method provides an override of the parent class SSE formatting method,
        ensuring that standard ParsedToken objects are formatted consistently with
        the base OutputParser implementation while maintaining OpenAI compatibility.
        
        Inheritance Features:
        - Delegates to parent class implementation
        - Maintains consistent SSE formatting across parsers
        - Provides compatibility with standard token processing
        - Ensures proper SSE protocol compliance
        
        Processing Flow:
        - Receives standard ParsedToken object
        - Calls parent class format_for_sse method
        - Returns properly formatted SSE string
        - Maintains consistency with base parser behavior
        
        Use Cases:
        - Processing converted standard tokens
        - Maintaining compatibility with base parser
        - Ensuring consistent SSE output format
        - Supporting mixed token type processing
        
        Args:
            parsed_token (ParsedToken): Standard parsed token to format for SSE
            
        Returns:
            str: SSE-formatted string following base parser conventions
            
        Notes:
        - Inherits base class SSE formatting behavior
        - Maintains consistency across different token types
        - Provides fallback for non-OpenAI specific tokens
        - Essential for mixed provider token processing
        """
        # Use the parent class method for standard tokens
        return super().format_for_sse(parsed_token)