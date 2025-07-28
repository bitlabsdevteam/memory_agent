"""Configuration settings for Trip Advisor - AI Agent system"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Trip Advisor - AI Agent system"""
    
    # LLM Provider Configuration
    DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "google_gemini")
    
    # Google API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Groq API Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "deepseek-r1-distill-llama-70b")
    
    # Perplexity API Configuration
    # Support both PPLX_API_KEY (official) and PERPLEXITY_API_KEY (legacy)
    PERPLEXITY_API_KEY = os.getenv("PPLX_API_KEY") or os.getenv("PERPLEXITY_API_KEY")
    PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar-pro")
    
    # LangSmith Configuration (Standard Environment Variables)
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "trip-agent")
    
    # Flask Configuration
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5001))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    # Agent Configuration
    AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", 0.7))
    AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", 5))
    AGENT_VERBOSE = os.getenv("AGENT_VERBOSE", "True").lower() == "true"
    
    # Memory Configuration
    MEMORY_MAX_MESSAGES = int(os.getenv("MEMORY_MAX_MESSAGES", 20))
    MEMORY_OPTIMIZATION_INTERVAL = int(os.getenv("MEMORY_OPTIMIZATION_INTERVAL", 10))
    
    # Streaming Configuration
    STREAMING_DELAY = float(os.getenv("STREAMING_DELAY", 0.01))
    STREAMING_ENABLED = os.getenv("STREAMING_ENABLED", "True").lower() == "true"
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    
    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        errors = []
        
        # Check if at least one LLM provider API key is configured
        if not any([cls.GOOGLE_API_KEY, cls.OPENAI_API_KEY, cls.GROQ_API_KEY, cls.PERPLEXITY_API_KEY]):
            errors.append("At least one LLM provider API key (GOOGLE_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, or PERPLEXITY_API_KEY) is required")
        
        # Validate DEFAULT_LLM_PROVIDER
        valid_providers = ["google_gemini", "openai", "groq", "perplexity"]
        if cls.DEFAULT_LLM_PROVIDER not in valid_providers:
            errors.append(f"DEFAULT_LLM_PROVIDER must be one of: {', '.join(valid_providers)}")
        
        # Check if the default provider has an API key
        if cls.DEFAULT_LLM_PROVIDER == "google_gemini" and not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY is required when DEFAULT_LLM_PROVIDER is google_gemini")
        elif cls.DEFAULT_LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when DEFAULT_LLM_PROVIDER is openai")
        elif cls.DEFAULT_LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required when DEFAULT_LLM_PROVIDER is groq")
        elif cls.DEFAULT_LLM_PROVIDER == "perplexity" and not cls.PERPLEXITY_API_KEY:
            errors.append("PERPLEXITY_API_KEY is required when DEFAULT_LLM_PROVIDER is perplexity")
        
        if cls.AGENT_TEMPERATURE < 0 or cls.AGENT_TEMPERATURE > 2:
            errors.append("AGENT_TEMPERATURE must be between 0 and 2")
        
        if cls.MEMORY_MAX_MESSAGES < 1:
            errors.append("MEMORY_MAX_MESSAGES must be at least 1")
        
        if cls.AGENT_MAX_ITERATIONS < 1:
            errors.append("AGENT_MAX_ITERATIONS must be at least 1")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print current configuration (excluding sensitive data)"""
        print("🔧 Trip Advisor - AI Agent Configuration:")
        print(f"   Default LLM Provider: {cls.DEFAULT_LLM_PROVIDER}")
        print(f"   Google Model: {cls.GOOGLE_MODEL}")
        print(f"   OpenAI Model: {cls.OPENAI_MODEL}")
        print(f"   Groq Model: {cls.GROQ_MODEL}")
        print(f"   Perplexity Model: {cls.PERPLEXITY_MODEL}")
        print(f"   Temperature: {cls.AGENT_TEMPERATURE}")
        print(f"   Max Iterations: {cls.AGENT_MAX_ITERATIONS}")
        print(f"   Memory Max Messages: {cls.MEMORY_MAX_MESSAGES}")
        print(f"   Streaming Enabled: {cls.STREAMING_ENABLED}")
        print(f"   Flask Host: {cls.FLASK_HOST}")
        print(f"   Flask Port: {cls.FLASK_PORT}")
        print(f"   Debug Mode: {cls.FLASK_DEBUG}")
        print(f"   Google API Key Set: {'Yes' if cls.GOOGLE_API_KEY else 'No'}")
        print(f"   OpenAI API Key Set: {'Yes' if cls.OPENAI_API_KEY else 'No'}")
        print(f"   Groq API Key Set: {'Yes' if cls.GROQ_API_KEY else 'No'}")
        print(f"   Perplexity API Key Set: {'Yes' if cls.PERPLEXITY_API_KEY else 'No'}")
        print(f"   LangSmith Tracing: {'Enabled' if cls.LANGSMITH_TRACING else 'Disabled'}")
        print(f"   LangSmith Project: {cls.LANGSMITH_PROJECT}")
        print(f"   LangSmith API Key Set: {'Yes' if cls.LANGSMITH_API_KEY else 'No'}")

# Development configuration
class DevelopmentConfig(Config):
    """Development-specific configuration"""
    FLASK_DEBUG = True
    AGENT_VERBOSE = True

# Production configuration
class ProductionConfig(Config):
    """Production-specific configuration"""
    FLASK_DEBUG = False
    AGENT_VERBOSE = False
    FLASK_HOST = "0.0.0.0"  # Allow external connections in Docker

# Testing configuration
class TestingConfig(Config):
    """Testing-specific configuration"""
    FLASK_DEBUG = True
    AGENT_VERBOSE = False
    MEMORY_MAX_MESSAGES = 5  # Smaller for testing
    STREAMING_DELAY = 0.001  # Faster for testing

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    return config_map.get(config_name, DevelopmentConfig)