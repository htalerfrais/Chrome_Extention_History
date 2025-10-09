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
    <div className="chat-window">
      {/* Chat header */}
      <div className="chat-header">
        <h2>Chat Assistant</h2>
        {conversationId && (
          <span className="conversation-badge">Active conversation</span>
        )}
      </div>

      {/* Messages container */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <p>Start a conversation with your browsing history assistant!</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <ChatBubble key={`${message.role}-${index}-${message.timestamp.getTime()}`} message={message} />
          ))
        )}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="chat-loading">
            <div className="chat-loading-dots">
              <span>.</span>
              <span>.</span>
              <span>.</span>
            </div>
          </div>
        )}
        
        {/* Auto-scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Error display */}
      {error && (
        <div className="chat-error">
          {error}
        </div>
      )}

      {/* Input container */}
      <div className="chat-input-container">
        <input
          type="text"
          className="chat-input"
          placeholder="Type your message..."
          value={inputValue}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
        />
        <button
          className="chat-send-button"
          onClick={handleSendMessage}
          disabled={isLoading || !inputValue.trim()}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
}

