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
        """Reset parser state for new conversation"""
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
        """Log messages to terminal with color coding"""
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
        """Remove all thinking tags from a token"""
        # Remove thinking start tags
        for pattern in self.thinking_start_patterns:
            token = re.sub(pattern, '', token, flags=re.IGNORECASE)
        
        # Remove thinking end tags
        for pattern in self.thinking_end_patterns:
            token = re.sub(pattern, '', token, flags=re.IGNORECASE)
        
        return token
    
    def detect_thinking_transition(self, accumulated_text: str) -> Tuple[bool, bool]:
        """Detect thinking start/end transitions in accumulated text"""
        thinking_start_found = bool(self.thinking_start_regex.search(accumulated_text))
        thinking_end_found = bool(self.thinking_end_regex.search(accumulated_text))
        
        return thinking_start_found, thinking_end_found
    
    def parse_token(self, token: str) -> Generator[ParsedToken, None, None]:
        """Parse a single token and yield appropriate ParsedToken objects"""
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
        """Parse a stream of tokens from any LLM provider"""
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
        """Extract the final response without thinking content"""
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
        """Format a ParsedToken for Server-Sent Events"""
        data = {
            'token': parsed_token.content,
            'type': parsed_token.token_type.value
        }
        
        # Add metadata if present
        if parsed_token.metadata:
            data.update(parsed_token.metadata)
        
        return f"data: {json.dumps(data)}\n\n"
    
    def validate_response_structure(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and standardize response structure from different providers"""
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