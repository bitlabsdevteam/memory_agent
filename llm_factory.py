"""LLM Factory for supporting multiple LLM providers"""

import os
import json
import time
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Generator, Optional
import google.generativeai as genai
from langchain_core.rate_limiters import InMemoryRateLimiter
import requests
from config import get_config
try:
    from openai import OpenAI, RateLimitError
except ImportError:
    OpenAI = None
    RateLimitError = None

try:
    from langchain_community.chat_models.perplexity import ChatPerplexity
except ImportError:
    ChatPerplexity = None

# Get configuration
config_class = get_config()
config = config_class()

def exponential_backoff_retry(func, max_retries=6, base_delay=1, max_delay=60):
    """
    Implements exponential backoff retry mechanism for handling rate limit errors from LLM APIs.
    
    This function provides a robust retry strategy that increases the delay between retries
    exponentially, helping to handle temporary API rate limits gracefully. It includes
    jitter to prevent thundering herd problems when multiple requests are retried simultaneously.
    
    Args:
        func (callable): The function to retry (typically an API call)
        max_retries (int): Maximum number of retry attempts (default: 6)
        base_delay (float): Initial delay in seconds before first retry (default: 1)
        max_delay (float): Maximum delay cap in seconds to prevent excessive waits (default: 60)
    
    Returns:
        Any: The return value of the successful function call
    
    Raises:
        Exception: Re-raises the original exception if max retries exceeded or non-rate-limit error
    
    Note:
        - Only retries on RateLimitError exceptions
        - Uses exponential backoff: delay = base_delay * (2 ^ attempt) + random jitter
        - Adds random jitter (0-1 seconds) to prevent synchronized retries
        - Non-rate-limit errors are raised immediately without retry
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            # Check if it's a rate limit error
            if RateLimitError and isinstance(e, RateLimitError):
                if attempt == max_retries - 1:
                    raise e
                
                # Calculate delay with exponential backoff and jitter
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                print(f"Rate limit hit, retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                # For non-rate-limit errors, raise immediately
                raise e
    
    raise Exception(f"Max retries ({max_retries}) exceeded")

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, model_name: str, temperature: float = 0.7, tools: Optional[Dict] = None):
        """
        Initialize the base LLM provider with common configuration parameters.
        
        This constructor sets up the fundamental attributes required by all LLM providers
        and calls the provider-specific initialization method. It establishes the
        foundation for API communication and tool integration.
        
        Args:
            api_key (str): API authentication key for the LLM service
            model_name (str): Specific model identifier (e.g., 'gpt-4', 'gemini-pro')
            temperature (float): Controls randomness in responses (0.0-1.0, default: 0.7)
                                Lower values = more deterministic, higher = more creative
            tools (Optional[Dict]): Dictionary of available tools/functions for the model
                                   Keys are tool names, values are callable functions
        
        Note:
            - Calls _initialize() which must be implemented by subclasses
            - Tools dictionary enables function calling capabilities
            - Temperature affects response creativity and consistency
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.tools = tools or {}
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """
        Initialize the provider-specific client and configuration.
        
        This abstract method must be implemented by each LLM provider subclass
        to set up their specific API client, authentication, and any provider-specific
        configuration. It's called automatically during __init__.
        
        Implementation should:
        - Configure the API client with the provided api_key
        - Set up any provider-specific settings (rate limiters, timeouts, etc.)
        - Initialize connection parameters
        - Set the provider name for identification
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
        pass
    
    @abstractmethod
    def generate_response(self, prompt: str, max_tokens: int = 2048) -> Dict[str, Any]:
        """
        Generate a complete response from the LLM in a single API call.
        
        This method sends a prompt to the LLM and waits for the complete response
        before returning. It's suitable for scenarios where you need the full
        response at once rather than streaming chunks.
        
        Args:
            prompt (str): The input text/question to send to the LLM
            max_tokens (int): Maximum number of tokens in the response (default: 2048)
        
        Returns:
            Dict[str, Any]: Standardized response dictionary containing:
                - response (str): The generated text response
                - success (bool): Whether the request was successful
                - provider (str): Name of the LLM provider
                - model (str): Model name used
                - error (str, optional): Error message if success=False
        
        Raises:
            NotImplementedError: If not implemented by subclass
        
        Note:
            - Should handle tool calls if tools are available
            - Must return standardized response format for consistency
            - Should include proper error handling and logging
        """
        pass
        pass
    
    @abstractmethod
    def stream_response(self, prompt: str, max_tokens: int = 2048) -> Generator[str, None, None]:
        """
        Stream response from the LLM as it's being generated.
        
        This method sends a prompt to the LLM and yields response chunks as they
        become available, enabling real-time display of the response. This provides
        better user experience for long responses.
        
        Args:
            prompt (str): The input text/question to send to the LLM
            max_tokens (int): Maximum number of tokens in the response (default: 2048)
        
        Yields:
            str: Individual chunks of the response as they're generated
        
        Raises:
            NotImplementedError: If not implemented by subclass
        
        Note:
            - Should yield empty strings or handle None chunks gracefully
            - Must handle streaming API errors and yield error messages
            - Should process tool calls after streaming completes if applicable
            - Each chunk should be a string that can be concatenated
        """
        pass
        pass
    
    def _execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool function"""
        if tool_name in self.tools:
            try:
                return self.tools[tool_name](**kwargs)
            except Exception as e:
                return f"Error executing {tool_name}: {str(e)}"
        return f"Tool {tool_name} not found"
    
    def _format_tools_for_prompt(self) -> str:
        """Format available tools for the prompt"""
        if not self.tools:
            return ""
        
        tools_description = "\n\nAvailable Tools:\n"
        for tool_name, tool_func in self.tools.items():
            # Get function signature and docstring
            import inspect
            sig = inspect.signature(tool_func)
            doc = tool_func.__doc__ or "No description available"
            tools_description += f"- {tool_name}{sig}: {doc}\n"
        
        tools_description += "\nTo use a tool, include in your response: TOOL_CALL: {tool_name}({parameters})\n"
        return tools_description

class GoogleGeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider"""
    
    def _initialize(self):
        """
        Initialize the Google Gemini API client and configuration.
        
        Sets up the Google Generative AI client with the provided API key
        and creates a GenerativeModel instance for the specified model.
        This method configures the global genai settings and establishes
        the connection to Google's Gemini API.
        
        Side Effects:
            - Configures global genai API key
            - Creates self.model as GenerativeModel instance
            - Sets provider for identification
        
        Note:
            - Uses the global genai.configure() which affects all genai operations
            - The model is ready for both streaming and non-streaming requests
        """
        self.provider = "google_gemini"
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_response(self, prompt: str, max_tokens: int = 2048) -> Dict[str, Any]:
        """
        Generate a complete response from Google Gemini with tool calling support.
        
        Sends the prompt to Gemini and waits for the complete response.
        Enhances the prompt with available tool information and processes
        any tool calls in the response. Uses the configured temperature
        and max_tokens settings to control response generation.
        
        Args:
            prompt (str): The input text/question to send to Gemini
            max_tokens (int): Maximum number of tokens in the response (default: 2048)
        
        Returns:
            Dict[str, Any]: Standardized response dictionary containing:
                - response (str): The generated text with tool results
                - success (bool): True if successful, False if error occurred
                - provider (str): "google_gemini"
                - model (str): The model name used
        
        Note:
            - Automatically appends tool information to the prompt
            - Processes TOOL_CALL: patterns in the response
            - Handles errors gracefully with standardized error format
        """
        try:
            # Add tools information to prompt
            enhanced_prompt = prompt + self._format_tools_for_prompt()
            
            response = self.model.generate_content(
                enhanced_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=max_tokens,
                )
            )
            
            response_text = response.text if response.text else "I apologize, but I couldn't process your request."
            
            # Process tool calls in the response
            processed_response = self._process_tool_calls(response_text)
            
            return {
                "response": processed_response,
                "success": True,
                "provider": "google_gemini",
                "model": self.model_name
            }
            
        except Exception as e:
            return {
                "response": f"Error generating response: {str(e)}",
                "success": False,
                "provider": "google_gemini",
                "model": self.model_name
            }
    
    def stream_response(self, prompt: str, max_tokens: int = 2048) -> Generator[str, None, None]:
        """
        Stream response from Google Gemini with real-time tool calling support.
        
        Sends the prompt to Gemini and yields response chunks as they become
        available, enabling real-time display. Enhances the prompt with tool
        information and processes tool calls after streaming completes.
        
        Args:
            prompt (str): The input text/question to send to Gemini
            max_tokens (int): Maximum number of tokens in the response (default: 2048)
        
        Yields:
            str: Individual chunks of the response as they're generated,
                 followed by tool execution results if applicable
        
        Note:
            - Automatically appends tool information to the prompt
            - Accumulates text to detect tool calls after streaming
            - Tool results are yielded as additional chunks after main response
            - Handles streaming errors gracefully
        """
        try:
            # Add tools information to prompt
            enhanced_prompt = prompt + self._format_tools_for_prompt()
            
            response = self.model.generate_content(
                enhanced_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=max_tokens,
                ),
                stream=True
            )
            
            accumulated_text = ""
            for chunk in response:
                if chunk.text:
                    accumulated_text += chunk.text
                    yield chunk.text
            
            # Process any tool calls after streaming is complete
            if "TOOL_CALL:" in accumulated_text:
                tool_results = self._extract_and_execute_tools(accumulated_text)
                if tool_results:
                    yield "\n\n" + tool_results
                    
        except Exception as e:
            yield f"Error streaming response: {str(e)}"

    def _process_tool_calls(self, response_text: str) -> str:
        """
        Process and execute tool calls found in the response text.
        
        Searches for TOOL_CALL: patterns in the text and executes the corresponding
        tools if they exist in the tools dictionary. Replaces tool call patterns
        with their execution results or error messages.
        
        Args:
            response_text (str): The response text that may contain tool call patterns
        
        Returns:
            str: The text with tool calls replaced by their results
        
        Tool Call Format:
            TOOL_CALL: tool_name(arg1=value1, arg2=value2)
        
        Processing:
            - Uses regex to find TOOL_CALL: patterns
            - Extracts and executes tools via _extract_and_execute_tools
            - Replaces all tool call patterns with execution results
            - Returns original text if no tool calls found
        
        Note:
            - Returns original text unchanged if no TOOL_CALL: patterns found
            - Uses regex substitution to replace all matching patterns
            - Relies on _extract_and_execute_tools for actual execution
        """
        if "TOOL_CALL:" not in response_text:
            return response_text
        
        # Extract and execute tool calls
        tool_results = self._extract_and_execute_tools(response_text)
        
        # Replace tool calls with results
        import re
        pattern = r'TOOL_CALL:\s*(\w+)\(([^)]*)\)'
        
        def replace_tool_call(match):
            return tool_results if tool_results else "Tool execution failed"
        
        processed_text = re.sub(pattern, replace_tool_call, response_text)
        return processed_text
    
    def _extract_and_execute_tools(self, text: str) -> str:
        """
        Extract and execute tool calls from text, returning formatted results.
        
        Searches for TOOL_CALL: patterns in the text and executes the corresponding
        tools, returning a formatted string with all tool execution results.
        This method handles parameter parsing and tool execution with error handling.
        
        Args:
            text (str): The text that may contain tool call patterns
        
        Returns:
            str: Formatted string containing all tool execution results,
                 with each result formatted as "**{tool_name} Result:**\n{result}"
                 or "**{tool_name} Error:**\n{error}" for failures
        
        Tool Call Format:
            TOOL_CALL: tool_name(parameters)
        
        Parameter Parsing:
            - First attempts to parse as Python literals using ast.literal_eval
            - Handles single parameter tuples by extracting the value
            - Falls back to treating parameters as string for "city" argument
            - Uses empty kwargs if no parameters provided
        
        Processing:
            - Uses regex to find all TOOL_CALL: patterns
            - Executes each tool via _execute_tool method
            - Formats results with markdown-style headers
            - Handles errors gracefully with error messages
        
        Note:
            - Assumes tools expect "city" parameter for string arguments
            - Returns empty string if no tool calls found
            - Each result is separated by double newlines
        """
        import re
        import ast
        
        pattern = r'TOOL_CALL:\s*(\w+)\(([^)]*)\)'
        matches = re.findall(pattern, text)
        
        results = []
        for tool_name, params_str in matches:
            try:
                # Parse parameters
                if params_str.strip():
                    # Try to evaluate as Python literals
                    try:
                        params = ast.literal_eval(f"({params_str})")
                        if isinstance(params, tuple) and len(params) == 1:
                            params = params[0]
                        kwargs = {"city": params} if isinstance(params, str) else {}
                    except:
                        # Fallback: treat as string parameter
                        kwargs = {"city": params_str.strip('"\'')} 
                else:
                    kwargs = {}
                
                # Execute tool
                result = self._execute_tool(tool_name, **kwargs)
                results.append(f"\n\n**{tool_name} Result:**\n{result}")
                
            except Exception as e:
                results.append(f"\n\n**{tool_name} Error:**\n{str(e)}")
        
        return "\n".join(results)

class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM Provider using LangChain with Rate Limiting"""
    
    def _initialize(self):
        """Initialize OpenAI client with FREE tier rate limiting
        
        Sets up the OpenAI client with FREE tier rate limiting configuration
        to handle the restrictive 3 requests per minute limit. Configures
        exponential backoff retry handling and disables built-in retries
        to provide better control over rate limit management.
        
        Configuration:
            - Rate limiter: 3 RPM (0.05 requests/second) with burst capacity
            - Timeout: 60 seconds for FREE tier latency
            - Retries: Disabled (handled by exponential_backoff_retry)
            - Provider: Set to "openai" for identification
        
        Side Effects:
            - Creates self.client as OpenAI instance
            - Sets up self.rate_limiter with FREE tier limits
            - Sets self.provider for tracking
        
        Raises:
            ImportError: If OpenAI package not installed
            Exception: If client initialization fails
        
        Note:
            - FREE tier has very restrictive limits (3 RPM)
            - Uses manual retry logic instead of built-in retries
            - Burst capacity allows 3 quick requests before rate limiting
        """
        try:
            # Set provider name for tracking
            self.provider = "openai"
            
            # Initialize rate limiter for FREE tier: 3 RPM = 0.05 requests per second
            # Using a more lenient approach to avoid blocking legitimate requests
            self.rate_limiter = InMemoryRateLimiter(
                requests_per_second=0.05,  # 3 requests per minute = 0.05 per second
                check_every_n_seconds=1,
                max_bucket_size=3  # Allow burst of 3 requests
            )
            
            if OpenAI is None:
                raise ImportError("OpenAI package not installed. Please install with: pip install openai")
            
            # Initialize OpenAI client without built-in retries (we handle this manually)
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=60.0,  # Increased timeout for FREE tier
                max_retries=0   # Disable built-in retries, we handle this with exponential backoff
            )
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            raise e
    
    def generate_response(self, prompt: str, max_tokens: int = 2048) -> Dict[str, Any]:
        """Generate response using OpenAI with exponential backoff retry
        
        Sends a prompt to OpenAI and waits for the complete response using
        FREE tier rate limiting and exponential backoff retry logic. Handles
        the restrictive 3 RPM limit gracefully with user-friendly error messages.
        
        Args:
            prompt (str): The input text/question to send to OpenAI
            max_tokens (int): Maximum number of tokens in the response (default: 2048)
        
        Returns:
            Dict[str, Any]: Standardized response dictionary containing:
                - response (str): The generated text or error message
                - success (bool): True if successful, False if error occurred
                - provider (str): "openai"
                - model (str): The model name used
                - rate_limited (bool, optional): True if rate limited
        
        Process Flow:
            1. Apply rate limiting with blocking acquisition
            2. Define API call function for retry wrapper
            3. Execute with exponential backoff retry
            4. Extract and return response content
            5. Handle errors with user-friendly messages
        
        Error Handling:
            - Rate limit errors: User-friendly FREE tier message
            - API errors: Wrapped with context information
            - Network errors: Handled by exponential backoff
        
        Note:
            - Uses blocking rate limiter for better UX
            - FREE tier specific error messages
            - Exponential backoff handles temporary failures
        """
        try:
            # Apply basic rate limiting first
            if not self.rate_limiter.acquire(blocking=True):  # Allow blocking for better UX
                return {
                    "response": "Rate limit exceeded. Please wait before making another request.",
                    "success": False,
                    "provider": "openai",
                    "model": self.model_name,
                    "rate_limited": True
                }
            
            # Define the API call function for retry logic
            def make_api_call():
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=max_tokens
                )
            
            # Use exponential backoff retry for the API call
            response = exponential_backoff_retry(make_api_call)
            
            response_text = response.choices[0].message.content if response.choices else "I apologize, but I couldn't process your request."
            
            return {
                "response": response_text,
                "success": True,
                "provider": "openai",
                "model": self.model_name
            }
            
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower():
                error_msg = "OpenAI API rate limit exceeded. This is normal for FREE tier users. Please wait a moment and try again."
            
            return {
                "response": f"Error generating response: {error_msg}",
                "success": False,
                "provider": "openai",
                "model": self.model_name
            }
    
    def stream_response(self, prompt: str, max_tokens: int = 2048) -> Generator[str, None, None]:
        """Stream response using OpenAI with exponential backoff retry
        
        Sends a prompt to OpenAI and yields response chunks as they become
        available, enabling real-time display. Uses FREE tier rate limiting
        and exponential backoff retry for robust streaming communication.
        
        Args:
            prompt (str): The input text/question to send to OpenAI
            max_tokens (int): Maximum number of tokens in the response (default: 2048)
        
        Yields:
            str: Individual chunks of the response as they're generated,
                 or error message if rate limited or API error occurs
        
        Process Flow:
            1. Apply rate limiting with blocking acquisition
            2. Define streaming API call function for retry wrapper
            3. Execute with exponential backoff retry
            4. Iterate through stream chunks
            5. Yield non-empty content from delta
            6. Handle errors with user-friendly messages
        
        Streaming Features:
            - Real-time response display for better UX
            - Rate limiting respects FREE tier limits
            - Exponential backoff handles temporary failures
            - Graceful error handling with yielded messages
        
        Error Handling:
            - Rate limit errors: User-friendly FREE tier message
            - Stream interruptions: Handled by exponential backoff
            - API errors: Yielded as error messages instead of exceptions
        
        Note:
            - Uses blocking rate limiter for better UX
            - Filters out chunks with empty content
            - FREE tier specific error messages
            - Stream errors don't break the generator
        """
        try:
            # Apply basic rate limiting first
            if not self.rate_limiter.acquire(blocking=True):  # Allow blocking for better UX
                yield "Rate limit exceeded. Please wait before making another request."
                return
            
            # Define the streaming API call function for retry logic
            def make_streaming_call():
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
            
            # Use exponential backoff retry for the streaming API call
            stream = exponential_backoff_retry(make_streaming_call)
            
            for chunk in stream:
                 if chunk.choices and chunk.choices[0].delta.content:
                     content = chunk.choices[0].delta.content
                     yield content
                     
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower():
                error_msg = "OpenAI API rate limit exceeded. This is normal for FREE tier users. Please wait a moment and try again."
            yield f"Error streaming response: {error_msg}"

