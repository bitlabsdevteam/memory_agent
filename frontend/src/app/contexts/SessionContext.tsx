'use client';

import { createContext, useContext, useState, ReactNode, useCallback } from 'react';

// Create context for session state
interface SessionContextType {
  isSessionActive: boolean;
  setIsSessionActive: (active: boolean) => void;
  newSessionHandler: (() => void) | null;
  setNewSessionHandler: (handler: (() => void) | null) => void;
  handleNewSession: () => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

interface SessionProviderProps {
  children: ReactNode;
}

export const SessionProvider = ({ children }: SessionProviderProps) => {
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [newSessionHandler, setNewSessionHandler] = useState<(() => void) | null>(null);
  
  const handleNewSession = useCallback(() => {
    if (newSessionHandler) {
      newSessionHandler();
    }
  }, [newSessionHandler]);
  
  const setNewSessionHandlerSafe = useCallback((handler: (() => void) | null) => {
    setNewSessionHandler(() => handler);
  }, []);
  
  return (
    <SessionContext.Provider value={{ 
      isSessionActive, 
      setIsSessionActive, 
      newSessionHandler, 
      setNewSessionHandler: setNewSessionHandlerSafe, 
      handleNewSession 
    }}>
      {children}
    </SessionContext.Provider>
  );
};