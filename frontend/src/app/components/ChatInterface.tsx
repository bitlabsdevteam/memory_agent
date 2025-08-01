'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import MemoryStatus from './MemoryStatus';
import SessionControls from './SessionControls';
import { useEnhancedStreaming } from '../hooks/useEnhancedStreaming';
import { ConnectionStatus, ThinkingDots } from './TypingAnimation';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'action' | 'observation' | 'error' | 'action_input' | 'final_answer_header' | 'thinking';
  content: string;
  timestamp: Date;
  isTemporary?: boolean; // Flag for temporary messages like thinking
  metadata?: {
    isThinking?: boolean;
    fadeOut?: boolean;
    [key: string]: any;
  };
}

interface MemoryInfo {
  session_id: string;
  message_count: number;
  messages: Array<{
    type: string;
    content: string;
  }>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

// Enhanced logging for debugging
const logDebug = (message: string, data?: any) => {
  console.log(`[ChatInterface Debug] ${message}`, data || '');
};

const logError = (message: string, error?: any) => {
  console.error(`[ChatInterface Error] ${message}`, error || '');
};

// Log API configuration on load
console.log('[ChatInterface] API Configuration:', {
  API_BASE_URL,
  NODE_ENV: process.env.NODE_ENV,
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL
});

interface ChatInterfaceProps {
  onProviderChange?: (provider: string) => void;
  currentProvider?: string;
  onSessionStateChange?: (isActive: boolean) => void;
  onNewSessionRequest?: (handler: () => void) => void;
}

export default function ChatInterface({ onProviderChange, currentProvider: propCurrentProvider, onSessionStateChange, onNewSessionRequest }: ChatInterfaceProps = {}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('default');
  const [isConnected, setIsConnected] = useState(false);
  const [memoryInfo, setMemoryInfo] = useState<MemoryInfo | null>(null);
  const [currentProvider, setCurrentProvider] = useState(propCurrentProvider || 'google_gemini');
  const [isSessionActive, setIsSessionActive] = useState(false);
  
  // Enhanced streaming with network resilience
  const { streamState, createResilientStream, disconnect } = useEnhancedStreaming({
    maxRetries: 3,
    retryDelay: 1000,
    onReconnect: () => {
      addSystemMessage('🔄 Connection restored', 'assistant');
      setIsConnected(true);
    },
    onError: (error) => {
      addSystemMessage(`❌ Streaming error: ${error.message}`, 'error');
      setIsConnected(false);
    }
  });
  
  // Update current provider when prop changes
  useEffect(() => {
    if (propCurrentProvider && propCurrentProvider !== currentProvider) {
      setCurrentProvider(propCurrentProvider);
    }
  }, [propCurrentProvider, currentProvider]);
  
  // Handle provider change
  const handleProviderChange = useCallback((provider: string) => {
    setCurrentProvider(provider);
    addSystemMessage(`🔄 Switched to ${provider} provider`, 'assistant');
    onProviderChange?.(provider);
  }, [onProviderChange]);

  // Handle new session creation
  const handleNewSession = useCallback(() => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    setMessages([]);
    setIsSessionActive(false);
    addSystemMessage(`🆕 Started new session: ${newSessionId.slice(-8)}`, 'assistant');
    localStorage.setItem('chatSessionId', newSessionId);
  }, []);
  const abortControllerRef = useRef<AbortController | null>(null);
  const messageIdCounter = useRef(0);
  
