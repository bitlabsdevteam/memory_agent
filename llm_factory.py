"""LLM Factory for supporting multiple LLM providers"""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Generator, Optional
import google.generativeai as genai
from langchain_openai import ChatOpenAI
import requests
from config import get_config

# Get configuration
config_class = get_config()
config = config_class()

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
    """OpenAI LLM Provider using LangChain"""
    
    def _initialize(self):
        """Initialize OpenAI client using LangChain"""
        try:
            self.client = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                openai_api_key=self.api_key,
                streaming=True
            )
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            raise e
    
    def generate_response(self, prompt: str, max_tokens: int = 2048) -> Dict[str, Any]:
        """Generate response using OpenAI via LangChain"""
        try:
            from langchain_core.messages import HumanMessage
            
            message = HumanMessage(content=prompt)
            response = self.client.invoke([message])
            
            response_text = response.content if response.content else "I apologize, but I couldn't process your request."
            
            return {
                "response": response_text,
                "success": True,
                "provider": "openai",
                "model": self.model_name
            }
            
        except Exception as e:
            return {
                "response": f"Error generating response: {str(e)}",
                "success": False,
                "provider": "openai",
                "model": self.model_name
            }
    
    def stream_response(self, prompt: str, max_tokens: int = 2048) -> Generator[str, None, None]:
        """Stream response from OpenAI via LangChain"""
        try:
            from langchain_core.messages import HumanMessage
            
            message = HumanMessage(content=prompt)
            
            for chunk in self.client.stream([message]):
                if chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            yield f"Error streaming response: {str(e)}"

class GroqProvider(BaseLLMProvider):
    """Groq LLM Provider (DeepSeek)"""
    
    def _initialize(self):
        """Initialize Groq client"""
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

class LLMFactory:
    """Factory class for creating LLM providers"""
    
    PROVIDERS = {
        "google_gemini": GoogleGeminiProvider,
        "openai": OpenAIProvider,
        "groq": GroqProvider
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