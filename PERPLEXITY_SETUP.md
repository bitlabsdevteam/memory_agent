# Perplexity LLM Provider Setup Guide

## Overview

The Perplexity provider has been successfully integrated into the Memory Agentic system using the official LangChain Perplexity integration, offering access to Perplexity's powerful language models with built-in rate limiting and error handling.

## Features

✅ **Rate Limiting**: Built-in rate limiting (20 RPM) to prevent API quota exhaustion  
✅ **Exponential Backoff**: Automatic retry logic with exponential backoff for rate limit errors  
✅ **Streaming Support**: Real-time streaming responses for better user experience  
✅ **Error Handling**: Comprehensive error handling with informative messages  
✅ **Output Parsing**: Proper handling of Perplexity's response format  
✅ **Thinking Support**: Compatible with the system's thinking/reasoning display  

## Setup Instructions

### 1. Install LangChain Perplexity Package

The Perplexity provider uses the official LangChain integration, which provides:

- **Official Support**: Direct integration with Perplexity's API
- **Better Error Handling**: Improved error messages and retry logic
- **Streaming Support**: Native streaming capabilities
- **Metadata Access**: Access to search results and citations

```bash
pip install -U langchain-perplexity
```

### 2. Get Perplexity API Key

1. Visit [Perplexity AI](https://www.perplexity.ai/)
2. Sign up for an account or log in
3. Navigate to your API settings
4. Generate a new API key
5. Copy the API key for configuration

### 3. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Perplexity API Configuration (using official PPLX_API_KEY)
PPLX_API_KEY=your_perplexity_api_key_here
PERPLEXITY_MODEL=sonar-pro

# Optional: Set as default provider
DEFAULT_LLM_PROVIDER=perplexity
```

### 4. Available Models

Perplexity offers several models. The default configuration uses:
- `sonar-pro` (recommended for most use cases)

Other available models:
- `sonar` (faster, less capable)
- `sonar-pro` (balanced performance and capability)

## Usage Examples

### Basic Usage

```python
from llm_factory import LLMFactory
from config import get_config

# Get configuration
config_class = get_config()
config = config_class()

# Create Perplexity provider
factory = LLMFactory()
provider = factory.create_provider(
    provider_name="perplexity",
    api_key=config.PERPLEXITY_API_KEY,
    model_name="sonar-pro",
    temperature=0.7
)

# Generate response
response = provider.generate_response(
    "What are the latest developments in AI?",
    max_tokens=500
)

print(response['response'])
```

### Streaming Usage

```python
# Stream response
for chunk in provider.stream_response(
    "Explain quantum computing in simple terms",
    max_tokens=300
):
    print(chunk, end="", flush=True)
```

### Using from Configuration

```python
# Create provider from config (requires PPLX_API_KEY in .env)
factory = LLMFactory()
provider = factory.create_from_config("perplexity")

response = provider.generate_response("Your question here")
```

## Rate Limiting Details

### Current Limits
- **Rate**: 20 requests per minute (0.3 requests per second)
- **Burst**: Up to 5 requests in quick succession
- **Retry**: Automatic exponential backoff on rate limit errors
- **Timeout**: 60 seconds per request

### Rate Limiting Behavior

1. **Blocking**: The rate limiter blocks requests when limits are exceeded
2. **Exponential Backoff**: Automatic retries with increasing delays
3. **Jitter**: Random delays added to prevent thundering herd
4. **Error Messages**: Clear feedback when rate limits are hit

## Testing

### Integration Test

```bash
# Test basic integration (no API key required)
python test_perplexity_integration.py
```

### Full Functionality Test

```bash
# Test with actual API calls (requires PERPLEXITY_API_KEY)
python test_perplexity.py
```

### Test Results Expected

✅ Provider Integration  
✅ Configuration Integration  
✅ Basic Functionality  
✅ Rate Limiting  
✅ Streaming  
✅ Reasoning & Thinking  

## API Endpoints

The Perplexity provider uses the following endpoint:
- **Base URL**: `https://api.perplexity.ai`
- **Chat Completions**: `/chat/completions`
- **Streaming**: `/chat/completions` with `stream=true`

## Error Handling

### Common Errors

1. **Rate Limit Exceeded (429)**
   - Automatic retry with exponential backoff
   - Clear error message for users

2. **Invalid API Key (401)**
   - Check your API key in `.env` file
   - Ensure key is valid and active

3. **Model Not Found (404)**
   - Verify model name in configuration
   - Check available models in Perplexity documentation

4. **Timeout Errors**
   - Automatic retry up to 6 times
   - 60-second timeout per request

### Error Response Format

```python
{
    "response": "Error message here",
    "success": False,
    "provider": "perplexity",
    "model": "model_name"
}
```

## Configuration Validation

The system validates Perplexity configuration:

```python
from config import get_config

config_class = get_config()
config = config_class()

# Validate configuration
errors = config.validate()
if errors:
    for error in errors:
        print(f"Configuration error: {error}")
```

## Integration with Backend

The Perplexity provider is fully integrated with the backend API:

1. **Available in Factory**: Listed in `LLMFactory.get_available_providers()`
2. **Config Support**: Full configuration support in `config.py`
3. **Validation**: Included in configuration validation
4. **Backend API**: Available through `/api/chat` endpoint

### Backend Usage

```bash
# Set Perplexity as default in .env
DEFAULT_LLM_PROVIDER=perplexity

# Start backend
python app.py

# Test via API
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from Perplexity!", "stream": false}'
```

## Best Practices

1. **Rate Limiting**: Don't disable rate limiting - it protects your API quota
2. **Error Handling**: Always check the `success` field in responses
3. **Timeouts**: Use appropriate timeouts for your use case
4. **Model Selection**: Choose the right model for your needs (small/large/huge)
5. **API Key Security**: Never commit API keys to version control

## Troubleshooting

### Provider Not Available
```python
# Check if perplexity is in available providers
factory = LLMFactory()
print(factory.get_available_providers())
# Should include 'perplexity'
```

### Configuration Issues
```python
# Check configuration
from config import get_config
config = get_config()()
print(f"API Key set: {bool(config.PERPLEXITY_API_KEY)}")
print(f"Model: {config.PERPLEXITY_MODEL}")
```

### Rate Limiting Issues
- Check if you're making too many requests
- Verify rate limiter is working with test script
- Monitor API usage in Perplexity dashboard

## Support

For issues with the Perplexity provider:

1. Run the integration test: `python test_perplexity_integration.py`
2. Check configuration with `config.validate()`
3. Verify API key is valid
4. Review error messages for specific issues

## Changelog

### v1.0.0 - Initial Release
- ✅ Perplexity provider implementation
- ✅ Rate limiting with exponential backoff
- ✅ Streaming support
- ✅ Configuration integration
- ✅ Comprehensive error handling
- ✅ Test suite
- ✅ Documentation