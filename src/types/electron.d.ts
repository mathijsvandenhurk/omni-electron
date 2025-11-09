// Type definitions for Electron API exposed via preload script

import type { OmniEvent } from './events';

export interface ElectronAPI {
  chat: (message: string, requestId?: string) => Promise<ChatResponse>;
  listModels: () => Promise<ModelsResponse>;
  getStatus: () => Promise<StatusResponse>;
  listFiles: (path: string) => Promise<FilesResponse>;
  listFilesRecursive: (path: string, options?: RecursiveListOptions) => Promise<RecursiveFilesResponse>;
  readFile: (filePath: string) => Promise<FileContentResponse>;
  openFile: (filePath: string) => Promise<void>;
  saveChatMessages: (messages: any[]) => Promise<{ success: boolean; error?: string }>;
  loadChatMessages: () => Promise<{ success: boolean; data?: any[]; error?: string }>;
  onChatProgress: (callback: (message: string) => void) => void;
  onChatEvent: (callback: (event: OmniEvent) => void) => void;  // New streaming API
  onTerminalLog: (callback: (data: { type: string; message: string }) => void) => void;
  onOpenFile: (callback: (filePath: string) => void) => void;
  removeChatProgressListener: () => void;
  removeChatEventListener: () => void;  // Cleanup for streaming listener
  removeTerminalLogListener: () => void;
  platform: string;
}

export interface RecursiveListOptions {
  maxDepth?: number;
  excludePatterns?: string[];
}

export interface FileTreeItem {
  name: string;
  path: string;
  type: 'file' | 'directory';
}

export interface RecursiveFilesResponse {
  success: boolean;
  data?: {
    files: string[];
    tree: FileTreeItem[];
  };
  error?: string;
}

export interface ChatResponse {
  success: boolean;
  data?: {
    answer: string;
    [key: string]: any;
  };
  error?: string;
}

export interface ModelsResponse {
  success: boolean;
  data?: string[];
  error?: string;
}

export interface StatusResponse {
  success: boolean;
  data?: {
    pythonReady: boolean;
    platform: string;
    version: string;
  };
  error?: string;
}

export interface FilesResponse {
  success: boolean;
  data?: {
    files: string[];
  };
  error?: string;
}

export interface FileContentResponse {
  success: boolean;
  data?: {
    content: string | null;
    isBinary: boolean;
    path: string;
    size: number;
  };
  error?: string;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
