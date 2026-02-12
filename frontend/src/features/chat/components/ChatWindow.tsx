import { useEffect, useRef } from 'react';
import ChatBubble from './ChatBubble';
import { useChatStore } from '../../../stores/useChatStore';

export default function ChatWindow() {
  const messages = useChatStore((s) => s.messages);
  const inputValue = useChatStore((s) => s.inputValue);
  const isLoading = useChatStore((s) => s.isLoading);
  const error = useChatStore((s) => s.error);
  const setInput = useChatStore((s) => s.setInput);
  const sendMessage = useChatStore((s) => s.sendMessage);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full text-white">
      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-2 thin-scrollbar">
        {messages.length === 0 ? (
          <div className="h-full w-full flex items-center justify-center text-white/40 text-sm">
            Start a conversation
          </div>
        ) : (
          messages.map((message, index) => (
            <ChatBubble key={`${message.role}-${index}-${message.timestamp.getTime()}`} message={message} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="px-4 py-2 text-xs text-red-400/80">{error}</div>
      )}

      <div className="px-4 py-3 flex items-center gap-2 border-t border-white/10 bg-[#080808]">
        <input
          type="text"
          className="flex-1 bg-transparent border-b border-white/20 outline-none px-0 py-2 text-sm placeholder-white/30 disabled:opacity-40"
          placeholder="Type your message..."
          value={inputValue}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          disabled={isLoading}
        />
        <button
          className="text-sm text-white/70 disabled:text-white/30"
          onClick={sendMessage}
          disabled={isLoading || !inputValue.trim()}
        >
          {isLoading ? 'Sending' : 'Send'}
        </button>
      </div>
    </div>
  );
}
