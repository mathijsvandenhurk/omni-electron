// Type definitions for Electron API exposed via preload script

export interface ElectronAPI {
  chat: (message: string) => Promise<ChatResponse>;
  listModels: () => Promise<ModelsResponse>;
  getStatus: () => Promise<StatusResponse>;
  listFiles: (path: string) => Promise<FilesResponse>;
  onChatProgress: (callback: (message: string) => void) => void;
  onTerminalLog: (callback: (data: { type: string; message: string }) => void) => void;
  platform: string;
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

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
