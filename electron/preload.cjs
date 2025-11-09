const { contextBridge, ipcRenderer } = require('electron');

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
   * @param {string} [requestId] - Optional request ID for streaming correlation
   * @returns {Promise<{success: boolean, data?: any, error?: string}>}
   */
  chat: (message, requestId) => ipcRenderer.invoke('chat', message, requestId),

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
   * List files recursively (VS Code style - full tree in one call)
   * @param {string} path - Directory path to scan
   * @param {object} options - Options: maxDepth, excludePatterns
   * @returns {Promise<{success: boolean, data?: {files: string[], tree: object[]}, error?: string}>}
   */
  listFilesRecursive: (path, options) => ipcRenderer.invoke('list-files-recursive', path, options),

  /**
   * Read file content
   * @param {string} filePath - Path to the file to read
   * @returns {Promise<{success: boolean, data?: {content: string, isBinary: boolean, path: string, size: number}, error?: string}>}
   */
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),

  /**
   * Open a file in the editor
   * @param {string} filePath - Path to the file to open
   * @returns {Promise<void>}
   */
  openFile: (filePath) => ipcRenderer.invoke('open-file', filePath),

  /**
   * Save chat messages to persistent storage
   * @param {Array} messages - Array of chat messages
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  saveChatMessages: (messages) => ipcRenderer.invoke('save-chat-messages', messages),

  /**
   * Load chat messages from persistent storage
   * @returns {Promise<{success: boolean, data?: Array, error?: string}>}
   */
  loadChatMessages: () => ipcRenderer.invoke('load-chat-messages'),

  /**
   * Listen for chat progress updates
   * @param {function} callback - Called with progress message
   */
  onChatProgress: (callback) => {
    ipcRenderer.on('chat-progress', (event, message) => callback(message));
  },

  /**
   * Listen for streaming chat events (new streaming protocol)
   * @param {function} callback - Called with streaming event object
   */
  onChatEvent: (callback) => {
    ipcRenderer.on('chat:event', (event, eventData) => callback(eventData));
  },

  /**
   * Listen for terminal log updates
   * @param {function} callback - Called with log data
   */
  onTerminalLog: (callback) => {
    ipcRenderer.on('terminal-log', (event, data) => callback(data));
  },

  /**
   * Listen for file open requests from main process
   * @param {function} callback - Called with file path
   */
  onOpenFile: (callback) => {
    ipcRenderer.on('open-file-in-editor', (event, filePath) => callback(filePath));
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
   * Remove chat event listener  
   */
  removeChatEventListener: () => {
    ipcRenderer.removeAllListeners('chat:event');
  },

  /**
   * Remove terminal log listener
   */
  removeTerminalLogListener: () => {
    ipcRenderer.removeAllListeners('terminal-log');
  }
});
