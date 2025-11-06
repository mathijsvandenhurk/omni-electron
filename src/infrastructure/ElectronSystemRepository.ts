/**
 * Electron IPC System Repository Implementation
 * Infrastructure layer - concrete implementation for system operations
 */

import { ISystemRepository } from '../core/repositories';
import { SystemStatus, TerminalLog } from '../core/entities/System';

export class ElectronSystemRepository implements ISystemRepository {
  async getStatus(): Promise<SystemStatus> {
    try {
      const response = await window.electronAPI.getStatus();
      if (response.success && response.data) {
        return {
          pythonReady: response.data.pythonReady || false,
          electronReady: true,
          backendVersion: response.data.version
        };
      }
      throw new Error(response.error || 'Failed to get system status');
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Unknown error');
    }
  }

  onTerminalLog(callback: (log: TerminalLog) => void): void {
    if (!window.electronAPI?.onTerminalLog) {
      console.warn('electronAPI.onTerminalLog not available');
      return;
    }
    
    window.electronAPI.onTerminalLog((data: any) => {
      callback({
        id: Date.now().toString(),
        source: data.source || 'SYSTEM',
        message: data.message || data,
        timestamp: new Date(data.timestamp || Date.now()),
        level: data.level || 'info'
      });
    });
  }

  removeTerminalLogListener(): void {
    if (!window.electronAPI?.removeTerminalLogListener) {
      console.warn('electronAPI.removeTerminalLogListener not available');
      return;
    }
    window.electronAPI.removeTerminalLogListener();
  }
}