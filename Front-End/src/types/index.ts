export type Role = "user" | "assistant" | "system";

export interface Recommendation {
  name: string;
  url: string;
  test_type: string;
  description?: string;
  score?: number;
  confidence?: number;
  recommendation_strength?: "high" | "medium" | "low" | string;
  explanation?: string;
}

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  createdAt: number;
  recommendations?: Recommendation[];
}

export interface ChatRequestMessage {
  role: Role;
  content: string;
}

export interface ChatRequest {
  messages: ChatRequestMessage[];
}

export interface ChatResponse {
  reply: string;
  recommendations: Recommendation[];
  end_of_conversation: boolean;
}

export interface APIError {
  message: string;
  status?: number;
  detail?: unknown;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
}
