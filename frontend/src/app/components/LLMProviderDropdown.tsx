'use client';

import { useState, useEffect } from 'react';

interface LLMProvider {
  name: string;
  isConfigured: boolean;
}

interface LLMProviderDropdownProps {
  onProviderChange: (provider: string) => void;
  currentProvider: string;
  isSessionActive?: boolean;
  onNewSession?: () => void;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export default function LLMProviderDropdown({ onProviderChange, currentProvider, isSessionActive = false, onNewSession }: LLMProviderDropdownProps) {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch available providers on component mount
  useEffect(() => {
    fetchProviders();
  }, []);
  
  const fetchProviders = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/llm/providers`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Transform the data into the format we need
      const providerList: LLMProvider[] = Object.keys(data.configured_providers).map(name => ({
        name,
        isConfigured: data.configured_providers[name]
      }));
      
      setProviders(providerList);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch providers');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleProviderChange = async (providerName: string) => {
    // Prevent provider switching if session is active
    if (isSessionActive) {
      setError('Cannot switch provider during an active session. Please start a new session to change providers.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/llm/switch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ provider: providerName })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Failed to switch provider: ${response.status}`);
      }
      
      onProviderChange(providerName);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to switch provider');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Map provider names to display names and icons
  const getProviderDisplay = (name: string) => {
    switch (name) {
      case 'google_gemini':
        return { display: 'Google Gemini', icon: '🌀' };
      case 'openai':
        return { display: 'OpenAI GPT-4o', icon: '🧠' };
      case 'groq':
        return { display: 'Groq DeepSeek', icon: '⚡' };
      case 'perplexity':
        return { display: 'Perplexity AI', icon: '🔍' };
      default:
        return { display: name, icon: '🤖' };
    }
  };
  
  const currentProviderDisplay = getProviderDisplay(currentProvider);
  
  return (
    <div className="w-full">
      <div className="relative">
        <select
          value={currentProvider}
          onChange={(e) => handleProviderChange(e.target.value)}
          disabled={isLoading || isSessionActive}
          className={`w-full px-3 py-2 text-sm text-black bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed appearance-none ${
            isSessionActive ? 'bg-gray-100 cursor-not-allowed' : ''
          }`}
        >
          {providers.map(provider => {
            const display = getProviderDisplay(provider.name);
            return (
              <option
                key={provider.name}
                value={provider.name}
                disabled={!provider.isConfigured}
              >
                {display.icon} {display.display}
                {!provider.isConfigured ? ' (Not Configured)' : ''}
              </option>
            );
          })}
        </select>
        
        {/* Custom dropdown arrow */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          ) : isSessionActive ? (
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          )}
        </div>
      </div>
      
      {/* Session active warning */}
      {isSessionActive && (
        <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
          <div className="flex items-center justify-between">
            <span className="text-yellow-700">
              🔒 Provider locked during active session
            </span>
            {onNewSession && (
              <button
                onClick={onNewSession}
                className="text-blue-600 hover:text-blue-800 underline ml-2"
              >
                New Session
              </button>
            )}
          </div>
        </div>
      )}
      
      {error && (
        <div className="mt-2 text-xs text-red-500">
          {error}
        </div>
      )}
    </div>
  );
}