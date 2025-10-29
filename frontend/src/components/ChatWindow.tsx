// ChatWindow component - main chat interface
// Handles conversation state and user interactions

import { useState, useEffect, useRef } from 'react';
import ChatBubble from './ChatBubble';
import { extensionBridge } from '../services/extensionBridge';
import type { ChatMessage, ChatApiResponse } from '../types/chat';

export default function ChatWindow() {
  // State management
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  
  // Ref for auto-scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle send message
  const handleSendMessage = async () => {
    const trimmedMessage = inputValue.trim();
    
    if (!trimmedMessage || isLoading) {
      return;
    }

    // Add user message to UI immediately
    const userMessage: ChatMessage = {
      role: 'user',
      content: trimmedMessage,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // Send message to backend via extensionBridge
      const result: ChatApiResponse = await extensionBridge.sendChatMessage(
        trimmedMessage,
        conversationId || undefined,
        messages
      );

      if (result.success && result.data) {
        // Add assistant response to UI
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: result.data.response,
          timestamp: new Date(result.data.timestamp)
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        setConversationId(result.data.conversation_id);
      } else {
        throw new Error(result.error || 'Failed to send message');
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setError(err instanceof Error ? err.message : 'Failed to send message');
      
      // Remove the optimistic user message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  // Handle Enter key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full text-white">
      <div className="px-4 py-3 border-b border-white/10">
        <h2 className="text-sm uppercase tracking-widest">Chat</h2>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-2">
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
        <div className="px-4 py-2 text-xs text-red-400 text-center">{error}</div>
      )}

      <div className="px-4 py-3 flex items-center gap-2 border-t border-white/10 bg-[#080808]">
        <input
          type="text"
          className="flex-1 bg-transparent border-b border-white/20 outline-none px-0 py-2 text-sm placeholder-white/30 disabled:opacity-40"
          placeholder="Type your message..."
          value={inputValue}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
        />
        <button
          className="text-sm text-white/70 disabled:text-white/30"
          onClick={handleSendMessage}
          disabled={isLoading || !inputValue.trim()}
        >
          {isLoading ? 'Sending' : 'Send'}
        </button>
      </div>
    </div>
  );
}

