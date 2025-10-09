// TypeScript types for chat functionality
// These mirror the backend Pydantic models for type safety and DRY principle

// === Core Types (mirror backend models) ===

export type MessageRole = 'user' | 'assistant' | 'system';

export type ChatProvider = 'openai' | 'anthropic' | 'google' | 'ollama';

export interface ChatMessage {
  role: MessageRole;
  content: string;
  timestamp: Date;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  history?: ChatMessage[];
  provider?: ChatProvider;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  timestamp: string;
  provider: string;
  model: string;
}

// === API Response wrapper (used by ApiClient) ===

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export type ChatApiResponse = ApiResponse<ChatResponse>;
