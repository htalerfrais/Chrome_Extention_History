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
    <div className={`chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'}`}>
      <div className="chat-bubble-content">
        {message.content}
      </div>
      <div className="chat-bubble-timestamp">
        {formatTime(message.timestamp)}
      </div>
    </div>
  );
}

