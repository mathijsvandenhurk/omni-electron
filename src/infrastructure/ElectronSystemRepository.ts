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
    // For now, we'll use the IPC renderer to remove listeners
    // This can be enhanced when the preload script is updated
    console.log('Terminal log listener cleanup requested');
  }
}