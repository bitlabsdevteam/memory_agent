# 🚀 Quick Start Guide - Memory Agentic

Get your Memory Agentic system up and running in 5 minutes!

## 📋 Prerequisites

- Python 3.8+
- Google API Key ([Get one here](https://makersuite.google.com/app/apikey))

## ⚡ Quick Setup

### 1. Setup Environment
```bash
# Make startup script executable (if not already)
chmod +x start.sh

# Run the automated setup
./start.sh
```

The startup script will:
- Create a virtual environment
- Install dependencies
- Create `.env` file from template
- Prompt you to add your Google API key
- Start the server

### 2. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your Google API key

# Start the server
python app.py
```

### 3. Get Your Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key
4. Add it to your `.env` file:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

## 🎮 Usage Options

### Option 1: Web Interface (Recommended)
1. Open `client.html` in your browser
2. Start chatting with the AI agent
3. Explore features like memory management and tool usage

### Option 2: API Testing
```bash
# Run comprehensive tests
python test_agent.py

# Run feature demonstrations
python example_usage.py
```

### Option 3: Direct API Calls
```bash
# Health check
curl http://localhost:5000/health

# Chat (basic)
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "session_id": "test"}'

# Memory status
curl http://localhost:5000/memory/status/test
```

## 🔧 Configuration

Customize your setup by editing `.env`:

```bash
# Model settings
GOOGLE_MODEL=gemini-pro
AGENT_TEMPERATURE=0.7
AGENT_MAX_ITERATIONS=5

# Memory settings
MEMORY_MAX_MESSAGES=20

# Server settings
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True
```

## 🎯 Key Features to Try

1. **Memory Persistence**: Ask the agent to remember information, then reference it later
2. **Tool Usage**: Try calculations, searches, and memory queries
3. **Session Management**: Use different session IDs to isolate conversations
4. **Streaming**: Watch responses appear in real-time

## 🆘 Troubleshooting

### Common Issues

**"Google API Key not found"**
- Check your `.env` file exists and contains the correct key
- Ensure no extra spaces around the key

**"Connection refused"**
- Make sure the Flask server is running (`python app.py`)
- Check if port 5000 is available

**"Module not found"**
- Activate your virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**"Streaming not working"**
- Try a different browser
- Check browser console for errors
- Ensure server is running and accessible

### Getting Help

1. Check the full [README.md](README.md) for detailed documentation
2. Run the test suite: `python test_agent.py`
3. Try the example demonstrations: `python example_usage.py`

## 🎉 Success!

If everything is working, you should see:
- ✅ Health check passes
- 🤖 Agent responds to messages
- 🧠 Memory persists across conversations
- 🛠️ Tools work correctly
- 📊 Memory management functions

**Happy chatting with your Memory Agentic system!** 🚀