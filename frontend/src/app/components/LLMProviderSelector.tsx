'use client';

import { useState, useEffect } from 'react';

interface LLMProvider {
  name: string;
  isConfigured: boolean;
}

interface LLMProviderSelectorProps {
  onProviderChange: (provider: string) => void;
  currentProvider: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export default function LLMProviderSelector({ onProviderChange, currentProvider }: LLMProviderSelectorProps) {
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
  
  return (
    <div className="p-3 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
      <div className="flex flex-col">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">LLM Provider:</span>
          {isLoading && (
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          )}
        </div>
        
        <div className="flex flex-wrap gap-2">
          {providers.map(provider => (
            <button
              key={provider.name}
              onClick={() => handleProviderChange(provider.name)}
              disabled={!provider.isConfigured || isLoading}
              className={`
                px-3 py-1.5 text-sm rounded-lg flex items-center gap-1.5
                ${!provider.isConfigured ? 'opacity-50 cursor-not-allowed bg-gray-200 text-gray-500' : 
                  provider.name === currentProvider ? 'bg-blue-500 text-white' : 'bg-white hover:bg-gray-100 text-gray-800'}
                transition-colors
              `}
              title={!provider.isConfigured ? 'API key not configured' : `Switch to ${getProviderDisplay(provider.name).display}`}
            >
              <span>{getProviderDisplay(provider.name).icon}</span>
              <span>{getProviderDisplay(provider.name).display}</span>
            </button>
          ))}
        </div>
        
        {error && (
          <div className="mt-2 text-sm text-red-500">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}