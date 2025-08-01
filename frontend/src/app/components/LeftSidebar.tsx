'use client';

import { useState } from 'react';
import LLMProviderDropdown from './LLMProviderDropdown';

interface LeftSidebarProps {
  onProviderChange?: (provider: string) => void;
  currentProvider?: string;
  isSessionActive?: boolean;
  onNewSession?: () => void;
}

export default function LeftSidebar({ onProviderChange, currentProvider = 'google_gemini', isSessionActive = false, onNewSession }: LeftSidebarProps) {
  const [activeItem, setActiveItem] = useState('chat');

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800">Trip Advisor</h2>
      </div>

      {/* LLM Provider Selector */}
      <div className="border-b border-gray-200">
        <div className="p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">LLM Provider</h3>
          {currentProvider && (
            <div className="mb-2 text-sm text-gray-600">
              Connected to: <span className="font-medium">{currentProvider}</span>
            </div>
          )}
          <LLMProviderDropdown 
            onProviderChange={onProviderChange || (() => {})} 
            currentProvider={currentProvider}
            isSessionActive={isSessionActive}
            onNewSession={onNewSession}
          />
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 p-2">
        <div className="space-y-1">
          {/* Navigation items can be added here in the future */}
        </div>
      </nav>

      {/* Sidebar Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center space-x-3 text-sm text-gray-600">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span>Connected</span>
        </div>
      </div>
    </aside>
  );
}