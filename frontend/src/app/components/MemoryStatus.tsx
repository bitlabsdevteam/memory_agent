'use client';

interface MemoryInfo {
  session_id: string;
  message_count: number;
  messages: Array<{
    type: string;
    content: string;
  }>;
}

interface MemoryStatusProps {
  memoryInfo: MemoryInfo | null;
  onRefresh: () => void;
}

export default function MemoryStatus({ memoryInfo, onRefresh }: MemoryStatusProps) {
  if (!memoryInfo) {
    return (
      <div className="bg-gray-50 dark:bg-gray-700 px-4 py-2 border-b border-gray-200 dark:border-gray-600">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-300">Loading memory status...</span>
          <button
            onClick={onRefresh}
            className="text-blue-500 hover:text-blue-600 text-sm"
          >
            Refresh
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 dark:bg-gray-700 px-4 py-2 border-b border-gray-200 dark:border-gray-600">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-600 dark:text-gray-300">
              Memory: {memoryInfo.message_count} messages
            </span>
          </div>
          
          {memoryInfo.message_count > 0 && (
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Recent: {memoryInfo.messages.slice(-2).map(msg => 
                `${msg.type}: ${msg.content.substring(0, 30)}${msg.content.length > 30 ? '...' : ''}`
              ).join(' | ')}
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={onRefresh}
            className="text-blue-500 hover:text-blue-600 text-sm flex items-center space-x-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Refresh</span>
          </button>
        </div>
      </div>
    </div>
  );
}