class GroqProvider(BaseLLMProvider):
    """Groq LLM Provider (DeepSeek)"""
    
    def _initialize(self):
        """
        Initialize the Groq provider configuration.
        
        Sets up the basic configuration for Groq API communication.
        Groq uses a direct HTTP API approach rather than a dedicated client library,
        so this method configures the base URL and headers for API requests.
        
        Side Effects:
            - Sets provider to "groq" for tracking and identification
            - Configures base_url for Groq's OpenAI-compatible API
            - Sets up headers with authorization and content type
        
        Note:
            - Groq doesn't require a client library initialization
            - Uses OpenAI-compatible API endpoints
            - Headers are reused for all API requests
        """
        self.provider = "groq"
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_response(self, prompt: str, max_tokens: int = 2048) -> Dict[str, Any]:
        """
        Generate a complete response from Groq API.
        
        Sends the prompt to Groq's OpenAI-compatible API and waits for the
        complete response. Uses HTTP POST request to the chat completions
        endpoint with the configured model and parameters.
        
        Args:
            prompt (str): The input text/question to send to Groq
            max_tokens (int): Maximum number of tokens in the response (default: 2048)
        
        Returns:
            Dict[str, Any]: Standardized response dictionary containing:
                - response (str): The generated text or error message
                - success (bool): True if successful, False if error occurred
                - provider (str): "groq"
                - model (str): The model name used
        
        API Communication:
            - Uses Groq's OpenAI-compatible chat completions endpoint
            - Sends POST request with JSON payload
            - Includes model, messages, temperature, and max_tokens
            - Raises HTTP errors for failed requests
        
        Error Handling:
            - HTTP errors: Handled by raise_for_status()
            - Missing response: Provides fallback message
            - All exceptions: Wrapped in standardized error format
        
        Note:
            - Uses OpenAI-compatible message format
            - Returns standardized response format for consistency
            - Handles both successful and error responses gracefully
        """
        try:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()
            data = response.json()
            
            response_text = data["choices"][0]["message"]["content"] if data.get("choices") else "I apologize, but I couldn't process your request."
            
            return {
                "response": response_text,
                "success": True,
                "provider": "groq",
                "model": self.model_name
            }
            
        except Exception as e:
            return {
                "response": f"Error generating response: {str(e)}",
                "success": False,
                "provider": "groq",
                "model": self.model_name
            }
    
    def stream_response(self, prompt: str, max_tokens: int = 2048) -> Generator[str, None, None]:
        """
        Stream response from Groq API as it's being generated.
        
        Sends the prompt to Groq's OpenAI-compatible API and yields response
        chunks as they become available. Uses HTTP streaming with Server-Sent
        Events (SSE) format to provide real-time response display.
        
        Args:
            prompt (str): The input text/question to send to Groq
            max_tokens (int): Maximum number of tokens in the response (default: 2048)
        
        Yields:
            str: Individual chunks of the response as they're generated,
                 or error message if an exception occurs
        
        API Communication:
            - Uses Groq's OpenAI-compatible chat completions endpoint
            - Sends POST request with streaming enabled
            - Processes Server-Sent Events (SSE) format response
            - Extracts content from delta objects in stream chunks
        
        Processing:
            - Iterates through response lines
            - Parses 'data: ' prefixed JSON chunks
            - Extracts content from choices[0].delta.content
            - Skips empty content and [DONE] markers
            - Handles JSON parsing errors gracefully
        
        Error Handling:
            - Network errors: Yields error message
            - JSON parsing errors: Silently continues
            - API errors: Yields error message
        
        Note:
            - Uses OpenAI-compatible API format
            - Handles SSE streaming protocol
            - Graceful error handling without breaking stream
        """
        try:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                stream=True
            )
            
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: ") and not line.startswith("data: [DONE]"):
                        data = json.loads(line[6:])
                        if data.get("choices") and data["choices"][0].get("delta") and data["choices"][0]["delta"].get("content"):
                            yield data["choices"][0]["delta"]["content"]
                            
        except Exception as e:
            yield f"Error streaming response: {str(e)}"

