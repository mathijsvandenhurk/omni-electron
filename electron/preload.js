import { contextBridge, ipcRenderer } from 'electron';

/**
 * Electron Preload Script
 * 
 * This script runs in a privileged context and exposes a safe API
 * to the renderer process (Vue app) via contextBridge.
 * 
 * Security: contextIsolation ensures renderer can't access Node.js directly
 */

// Expose protected methods to renderer
contextBridge.exposeInMainWorld('electronAPI', {
  /**
   * Send a chat message to the LLM
   * @param {string} message - User message
   * @returns {Promise<{success: boolean, data?: any, error?: string}>}
   */
  chat: (message) => ipcRenderer.invoke('chat', message),

  /**
   * List available LLM models
   * @returns {Promise<{success: boolean, data?: string[], error?: string}>}
   */
  listModels: () => ipcRenderer.invoke('list-models'),

  /**
   * Get system status
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getStatus: () => ipcRenderer.invoke('get-status'),

  /**
   * List files in a directory
   * @param {string} path - Directory path to list
   * @returns {Promise<{success: boolean, data?: {files: string[]}, error?: string}>}
   */
  listFiles: (path) => ipcRenderer.invoke('list-files', path),

  /**
   * Listen for chat progress updates
   * @param {function} callback - Called with progress message
   */
  onChatProgress: (callback) => {
    ipcRenderer.on('chat-progress', (event, message) => callback(message));
  },

  /**
   * Listen for terminal log updates
   * @param {function} callback - Called with log data
   */
  onTerminalLog: (callback) => {
    ipcRenderer.on('terminal-log', (event, data) => callback(data));
  },

  /**
   * Platform information
   */
  platform: process.platform,

  /**
   * Remove chat progress listener
   */
  removeChatProgressListener: () => {
    ipcRenderer.removeAllListeners('chat-progress');
  },

  /**
   * Remove terminal log listener
   */
  removeTerminalLogListener: () => {
    ipcRenderer.removeAllListeners('terminal-log');
  }
});
