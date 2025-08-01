'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

// Create context for provider state
interface ProviderContextType {
  currentProvider: string;
  setCurrentProvider: (provider: string) => void;
}

const ProviderContext = createContext<ProviderContextType | undefined>(undefined);

export const useProvider = () => {
  const context = useContext(ProviderContext);
  if (!context) {
    throw new Error('useProvider must be used within a ProviderContext');
  }
  return context;
};

interface ProviderProviderProps {
  children: ReactNode;
}

export const ProviderProvider = ({ children }: ProviderProviderProps) => {
  const [currentProvider, setCurrentProvider] = useState('google_gemini');
  
  return (
    <ProviderContext.Provider value={{ currentProvider, setCurrentProvider }}>
      {children}
    </ProviderContext.Provider>
  );
};