class PerplexityProvider(BaseLLMProvider):
    """Perplexity LLM Provider using ChatPerplexity from langchain-perplexity"""
    
    def _initialize(self):
        """
        Initialize Perplexity client using ChatPerplexity with rate limiting.
        
        Sets up the ChatPerplexity client from langchain-perplexity package
        and configures rate limiting to handle Perplexity's API limits.
        The client is initialized with environment variable configuration
        for better security and compatibility.
        
        Configuration:
            - Rate limiter: 20 RPM (0.3 requests/second) with burst capacity
            - Environment: Sets PPLX_API_KEY for ChatPerplexity
            - Client: ChatPerplexity with model and temperature settings
            - Provider: Set to "perplexity" for identification
        
        Side Effects:
            - Sets PPLX_API_KEY environment variable
            - Creates self.client as ChatPerplexity instance
            - Sets up self.rate_limiter with conservative limits
            - Sets self.provider for tracking
        
        Raises:
            ImportError: If langchain-perplexity package not installed
            Exception: If client initialization fails
        
        Note:
            - Uses environment variable for API key (ChatPerplexity requirement)
            - Conservative rate limiting to avoid API limits
            - Burst capacity allows small bursts of requests
        """
        self.provider = "perplexity"
        
        if ChatPerplexity is None:
            raise ImportError("langchain-perplexity package not installed. Please install with: pip install langchain-perplexity")
        
        # Initialize ChatPerplexity client
        # Set the PPLX_API_KEY environment variable for ChatPerplexity
        import os
        os.environ["PPLX_API_KEY"] = self.api_key
        
        # Initialize without explicit pplx_api_key parameter - it will be picked up from environment
        self.client = ChatPerplexity(
            model=self.model_name,
            temperature=self.temperature
        )
        
        # Initialize rate limiter for Perplexity: 20 RPM = 0.33 requests per second
        # Being conservative to avoid rate limits
        self.rate_limiter = InMemoryRateLimiter(
            requests_per_second=0.3,  # Slightly under 20 RPM to be safe
            check_every_n_seconds=1,
            max_bucket_size=5  # Allow small bursts
        )
    
    def generate_response(self, prompt: str, max_tokens: int = 2048) -> Dict[str, Any]:
        """
        Generate a complete response from Perplexity using ChatPerplexity with rate limiting.
        
        Sends the prompt to Perplexity and waits for the complete response using
        the ChatPerplexity client. Applies rate limiting and exponential backoff
        retry logic to handle API limits gracefully.
        
        Args:
            prompt (str): The input text/question to send to Perplexity
            max_tokens (int): Maximum number of tokens (unused by ChatPerplexity)
        
        Returns:
            Dict[str, Any]: Standardized response dictionary containing:
                - response (str): The generated text or error message
                - success (bool): True if successful, False if error occurred
                - provider (str): "perplexity"
                - model (str): The model name used
                - rate_limited (bool, optional): True if rate limited
        
        Process Flow:
            1. Apply rate limiting with blocking acquisition
            2. Create HumanMessage for ChatPerplexity format
            3. Execute with exponential backoff retry
            4. Extract content from response object
            5. Handle errors with user-friendly messages
        
        Error Handling:
            - Rate limit errors: User-friendly Perplexity-specific message
            - API errors: Wrapped with context information
            - Network errors: Handled by exponential backoff
        
        Note:
            - Uses blocking rate limiter for better UX
            - ChatPerplexity uses LangChain message format
            - Exponential backoff handles temporary failures
            - max_tokens parameter not used by ChatPerplexity
        """
        try:
            # Apply rate limiting first
            if not self.rate_limiter.acquire(blocking=True):
                return {
                    "response": "Rate limit exceeded. Please wait before making another request.",
                    "success": False,
                    "provider": "perplexity",
                    "model": self.model_name,
                    "rate_limited": True
                }
            
            # Define the API call function for retry logic
            def make_api_call():
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=prompt)]
                return self.client.invoke(messages)
            
            # Use exponential backoff retry for the API call
            response = exponential_backoff_retry(make_api_call)
            
            # Extract response text from ChatPerplexity response
            response_text = response.content if hasattr(response, 'content') and response.content else "I apologize, but I couldn't process your request."
            
            return {
                "response": response_text,
                "success": True,
                "provider": "perplexity",
                "model": self.model_name
            }
            
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                error_msg = "Perplexity API rate limit exceeded. Please wait a moment and try again."
            
            return {
                "response": f"Error generating response: {error_msg}",
                "success": False,
                "provider": "perplexity",
                "model": self.model_name
            }
    
    def stream_response(self, prompt: str, max_tokens: int = 2048) -> Generator[str, None, None]:
        """
        Stream response from Perplexity using ChatPerplexity with rate limiting.
        
        Sends the prompt to Perplexity and yields response chunks as they become
        available using the ChatPerplexity streaming interface. Applies rate limiting
        and exponential backoff retry for robust streaming communication.
        
        Args:
            prompt (str): The input text/question to send to Perplexity
            max_tokens (int): Maximum number of tokens (unused by ChatPerplexity)
        
        Yields:
            str: Individual chunks of the response as they're generated,
                 or error message if rate limited or API error occurs
        
        Process Flow:
            1. Apply rate limiting with blocking acquisition
            2. Create HumanMessage for ChatPerplexity format
            3. Execute streaming call with exponential backoff retry
            4. Iterate through stream chunks
            5. Yield non-empty content from chunks
            6. Handle errors with user-friendly messages
        
        Streaming Features:
            - Real-time response display for better UX
            - Rate limiting respects Perplexity API limits
            - Exponential backoff handles temporary failures
            - Graceful error handling with yielded messages
        
        Error Handling:
            - Rate limit errors: User-friendly Perplexity-specific message
            - Stream interruptions: Handled by exponential backoff
            - API errors: Yielded as error messages instead of exceptions
        
        Note:
            - Uses blocking rate limiter for better UX
            - ChatPerplexity uses LangChain streaming format
            - Filters out chunks with empty content
            - max_tokens parameter not used by ChatPerplexity
        """
        try:
            # Apply rate limiting first
            if not self.rate_limiter.acquire(blocking=True):
                yield "Rate limit exceeded. Please wait before making another request."
                return
            
            # Define the streaming API call function for retry logic
            def make_streaming_call():
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=prompt)]
                return self.client.stream(messages)
            
            # Use exponential backoff retry for the streaming API call
            stream = exponential_backoff_retry(make_streaming_call)
            
            # Process streaming response using ChatPerplexity interface
            for chunk in stream:
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                            
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                error_msg = "Perplexity API rate limit exceeded. Please wait a moment and try again."
            yield f"Error streaming response: {error_msg}"