  // Generate unique message ID
  const generateMessageId = useCallback((type: string) => {
    messageIdCounter.current += 1;
    return `${Date.now()}_${type}_${messageIdCounter.current}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Initialize session ID from localStorage on client side
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('chatSessionId');
      if (stored) {
        setSessionId(stored);
      } else {
        const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        setSessionId(newSessionId);
        localStorage.setItem('chatSessionId', newSessionId);
      }
    }
  }, []);

  // Track session activity based on messages
  useEffect(() => {
    const hasUserMessages = messages.some(msg => msg.type === 'user');
    setIsSessionActive(hasUserMessages);
    onSessionStateChange?.(hasUserMessages);
  }, [messages, onSessionStateChange]);

  // Provide new session handler to parent
  useEffect(() => {
    onNewSessionRequest?.(handleNewSession);
  }, [handleNewSession, onNewSessionRequest]);

  // Health check on component mount
  useEffect(() => {
    if (sessionId && sessionId !== 'default') {
      checkHealth();
      fetchMemoryStatus();
      fetchCurrentProvider();
    }
  }, [sessionId]);

  // Initial connection check after component mounts
  useEffect(() => {
    const timer = setTimeout(() => {
      // Only run if sessionId is properly set
      if (sessionId && sessionId !== 'default') {
        checkHealth();
        fetchMemoryStatus();
        fetchCurrentProvider();
      }
    }, 500); // Increased delay to ensure session ID is properly set
    
    return () => clearTimeout(timer);
  }, [sessionId]); // Keep only sessionId dependency to avoid re-render issues

  // Save session ID to localStorage whenever it changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('chatSessionId', sessionId);
    }
  }, [sessionId]);

  const checkHealth = async () => {
    const healthUrl = `${API_BASE_URL}/api/v1/health`;
    logDebug('Starting health check', { url: healthUrl });
    
    try {
      const response = await fetch(healthUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        mode: 'cors'
      });
      
      logDebug('Health check response received', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        headers: Object.fromEntries(response.headers.entries())
      });
      
      if (response.ok) {
        const data = await response.text();
        logDebug('Health check successful', { responseData: data });
        setIsConnected(true);
        addSystemMessage('✅ Connected to backend server', 'assistant');
      } else {
        logError('Health check failed', { status: response.status, statusText: response.statusText });
        setIsConnected(false);
        addSystemMessage(`❌ Health check failed - server responded with ${response.status}`, 'error');
      }
    } catch (error) {
      logError('Health check error', error);
      setIsConnected(false);
      addSystemMessage(`❌ Connection error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  const fetchMemoryStatus = async () => {
    // Don't fetch if sessionId is not properly initialized
    if (!sessionId || sessionId === 'default') {
      console.log('Skipping memory status fetch - sessionId not ready:', sessionId);
      return;
    }
    
    try {
      console.log('Fetching memory status for session:', sessionId);
      const url = `${API_BASE_URL}/api/v1/memory/status/${sessionId}`;
      console.log('Request URL:', url);
      
      // Add timeout and more detailed error handling
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, 30000); // 30 second timeout (increased from 10 seconds)
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        mode: 'cors',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (response.ok) {
        const data = await response.json();
        console.log('Memory status data:', data);
        setMemoryInfo(data);
      } else {
        const errorText = await response.text();
        console.error('Memory status request failed with status:', response.status);
        console.error('Error response body:', errorText);
      }
    } catch (error) {
      // Only log errors that are not intentional aborts
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Memory status request was aborted (likely due to timeout)');
        // Set a fallback memory info to prevent UI issues
        setMemoryInfo({
          session_id: sessionId,
          message_count: 0,
          messages: []
        });
        return; // Don't treat timeout as an error
      }
      
      console.error('Error fetching memory status:', error);
      if (error instanceof Error) {
        console.error('Error details:', {
          message: error.message,
          name: error.name,
          stack: error.stack
        });
        
        if (error.message.includes('Failed to fetch')) {
          console.error('Network error - check if backend is running on port 5001');
        }
      }
      
      // Set fallback memory info on any error
      setMemoryInfo({
        session_id: sessionId,
        message_count: 0,
        messages: []
      });
    }
  };
  
