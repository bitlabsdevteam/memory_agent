import React from 'react';
import { TypeAnimation } from 'react-type-animation';

interface TypingAnimationProps {
  text: string;
  speed?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 99;
  className?: string;
  onComplete?: () => void;
  showCursor?: boolean;
  delay?: number;
  smooth?: boolean;
}

export const TypingAnimation: React.FC<TypingAnimationProps> = ({
  text,
  speed = 50,
  className = '',
  onComplete,
  showCursor = true,
  delay = 0,
  smooth = true
}) => {
  const [isVisible, setIsVisible] = React.useState(delay === 0);
  
  React.useEffect(() => {
    if (delay > 0) {
      const timer = setTimeout(() => {
        setIsVisible(true);
      }, delay);
      return () => clearTimeout(timer);
    }
  }, [delay]);

  if (!isVisible) {
    return <span className={className}></span>;
  }

  return (
    <span className={`${className} ${smooth ? 'transition-opacity duration-300' : ''}`}>
      <TypeAnimation
        sequence={[
          text,
          () => onComplete?.()
        ]}
        wrapper="span"
        speed={speed}
        cursor={showCursor}
        repeat={0}
        style={{
          fontSize: 'inherit',
          lineHeight: 'inherit'
        }}
      />
    </span>
  );
};

// Streaming text component that builds up character by character
interface StreamingTextProps {
  content: string;
  isComplete: boolean;
  className?: string;
  typingSpeed?: number;
  minDisplayTime?: number;
}

export const StreamingText: React.FC<StreamingTextProps> = ({
  content,
  isComplete,
  className = '',
  typingSpeed = 30,
  minDisplayTime = 0
}) => {
  const [displayedContent, setDisplayedContent] = React.useState('');
  const [currentWordIndex, setCurrentWordIndex] = React.useState(0);
  const [startTime] = React.useState(Date.now());
  const [canComplete, setCanComplete] = React.useState(false);
  const words = React.useMemo(() => content.split(' '), [content]);

  React.useEffect(() => {
    // Check if minimum display time has passed
    const timeElapsed = Date.now() - startTime;
    if (timeElapsed >= minDisplayTime) {
      setCanComplete(true);
    } else {
      const timer = setTimeout(() => {
        setCanComplete(true);
      }, minDisplayTime - timeElapsed);
      return () => clearTimeout(timer);
    }
  }, [startTime, minDisplayTime]);

  React.useEffect(() => {
    if (isComplete && canComplete) {
      setDisplayedContent(content);
      return;
    }

    if (currentWordIndex < words.length) {
      const timer = setTimeout(() => {
        const wordsToShow = words.slice(0, currentWordIndex + 1);
        setDisplayedContent(wordsToShow.join(' '));
        setCurrentWordIndex(currentWordIndex + 1);
      }, typingSpeed * 10); // Slower for word-by-word

      return () => clearTimeout(timer);
    }
  }, [words, currentWordIndex, isComplete, canComplete, content, typingSpeed]);

  React.useEffect(() => {
    // Reset when content changes (new message)
    if (content.length < displayedContent.length) {
      setDisplayedContent('');
      setCurrentWordIndex(0);
    }
  }, [content, displayedContent.length]);

  return (
    <span className={className}>
      {displayedContent}
      {(!isComplete || !canComplete) && currentWordIndex < words.length && (
        <span className="animate-pulse">|</span>
      )}
    </span>
  );
};

// Enhanced thinking dots animation with modern styling
interface ThinkingDotsProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  color?: 'gray' | 'blue' | 'purple' | 'yellow';
  variant?: 'bounce' | 'pulse' | 'wave';
}

export const ThinkingDots: React.FC<ThinkingDotsProps> = ({ 
  className = '', 
  size = 'md',
  color = 'gray',
  variant = 'wave'
}) => {
  const sizeClasses = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-3 h-3'
  };

  const colorClasses = {
    gray: 'bg-gray-400',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    yellow: 'bg-yellow-500'
  };

  const baseClasses = `${sizeClasses[size]} ${colorClasses[color]} rounded-full`;

  if (variant === 'pulse') {
    return (
      <div className={`flex space-x-1 ${className}`}>
        <div className={`${baseClasses} animate-pulse`} style={{ animationDelay: '0ms' }}></div>
        <div className={`${baseClasses} animate-pulse`} style={{ animationDelay: '200ms' }}></div>
        <div className={`${baseClasses} animate-pulse`} style={{ animationDelay: '400ms' }}></div>
      </div>
    );
  }

  if (variant === 'bounce') {
    return (
      <div className={`flex space-x-1 ${className}`}>
        <div className={`${baseClasses} animate-bounce`} style={{ animationDelay: '0ms' }}></div>
        <div className={`${baseClasses} animate-bounce`} style={{ animationDelay: '150ms' }}></div>
        <div className={`${baseClasses} animate-bounce`} style={{ animationDelay: '300ms' }}></div>
      </div>
    );
  }

  // Wave animation (default)
  return (
    <div className={`flex space-x-1 items-center ${className}`}>
      <div 
        className={`${baseClasses} animate-pulse`} 
        style={{ 
          animationDelay: '0ms',
          animationDuration: '1.4s'
        }}
      ></div>
      <div 
        className={`${baseClasses} animate-pulse`} 
        style={{ 
          animationDelay: '0.2s',
          animationDuration: '1.4s'
        }}
      ></div>
      <div 
        className={`${baseClasses} animate-pulse`} 
        style={{ 
          animationDelay: '0.4s',
          animationDuration: '1.4s'
        }}
      ></div>
    </div>
  );
};

// Modern thinking indicator with avatar and status
interface ThinkingIndicatorProps {
  className?: string;
  message?: string;
  showAvatar?: boolean;
  variant?: 'compact' | 'detailed';
}

