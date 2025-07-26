"""Configuration settings for Memory Agentic system"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Memory Agentic system"""
    
    # Google API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
    
    # Flask Configuration
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
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
        
        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY is required")
        
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
        print("🔧 Memory Agentic Configuration:")
        print(f"   Model: {cls.GOOGLE_MODEL}")
        print(f"   Temperature: {cls.AGENT_TEMPERATURE}")
        print(f"   Max Iterations: {cls.AGENT_MAX_ITERATIONS}")
        print(f"   Memory Max Messages: {cls.MEMORY_MAX_MESSAGES}")
        print(f"   Streaming Enabled: {cls.STREAMING_ENABLED}")
        print(f"   Flask Host: {cls.FLASK_HOST}")
        print(f"   Flask Port: {cls.FLASK_PORT}")
        print(f"   Debug Mode: {cls.FLASK_DEBUG}")
        print(f"   API Key Set: {'Yes' if cls.GOOGLE_API_KEY else 'No'}")

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
    FLASK_HOST = "127.0.0.1"  # More secure for production

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