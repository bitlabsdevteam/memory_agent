import { useState, useRef, useCallback } from 'react';

interface StreamData {
  type: string;
  token?: string;
  [key: string]: unknown;
}

interface StreamOptions {
  maxRetries?: number;
  retryDelay?: number;
  onReconnect?: () => void;
  onError?: (error: Error) => void;
}

interface StreamState {
  isConnected: boolean;
  isReconnecting: boolean;
  retryCount: number;
  error: Error | null;
}

export const useEnhancedStreaming = (options: StreamOptions = {}) => {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    onReconnect,
    onError
  } = options;

  const [streamState, setStreamState] = useState<StreamState>({
    isConnected: false,
    isReconnecting: false,
    retryCount: 0,
    error: null
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const cleanup = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
  }, []);

  const attemptReconnection = useCallback(async (
    streamFunction: () => Promise<void>,
    currentRetryCount: number
  ) => {
    if (currentRetryCount >= maxRetries) {
      setStreamState(prev => ({
        ...prev,
        isReconnecting: false,
        error: new Error(`Failed to reconnect after ${maxRetries} attempts`)
      }));
      return;
    }

    setStreamState(prev => ({
      ...prev,
      isReconnecting: true,
      retryCount: currentRetryCount + 1
    }));

    retryTimeoutRef.current = setTimeout(async () => {
      try {
        await streamFunction();
        setStreamState(prev => ({
          ...prev,
          isConnected: true,
          isReconnecting: false,
          retryCount: 0,
          error: null
        }));
        onReconnect?.();
      } catch (error) {
        console.warn(`Reconnection attempt ${currentRetryCount + 1} failed:`, error);
        await attemptReconnection(streamFunction, currentRetryCount + 1);
      }
    }, retryDelay * Math.pow(2, currentRetryCount)); // Exponential backoff
  }, [maxRetries, retryDelay, onReconnect]);

  const createResilientStream = useCallback(async (
    url: string,
    options: RequestInit,
    onData: (data: StreamData) => void,
    onComplete?: () => void
  ) => {
    cleanup();
    abortControllerRef.current = new AbortController();

    const streamFunction = async () => {
      const response = await fetch(url, {
        ...options,
        signal: abortControllerRef.current?.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      setStreamState(prev => ({ ...prev, isConnected: true, error: null }));

      const decoder = new TextDecoder();
      let buffer = '';

      try {
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
                console.error('Error parsing SSE data:', e);
              }
            }
          }
        }
        onComplete?.();
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          return; // Expected abortion
        }
        throw error;
      }
    };

    try {
      await streamFunction();
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Unknown streaming error');
      setStreamState(prev => ({ ...prev, isConnected: false, error: err }));
      onError?.(err);
      
      // Attempt reconnection for network errors
      if (err.message.includes('fetch') || err.message.includes('network')) {
        await attemptReconnection(streamFunction, 0);
      }
    }
  }, [cleanup, attemptReconnection, onError]);

  const disconnect = useCallback(() => {
    cleanup();
    setStreamState({
      isConnected: false,
      isReconnecting: false,
      retryCount: 0,
      error: null
    });
  }, [cleanup]);

  return {
    streamState,
    createResilientStream,
    disconnect
  };
};