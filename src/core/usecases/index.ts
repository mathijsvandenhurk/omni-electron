/**
 * Use Cases - Application Layer
 * Business logic and orchestration without implementation details
 */

import { IChatRepository, ISystemRepository, RepositoryResult } from '../repositories';
import { MessageProgress } from '../entities/Message';
import { SystemStatus, TerminalLog } from '../entities/System';

/**
 * Chat Use Cases
 * Orchestrates chat-related business operations
 */
export class ChatUseCases {
  constructor(private chatRepository: IChatRepository) {}

  async sendMessage(message: string): Promise<RepositoryResult<string>> {
    try {
      if (!message.trim()) {
        return { success: false, error: 'Message cannot be empty' };
      }

      const response = await this.chatRepository.sendMessage(message);
      return { success: true, data: response };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }

  async getAvailableModels(): Promise<RepositoryResult<string[]>> {
    try {
      const models = await this.chatRepository.getModels();
      return { success: true, data: models };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to fetch models' 
      };
    }
  }

  onMessageProgress(callback: (progress: MessageProgress) => void): void {
    this.chatRepository.onProgress(callback);
  }

  removeProgressListener(): void {
    this.chatRepository.removeProgressListener();
  }
}

/**
 * System Use Cases
 * Orchestrates system-related business operations
 */
export class SystemUseCases {
  constructor(private systemRepository: ISystemRepository) {}

  async getSystemStatus(): Promise<RepositoryResult<SystemStatus>> {
    try {
      const status = await this.systemRepository.getStatus();
      return { success: true, data: status };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to get system status' 
      };
    }
  }

  onTerminalLog(callback: (log: TerminalLog) => void): void {
    this.systemRepository.onTerminalLog(callback);
  }

  removeTerminalLogListener(): void {
    this.systemRepository.removeTerminalLogListener();
  }
}