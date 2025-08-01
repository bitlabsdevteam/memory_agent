'use client';

import { useEffect, useRef } from 'react';
import { ThinkingDots } from './TypingAnimation';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'action' | 'observation' | 'error' | 'action_input' | 'final_answer_header' | 'thinking';
  content: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

export default function MessageList({ messages, isLoading }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // Force re-render when messages change
  useEffect(() => {
    // This is just to ensure the component re-renders when messages change
  }, [messages.length, messages.map(m => m.content).join('')]);

  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getMessageStyle = (type: string) => {
    switch (type) {
      case 'user':
        return 'bg-blue-600 text-white ml-auto shadow-sm';
      case 'assistant':
        return 'bg-gray-100 text-gray-800 shadow-sm';
      case 'thinking':
        return 'bg-gray-50 text-black border border-gray-200 italic shadow-sm';
      case 'action':
        return 'bg-yellow-50 text-yellow-800 border border-yellow-200 shadow-sm';
      case 'action_input':
        return 'bg-blue-50 text-blue-800 border border-blue-200 shadow-sm';
      case 'observation':
        return 'bg-green-50 text-green-800 border border-green-200 shadow-sm';
      case 'final_answer_header':
        return 'bg-gray-100 text-gray-800 font-semibold shadow-sm';
      case 'error':
        return 'bg-red-50 text-red-800 border border-red-200 shadow-sm';
      default:
        return 'bg-gray-100 text-gray-800 shadow-sm';
    }
  };

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'user':
        return '👤';
      case 'assistant':
        return '🤖';
      case 'thinking':
        return '🧠';
      case 'action':
        return '🔧';
      case 'action_input':
        return '📝';
      case 'observation':
        return '📊';
      case 'final_answer_header':
        return '💬';
      case 'error':
        return '❌';
      default:
        return '💬';
    }
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-4 bg-gray-50">
      {messages.length === 0 && (
        <div className="text-center text-gray-500 py-12">
          <div className="text-5xl mb-4">👋</div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">Hello! I&apos;m your Trip Advisor - AI Agent</h3>
          <p className="text-gray-600 mb-2">I can remember our entire conversation and help you with:</p>
          <div className="flex flex-wrap justify-center gap-2 mt-4">
            <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">Weather Information</span>
            <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm">Local Time</span>
            <span className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm">City Facts</span>
            <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm">Travel Planning</span>
          </div>
          <p className="text-sm mt-4 text-gray-500">Try asking me something!</p>
        </div>
      )}
      
      {messages.map((message) => (
        <div
          key={`${message.id}-${message.content.length}`}
          className={`flex items-start space-x-3 fade-in ${
            message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
          } ${
            message.metadata?.fadeOut ? 'fade-out' : ''
          }`}
        >
          <div className="flex-shrink-0">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
              message.type === 'user' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white border-2 border-gray-200'
            }`}>
              {getMessageIcon(message.type)}
            </div>
          </div>
          <div className={`max-w-xs lg:max-w-2xl px-4 py-3 rounded-2xl ${getMessageStyle(message.type)} facebook-card`}>
            <div key={`content-${message.id}-${message.content.length}`} className="break-words leading-relaxed">
              {message.type === 'thinking' ? (
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">🧠 Thinking</span>
                    <ThinkingDots size="sm" />
                  </div>
                  {message.content && (
                    <div className="text-sm text-gray-600 font-mono bg-gray-50 p-2 rounded border-l-4 border-blue-300">
                      {message.content.replace(/^>\s*/, '')}
                    </div>
                  )}
                </div>
              ) : (
                message.content.replace(/^>\s*/, '')
              )}
            </div>
            <div className="text-xs opacity-60 mt-2 font-medium">
              {formatTime(message.timestamp)}
            </div>
          </div>
        </div>
      ))}
      
      {isLoading && (
        <div className="flex items-start space-x-3 fade-in">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-white border-2 border-gray-200 flex items-center justify-center text-sm">
              🤖
            </div>
          </div>
          <div className="bg-gray-100 px-4 py-3 rounded-2xl shadow-sm">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
}