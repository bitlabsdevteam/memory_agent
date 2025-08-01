import React, { useState, useCallback } from 'react';
import { useChat } from 'ai/react';

interface UseAIChatOptions {
  sessionId: string;
  apiUrl?: string;
  onThinking?: (content: string) => void;
  onThinkingEnd?: () => void;
  onError?: (error: Error) => void;
}

interface ParsedMessage {
  id: string;
  role: 'user' | 'assistant' | 'thinking' | 'system';
  content: string;
  timestamp: Date;
  isThinking?: boolean;
}

export const useAIChat = (options: UseAIChatOptions) => {
  const {
    sessionId,
    apiUrl = '/api/v1/chat',
    onThinking,
    onThinkingEnd,
    onError
  } = options;

  const [thinkingContent, setThinkingContent] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [parsedMessages, setParsedMessages] = useState<ParsedMessage[]>([]);

  const {
    messages,
    input,
    handleInputChange,
    handleSubmit: originalHandleSubmit,
    isLoading,
    error,
    reload,
    stop
  } = useChat({
    api: apiUrl,
    body: {
      session_id: sessionId
    },
    onResponse: async (response) => {
      if (!response.ok) {
        const errorText = await response.text();
        onError?.(new Error(`HTTP ${response.status}: ${errorText}`));
      }
    },
    onFinish: () => {
      if (isThinking) {
        setIsThinking(false);
        onThinkingEnd?.();
      }
    },
    onError: (error) => {
      onError?.(error);
    },
    // Custom stream processing
    streamMode: 'text',
    experimental_onFunctionCall: undefined
  });

  // Parse streaming content to extract thinking vs response
  const parseStreamContent = useCallback((content: string) => {
    const thinkingRegex = /<thinking>([\s\S]*?)<\/thinking>/g;
    const matches = [...content.matchAll(thinkingRegex)];
    
    if (matches.length > 0) {
      const thinkingText = matches.map(match => match[1]).join('\n');
      const responseText = content.replace(thinkingRegex, '').trim();
      
      if (thinkingText !== thinkingContent) {
        setThinkingContent(thinkingText);
        setIsThinking(true);
        onThinking?.(thinkingText);
      }
      
      return responseText;
    }
    
    return content;
  }, [thinkingContent, onThinking]);

  // Enhanced submit handler with thinking support
  const handleSubmit = useCallback((e: React.FormEvent<HTMLFormElement>) => {
    setThinkingContent('');
    setIsThinking(false);
    originalHandleSubmit(e);
  }, [originalHandleSubmit]);

  // Convert messages to parsed format
  const convertToParsedMessages = useCallback((): ParsedMessage[] => {
    return messages.map(msg => ({
      id: msg.id,
      role: msg.role as 'user' | 'assistant',
      content: msg.role === 'assistant' ? parseStreamContent(msg.content) : msg.content,
      timestamp: new Date(msg.createdAt || Date.now())
    }));
  }, [messages, parseStreamContent]);

  // Update parsed messages when messages change
  React.useEffect(() => {
    setParsedMessages(convertToParsedMessages());
  }, [convertToParsedMessages]);

  return {
    messages: parsedMessages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error,
    reload,
    stop,
    thinkingContent,
    isThinking,
    // Additional utilities
    clearMessages: () => setParsedMessages([]),
    addSystemMessage: (content: string) => {
      const systemMessage: ParsedMessage = {
        id: `system-${Date.now()}`,
        role: 'system',
        content,
        timestamp: new Date()
      };
      setParsedMessages(prev => [...prev, systemMessage]);
    }
  };
};

// Hook for advanced streaming with custom protocols
export const useAdvancedStreaming = () => {
  const [connectionState, setConnectionState] = useState<{
    status: 'disconnected' | 'connecting' | 'connected' | 'reconnecting';
    retryCount: number;
    lastError?: Error;
  }>({ status: 'disconnected', retryCount: 0 });

  const createStreamWithRetry = useCallback(async (
    url: string,
    options: RequestInit,
    onData: (data: Record<string, unknown>) => void,
    maxRetries = 3
  ) => {
    let retryCount = 0;
    
    const attemptConnection = async (): Promise<void> => {
      try {
        setConnectionState(prev => ({ 
          ...prev, 
          status: retryCount > 0 ? 'reconnecting' : 'connecting',
          retryCount 
        }));

        const response = await fetch(url, options);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        setConnectionState(prev => ({ ...prev, status: 'connected', retryCount: 0 }));

        const reader = response.body?.getReader();
        if (!reader) throw new Error('No response body');

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                onData(data);
              } catch (e) {
                console.warn('Failed to parse SSE data:', e);
              }
            }
          }
        }
      } catch (error) {
        const err = error instanceof Error ? error : new Error('Unknown error');
        setConnectionState(prev => ({ ...prev, lastError: err }));
        
        if (retryCount < maxRetries && !err.message.includes('AbortError')) {
          retryCount++;
          const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 10000); // Exponential backoff, max 10s
          await new Promise(resolve => setTimeout(resolve, delay));
          return attemptConnection();
        } else {
          setConnectionState(prev => ({ ...prev, status: 'disconnected' }));
          throw err;
        }
      }
    };

    return attemptConnection();
  }, []);

  return {
    connectionState,
    createStreamWithRetry
  };
};