/**
 * Electron IPC Chat Repository Implementation
 * Infrastructure layer - concrete implementation for chat operations
 */

import { IChatRepository } from '../core/repositories';
import { MessageProgress } from '../core/entities/Message';

export class ElectronChatRepository implements IChatRepository {

  async sendMessage(message: string): Promise<string> {
    try {
      const response = await window.electronAPI.chat(message);
      if (response.success && response.data) {
        // Extract the answer from the response data
        return response.data.answer || JSON.stringify(response.data);
      }
      throw new Error(response.error || 'Failed to send message');
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Unknown error');
    }
  }

  async getModels(): Promise<string[]> {
    try {
      const response = await window.electronAPI.listModels();
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error || 'Failed to fetch models');
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Unknown error');
    }
  }

  onProgress(callback: (progress: MessageProgress) => void): void {
    window.electronAPI.onChatProgress((message: string) => {
      callback({
        messageId: Date.now().toString(),
        content: message,
        isComplete: false
      });
    });
  }

  removeProgressListener(): void {
    // For now, we'll use the IPC renderer to remove listeners
    // This can be enhanced when the preload script is updated
    console.log('Progress listener cleanup requested');
  }
}