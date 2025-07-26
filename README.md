# Memory Agentic - LangChain React Agent with Optimized Memory Management

A sophisticated AI agent built with LangChain's React framework, featuring Google Gemini integration, optimized memory management using `RunnableWithMessageHistory`, and real-time streaming capabilities through a Flask API.

## 🚀 Features

- **React Agent Framework**: Built using LangChain's React (Reasoning and Acting) pattern
- **Google Gemini Integration**: Powered by Google's Gemini Pro model for advanced reasoning
- **Optimized Memory Management**: Uses `RunnableWithMessageHistory` for efficient conversation memory
- **Real-time Streaming**: Token-by-token streaming responses via Server-Sent Events (SSE)
- **Session Management**: Multiple conversation sessions with isolated memory
- **Memory Optimization**: Automatic memory cleanup to prevent memory bloat
- **Tool Integration**: Extensible tool system with search, calculator, and memory info tools
- **Web Interface**: Beautiful HTML client for testing and interaction

## 🏗️ Architecture

### Core Components

1. **MemoryOptimizedAgent**: Main agent class with memory management
2. **RunnableWithMessageHistory**: LangChain's memory management wrapper
3. **Flask API**: RESTful API with streaming endpoints
4. **Session Management**: Thread-safe session handling
5. **Tool System**: Extensible tools for agent capabilities

### Memory Management Strategy

- **Session-based Memory**: Each conversation session has isolated memory
- **Automatic Optimization**: Keeps only recent messages (configurable limit)
- **Thread-safe Operations**: Concurrent session handling with locks
- **Memory Status Monitoring**: Real-time memory usage tracking

## 📋 Prerequisites

- Python 3.8+
- Google API Key (for Gemini access)
- Modern web browser (for the client interface)

## 🛠️ Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd /Users/davidbong/Documents/agentic_projects/memory_agentic
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Google API key:
   ```
   GOOGLE_API_KEY=your_actual_google_api_key_here
   ```

## 🔑 Getting Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and add it to your `.env` file

## 🚀 Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### Using the Web Interface

1. Open `client.html` in your web browser
2. The interface will automatically connect to the server
3. Start chatting with the AI agent

### API Endpoints

#### Chat with Streaming
```http
POST /chat
Content-Type: application/json

{
  "message": "Hello, can you help me with math?",
  "session_id": "user123"
}
```

#### Check Memory Status
```http
GET /memory/status/{session_id}
```

#### Clear Session Memory
```http
DELETE /memory/clear/{session_id}
```

#### Health Check
```http
GET /health
```

## 🔧 Configuration

### Memory Optimization

You can adjust memory settings in `app.py`:

```python
# Maximum messages to keep in memory per session
self._optimize_memory(session_id, max_messages=20)
```

### Model Configuration

```python
self.llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    temperature=0.7,  # Adjust creativity
    streaming=True
)
```

## 🛠️ Available Tools

The agent comes with built-in tools:

1. **Search Tool**: Simulated web search functionality
2. **Calculator Tool**: Mathematical calculations
3. **Memory Info Tool**: Conversation memory statistics

### Adding Custom Tools

Extend the `_create_tools()` method in `MemoryOptimizedAgent`:

```python
def custom_tool(input_text: str) -> str:
    """Your custom tool implementation"""
    return f"Custom result for: {input_text}"

tools.append(Tool(
    name="custom_tool",
    description="Description of what your tool does",
    func=custom_tool
))
```

## 📊 Memory Management Details

### Session Isolation
- Each session has its own `ChatMessageHistory`
- Sessions are identified by unique session IDs
- Memory is isolated between different users/sessions

### Automatic Optimization
- Prevents memory bloat by limiting message history
- Configurable message limits per session
- Maintains conversation context while managing resources

### Thread Safety
- Uses threading locks for concurrent access
- Safe for multiple simultaneous users
- Session data integrity guaranteed

## 🔍 Monitoring and Debugging

### Memory Status
Monitor memory usage through the API:
```bash
curl http://localhost:5000/memory/status/your_session_id
```

### Logs
The Flask app runs in debug mode and provides detailed logs:
- Agent reasoning steps
- Tool executions
- Memory operations
- API requests

## 🚨 Troubleshooting

### Common Issues

1. **"Google API Key not found"**
   - Ensure your `.env` file contains the correct API key
   - Verify the key is valid and has Gemini API access

2. **"Connection refused"**
   - Make sure the Flask server is running
   - Check if port 5000 is available

3. **"Streaming not working"**
   - Ensure your browser supports Server-Sent Events
   - Check browser console for JavaScript errors

4. **"Memory not persisting"**
   - Verify session IDs are consistent
   - Check server logs for memory optimization triggers

### Performance Tips

- Adjust `max_messages` based on your memory requirements
- Use shorter session IDs for better performance
- Monitor memory usage in production environments
- Consider implementing persistent storage for long-term memory

## 🔮 Future Enhancements

- [ ] Persistent memory storage (Redis/Database)
- [ ] Advanced memory summarization
- [ ] Custom tool marketplace
- [ ] Multi-modal capabilities
- [ ] Advanced session analytics
- [ ] WebSocket support for real-time updates

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

---

**Built with ❤️ using LangChain, Google Gemini, and Flask**# memory_agent