export const ThinkingIndicator: React.FC<ThinkingIndicatorProps> = ({
  className = '',
  message = '',
  showAvatar = true,
  variant = 'detailed'
}) => {
  if (variant === 'compact') {
    return (
      <div className={`flex items-center space-x-2 py-2 px-3 bg-gray-50 rounded-lg border ${className}`}>
        <ThinkingDots size="sm" color="gray" variant="wave" />
        <span className="text-sm text-gray-600 font-medium">{message}</span>
      </div>
    );
  }

  return (
    <div className={`flex items-start space-x-3 py-4 px-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200 shadow-sm ${className}`}>
      {showAvatar && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M9.504 1.132a1 1 0 01.992 0l1.75 1a1 1 0 11-.992 1.736L10 3.152l-1.254.716a1 1 0 11-.992-1.736l1.75-1zM5.618 4.504a1 1 0 01-.372 1.364L5.016 6l.23.132a1 1 0 11-.992 1.736L3 7.723V8a1 1 0 01-2 0V6a.996.996 0 01.52-.878l1.734-.99a1 1 0 011.364.372zm8.764 0a1 1 0 011.364-.372l1.734.99A.996.996 0 0118 6v2a1 1 0 11-2 0v-.277l-1.254.145a1 1 0 11-.992-1.736L14.984 6l-.23-.132a1 1 0 01-.372-1.364zm-7 4a1 1 0 011.364-.372L10 8.848l1.254-.716a1 1 0 11.992 1.736L11 10.723V12a1 1 0 11-2 0v-1.277l-1.246-.855a1 1 0 01-.372-1.364zM3 11a1 1 0 011 1v1.277l1.246.855a1 1 0 01-.992 1.736L3 15.723V17a1 1 0 01-2 0v-2a.996.996 0 01.52-.878L3 13.277V12a1 1 0 011-1zm14 0a1 1 0 011 1v1.277l1.48 1.145A.996.996 0 0118 15v2a1 1 0 11-2 0v-1.277l-1.254-.145a1 1 0 11-.992-1.736L15.016 14l-.23-.132A1 1 0 0115 12a1 1 0 011-1zm-6 2a1 1 0 01.372 1.364L11 14.5l-.372.136a1 1 0 11-.992-1.736L10 12.848l.372-.136A1 1 0 0111 13z" clipRule="evenodd" />
            </svg>
          </div>
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-700">{message}</span>
          <ThinkingDots size="sm" color="blue" variant="wave" />
        </div>
        <div className="mt-1">
          <div className="flex space-x-1">
            <div className="h-1 w-8 bg-blue-200 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
            <div className="h-1 w-6 bg-blue-200 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: '40%', animationDelay: '0.2s' }}></div>
            </div>
            <div className="h-1 w-4 bg-blue-200 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: '80%', animationDelay: '0.4s' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Connection status indicator
interface ConnectionStatusProps {
  isConnected: boolean;
  isReconnecting: boolean;
  retryCount: number;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isConnected,
  isReconnecting,
  retryCount
}) => {
  if (isConnected) {
    return (
      <div className="flex items-center space-x-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-full">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
        <span className="text-sm font-medium text-green-700">Connected</span>
      </div>
    );
  }

  if (isReconnecting) {
    return (
      <div className="flex items-center space-x-2 px-3 py-1.5 bg-yellow-50 border border-yellow-200 rounded-full">
        <div className="w-2 h-2 bg-yellow-500 rounded-full animate-spin"></div>
        <span className="text-sm font-medium text-yellow-700">Reconnecting... (attempt {retryCount})</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 px-3 py-1.5 bg-red-50 border border-red-200 rounded-full">
      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
      <span className="text-sm font-medium text-red-700">Disconnected</span>
    </div>
  );
};

// Status badge component for different message states
interface StatusBadgeProps {
  status: 'thinking' | 'streaming' | 'complete' | 'error' | 'tool_call' | 'tool_result';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const statusConfig = {
    thinking: {
      icon: '🤔',
      label: 'Thinking',
      bgColor: 'bg-yellow-100',
      textColor: 'text-yellow-800',
      borderColor: 'border-yellow-200'
    },
    streaming: {
      icon: '✍️',
      label: 'Writing',
      bgColor: 'bg-blue-100',
      textColor: 'text-blue-800',
      borderColor: 'border-blue-200'
    },
    complete: {
      icon: '✅',
      label: 'Complete',
      bgColor: 'bg-green-100',
      textColor: 'text-green-800',
      borderColor: 'border-green-200'
    },
    error: {
      icon: '❌',
      label: 'Error',
      bgColor: 'bg-red-100',
      textColor: 'text-red-800',
      borderColor: 'border-red-200'
    },
    tool_call: {
      icon: '🔧',
      label: 'Using Tool',
      bgColor: 'bg-purple-100',
      textColor: 'text-purple-800',
      borderColor: 'border-purple-200'
    },
    tool_result: {
      icon: '📋',
      label: 'Tool Result',
      bgColor: 'bg-indigo-100',
      textColor: 'text-indigo-800',
      borderColor: 'border-indigo-200'
    }
  };

  const config = statusConfig[status];

  return (
    <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full border text-xs font-medium ${config.bgColor} ${config.textColor} ${config.borderColor} ${className}`}>
      <span>{config.icon}</span>
      <span>{config.label}</span>
      {(status === 'thinking' || status === 'streaming' || status === 'tool_call') && (
        <ThinkingDots size="sm" color={status === 'thinking' ? 'yellow' : status === 'tool_call' ? 'purple' : 'blue'} variant="pulse" />
      )}
    </div>
  );
};