from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from typing import Optional, Dict, Any

class LLMFactory:
    """Factory class for creating different LLM instances.
    
    This class implements the factory design pattern to create different LLM instances
    based on the provider and model name. It supports OpenAI, Groq, and Google models.
    """
    
    @staticmethod
    def create_llm(provider: str = "openai", model_name: Optional[str] = None, **kwargs) -> Any:
        """Create an LLM instance based on the provider and model name.
        
        Args:
            provider: The LLM provider (openai, groq, google)
            model_name: The specific model name to use
            **kwargs: Additional arguments to pass to the LLM constructor
        
        Returns:
            An instance of the specified LLM
        
        Raises:
            ValueError: If the provider is not supported
        """
        provider = provider.lower()
        
        if provider == "openai":
            return LLMFactory._create_openai_llm(model_name, **kwargs)
        elif provider == "groq":
            return LLMFactory._create_groq_llm(model_name, **kwargs)
        elif provider == "google":
            return LLMFactory._create_google_llm(model_name, **kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def _create_openai_llm(model_name: Optional[str] = None, **kwargs) -> ChatOpenAI:
        """Create an OpenAI LLM instance."""
        default_model = "gpt-4o-mini"
        model = model_name or default_model
        
        # Get API key from environment variable
        api_key = kwargs.pop("api_key", os.getenv("OPENAI_API_KEY"))
        
        # Set default parameters if not provided
        temperature = kwargs.pop("temperature", 0.7)
        print('OpenAI is being use')
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=api_key,
            streaming=True,
            stop=["\nObservation:"],
            **kwargs
        )
    
    @staticmethod
    def _create_groq_llm(model_name: Optional[str] = None, **kwargs) -> ChatGroq:
        """Create a Groq LLM instance."""
        default_model = "deepseek-r1-distill-llama-70b"
        model = model_name or default_model
        
        # Get API key from environment variable
        api_key = kwargs.pop("api_key", os.getenv("GROQ_API_KEY"))
        
        # Set default parameters if not provided
        temperature = kwargs.pop("temperature", 0.7)
        print('deepseek is being use')
        return ChatGroq(
            model=model,
            temperature=temperature,
            groq_api_key=api_key,
            stop=["\nObservation:"],
            **kwargs
        )
    
    @staticmethod
    def _create_google_llm(model_name: Optional[str] = None, **kwargs) -> ChatGoogleGenerativeAI:
        """Create a Google LLM instance."""
        default_model = "gemini-1.5-flash"
        model = model_name or default_model
        
        # Get API key from environment variable
        api_key = kwargs.pop("api_key", os.getenv("GOOGLE_API_KEY"))
        
        # Set default parameters if not provided
        temperature = kwargs.pop("temperature", 0.7)
        print('Google is being use')
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key,
            stop=["\nObservation:"],
            **kwargs
        )