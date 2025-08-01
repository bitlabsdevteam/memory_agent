'use client';

import { useState } from 'react';

interface SessionControlsProps {
  sessionId: string;
  onSessionChange: (sessionId: string) => void;
  onClearMemory: () => void;
}

export default function SessionControls({ sessionId, onSessionChange, onClearMemory }: SessionControlsProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [newSessionId, setNewSessionId] = useState(sessionId);

  const handleSessionUpdate = () => {
    if (newSessionId.trim() && newSessionId !== sessionId) {
      onSessionChange(newSessionId.trim());
    }
    setIsEditing(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSessionUpdate();
    } else if (e.key === 'Escape') {
      setNewSessionId(sessionId);
      setIsEditing(false);
    }
  };

  return (
    <div className="flex items-center space-x-3" style={{display: 'none'}}>
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium">Session:</span>
        {isEditing ? (
          <input
            type="text"
            value={newSessionId}
            onChange={(e) => setNewSessionId(e.target.value)}
            onBlur={handleSessionUpdate}
            onKeyPress={handleKeyPress}
            className="px-2 py-1 text-sm bg-white/20 border border-white/30 rounded text-white placeholder-white/70 focus:outline-none focus:ring-1 focus:ring-white/50"
            placeholder="Session ID"
            autoFocus
          />
        ) : (
          <button
            onClick={() => setIsEditing(true)}
            className="px-2 py-1 text-sm bg-white/20 hover:bg-white/30 rounded transition-colors"
          >
            {sessionId}
          </button>
        )}
      </div>
      
      <div className="flex space-x-2">
        <button
          onClick={onClearMemory}
          className="px-3 py-1 text-sm bg-red-500/80 hover:bg-red-500 rounded transition-colors flex items-center space-x-1"
          title="Clear Memory"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          <span>Clear</span>
        </button>
        
        <button
          onClick={() => {
            const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            onSessionChange(newSessionId);
          }}
          className="px-3 py-1 text-sm bg-green-500/80 hover:bg-green-500 rounded transition-colors flex items-center space-x-1"
          title="New Session"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>New</span>
        </button>
      </div>
    </div>
  );
}