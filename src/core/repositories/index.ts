/**
 * Repository Interfaces - Domain Layer Contracts
 * These define the contract for data access without implementation details
 */

import { MessageProgress } from '../entities/Message';
import { SystemStatus, TerminalLog } from '../entities/System';
import { DirectoryListing } from '../entities/FileSystem';

/**
 * Chat Repository Interface
 * Defines contract for chat-related data operations
 */
export interface IChatRepository {
  sendMessage(message: string): Promise<string>;
  getModels(): Promise<string[]>;
  onProgress(callback: (progress: MessageProgress) => void): void;
  removeProgressListener(): void;
}

/**
 * System Repository Interface  
 * Defines contract for system-related operations
 */
export interface ISystemRepository {
  getStatus(): Promise<SystemStatus>;
  onTerminalLog(callback: (log: TerminalLog) => void): void;
  removeTerminalLogListener(): void;
}

/**
 * File System Repository Interface
 * Defines contract for file system operations  
 */
export interface IFileSystemRepository {
  listDirectory(path: string): Promise<DirectoryListing>;
  readFile(path: string): Promise<string>;
  writeFile(path: string, content: string): Promise<void>;
}

/**
 * Result wrapper for repository operations
 */
export interface RepositoryResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}