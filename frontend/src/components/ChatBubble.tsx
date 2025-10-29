// ChatBubble component - displays individual chat messages
// Shows message from user or assistant with appropriate styling

import type { ChatMessage } from '../types/chat';

interface ChatBubbleProps {
  message: ChatMessage;
}

export default function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === 'user';
  
  // Format timestamp for display
  const formatTime = (timestamp: Date): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] space-y-2 ${isUser ? 'text-white' : 'text-white/70'}`}>
        <p className="text-sm leading-relaxed whitespace-pre-line">
          {message.content}
        </p>
        <span className="block text-[10px] uppercase tracking-[0.25em] text-white/40">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}

