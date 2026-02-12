import { useEffect, useRef } from 'react';
import { Send } from 'lucide-react';
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 thin-scrollbar">
        {messages.length === 0 ? (
          <div className="h-full w-full flex items-center justify-center text-text-ghost text-sm">
            Start a conversation
          </div>
        ) : (
          messages.map((message, index) => (
            <ChatBubble key={`${message.role}-${index}-${message.timestamp.getTime()}`} message={message} />
          ))
        )}
        {isLoading && (
          <div className="flex justify-start animate-fade-in-up">
            <div className="bg-bg-elevated rounded-xl px-4 py-3 animate-dot-bounce text-text-tertiary text-lg tracking-widest">
              <span>.</span><span>.</span><span>.</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error */}
      {error && (
        <div className="mx-5 mb-2 px-3 py-2 text-xs text-error bg-error/10 rounded-lg">{error}</div>
      )}

      {/* Input area */}
      <div className="px-5 py-4 border-t border-line">
        <div className="flex items-end gap-2 bg-surface rounded-xl px-4 py-2">
          <textarea
            className="flex-1 bg-transparent outline-none py-1.5 text-sm text-text placeholder-text-ghost resize-none min-h-[24px] max-h-[120px] leading-relaxed disabled:opacity-40"
            placeholder="Ask about your browsing history..."
            value={inputValue}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
          />
          <button
            className="p-2 rounded-lg text-text-tertiary hover:text-accent hover:bg-accent-subtle disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-text-tertiary transition-colors duration-150 flex-shrink-0"
            onClick={sendMessage}
            disabled={isLoading || !inputValue.trim()}
            title="Send message"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
