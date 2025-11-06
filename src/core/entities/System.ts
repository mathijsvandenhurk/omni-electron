/**
 * Core Entity: System Status
 * Represents application system status in the domain layer
 */

export interface SystemStatus {
  pythonReady: boolean;
  electronReady: boolean;
  backendVersion?: string;
  memory?: MemoryUsage;
  uptime?: number;
}

export interface MemoryUsage {
  rss: number;
  heapUsed: number;
  heapTotal: number;
  external: number;
}

export interface TerminalLog {
  id: string;
  source: 'SYSTEM' | 'PYTHON' | 'ELECTRON';
  message: string;
  timestamp: Date;
  level: 'info' | 'warning' | 'error' | 'debug';
}