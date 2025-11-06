/**
 * Core Entity: Message
 * Represents a chat message in the domain layer
 */

export interface Message {
  id: string;
  content: string;
  timestamp: Date;
  source: 'user' | 'assistant' | 'system';
  status?: 'pending' | 'complete' | 'error';
  metadata?: Record<string, any>;
}

export interface MessageProgress {
  messageId: string;
  content: string;
  isComplete: boolean;
}

export interface ChatSession {
  id: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}