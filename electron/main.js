import { app, BrowserWindow, ipcMain } from 'electron';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load .env file
dotenv.config({ path: path.join(__dirname, '../.env') });

// Override console methods to send logs to terminal
const originalConsoleLog = console.log;
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

function sendToTerminal(level, ...args) {
  const message = args.map(arg => 
    typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
  ).join(' ');
  
  if (mainWindow) {
    mainWindow.webContents.send('terminal-log', {
      source: 'ELECTRON',
      message: `[${level.toUpperCase()}] ${message}`,
      timestamp: new Date().toLocaleTimeString()
    });
  }
}

console.log = (...args) => {
  originalConsoleLog(...args);
  sendToTerminal('info', ...args);
};

console.error = (...args) => {
  originalConsoleError(...args);
  sendToTerminal('error', ...args);
};

console.warn = (...args) => {
  originalConsoleWarn(...args);
  sendToTerminal('warn', ...args);
};

let mainWindow = null;
let pythonProcess = null;
let pythonReady = false;
let messageId = 0;
let pendingRequests = new Map();

/**
 * Create the main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    icon: path.join(__dirname, '../build/icon.png')
  });

  // Load Vite dev server in development, or built files in production
  // In dev mode, always use Vite dev server
  const isDev = !app.isPackaged;
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Spawn Python backend process and setup JSON-RPC communication
 */
function startPythonBackend() {
  const pythonExecutable = process.env.PYTHON_PATH || 'python3';
  const pythonScript = path.join(__dirname, '../backend/main.py');

  console.log('[Electron] Starting Python backend:', pythonExecutable, pythonScript);

  // Send startup log to terminal
  if (mainWindow) {
    mainWindow.webContents.send('terminal-log', {
      source: 'SYSTEM',
      message: '🚀 Starting Omni Python backend...',
      timestamp: new Date().toLocaleTimeString()
    });
  }

  pythonProcess = spawn(pythonExecutable, [pythonScript], {
    stdio: ['pipe', 'pipe', 'pipe']
  });

  // Handle Python stdout (JSON-RPC responses)
  pythonProcess.stdout.on('data', (data) => {
    const lines = data.toString().split('\n').filter(line => line.trim());
    
    for (const line of lines) {
      // Send all Python stdout to terminal (except JSON responses)
      if (!line.startsWith('{') && line.trim() && mainWindow) {
        mainWindow.webContents.send('terminal-log', {
          source: 'PYTHON',
          message: line,
          timestamp: new Date().toLocaleTimeString()
        });
      }
      
      try {
        const response = JSON.parse(line);
        console.log('[Electron] Python response:', response);

        // Resolve pending request
        const requestId = response.id;
        if (pendingRequests.has(requestId)) {
          const { resolve, reject } = pendingRequests.get(requestId);
          pendingRequests.delete(requestId);

          if (response.error) {
            reject(new Error(response.error));
          } else {
            resolve(response.result);
          }
        }
      } catch (err) {
        // Not JSON, ignore or log as regular output
        if (line.trim()) {
          console.log('[Python stdout]', line);
        }
      }
    }
  });

  // Handle Python stderr (logging + progress updates + heartbeat)
  pythonProcess.stderr.on('data', (data) => {
    const output = data.toString().trim();
    console.log('[Python]', output);
    
    // Send all Python stderr to terminal
    if (mainWindow) {
      mainWindow.webContents.send('terminal-log', {
        source: 'PYTHON',
        message: output,
        timestamp: new Date().toLocaleTimeString()
      });
    }
    
    // Check for heartbeat signals (but don't return early - also process progress)
    if (output.includes('⏱️')) {
      // Update activity timestamp for all pending requests
      const now = Date.now();
      for (const [id, requestData] of pendingRequests.entries()) {
        if (requestData.lastActivity) {
          requestData.lastActivity = now;
        }
      }
      // Don't return - continue to check for progress messages too
    }
    
    // Check for progress updates (lines starting with [PROGRESS])
    if (output.includes('[PROGRESS]')) {
      const lines = output.split('\n');
      for (const line of lines) {
        if (line.includes('[PROGRESS]') && mainWindow) {
          const encodedMessage = line.replace(/.*\[PROGRESS\]\s*/, '');
          if (encodedMessage.trim()) {
            try {
              // Decode the JSON-encoded message to restore multi-line content
              const decodedMessage = JSON.parse(encodedMessage.trim());
              console.log('[Electron] Forwarding decoded progress:', decodedMessage);
              
              // Also send to terminal for debugging
              mainWindow.webContents.send('terminal-log', {
                type: 'electron',
                message: `[DEBUG] Forwarding decoded progress: ${decodedMessage.substring(0, 100)}${decodedMessage.length > 100 ? '...' : ''}`
              });
              
              mainWindow.webContents.send('chat-progress', decodedMessage);
            } catch (e) {
              // Fallback for non-JSON messages (backward compatibility)
              const fallbackMessage = encodedMessage.trim();
              console.log('[Electron] Forwarding fallback progress:', fallbackMessage);
              mainWindow.webContents.send('chat-progress', fallbackMessage);
            }
          }
        }
      }
      
      // Update activity timestamp for all pending requests
      // Progress indicates the backend is actively working
      const now = Date.now();
      for (const [id, requestData] of pendingRequests.entries()) {
        if (requestData.lastActivity) {
          requestData.lastActivity = now;
        }
      }
    }
    
    // Send all Python logs to terminal (except heartbeats and progress)
    if (mainWindow && !output.includes('⏱️') && !output.includes('[PROGRESS]')) {
      mainWindow.webContents.send('terminal-log', {
        type: 'python',
        message: output
      });
    }
  });

  // Handle Python process exit
  pythonProcess.on('close', (code) => {
    console.log(`[Electron] Python process exited with code ${code}`);
    pythonReady = false;
    pythonProcess = null;
  });

  // Mark as ready after a short delay
  setTimeout(() => {
    pythonReady = true;
    console.log('[Electron] Python backend ready');
    
    // Send ready notification to terminal
    if (mainWindow) {
      mainWindow.webContents.send('terminal-log', {
        source: 'SYSTEM',
        message: '✅ Python backend ready - Omni is online!',
        timestamp: new Date().toLocaleTimeString()
      });
    }
  }, 2000);
}

