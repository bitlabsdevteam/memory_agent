#!/bin/bash

# Memory Agentic Startup Script
# This script helps you start the Memory Agentic system

echo "🚀 Memory Agentic - LangChain React Agent with Optimized Memory Management"
echo "================================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
echo "📋 Checking dependencies..."
if ! pip show langchain >/dev/null 2>&1; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
else
    echo "✅ Dependencies already installed"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "🔑 Please edit the .env file and add your Google API key:"
    echo "   GOOGLE_API_KEY=your_actual_google_api_key_here"
    echo ""
    echo "💡 Get your API key from: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press Enter after you've updated the .env file..."
fi

# Check if Google API key is set
source .env
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_google_api_key_here" ]; then
    echo "❌ Google API key not properly set in .env file"
    echo "Please edit .env and add your actual Google API key"
    exit 1
fi

echo "✅ Google API key found"
echo ""
echo "🌐 Starting Flask server..."
echo "📱 Web interface will be available at: http://localhost:5000"
echo "🖥️  Open client.html in your browser to interact with the agent"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
python app.py