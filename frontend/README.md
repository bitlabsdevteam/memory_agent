# Memory Agentic AI - Frontend

A modern React/Next.js frontend for interacting with the Memory Agentic AI backend.

## Features

- 🎨 **Modern UI**: Clean, responsive design with dark mode support
- 💬 **Real-time Chat**: Streaming responses from the AI agent
- 🧠 **Memory Management**: View and manage conversation memory
- 🔧 **Session Control**: Switch between different conversation sessions
- ⚡ **Tool Integration**: Visual feedback for agent actions and observations
- 📱 **Responsive**: Works on desktop, tablet, and mobile devices

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend server running on `http://localhost:5001`

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and visit `http://localhost:3000`

## Usage

### Chat Interface

- Type your message in the input field at the bottom
- Press Enter to send (Shift+Enter for new line)
- Watch as the AI responds with streaming text
- See real-time tool usage (actions and observations)

### Session Management

- Click on the session ID in the header to rename it
- Use "New" button to start a fresh session
- Use "Clear" button to clear current session memory

### Memory Status

- View current memory status in the header
- See message count and recent conversation snippets
- Refresh memory status manually if needed

### Message Types

- 👤 **User Messages**: Your input messages
- 🤖 **Assistant Messages**: AI responses
- ⚡ **Actions**: Tools being used by the AI
- 👁️ **Observations**: Results from tool usage
- ❌ **Errors**: Error messages and warnings

## Configuration

The frontend is configured to connect to the backend at `http://localhost:5001`. If your backend is running on a different port, update the `API_BASE_URL` constant in `src/app/components/ChatInterface.tsx`.

## Technology Stack

- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Server-Sent Events**: Real-time streaming communication

## Components

- `ChatInterface`: Main chat component with state management
- `MessageList`: Displays conversation messages with different types
- `MessageInput`: Input field with send functionality
- `SessionControls`: Session management and memory controls
- `MemoryStatus`: Displays current memory information
