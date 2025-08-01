'use client';

import ChatInterface from './components/ChatInterface';
import { useProvider } from './contexts/ProviderContext';
import { useSession } from './contexts/SessionContext';

export default function Home() {
  const { currentProvider, setCurrentProvider } = useProvider();
  const { setIsSessionActive, setNewSessionHandler } = useSession();
  
  const handleSessionStateChange = (isActive: boolean) => {
    setIsSessionActive(isActive);
  };
  
  const handleNewSessionRequest = (handler: () => void) => {
    setNewSessionHandler(handler);
  };
  
  return (
    <div className="h-full flex flex-col">
      {/* Master Page Content - Chat Interface as Main Sub-page */}
      <div className="flex-1 flex flex-col min-h-0">
        <ChatInterface 
          currentProvider={currentProvider}
          onProviderChange={setCurrentProvider}
          onSessionStateChange={handleSessionStateChange}
          onNewSessionRequest={handleNewSessionRequest}
        />
      </div>
    </div>
  );
}
