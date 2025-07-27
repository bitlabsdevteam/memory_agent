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
    from langchain_perplexity import ChatPerplexity
except ImportError:
    ChatPerplexity = None

# Get configuration
config_class = get_config()
config = config_class()

def exponential_backoff_retry(func, max_retries=6, base_delay=1, max_delay=60):
    """Retry function with exponential backoff for rate limit errors"""
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
    
    def __init__(self, api_key: str, model_name: str, temperature: float = 0.7):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """Initialize the provider-specific client"""
        pass
    
    @abstractmethod
    def generate_response(self, prompt: str, max_tokens: int = 2048) -> Dict[str, Any]:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def stream_response(self, prompt: str, max_tokens: int = 2048) -> Generator[str, None, None]:
        """Stream response from the LLM"""
        pass

class GoogleGeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider"""
    
    def _initialize(self):
        """Initialize Google Gemini client"""
        self.provider = "google_gemini"
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_response(self, prompt: str, max_tokens: int = 2048) -> Dict[str, Any]:
        """Generate response using Google Gemini"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=max_tokens,
                )
            )
            
            response_text = response.text if response.text else "I apologize, but I couldn't process your request."
            
            return {
                "response": response_text,
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
        """Stream response from Google Gemini"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=max_tokens,
                ),
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"Error streaming response: {str(e)}"

class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM Provider using LangChain with Rate Limiting"""
    
    def _initialize(self):
        """Initialize OpenAI client with FREE tier rate limiting"""
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
        """Generate response using OpenAI with exponential backoff retry"""
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
        """Stream response using OpenAI with exponential backoff retry"""
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
        """Initialize Groq client"""
        self.provider = "groq"
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_response(self, prompt: str, max_tokens: int = 2048) -> Dict[str, Any]:
        """Generate response using Groq"""
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
        """Stream response from Groq"""
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
        """Initialize Perplexity client using ChatPerplexity"""
        self.provider = "perplexity"
        
        if ChatPerplexity is None:
            raise ImportError("langchain-perplexity package not installed. Please install with: pip install langchain-perplexity")
        
        # Initialize ChatPerplexity client
        # Set the PPLX_API_KEY environment variable for ChatPerplexity
        import os
        os.environ["PPLX_API_KEY"] = self.api_key
        
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
        """Generate response using Perplexity with ChatPerplexity"""
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
        """Stream response from Perplexity using ChatPerplexity"""
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
    def create_provider(cls, provider_name: str, api_key: str, model_name: str, temperature: float = 0.7) -> BaseLLMProvider:
        """Create an LLM provider instance"""
        if provider_name not in cls.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider_name}. Supported providers: {list(cls.PROVIDERS.keys())}")
        
        provider_class = cls.PROVIDERS[provider_name]
        return provider_class(api_key, model_name, temperature)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available providers"""
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def create_from_config(cls, provider_name: str) -> BaseLLMProvider:
        """Create provider from configuration"""
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
            temperature=getattr(config, "AGENT_TEMPERATURE", 0.7)
        )