class LLMFactory:
    """Factory class for creating LLM providers"""
    
    PROVIDERS = {
        "google_gemini": GoogleGeminiProvider,
        "openai": OpenAIProvider,
        "groq": GroqProvider,
        "perplexity": PerplexityProvider
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, api_key: str, model_name: str, temperature: float = 0.7, tools: Optional[Dict] = None) -> BaseLLMProvider:
        """
        Create an LLM provider instance based on the provider name.
        
        Factory method that instantiates the appropriate LLM provider class
        based on the provider name. Supports multiple LLM providers with
        consistent interface and configuration.
        
        Args:
            provider_name (str): Name of the LLM provider
                               Supported: "google_gemini", "openai", "groq", "perplexity"
            api_key (str): API authentication key for the provider
            model_name (str): Specific model identifier for the provider
            temperature (float): Controls response randomness (0.0-1.0, default: 0.7)
            tools (Optional[Dict]): Dictionary of available tools/functions
        
        Returns:
            BaseLLMProvider: Configured provider instance ready for use
        
        Raises:
            ValueError: If provider_name is not supported
        
        Supported Providers:
            - google_gemini: Google's Gemini models with tool calling
            - openai: OpenAI's GPT models with rate limiting
            - groq: Groq's fast inference models
            - perplexity: Perplexity's search-augmented models
        
        Note:
            - All providers implement the same BaseLLMProvider interface
            - Tools parameter enables function calling where supported
        """
        if provider_name not in cls.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider_name}. Supported providers: {list(cls.PROVIDERS.keys())}")
        
        provider_class = cls.PROVIDERS[provider_name]
        return provider_class(api_key, model_name, temperature, tools)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """
        Get list of available LLM providers supported by the factory.
        
        Returns a list of all LLM provider names that can be used with
        the create_provider method. This is useful for validation,
        configuration, and user interface purposes.
        
        Returns:
            list: List of supported provider names:
                  ["google_gemini", "openai", "groq", "perplexity"]
        
        Provider Capabilities:
            - google_gemini: Tool calling, streaming, content generation
            - openai: Streaming, rate limiting, chat completions
            - groq: Fast inference, streaming, OpenAI-compatible
            - perplexity: Search-augmented responses, streaming
        
        Note:
            - All providers support both streaming and non-streaming responses
            - Tool support varies by provider implementation
        """
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def create_from_config(cls, provider_name: str, tools: Optional[Dict] = None) -> BaseLLMProvider:
        """
        Create provider from configuration with automatic parameter mapping.
        
        Convenience method that creates an LLM provider using configuration
        settings from the global config object. Maps provider names to their
        corresponding API keys and model names automatically.
        
        Args:
            provider_name (str): Name of the LLM provider
                               Must be one of the supported providers
            tools (Optional[Dict]): Dictionary of available tools/functions
        
        Returns:
            BaseLLMProvider: Configured provider instance with config-based settings
        
        Raises:
            ValueError: If provider_name is not supported or API key is missing
        
        Required Config Attributes:
            - google_gemini: GOOGLE_API_KEY, GOOGLE_MODEL
            - openai: OPENAI_API_KEY, OPENAI_MODEL
            - groq: GROQ_API_KEY, GROQ_MODEL
            - perplexity: PERPLEXITY_API_KEY, PERPLEXITY_MODEL
            - Optional: AGENT_TEMPERATURE (defaults to 0.7)
        
        Configuration Mapping:
            - Automatically maps provider names to config attributes
            - Uses default models if not specified in config
            - Uses default temperature if not specified in config
            - Passes through tools parameter for function calling
        
        Note:
            - Simplifies provider creation from centralized configuration
            - Reduces boilerplate code for common configuration patterns
            - Uses global config object from module imports
        """
        # Map provider names to config attributes
        provider_configs = {
            "google_gemini": {
                "api_key": getattr(config, "GOOGLE_API_KEY", None),
                "model_name": getattr(config, "GOOGLE_MODEL", "gemini-1.5-flash")
            },
            "openai": {
                "api_key": getattr(config, "OPENAI_API_KEY", None),
                "model_name": getattr(config, "OPENAI_MODEL", "gpt-4o")
            },
            "groq": {
                "api_key": getattr(config, "GROQ_API_KEY", None),
                "model_name": getattr(config, "GROQ_MODEL", "deepseek-r1-distill-llama-70b")
            },
            "perplexity": {
                "api_key": getattr(config, "PERPLEXITY_API_KEY", None),
                "model_name": getattr(config, "PERPLEXITY_MODEL", "sonar-pro")
            }
        }
        
        if provider_name not in provider_configs:
            raise ValueError(f"Unsupported provider: {provider_name}")
        
        provider_config = provider_configs[provider_name]
        api_key = provider_config["api_key"]
        model_name = provider_config["model_name"]
        
        if not api_key:
            raise ValueError(f"API key not found for provider: {provider_name}")
        
        return cls.create_provider(
            provider_name=provider_name,
            api_key=api_key,
            model_name=model_name,
            temperature=getattr(config, "AGENT_TEMPERATURE", 0.7),
            tools=tools
        )