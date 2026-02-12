import { create } from 'zustand';
import { extensionBridge } from '../services/extensionBridge';
import type { ChatMessage, ChatApiResponse } from '../types/chat';

interface ChatStore {
  // State
  messages: ChatMessage[];
  inputValue: string;
  isLoading: boolean;
  error: string | null;
  conversationId: string | null;

  // Actions
  setInput: (value: string) => void;
  sendMessage: () => Promise<void>;
  clearConversation: () => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  // Initial state
  messages: [],
  inputValue: '',
  isLoading: false,
  error: null,
  conversationId: null,

  setInput: (value: string) => {
    set({ inputValue: value });
  },

  sendMessage: async () => {
    const { inputValue, isLoading, conversationId, messages } = get();
    const trimmedMessage = inputValue.trim();

    if (!trimmedMessage || isLoading) {
      return;
    }

    // Add user message to UI immediately
    const userMessage: ChatMessage = {
      role: 'user',
      content: trimmedMessage,
      timestamp: new Date(),
    };

    set({
      messages: [...messages, userMessage],
      inputValue: '',
      isLoading: true,
      error: null,
    });

    try {
      const result: ChatApiResponse = await extensionBridge.sendChatMessage(
        trimmedMessage,
        conversationId || undefined,
        messages
      );

      if (result.success && result.data) {
        const sources = result.data.sources ?? [];
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: result.data.response,
          timestamp: new Date(result.data.timestamp),
          sources,
        };

        set((state) => ({
          messages: [...state.messages, assistantMessage],
          conversationId: result.data!.conversation_id,
        }));
      } else {
        throw new Error(result.error || 'Failed to send message');
      }
    } catch (err) {
      console.error('Error sending message:', err);
      set((state) => ({
        error: err instanceof Error ? err.message : 'Failed to send message',
        // Remove the optimistic user message on error
        messages: state.messages.slice(0, -1),
      }));
    } finally {
      set({ isLoading: false });
    }
  },

  clearConversation: () => {
    set({
      messages: [],
      conversationId: null,
      error: null,
    });
  },
}));