/**
 * Send JSON-RPC request to Python backend with smart timeout handling
 */
function callPython(method, params = {}) {
  return new Promise((resolve, reject) => {
    if (!pythonReady || !pythonProcess) {
      reject(new Error('Python backend not ready'));
      return;
    }

    const id = ++messageId;
    const request = {
      jsonrpc: '2.0',
      id,
      method,
      params
    };

    // Store promise handlers with smart timeout
    const requestData = { 
      resolve, 
      reject, 
      startTime: Date.now(),
      lastActivity: Date.now(),
      timeoutHandle: null
    };
    
    pendingRequests.set(id, requestData);

    // Send to Python stdin
    const message = JSON.stringify(request) + '\n';
    pythonProcess.stdin.write(message);

    // Smart timeout function that resets on activity
    const createTimeout = () => {
      if (requestData.timeoutHandle) {
        clearTimeout(requestData.timeoutHandle);
      }
      
      requestData.timeoutHandle = setTimeout(() => {
        if (pendingRequests.has(id)) {
          const elapsed = Date.now() - requestData.startTime;
          const sinceActivity = Date.now() - requestData.lastActivity;
          
          // Only timeout if no activity for 30 seconds AND total time > 2 minutes
          if (sinceActivity > 30000 && elapsed > 120000) {
            pendingRequests.delete(id);
            reject(new Error(`Request timeout after ${Math.round(elapsed/1000)}s (no activity for ${Math.round(sinceActivity/1000)}s)`));
          } else {
            // Extend timeout if we've seen recent activity
            createTimeout();
          }
        }
      }, 15000); // Check every 15 seconds
    };

    createTimeout();
  });
}

/**
 * IPC Handlers - Called from renderer process
 */

// Chat with LLM
ipcMain.handle('chat', async (event, message) => {
  try {
    const result = await callPython('chat', { message });
    return { success: true, data: result };
  } catch (error) {
    console.error('[Electron] Chat error:', error);
    return { success: false, error: error.message };
  }
});

// List available LLM models
ipcMain.handle('list-models', async () => {
  try {
    const result = await callPython('list_models', {});
    return { success: true, data: result };
  } catch (error) {
    console.error('[Electron] List models error:', error);
    return { success: false, error: error.message };
  }
});

// Get system status
ipcMain.handle('get-status', async () => {
  return {
    success: true,
    data: {
      pythonReady,
      platform: process.platform,
      version: app.getVersion()
    }
  };
});

/**
 * App lifecycle
 */

app.on('ready', () => {
  startPythonBackend();
  createWindow();
});

app.on('window-all-closed', () => {
  // Kill Python process when app closes
  if (pythonProcess) {
    pythonProcess.kill();
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// Cleanup on exit
process.on('exit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});
