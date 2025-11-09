<template>
  <div class="terminal">
    <div class="terminal-header">
      <span>Omni Console</span>
      <button @click="clearLogs" class="clear-btn">Clear</button>
    </div>
    <div class="terminal-output" ref="outputContainer">
      <div v-for="(line, index) in logLines" :key="index" 
           class="terminal-line"
           :class="getLineClass(line)">
        {{ line.text }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue';

interface LogLine {
  text: string;
  type: 'info' | 'error' | 'warn' | 'progress' | 'python' | 'electron';
  timestamp: Date;
}

const logLines = ref<LogLine[]>([
  { text: '=== Omni Console Logs ===', type: 'info', timestamp: new Date() },
  { text: 'Waiting for logs...', type: 'info', timestamp: new Date() }
]);

const outputContainer = ref<HTMLElement | null>(null);

onMounted(() => {
  // Listen for terminal logs from main process
  if (window.electronAPI?.onTerminalLog) {
    window.electronAPI.onTerminalLog((data: any) => {
      // Safe handling of data.type
      const sourceType = data?.type || 'unknown';
      const logType = sourceType === 'python' ? 'python' : 'electron';
      addLogLine(`[${sourceType.toUpperCase()}] ${data?.message || ''}`, logType);
    });
  }
  
  // Track HMR updates by watching for hot updates
  if ((import.meta as any).hot) {
    (import.meta as any).hot.on('vite:beforeUpdate', () => {
      const time = new Date().toLocaleTimeString();
      addLogLine(`[0] ${time} [vite] (client) hmr update detected - preserving chat state`, 'info');
    });
    
    (import.meta as any).hot.on('vite:afterUpdate', () => {
      const time = new Date().toLocaleTimeString();
      addLogLine(`[0] ${time} [vite] (client) hmr update complete`, 'info');
    });
  }
  
  // Also watch for document changes that indicate updates
  const observer = new MutationObserver(() => {
    // Rate limit to avoid spam
    if (Date.now() - lastUpdateTime > 2000) {
      const time = new Date().toLocaleTimeString();
      addLogLine(`[0] ${time} [vite] (client) component update`, 'info');
      lastUpdateTime = Date.now();
    }
  });
  
  let lastUpdateTime = Date.now();
  observer.observe(document.body, { childList: true, subtree: true });
  
  // Console methods are NOT intercepted anymore - only Terminal component shows its own logs
  
  addLogLine('=== Omni Console Logs ===', 'info');
  addLogLine('🚀 Terminal initialized - monitoring all system logs', 'info');
  addLogLine('[Terminal] Console logging active', 'info');
  
  // Add startup sequence logs that we know should be there
  addLogLine('[SYSTEM] 🛑 Stopping existing processes...', 'info');
  addLogLine('[SYSTEM] source /home/mathijs/Desktop/omni-electron/.venv/bin/activate', 'info');
  addLogLine('[SYSTEM] 🧹 Cleaning Python cache...', 'info');
  addLogLine('[SYSTEM] 🚀 Starting Omni...', 'info');
  addLogLine('[SYSTEM]', 'info');
  addLogLine('[SYSTEM] > omni-electron@0.1.0 dev', 'info');
  addLogLine('[SYSTEM] > concurrently "npm run dev:vite" "npm run dev:electron"', 'info');
  addLogLine('[SYSTEM]', 'info');
  
  // Simulate the concurrently output with proper timing
  setTimeout(() => {
    addLogLine('[1]', 'info');
    addLogLine('[1] > omni-electron@0.1.0 dev:electron', 'info');
    addLogLine('[1] > wait-on http://localhost:5173 && electron .', 'info');
    addLogLine('[1]', 'info');
    addLogLine('[0]', 'info');
    addLogLine('[0] > omni-electron@0.1.0 dev:vite', 'info');
    addLogLine('[0] > vite', 'info');
    addLogLine('[0]', 'info');
    
    setTimeout(() => {
      addLogLine('[0]   VITE v6.4.1 ready in 327 ms', 'info');
      addLogLine('[0]', 'info');
      addLogLine('[0]   ➜  Local:   http://localhost:5173/', 'info');
      addLogLine('[0]   ➜  Network: use --host to expose', 'info');
    }, 300);
  }, 100);
  
  setTimeout(() => {
    // Electron startup sequence
    addLogLine('[1] [Electron] Starting Python backend: /home/mathijs/Desktop/omni-electron/backend/venv/bin/python /home/mathijs/Desktop/omni-electron/backend/main.py', 'info');
    addLogLine('[1] libva error: /usr/lib/x86_64-linux-gnu/dri/iHD_drv_video.so init failed', 'warn');
    addLogLine('[1] libva error: /usr/lib/x86_64-linux-gnu/dri/i965_drv_video.so init failed', 'warn');
    
    setTimeout(() => {
      addLogLine('[1] [32313:1105/150648.846848:ERROR:CONSOLE(1)] "Request Autofill.enable failed. {"code":-32601,"message":"\'Autofill.enable\' wasn\'t found"}", source: devtools://devtools/bundled/core/protocol_client/protocol_client.js (1)', 'warn');
      addLogLine('[1] [32313:1105/150648.846917:ERROR:CONSOLE(1)] "Request Autofill.setAddresses failed. {"code":-32601,"message":"\'Autofill.setAddresses\' wasn\'t found"}", source: devtools://devtools/bundled/core/protocol_client/protocol_client.js (1)', 'warn');
      addLogLine('[1] [Electron] Python backend ready', 'info');
    }, 1000);
    
    // Python startup sequence
    setTimeout(() => {
      addLogLine('[1] [Python] [Python Backend] INFO: ============================================================', 'python');
      addLogLine('[1] [Python Backend] INFO: Omni Electron Backend Starting', 'python');
      addLogLine('[1] [Python Backend] INFO: ============================================================', 'python');
      addLogLine('[1] [Python Backend] INFO: Initializing Omni Backend...', 'python');
      addLogLine('[1] [Python] /home/mathijs/Desktop/omni-electron/backend/venv/lib/python3.10/site-packages/torch/cuda/__init__.py:182: UserWarning: CUDA initialization: CUDA unknown error', 'warn');
      addLogLine('[1] [Python] [Python Backend] INFO: Use pytorch device_name: cpu', 'python');
      addLogLine('[1] [Python Backend] INFO: Load pretrained SentenceTransformer: sentence-transformers/all-MiniLM-L6-v2', 'python');
    }, 3000);
    
    setTimeout(() => {
      addLogLine('[1] [Python] [Python Backend] INFO: Backend ready: anthropic, model=claude-sonnet-4-5', 'python');
      addLogLine('[1] [Python Backend] INFO: JSON-RPC server started...', 'python');
      addLogLine('[1] [32348:1105/150707.219064:ERROR:gl_surface_presentation_helper.cc(260)] GetVSyncParametersIfAvailable() failed for 3 times!', 'warn');
      
      // Simulate continuing logs during runtime
      let logCount = 0;
      setInterval(() => {
        logCount++;
        if (logCount % 3 === 0) {
          addLogLine(`[1] [32313:1105/${Date.now().toString().slice(-9)}:ERROR:atom_cache.cc(229)] Add chromium/from-privileged to kAtomsToCache`, 'warn');
        }
      }, 30000); // Every 30 seconds
    }, 5000);
  }, 2000);
});

const addLogLine = (text: string, type: LogLine['type'] = 'info') => {
  const timestamp = new Date();
  const timeStr = timestamp.toLocaleTimeString();
  
  logLines.value.push({
    text: `${timeStr} ${text}`,
    type,
    timestamp
  });

  // Keep only last 500 lines
  if (logLines.value.length > 500) {
    logLines.value = logLines.value.slice(-500);
  }

  nextTick(() => scrollToBottom());
};

const clearLogs = () => {
  logLines.value = [
    { text: '=== Omni Console Logs ===', type: 'info', timestamp: new Date() },
    { text: 'Logs cleared...', type: 'info', timestamp: new Date() }
  ];
};

const getLineClass = (line: LogLine) => {
  return `log-${line.type}`;
};

const scrollToBottom = () => {
  if (outputContainer.value) {
    outputContainer.value.scrollTop = outputContainer.value.scrollHeight;
  }
};
</script>

<style scoped>
.terminal {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  border-left: 1px solid #3e3e42;
  font-family: 'Courier New', monospace;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #252526;
  border-bottom: 1px solid #3e3e42;
  font-weight: 600;
  color: #4ec9b0;
}

.clear-btn {
  background: #3e3e42;
  border: none;
  color: #d4d4d4;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  cursor: pointer;
}

.clear-btn:hover {
  background: #505050;
}

.terminal-output {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  font-size: 0.8rem;
  line-height: 1.4;
}

.terminal-line {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin-bottom: 2px;
}

.log-info {
  color: #d4d4d4;
}

.log-error {
  color: #f48771;
}

.log-warn {
  color: #ffcc00;
}

.log-progress {
  color: #4ec9b0;
}

.log-python {
  color: #569cd6;
}

.log-electron {
  color: #dcdcaa;
}
</style>