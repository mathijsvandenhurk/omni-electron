/**
 * System Composable - Presentation Layer  
 * Vue composition API for system functionality using Clean Architecture
 */

import { ref, onMounted, onUnmounted } from 'vue';
import { SystemUseCases } from '../core/usecases';
import { ElectronSystemRepository } from '../infrastructure/ElectronSystemRepository';
import { SystemStatus, TerminalLog } from '../core/entities/System';

// Create global system use cases instance
const systemRepository = new ElectronSystemRepository();
const systemUseCases = new SystemUseCases(systemRepository);

export function useSystem() {
  const status = ref<SystemStatus>({
    pythonReady: false,
    electronReady: false
  });
  const terminalLogs = ref<TerminalLog[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Get system status
  const refreshStatus = async () => {
    isLoading.value = true;
    error.value = null;

    try {
      const result = await systemUseCases.getSystemStatus();
      
      if (result.success && result.data) {
        status.value = result.data;
      } else {
        error.value = result.error || 'Failed to get system status';
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
    } finally {
      isLoading.value = false;
    }
  };

  // Add terminal log
  const addTerminalLog = (log: TerminalLog) => {
    terminalLogs.value.push(log);
    
    // Keep only last 1000 logs to prevent memory issues
    if (terminalLogs.value.length > 1000) {
      terminalLogs.value = terminalLogs.value.slice(-1000);
    }
  };

  // Clear terminal logs
  const clearTerminalLogs = () => {
    terminalLogs.value = [];
  };

  // Setup terminal log listening
  const setupTerminalLogListener = () => {
    systemUseCases.onTerminalLog(addTerminalLog);
  };

  // Computed status text and class
  const statusText = ref('Initializing...');
  const statusClass = ref('loading');

  const updateStatusDisplay = () => {
    if (status.value.pythonReady && status.value.electronReady) {
      statusText.value = 'Ready';
      statusClass.value = 'ready';
    } else if (status.value.electronReady) {
      statusText.value = 'Backend Starting...';
      statusClass.value = 'loading';
    } else {
      statusText.value = 'Error';
      statusClass.value = 'error';
    }
  };

  // Auto-refresh status
  onMounted(() => {
    refreshStatus();
    setupTerminalLogListener();
    
    // Auto-refresh every 5 seconds if not ready
    const interval = setInterval(() => {
      if (!status.value.pythonReady) {
        refreshStatus();
      }
      updateStatusDisplay();
    }, 5000);

    // Cleanup interval on unmount
    onUnmounted(() => {
      clearInterval(interval);
      systemUseCases.removeTerminalLogListener();
    });
  });

  return {
    status,
    statusText,
    statusClass,
    terminalLogs,
    isLoading,
    error,
    refreshStatus,
    clearTerminalLogs,
    setupTerminalLogListener
  };
}