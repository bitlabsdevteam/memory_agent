'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useEnhancedStreaming } from '../hooks/useEnhancedStreaming';
import { TypingAnimation, StreamingText, ThinkingDots, ConnectionStatus, ThinkingIndicator, StatusBadge } from './TypingAnimation';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'thinking' | 'tool_call' | 'tool_result' | 'action' | 'action_input' | 'observation' | 'final_answer_header' | 'error' | 'system';
  content: string;
  timestamp: Date;
  isTemporary?: boolean;
  isStreaming?: boolean;
  metadata?: Record<string, string | number | boolean>;
}

interface EnhancedChatInterfaceProps {
  sessionId: string;
  onSessionUpdate?: (sessionId: string) => void;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

const generateMessageId = (type: string) => `${type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

export const EnhancedChatInterface: React.FC<EnhancedChatInterfaceProps> = ({
  sessionId,
  onSessionUpdate
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { streamState, createResilientStream, disconnect } = useEnhancedStreaming({
    maxRetries: 3,
    retryDelay: 1000,
    onReconnect: () => {
      addSystemMessage('🔄 Connection restored', 'system');
    },
    onError: (error) => {
      addSystemMessage(`❌ Connection error: ${error.message}`, 'error');
    }
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addSystemMessage = (content: string, type: 'system' | 'error' = 'system') => {
    const systemMessage: Message = {
      id: generateMessageId('system'),
      type,
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, systemMessage]);
  };

  const cleanupTemporaryMessages = () => {
    setMessages(prev => prev.filter(msg => !msg.isTemporary));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const content = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    // Add user message
    const userMessage: Message = {
      id: generateMessageId('user'),
      type: 'user',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    let thinkingMessage: Message | null = null;
    let assistantMessage: Message | null = null;
    let toolCallMessage: Message | null = null;

    try {
      await createResilientStream(
        `${API_BASE_URL}/api/v1/chat`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({
            message: content,
            session_id: sessionId
          }),
          mode: 'cors'
        },
        (data) => {
          if (data.type === 'thinking_start') {
            if (!thinkingMessage) {
              thinkingMessage = {
                id: generateMessageId('thinking'),
                type: 'thinking',
                content: '',
                timestamp: new Date(),
                isTemporary: true,
                isStreaming: true
              };
              setMessages(prev => [...prev, thinkingMessage!]);
            }
          } else if (data.type === 'thinking') {
            if (thinkingMessage) {
              const updatedContent = thinkingMessage.content + (data.token || '');
              thinkingMessage.content = updatedContent;
              setMessages(prev => {
                return prev.map(msg => {
                  if (msg.id === thinkingMessage!.id) {
                    return { ...msg, content: updatedContent };
                  }
                  return msg;
                });
              });
            }
          } else if (data.type === 'thinking_end') {
            if (thinkingMessage) {
              // Mark thinking as complete and schedule removal
              setMessages(prev => {
                return prev.map(msg => {
                  if (msg.id === thinkingMessage!.id) {
                    return { ...msg, isStreaming: false };
                  }
                  return msg;
                });
              });
              
              setTimeout(() => {
                setMessages(prev => prev.filter(msg => msg.id !== thinkingMessage?.id));
              }, 2000); // Show thinking for 2 seconds after completion
            }
            
            // Prepare for response
            assistantMessage = {
              id: generateMessageId('assistant'),
              type: 'assistant',
              content: '',
              timestamp: new Date(),
              isStreaming: true
            };
            setMessages(prev => [...prev, assistantMessage!]);
          } else if (data.type === 'tool_call_start') {
            // Start a new tool call message
            toolCallMessage = {
              id: generateMessageId('tool_call'),
              type: 'tool_call',
              content: '',
              timestamp: new Date(),
              isStreaming: true,
              metadata: {
                tool_name: (data.tool_name as string) || 'unknown',
                type: data.type
              }
            };
            setMessages(prev => [...prev, toolCallMessage!]);
          } else if (data.type === 'tool_call') {
            if (toolCallMessage) {
              const updatedContent = data.token || '';
              toolCallMessage.content = updatedContent;
              setMessages(prev => {
                return prev.map(msg => {
                  if (msg.id === toolCallMessage!.id) {
                    return { 
                      ...msg, 
                      content: updatedContent, 
                      metadata: { 
                        ...msg.metadata, 
                        tool_name: (data.tool_name as string) || msg.metadata?.tool_name || 'unknown',
                        parameters: (data.parameters as string) || ''
                      } 
                    };
                  }
                  return msg;
                });
              });
            }
          } else if (data.type === 'tool_call_end') {
            if (toolCallMessage) {
              // Mark tool call as complete
              setMessages(prev => {
                return prev.map(msg => {
                  if (msg.id === toolCallMessage!.id) {
                    return { ...msg, isStreaming: false };
                  }
                  return msg;
                });
              });
            }
          } else if (data.type === 'tool_result_start') {
            // Start a new tool result message
            const toolResultMessage: Message = {
              id: generateMessageId('tool_result'),
              type: 'tool_result',
              content: '',
              timestamp: new Date(),
              isStreaming: true,
              metadata: {
                type: data.type
              }
            };
            setMessages(prev => [...prev, toolResultMessage]);
          } else if (data.type === 'tool_result') {
            // Update the latest tool result message
            setMessages(prev => {
              const lastToolResultIndex = prev.findIndex((msg, index) => 
                msg.type === 'tool_result' && index === prev.length - 1
              );
              if (lastToolResultIndex !== -1) {
                const updatedContent = prev[lastToolResultIndex].content + (data.token || '');
                return prev.map((msg, index) => {
                  if (index === lastToolResultIndex) {
                    return { ...msg, content: updatedContent };
                  }
                  return msg;
                });
              }
              return prev;
            });
          } else if (data.type === 'tool_result_end') {
            // Mark the latest tool result as complete
            setMessages(prev => {
              const lastToolResultIndex = prev.findIndex((msg, index) => 
                msg.type === 'tool_result' && index === prev.length - 1
              );
              if (lastToolResultIndex !== -1) {
                return prev.map((msg, index) => {
                  if (index === lastToolResultIndex) {
                    return { ...msg, isStreaming: false };
                  }
                  return msg;
                });
              }
              return prev;
            });
          } else if (data.type === 'response') {
            if (assistantMessage) {
              const updatedContent = assistantMessage.content + (data.token || '');
              assistantMessage.content = updatedContent;
              setMessages(prev => {
                return prev.map(msg => {
                  if (msg.id === assistantMessage!.id) {
                    return { ...msg, content: updatedContent };
                  }
                  return msg;
                });
              });
            }
          } else if (data.type === 'complete') {
            // Mark assistant message as complete
            if (assistantMessage) {
              setMessages(prev => {
                return prev.map(msg => {
                  if (msg.id === assistantMessage!.id) {
                    return { ...msg, isStreaming: false };
                  }
                  return msg;
                });
              });
            }
            cleanupTemporaryMessages();
          } else if (data.type === 'error') {
            const errorMessage: Message = {
              id: generateMessageId('error'),
              type: 'error',
              content: data.token || 'An error occurred',
              timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
          }
        },
        () => {
          setIsLoading(false);
        }
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      addSystemMessage(`❌ Error: ${errorMessage}`, 'error');
      setIsLoading(false);
    }
  };

  const getMessageStyle = (type: string) => {
    switch (type) {
      case 'user':
        return 'bg-blue-500 text-white ml-auto';
      case 'assistant':
        return 'bg-gray-100 text-gray-900';
      case 'thinking':
        return 'bg-yellow-50 text-black border-l-4 border-yellow-400';
      case 'tool_call':
        return 'bg-purple-50 text-purple-900 border-l-4 border-purple-400';
      case 'tool_result':
        return 'bg-indigo-50 text-indigo-900 border-l-4 border-indigo-400';
      case 'error':
        return 'bg-red-100 text-red-800 border-l-4 border-red-400';
      case 'system':
        return 'bg-green-100 text-green-800 border-l-4 border-green-400';
      default:
        return 'bg-gray-100 text-gray-900';
    }
  };

  const renderMessageContent = (message: Message) => {
    if (message.type === 'thinking') {
      if (message.isStreaming) {
        return (
          <div className="space-y-3">
            <ThinkingIndicator 
              message=""
              variant="detailed"
              className="w-full"
            />
            {message.content && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <StatusBadge status="thinking" />
                </div>
                <StreamingText 
                  content={message.content} 
                  isComplete={!message.isStreaming} 
                  typingSpeed={100}
                  minDisplayTime={1500}
                  className="text-sm text-gray-700"
                />
              </div>
            )}
          </div>
        );
      } else {
        return (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-2">
              <StatusBadge status="complete" />
              <span className="text-sm font-medium text-gray-600">Thought Process</span>
            </div>
            <div className="text-sm text-gray-700">{message.content}</div>
          </div>
        );
      }
    }

    if (message.type === 'tool_call') {
      return (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <StatusBadge status={message.isStreaming ? 'tool_call' : 'complete'} />
              <span className="text-sm font-medium text-purple-700">Function Call</span>
            </div>
            <span className="text-xs font-mono bg-purple-100 px-2 py-1 rounded border">
              {message.metadata?.tool_name || 'unknown'}
            </span>
          </div>
          {message.content && (
            <div className="bg-white border border-purple-200 rounded p-3">
              <StreamingText 
                content={message.content} 
                isComplete={!message.isStreaming} 
                typingSpeed={30}
                className="text-sm font-mono text-gray-800"
              />
            </div>
          )}
        </div>
      );
    }

    if (message.type === 'tool_result') {
      return (
        <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 space-y-3">
          <div className="flex items-center space-x-2">
            <StatusBadge status={message.isStreaming ? 'tool_result' : 'complete'} />
            <span className="text-sm font-medium text-indigo-700">Function Result</span>
          </div>
          {message.content && (
            <div className="bg-white border border-indigo-200 rounded p-3">
              <StreamingText 
                content={message.content} 
                isComplete={!message.isStreaming} 
                typingSpeed={25}
                className="text-sm text-gray-800"
              />
            </div>
          )}
        </div>
      );
    }

    if (message.type === 'assistant') {
      if (message.isStreaming) {
        return (
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <StatusBadge status="streaming" />
            </div>
            <StreamingText 
              content={message.content} 
              isComplete={!message.isStreaming} 
              typingSpeed={25}
              className="text-gray-800 leading-relaxed"
            />
          </div>
        );
      } else {
        return (
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <StatusBadge status="complete" />
            </div>
            <div className="text-gray-800 leading-relaxed">{message.content}</div>
          </div>
        );
      }
    }

    if (message.type === 'error') {
      return (
        <div className="space-y-2">
          <StatusBadge status="error" />
          <div className="text-red-700">{message.content}</div>
        </div>
      );
    }

    if (message.isStreaming) {
      return (
        <StreamingText 
          content={message.content} 
          isComplete={!message.isStreaming} 
          typingSpeed={30}
          className="text-gray-800"
        />
      );
    }

    return (
      <div className="text-gray-800">{message.content}</div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Connection Status */}
      <div className="p-2 border-b">
        <ConnectionStatus 
          isConnected={streamState.isConnected}
          isReconnecting={streamState.isReconnecting}
          retryCount={streamState.retryCount}
        />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`max-w-3xl p-3 rounded-lg ${getMessageStyle(message.type)} ${
              message.type === 'user' ? 'ml-auto' : 'mr-auto'
            }`}
          >
            <div className="text-sm opacity-70 mb-1">
              {message.type.charAt(0).toUpperCase() + message.type.slice(1)}
            </div>
            {renderMessageContent(message)}
            <div className="text-xs opacity-50 mt-2">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  );
};