  const fetchCurrentProvider = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/llm/providers`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        mode: 'cors'
      });
      if (response.ok) {
        const data = await response.json();
        setCurrentProvider(data.current_provider);
      }
    } catch (error) {
      console.error('Error fetching current provider:', error);
    }
  };

  const addSystemMessage = (content: string, type: 'assistant' | 'error' = 'assistant') => {
    const message: Message = {
      id: generateMessageId('system'),
      type,
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
  };
  
  // Clean up temporary messages (like thinking messages)
  const cleanupTemporaryMessages = useCallback(() => {
    setMessages(prev => prev.filter(msg => !msg.isTemporary));
  }, []);

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) {
      logDebug('Message send blocked', { hasContent: !!content.trim(), isLoading });
      return;
    }

    logDebug('Starting message send', { content: content.trim(), sessionId });

    // Clean up any existing temporary messages
    cleanupTemporaryMessages();

    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Add user message
    const userMessage: Message = {
      id: generateMessageId('user'),
      type: 'user',
      content: content.trim(),
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    let thinkingMessage: Message | null = null;
    let assistantMessage: Message | null = null;

    try {
      const chatUrl = `${API_BASE_URL}/api/v1/chat`;
      const requestBody = {
        message: content,
        session_id: sessionId
      };
      
      logDebug('Creating resilient stream', {
        url: chatUrl,
        requestBody,
        isConnected
      });
      
      await createResilientStream(
        chatUrl,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(requestBody)
        },
        (data) => {
          logDebug('Received streaming data', { type: data.type, hasToken: !!data.token });
          
          if (data.type === 'thinking_start') {
            if (!thinkingMessage) {
              thinkingMessage = {
                id: generateMessageId('thinking'),
                type: 'thinking',
                content: '',
                timestamp: new Date(),
                isTemporary: true
              };
              setMessages(prev => [...prev, thinkingMessage!]);
            }
          } else if (data.type === 'thinking') {
            if (thinkingMessage) {
              const updatedContent = thinkingMessage.content + data.token;
              // Store the raw content but don't display it - MessageList will show "Thinking..." indicator
              thinkingMessage.content = updatedContent;
              setMessages(prev => {
                return prev.map(msg => {
                  if (msg.id === thinkingMessage!.id) {
                    return { ...msg, content: '', metadata: { ...(msg.metadata || {}), isThinking: true } };
                  }
                  return msg;
                });
              });
            }
          } else if (data.type === 'thinking_end') {
            // Add fade-out class to thinking message and schedule removal
            if (thinkingMessage) {
              setMessages(prev => {
                return prev.map(msg => {
                  if (msg.id === thinkingMessage!.id) {
                    return { ...msg, metadata: { ...(msg.metadata || {}), fadeOut: true } };
                  }
                  return msg;
                });
              });
              
              // Remove thinking message after fade animation
              setTimeout(() => {
                setMessages(prev => prev.filter(msg => msg.id !== thinkingMessage?.id));
              }, 1500); // Increased delay for fade animation
            }
            // Prepare for response
            assistantMessage = {
              id: generateMessageId('assistant'),
              type: 'assistant',
              content: '',
              timestamp: new Date()
            };
            setMessages(prev => [...prev, assistantMessage!]);
          } else if (data.type === 'response') {
            // Create assistant message if it doesn't exist (fallback)
            if (!assistantMessage) {
              assistantMessage = {
                id: generateMessageId('assistant'),
                type: 'assistant',
                content: '',
                timestamp: new Date()
              };
              setMessages(prev => [...prev, assistantMessage!]);
            }
            
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
          } else if (data.type === 'action') {
            const actionMessage: Message = {
              id: generateMessageId('action'),
              type: 'action',
              content: data.token || '',
              timestamp: new Date()
            };
            setMessages(prev => [...prev, actionMessage]);
          } else if (data.type === 'action_input') {
            const actionInputMessage: Message = {
              id: generateMessageId('action_input'),
              type: 'action_input',
              content: data.token || '',
              timestamp: new Date()
            };
            setMessages(prev => [...prev, actionInputMessage]);
          } else if (data.type === 'observation') {
            const observationMessage: Message = {
              id: generateMessageId('observation'),
              type: 'observation',
              content: data.token || '',
              timestamp: new Date()
            };
            setMessages(prev => [...prev, observationMessage]);
          } else if (data.type === 'final_answer_header') {
            const finalAnswerMessage: Message = {
              id: generateMessageId('final_answer_header'),
              type: 'final_answer_header',
              content: data.token || '',
              timestamp: new Date()
            };
            setMessages(prev => [...prev, finalAnswerMessage]);
          } else if (data.type === 'error') {
            if (assistantMessage) {
              const updatedContent = assistantMessage.content + (data.token || '');
              assistantMessage.content = updatedContent;
              setMessages(prev => {
                return prev.map(msg => {
                  if (msg.id === assistantMessage!.id) {
                    return { ...msg, content: updatedContent, type: 'error' };
                  }
                  return msg;
                });
              });
            } else {
              const errorMessage: Message = {
                id: generateMessageId('error'),
                type: 'error',
                content: data.token || '',
                timestamp: new Date()
              };
              setMessages(prev => [...prev, errorMessage]);
            }
          } else if (data.type === 'complete') {
            cleanupTemporaryMessages();
          }
        },
        () => {
          logDebug('Streaming completed successfully');
          setIsLoading(false);
          // Add a delay before fetching memory status to ensure backend has stored the response
          setTimeout(() => {
            logDebug('Fetching memory status after completion');
            fetchMemoryStatus();
          }, 2000); // Wait 2 seconds before refreshing memory
        }
      );
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      logError('Streaming error occurred', error);
      addSystemMessage(`Streaming error: ${errorMessage}`, 'error');
      setIsLoading(false);
    }
  };

  const clearMemory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/memory/clear/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        mode: 'cors'
      });
      if (response.ok) {
        setMessages([]);
        addSystemMessage('🧹 Memory cleared for this session', 'assistant');
        fetchMemoryStatus();
      }
    } catch (error) {
      addSystemMessage('Error clearing memory', 'error');
    }
  };

  const updateSession = (newSessionId: string) => {
    setSessionId(newSessionId);
    setMessages([]);
    setIsSessionActive(false);
    addSystemMessage(`📝 Switched to session: ${newSessionId}`, 'assistant');
    // Session ID will be automatically saved to localStorage via useEffect
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Control Panel */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <ConnectionStatus 
                isConnected={isConnected}
                isReconnecting={streamState.isReconnecting}
                retryCount={streamState.retryCount}
              />
              <div className="h-4 w-px bg-gray-300"></div>
              <span className="text-sm text-gray-600">Session: {sessionId.slice(-8)}</span>
            </div>
            <SessionControls 
              sessionId={sessionId}
              onSessionChange={updateSession}
              onClearMemory={clearMemory}
            />
          </div>
          
          {/* Memory Status */}
          <MemoryStatus memoryInfo={memoryInfo} onRefresh={fetchMemoryStatus} />
        </div>
      </div>

      {/* Main Chat Area - Scrollable Sub-page */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="max-w-4xl mx-auto w-full h-full flex flex-col">
          {/* Scrollable Messages Area */}
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            {/* Example Prompts - Only shown when no messages */}
            {messages.length === 0 && (
              <div className="p-6 flex-shrink-0">
                <h3 className="text-lg font-semibold mb-4 text-gray-800">Try asking about:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {[
                    "What's the weather like in Paris?",
                    "What time is it in Tokyo?",
                    "Tell me about London",
                    "Plan my visit to New York"
                  ].map((example, index) => (
                    <button
                      key={index}
                      onClick={() => sendMessage(example)}
                      className="text-left p-4 bg-white hover:bg-blue-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-all text-sm text-gray-700 hover:text-blue-700 shadow-sm"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Messages List - Scrollable */}
            <div className="flex-1 min-h-0">
              <MessageList messages={messages} isLoading={isLoading} />
            </div>
          </div>

          {/* Fixed Input Area */}
          <div className="flex-shrink-0 border-t border-gray-200 bg-white">
            <div className="p-4">
              <MessageInput 
                onSendMessage={sendMessage}
                disabled={!isConnected || isLoading}
                isLoading={isLoading}
              />
            </div>
          </div>
        </div>
       </div>
     </div>
   );
}