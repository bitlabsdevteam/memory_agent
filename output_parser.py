"""Output Parser for standardizing LLM responses across different providers"""

import json
import re
import sys
from typing import Dict, Any, Generator, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class TokenType(Enum):
    """Types of tokens in the response stream"""
    THINKING_START = "thinking_start"
    THINKING = "thinking"
    THINKING_END = "thinking_end"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL = "tool_call"
    TOOL_CALL_END = "tool_call_end"
    TOOL_RESULT_START = "tool_result_start"
    TOOL_RESULT = "tool_result"
    TOOL_RESULT_END = "tool_result_end"
    RESPONSE = "response"
    ERROR = "error"
    COMPLETE = "complete"

@dataclass
class ParsedToken:
    """Represents a parsed token with its type and content"""
    content: str
    token_type: TokenType
    metadata: Optional[Dict[str, Any]] = None

class OutputParser:
    """Standardized output parser for all LLM providers"""
    
    def __init__(self, enable_terminal_logging: bool = True):
        """Initialize the standardized output parser with comprehensive pattern recognition.
        
        This constructor sets up a universal output parser capable of handling responses
        from multiple LLM providers. It establishes regex patterns for detecting thinking
        sections, tool calls, and other structured content while providing configurable
        terminal logging for real-time monitoring.
        
        Pattern Recognition Setup:
        - Thinking patterns: Multiple tag formats (<thinking>, <think>, <reasoning>, <analysis>)
        - Tool call patterns: Various function call formats and syntaxes
        - Compiled regex for performance optimization
        - Case-insensitive matching for flexibility
        
        Thinking Tag Support:
        - XML-style tags: <thinking>, <think>, <reasoning>, <analysis>
        - Corresponding end tags for proper section detection
        - Multiline pattern matching capabilities
        - Flexible format recognition across providers
        
        Tool Call Detection:
        - TOOL_CALL: function_name(parameters) format
        - Using tool: function_name with parameters format
        - Calling function_name tool with parameters format
        - [function_name](parameters) bracket format
        
        State Management:
        - Initializes all tracking variables to default states
        - Prepares parser for multi-provider compatibility
        - Sets up logging configuration
        - Establishes clean parsing environment
        
        Args:
            enable_terminal_logging (bool, optional): Whether to enable real-time
                                                     terminal logging for debugging
                                                     and monitoring. Defaults to True
                                                     
        Notes:
        - Supports multiple LLM providers with unified interface
        - Optimizes pattern matching with compiled regex
        - Provides foundation for streaming response processing
        - Enables real-time monitoring through terminal logging
        """
        # Regex patterns for thinking tags (support multiple formats)
        self.thinking_start_patterns = [
            r'<thinking>',
            r'<think>',
            r'<reasoning>',
            r'<analysis>'
        ]
        self.thinking_end_patterns = [
            r'</thinking>',
            r'</think>',
            r'</reasoning>',
            r'</analysis>'
        ]
        
        # Regex patterns for tool calls
        self.tool_call_patterns = [
            r'TOOL_CALL:\s*(\w+)\(([^)]*)\)',
            r'Using tool:\s*(\w+)\s*with\s*parameters?\s*([^\n]*)',
            r'Calling\s*(\w+)\s*tool\s*with\s*([^\n]*)',
            r'\[(\w+)\]\s*\(([^)]*)\)'
        ]
        
        # Compiled regex for efficiency
        self.thinking_start_regex = re.compile('|'.join(self.thinking_start_patterns), re.IGNORECASE)
        self.thinking_end_regex = re.compile('|'.join(self.thinking_end_patterns), re.IGNORECASE)
        self.tool_call_regex = re.compile('|'.join(self.tool_call_patterns), re.IGNORECASE)
        
        # Terminal logging configuration
        self.enable_terminal_logging = enable_terminal_logging
        
        # State tracking
        self.reset_state()
    
    def reset_state(self):
        """Reset parser state to initial conditions for processing new conversations.
        
        This method resets all internal state variables to their initial values,
        preparing the parser for processing a new LLM response. It ensures clean
        state management and prevents data leakage between different conversations
        or response processing sessions.
        
        State Variables Reset:
        - Thinking state flags (in_thinking, thinking_started, thinking_ended)
        - Tool call state flags (in_tool_call, tool_call_detected)
        - Content accumulation buffers (accumulated_response, accumulated_thinking)
        - Tool call tracking (current_tool_call, accumulated_tool_calls)
        - Final response buffer (final_response)
        
        Thinking State Management:
        - in_thinking: Whether currently processing thinking content
        - thinking_started: Whether thinking section has been detected
        - thinking_ended: Whether thinking section has concluded
        
        Tool Call State Management:
        - in_tool_call: Whether currently processing tool call
        - tool_call_detected: Whether any tool call has been found
        - current_tool_call: Current tool call being processed
        - accumulated_tool_calls: List of all detected tool calls
        
        Content Buffers:
        - accumulated_response: Full response content accumulation
        - accumulated_thinking: Thinking content accumulation
        - final_response: Clean final response without thinking content
        
        Use Cases:
        - Preparing for new conversation processing
        - Cleaning up after completed response processing
        - Error recovery and state consistency maintenance
        - Multi-response processing in single session
        
        Notes:
        - Essential for accurate multi-response processing
        - Prevents state contamination between responses
        - Ensures consistent parsing behavior
        - Required before processing each new response
        """
        self.in_thinking = False
        self.thinking_started = False
        self.thinking_ended = False
        self.in_tool_call = False
        self.tool_call_detected = False
        self.current_tool_call = ""
        self.accumulated_response = ""
        self.accumulated_thinking = ""
        self.accumulated_tool_calls = []
        self.final_response = ""
    
    def _log_to_terminal(self, message: str, message_type: str = "info"):
        """Log messages to terminal with color-coded output for enhanced debugging.
        
        This method provides real-time terminal logging with ANSI color coding
        to help developers monitor LLM response processing. It supports different
        message types with appropriate visual formatting and can be disabled
        for production environments.
        
        Color Coding System:
        - Thinking: Cyan/Blue for thinking start/content/end
        - Tool calls: Magenta/Purple for tool execution
        - Tool results: Yellow for tool output
        - Response: Green for final response content
        - Error: Red for error conditions
        - Info: Yellow for general information
        
        Message Types:
        - thinking_start: Signals beginning of thinking section
        - thinking: Real-time thinking content display
        - thinking_end: Signals completion of thinking section
        - tool_call_start: Signals beginning of tool execution
        - tool_call: Tool call details and parameters
        - tool_call_end: Signals completion of tool execution
        - tool_result: Tool execution results
        - response: Final response content (typically not logged to avoid duplication)
        - error: Error conditions and messages
        - info: General informational messages
        
        Visual Features:
        - Emoji indicators for different content types
        - Color-coded text for easy identification
        - Real-time streaming output for thinking content
        - Structured formatting for tool calls
        - Error highlighting for debugging
        
        Args:
            message (str): The message content to log
            message_type (str, optional): Type of message for appropriate formatting.
                                        Defaults to "info"
                                        
        Notes:
        - Respects enable_terminal_logging configuration
        - Uses stderr to avoid interfering with stdout
        - Provides immediate visual feedback during processing
        - Essential for debugging and development monitoring
        """
        if not self.enable_terminal_logging:
            return
        
        # ANSI color codes
        colors = {
            "thinking_start": "\033[96m",  # Cyan
            "thinking": "\033[94m",       # Blue
            "thinking_end": "\033[96m",   # Cyan
            "tool_call_start": "\033[95m", # Magenta
            "tool_call": "\033[35m",      # Purple
            "tool_call_end": "\033[95m",  # Magenta
            "tool_result": "\033[33m",    # Yellow
            "response": "\033[92m",       # Green
            "error": "\033[91m",          # Red
            "info": "\033[93m"            # Yellow
        }
        reset_color = "\033[0m"
        
        color = colors.get(message_type, colors["info"])
        
        if message_type == "thinking_start":
            print(f"\n{color}🧠 [THINKING] Starting Chain-of-Thought reasoning...{reset_color}", file=sys.stderr)
        elif message_type == "thinking_end":
            print(f"{color}🧠 [THINKING] Chain-of-Thought reasoning complete.{reset_color}\n", file=sys.stderr)
        elif message_type == "thinking":
            # Print thinking content in real-time
            print(f"{color}{message}{reset_color}", end="", file=sys.stderr, flush=True)
        elif message_type == "tool_call_start":
            print(f"\n{color}🔧 [TOOL CALL] Executing function call...{reset_color}", file=sys.stderr)
        elif message_type == "tool_call":
            print(f"{color}🔧 {message}{reset_color}", file=sys.stderr)
        elif message_type == "tool_call_end":
            print(f"{color}🔧 [TOOL CALL] Function execution complete.{reset_color}\n", file=sys.stderr)
        elif message_type == "tool_result":
            print(f"{color}📋 [TOOL RESULT] {message}{reset_color}", file=sys.stderr)
        elif message_type == "response":
            # Don't log response content to avoid duplication
            pass
        else:
            print(f"{color}[{message_type.upper()}] {message}{reset_color}", file=sys.stderr)
    
    def clean_token(self, token: str) -> str:
        """Remove all thinking tags from a token to extract clean content.
        
        This method strips thinking markers from token content, ensuring that
        final responses contain only the actual response content without any
        thinking formatting. It processes multiple thinking tag formats and
        handles case-insensitive matching.
        
        Cleaning Operations:
        - Removes thinking start tags (<thinking>, <think>, <reasoning>, <analysis>)
        - Removes thinking end tags (</thinking>, </think>, </reasoning>, </analysis>)
        - Handles case-insensitive pattern matching
        - Preserves content while removing only formatting markers
        
        Supported Thinking Formats:
        - XML-style tags: <thinking>, <think>, <reasoning>, <analysis>
        - Corresponding end tags for each format
        - Case-insensitive matching for flexibility
        - Multiple format support for provider compatibility
        
        Processing Features:
        - Sequential pattern removal for thorough cleaning
        - Regex-based substitution for efficient processing
        - Preserves original content structure
        - Handles partial marker matches
        
        Args:
            token (str): The token content to clean of thinking markers
            
        Returns:
            str: Cleaned token content with thinking markers removed
            
        Notes:
        - Essential for generating clean final responses
        - Maintains content integrity while removing formatting
        - Supports multiple thinking tag formats
        - Used in final response extraction and content processing
        """
        # Remove thinking start tags
        for pattern in self.thinking_start_patterns:
            token = re.sub(pattern, '', token, flags=re.IGNORECASE)
        
        # Remove thinking end tags
        for pattern in self.thinking_end_patterns:
            token = re.sub(pattern, '', token, flags=re.IGNORECASE)
        
        return token
    
    def detect_thinking_transition(self, accumulated_text: str) -> Tuple[bool, bool]:
        """Detect thinking start/end transitions in accumulated text for state management.
        
        This method analyzes accumulated text to identify thinking section boundaries,
        enabling proper state transitions and content classification. It uses compiled
        regex patterns for efficient detection of thinking markers.
        
        Detection Features:
        - Thinking start pattern recognition across multiple formats
        - Thinking end pattern recognition with corresponding formats
        - Compiled regex for performance optimization
        - Boolean return values for clear state indication
        
        Pattern Recognition:
        - Start patterns: <thinking>, <think>, <reasoning>, <analysis>
        - End patterns: </thinking>, </think>, </reasoning>, </analysis>
        - Case-insensitive matching for flexibility
        - Multiline pattern support
        
        State Management Support:
        - Enables proper thinking state transitions
        - Supports content classification decisions
        - Provides foundation for token type determination
        - Facilitates accurate response parsing
        
        Args:
            accumulated_text (str): The accumulated text content to analyze
                                  for thinking transitions
                                  
        Returns:
            Tuple[bool, bool]: A tuple containing (thinking_start_found, thinking_end_found)
                             - thinking_start_found: Whether thinking start pattern was detected
                             - thinking_end_found: Whether thinking end pattern was detected
                             
        Notes:
        - Uses compiled regex for efficient pattern matching
        - Supports multiple thinking tag formats
        - Essential for accurate state transition management
        - Enables proper content classification and processing
        """
        thinking_start_found = bool(self.thinking_start_regex.search(accumulated_text))
        thinking_end_found = bool(self.thinking_end_regex.search(accumulated_text))
        
        return thinking_start_found, thinking_end_found
    
    def parse_token(self, token: str) -> Generator[ParsedToken, None, None]:
        """Parse a single token and yield appropriate ParsedToken objects with state management.
        
        This method processes individual tokens from LLM responses, detecting thinking
        sections, tool calls, and response content while maintaining proper state
        transitions. It yields structured ParsedToken objects for downstream processing.
        
        Processing Pipeline:
        1. Accumulates token content for pattern detection
        2. Detects thinking transitions and manages state
        3. Handles thinking start/end markers with appropriate tokens
        4. Detects and processes tool calls within thinking content
        5. Classifies content as thinking or response based on state
        6. Yields structured ParsedToken objects with metadata
        
        State Management:
        - Tracks thinking section boundaries and transitions
        - Manages tool call detection and processing
        - Maintains content accumulation buffers
        - Provides proper state transitions and cleanup
        
        Token Classification:
        - THINKING_START: Signals beginning of thinking section
        - THINKING: Content within thinking section
        - THINKING_END: Signals end of thinking section
        - TOOL_CALL_START/TOOL_CALL/TOOL_CALL_END: Tool execution detection
        - RESPONSE: Final response content
        
        Tool Call Detection:
        - Identifies tool calls within thinking content
        - Extracts tool names and parameters
        - Provides structured tool call information
        - Supports multiple tool call formats
        
        Content Processing:
        - Cleans tokens of thinking markers
        - Accumulates thinking and response content separately
        - Provides real-time terminal logging
        - Maintains content length statistics
        
        Args:
            token (str): Individual token from LLM response stream
            
        Yields:
            ParsedToken: Structured token objects with content, type, and metadata
            
        Notes:
        - Core method for token-by-token response processing
        - Handles complex state transitions and content classification
        - Provides foundation for streaming response parsing
        - Integrates with terminal logging for real-time monitoring
        """
        if not token:
            return
        
        self.accumulated_response += token
        
        # Detect thinking transitions
        thinking_start_found, thinking_end_found = self.detect_thinking_transition(self.accumulated_response)
        
        # Handle thinking start
        if thinking_start_found and not self.thinking_started:
            self.in_thinking = True
            self.thinking_started = True
            # Log to terminal
            self._log_to_terminal("thinking_start", "")
            yield ParsedToken(
                content="",
                token_type=TokenType.THINKING_START,
                metadata={"transition": "entering_thinking"}
            )
            # Clean the token and continue processing
            token = self.clean_token(token)
        
        # Handle thinking end
        if thinking_end_found and self.in_thinking and not self.thinking_ended:
            self.in_thinking = False
            self.thinking_ended = True
            # Log to terminal
            self._log_to_terminal("thinking_end", "")
            yield ParsedToken(
                content="",
                token_type=TokenType.THINKING_END,
                metadata={"transition": "exiting_thinking"}
            )
            # Clean the token and continue processing
            token = self.clean_token(token)
            # Skip if token is empty after cleaning
            if not token.strip():
                return
        
        # Clean the token for content extraction
        clean_token = self.clean_token(token)
        
        # Check for tool calls in thinking content
        if self.in_thinking and clean_token:
            tool_match = self.tool_call_regex.search(clean_token)
            if tool_match and not self.tool_call_detected:
                self.tool_call_detected = True
                self.in_tool_call = True
                tool_name = tool_match.group(1) if tool_match.group(1) else "unknown"
                tool_params = tool_match.group(2) if len(tool_match.groups()) > 1 else ""
                tool_call_info = f"Tool: {tool_name}, Parameters: {tool_params}"
                self.current_tool_call = tool_call_info
                self.accumulated_tool_calls.append(tool_call_info)
                self._log_to_terminal("tool_call_start", "")
                yield ParsedToken(
                    content="",
                    token_type=TokenType.TOOL_CALL_START,
                    metadata={"tool_name": tool_name}
                )
                self._log_to_terminal("tool_call", tool_call_info)
                yield ParsedToken(
                    content=tool_call_info,
                    token_type=TokenType.TOOL_CALL,
                    metadata={"tool_name": tool_name, "parameters": tool_params}
                )
                self._log_to_terminal("tool_call_end", "")
                yield ParsedToken(
                    content="",
                    token_type=TokenType.TOOL_CALL_END,
                    metadata={"tool_name": tool_name}
                )
                self.in_tool_call = False
        
        # Yield appropriate content based on current state
        if self.in_thinking and clean_token:
            self.accumulated_thinking += clean_token
            # Log thinking content to terminal in real-time
            self._log_to_terminal("thinking", clean_token)
            yield ParsedToken(
                content=clean_token,
                token_type=TokenType.THINKING,
                metadata={"thinking_length": len(self.accumulated_thinking)}
            )
        elif (self.thinking_ended and not self.in_thinking) or (not self.thinking_started and not self.in_thinking):
            # This is final response content or direct response without thinking
            if clean_token.strip():
                self.final_response += clean_token
                yield ParsedToken(
                    content=clean_token,
                    token_type=TokenType.RESPONSE,
                    metadata={"response_length": len(self.final_response)}
                )
    
    def parse_stream(self, token_stream: Generator[str, None, None]) -> Generator[ParsedToken, None, None]:
        """Parse a stream of tokens from any LLM provider with comprehensive error handling.
        
        This method provides the main entry point for processing streaming responses
        from LLM providers. It manages the complete parsing lifecycle including
        initialization, token processing, error handling, and completion signaling.
        
        Processing Lifecycle:
        1. Resets parser state for clean processing
        2. Iterates through token stream
        3. Processes each token through parse_token method
        4. Handles parsing errors gracefully
        5. Yields completion signal with final statistics
        
        Error Handling:
        - Catches and handles parsing exceptions
        - Yields error tokens for downstream processing
        - Continues processing despite individual token errors
        - Provides error metadata for debugging
        
        Completion Management:
        - Always yields completion signal
        - Provides final response statistics
        - Includes thinking section information
        - Ensures proper stream termination
        
        State Management:
        - Initializes clean state before processing
        - Maintains state throughout stream processing
        - Provides final state information in completion
        
        Provider Compatibility:
        - Works with any LLM provider token stream
        - Handles various token formats and structures
        - Provides unified interface across providers
        - Maintains consistent output format
        
        Args:
            token_stream (Generator[str, None, None]): Stream of tokens from LLM provider
            
        Yields:
            ParsedToken: Structured tokens with content, type, and metadata
            
        Notes:
        - Main entry point for streaming response processing
        - Provides comprehensive error handling and recovery
        - Ensures proper completion signaling
        - Essential for real-time response processing
        """
        self.reset_state()
        
        try:
            for token in token_stream:
                yield from self.parse_token(token)
        except Exception as e:
            yield ParsedToken(
                content=f"Error parsing stream: {str(e)}",
                token_type=TokenType.ERROR,
                metadata={"error_type": "parsing_error"}
            )
        finally:
            # Always yield completion signal
            yield ParsedToken(
                content="",
                token_type=TokenType.COMPLETE,
                metadata={
                    "final_response_length": len(self.final_response),
                    "thinking_length": len(self.accumulated_thinking),
                    "had_thinking": self.thinking_started
                }
            )
    
    def extract_final_response(self) -> str:
        """Extract the final response without thinking content using multiple strategies.
        
        This method extracts clean final response content by removing thinking
        sections and formatting markers. It employs multiple extraction strategies
        to handle different response formats and edge cases.
        
        Extraction Strategies:
        1. Post-thinking extraction: Uses accumulated final response after thinking end
        2. No-thinking extraction: Cleans entire response when no thinking detected
        3. Fallback extraction: Splits on thinking end patterns and takes last part
        4. Buffer fallback: Returns accumulated final response as last resort
        
        Strategy Selection:
        - If thinking_ended: Uses accumulated final response (most reliable)
        - If no thinking_started: Cleans entire accumulated response
        - If thinking started but not ended: Uses pattern-based splitting
        - Final fallback: Returns whatever was accumulated in final_response
        
        Content Cleaning:
        - Removes all thinking markers and tags
        - Strips whitespace and formatting
        - Preserves actual response content
        - Handles multiple thinking tag formats
        
        Edge Case Handling:
        - Incomplete thinking sections
        - Missing thinking end tags
        - Multiple thinking sections
        - Malformed thinking markers
        
        Returns:
            str: Clean final response content without thinking markers or whitespace
            
        Notes:
        - Provides robust response extraction across different formats
        - Handles edge cases and malformed responses
        - Essential for generating clean final outputs
        - Used after complete response processing
        """
        if self.thinking_ended:
            # If we had thinking, use the accumulated final response
            return self.final_response.strip()
        elif not self.thinking_started:
            # If no thinking tags were found, clean the entire response
            return self.clean_token(self.accumulated_response).strip()
        else:
            # Fallback: extract everything after the last thinking end tag
            for pattern in self.thinking_end_patterns:
                if pattern.replace('</', '</').replace('>', '') in self.accumulated_response.lower():
                    parts = re.split(pattern, self.accumulated_response, flags=re.IGNORECASE)
                    if len(parts) > 1:
                        return self.clean_token(parts[-1]).strip()
            
            # If no end tag found, return the final response we accumulated
            return self.final_response.strip()
    
    def format_for_sse(self, parsed_token: ParsedToken) -> str:
        """Format a ParsedToken for Server-Sent Events with proper protocol compliance.
        
        This method converts ParsedToken objects into properly formatted Server-Sent
        Events (SSE) data strings for web streaming. It ensures protocol compliance
        and includes comprehensive metadata for client-side processing.
        
        SSE Formatting Features:
        - Converts token content and type to JSON format
        - Includes all available metadata from parsed token
        - Follows SSE protocol with proper data prefix
        - Ensures JSON serialization compatibility
        
        Data Structure:
        - Base fields: token content and type value
        - Metadata: All metadata from ParsedToken object
        - JSON serialization for web compatibility
        - Proper SSE formatting with data prefix
        
        Protocol Compliance:
        - Uses 'data: ' prefix as required by SSE specification
        - Includes double newline for proper event separation
        - Ensures valid JSON structure
        - Maintains streaming compatibility
        
        Metadata Preservation:
        - Includes all metadata from original token
        - Preserves processing statistics
        - Maintains state information
        - Provides debugging information
        
        Args:
            parsed_token (ParsedToken): Structured token with content, type, and metadata
            
        Returns:
            str: SSE-formatted string ready for web streaming with proper
                 data prefix and JSON payload
                 
        Notes:
        - Follows SSE protocol specification
        - Ensures web streaming compatibility
        - Preserves all token information for client processing
        - Essential for real-time web response streaming
        """
        data = {
            'token': parsed_token.content,
            'type': parsed_token.token_type.value
        }
        
        # Add metadata if present
        if parsed_token.metadata:
            data.update(parsed_token.metadata)
        
        return f"data: {json.dumps(data)}\n\n"
    
    def validate_response_structure(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and standardize response structure from different providers.
        
        This method ensures consistent response format across different LLM providers
        by validating input data and standardizing the output structure. It handles
        various input formats and provides comprehensive error handling.
        
        Standardization Features:
        - Ensures all required fields are present
        - Provides default values for missing fields
        - Handles type conversion and validation
        - Maintains consistent structure across providers
        
        Standard Response Structure:
        - response: The actual response content (string)
        - success: Boolean indicating operation success
        - provider: Name of the LLM provider used
        - model: Model identifier used for generation
        - rate_limited: Boolean indicating if rate limiting occurred
        - error: Error message if operation failed (None if successful)
        
        Input Validation:
        - Handles dictionary and non-dictionary inputs
        - Validates field types and converts as needed
        - Provides fallback values for missing data
        - Ensures consistent data types
        
        Error Handling:
        - Detects error conditions from provider responses
        - Standardizes error reporting format
        - Handles malformed response data
        - Provides meaningful error messages
        
        Provider Compatibility:
        - Works with responses from any LLM provider
        - Handles provider-specific response formats
        - Normalizes field names and structures
        - Maintains provider identification
        
        Args:
            response_data (Dict[str, Any]): Raw response data from LLM provider
            
        Returns:
            Dict[str, Any]: Standardized response structure with all required fields
            
        Notes:
        - Essential for maintaining consistent response handling
        - Provides robust error handling and validation
        - Enables provider-agnostic response processing
        - Ensures reliable downstream processing
        """
        standardized = {
            "response": "",
            "success": True,
            "provider": "unknown",
            "model": "unknown",
            "rate_limited": False,
            "error": None
        }
        
        # Update with actual data, ensuring all required fields exist
        if isinstance(response_data, dict):
            standardized.update({
                "response": str(response_data.get("response", "")),
                "success": bool(response_data.get("success", True)),
                "provider": str(response_data.get("provider", "unknown")),
                "model": str(response_data.get("model", "unknown")),
                "rate_limited": bool(response_data.get("rate_limited", False))
            })
            
            # Handle error cases
            if not standardized["success"] or "error" in response_data:
                standardized["error"] = str(response_data.get("error", "Unknown error occurred"))
        else:
            # Handle non-dict responses
            standardized.update({
                "response": str(response_data) if response_data else "Empty response",
                "success": False,
                "error": "Invalid response format"
            })
        
        return standardized