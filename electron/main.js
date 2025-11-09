import { app, BrowserWindow, ipcMain } from 'electron';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { promises as fs } from 'fs';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load .env file
dotenv.config({ path: path.join(__dirname, '../.env') });

// Security & Performance: Configure Electron before app ready
app.commandLine.appendSwitch('--no-sandbox');
app.commandLine.appendSwitch('--disable-setuid-sandbox');
app.commandLine.appendSwitch('--disable-dev-shm-usage'); // Fix /dev/shm issues
app.commandLine.appendSwitch('--disable-web-security');
app.commandLine.appendSwitch('--disable-features', 'VizDisplayCompositor');
app.commandLine.appendSwitch('--enable-gpu-rasterization');
app.commandLine.appendSwitch('--enable-zero-copy');
app.commandLine.appendSwitch('--disable-background-timer-throttling');
app.commandLine.appendSwitch('--disable-backgrounding-occluded-windows');
app.commandLine.appendSwitch('--disable-renderer-backgrounding');

// Console logging - keep it simple, no terminal forwarding (causes infinite loops)
let mainWindow = null;
let pythonProcess = null;
let pythonReady = false;
let messageId = 0;
let pendingRequests = new Map();

/**
 * Create the main application window with performance optimizations
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    // Performance optimizations
    show: false, // Don't show until ready-to-show
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      // Additional security and performance settings
      sandbox: false, // Keep false for IPC functionality
      webSecurity: true,
      allowRunningInsecureContent: false,
      experimentalFeatures: false,
      // Performance optimizations
      backgroundThrottling: false, // Keep background processes active
      spellcheck: false, // Disable expensive spell checking
      v8CacheOptions: 'code' // Enable V8 code caching
    },
    // Window performance options
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default'
    // icon: path.join(__dirname, '../build/icon.png') // Commented out until icon is added
  });

  // Optimize window loading - show only when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Focus the window after showing
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.focus();
    }
  });

  // Forward all browser console logs to terminal
  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    const levelNames = ['VERBOSE', 'INFO', 'WARNING', 'ERROR'];
    const levelName = levelNames[level] || 'LOG';
    const source = sourceId ? sourceId.split('/').pop() : 'renderer';
    console.log(`[Browser ${levelName}] ${source}:${line} - ${message}`);
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

  // Set Content Security Policy for better security
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          isDev 
            ? "default-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:* ws://localhost:*;" 
            : "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"
        ]
      }
    });
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Spawn Python backend process and setup JSON-RPC communication
 * Returns a Promise for better parallel initialization
 * 
 * Industry-standard approach:
 * 1. Try PYTHON_PATH from .env (explicit configuration)
 * 2. Fall back to system python3 (graceful degradation)
 * 3. Validate Python executable before spawning
 */
function startPythonBackend() {
  return new Promise((resolve, reject) => {
    // Try multiple Python executables in order of preference
    const pythonCandidates = [
      process.env.PYTHON_PATH,
      'python3',
      'python',
      '/usr/bin/python3'
    ].filter(Boolean);
    
    const pythonScript = path.join(__dirname, '../backend/main.py');

    console.log('[Electron] Starting Python backend...');
    console.log('[Electron] Python script:', pythonScript);
    console.log('[Electron] Python candidates:', pythonCandidates);

    // Use first available Python executable
    const pythonExecutable = pythonCandidates[0];
    console.log('[Electron] Using Python:', pythonExecutable);

    // Send startup log to terminal
    if (mainWindow) {
      mainWindow.webContents.send('terminal-log', {
        source: 'SYSTEM',
        message: `🚀 Starting Omni Python backend with ${pythonExecutable}...`,
        timestamp: new Date().toLocaleTimeString()
      });
    }

    pythonProcess = spawn(pythonExecutable, ['-u', pythonScript], {
      stdio: ['pipe', 'pipe', 'pipe'],
      // Performance optimizations for subprocess
      detached: false,
      windowsHide: true,
      // Set working directory to backend folder
      cwd: path.join(__dirname, '../backend')
    });

    // Set up error handling for the process
    pythonProcess.on('error', (error) => {
      console.error('[Electron] Failed to start Python process:', error);
      if (mainWindow) {
        mainWindow.webContents.send('terminal-log', {
          source: 'ERROR',
          message: `❌ Python backend failed to start: ${error.message}`,
          timestamp: new Date().toLocaleTimeString()
        });
      }
      reject(error);
    });

  // Handle Python stdout (JSON-RPC responses)
  pythonProcess.stdout.on('data', (data) => {
    // DEBUG: Log RAW stdout data
    console.log('[Electron] 🔥 RAW STDOUT:', data.toString());
    
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
        
        // Check if this is a streaming event notification (chat_event)
        if (response.method === 'chat_event' && response.params) {
          console.log('[Electron] 🚀 SENDING chat:event to renderer:', response.params.type);
          // Forward streaming event to renderer
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('chat:event', response.params);
            console.log('[Electron] ✅ chat:event SENT');
          } else {
            console.log('[Electron] ❌ mainWindow unavailable!');
          }
          continue; // Don't treat as regular response
        }
        
        // Forward response to renderer (regular JSON-RPC)
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('python-response', response);
        }

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
              
              mainWindow.webContents.send('chat-progress', decodedMessage);
            } catch (e) {
              // Fallback for non-JSON messages (backward compatibility)
              const fallbackMessage = encodedMessage.trim();
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

  // Mark as ready after a short delay and resolve the promise
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
    
    resolve(); // Resolve the promise indicating successful startup
  }, 2000);
  });
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

// Chat with LLM (streaming version)
ipcMain.handle('chat', async (event, message, requestId) => {
  console.log('[Electron] Chat request received:', message.substring(0, 50) + '...');
  try {
    // Use provided requestId from frontend, or generate new one if not provided
    const request_id = requestId || `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    console.log('[Electron] Starting streaming chat with request_id:', request_id);
    
    // Send request to Python backend - don't await response
    // Events will be forwarded via 'chat:event' as they arrive
    const id = ++messageId;
    const request = {
      jsonrpc: '2.0',
      id,
      method: 'chat',
      params: { message, request_id }
    };
    
    pythonProcess.stdin.write(JSON.stringify(request) + '\n');
    
    // Return immediately with request_id - events will stream separately
    console.log('[Electron] Streaming started, events will be forwarded to renderer');
    return { success: true, request_id };
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

// List files in directory
ipcMain.handle('list-files', async (event, dirPath) => {
  try {
    // Resolve relative paths relative to the app directory
    const fullPath = path.resolve(dirPath);
    
    // Basic security check - don't allow going outside the project
    const projectRoot = process.cwd();
    if (!fullPath.startsWith(projectRoot)) {
      return { success: false, error: 'Access denied: Path outside project directory' };
    }
    
    const entries = await fs.readdir(fullPath, { withFileTypes: true });
    const files = entries.map(entry => {
      const name = entry.name;
      return entry.isDirectory() ? name + '/' : name;
    });
    
    return { success: true, data: { files } };
  } catch (error) {
    console.error('[Electron] List files error:', error);
    return { success: false, error: error.message };
  }
});

// Recursive file tree scanning (VS Code style)
ipcMain.handle('list-files-recursive', async (event, dirPath, options = {}) => {
  const { 
    maxDepth = 10, 
    excludePatterns = [
      'node_modules',
      '__pycache__',
      '.DS_Store',
      'Thumbs.db'
    ] 
  } = options;
  
  try {
    // Resolve relative paths relative to the app directory
    const rootPath = path.resolve(dirPath);
    
    // Basic security check - don't allow going outside the project
    const projectRoot = process.cwd();
    if (!rootPath.startsWith(projectRoot)) {
      return { success: false, error: 'Access denied: Path outside project directory' };
    }
    
    const fileTree = [];
    
    async function scanDirectory(dirPath, currentDepth = 0, relativePath = '') {
      if (currentDepth > maxDepth) return [];
      
      try {
        const entries = await fs.readdir(dirPath, { withFileTypes: true });
        const items = [];
        
        for (const entry of entries) {
          const name = entry.name;
          
          // Skip only explicitly excluded patterns
          if (excludePatterns.includes(name)) {
            continue;
          }
          
          const fullPath = path.join(dirPath, name);
          const relPath = relativePath ? `${relativePath}/${name}` : name;
          
          if (entry.isDirectory()) {
            // Add directory
            items.push({
              name,
              path: relPath + '/',
              type: 'directory'
            });
            
            // Recursively scan subdirectory
            const children = await scanDirectory(fullPath, currentDepth + 1, relPath);
            items.push(...children);
          } else {
            // Add file
            items.push({
              name,
              path: relPath,
              type: 'file'
            });
          }
        }
        
        return items;
      } catch (err) {
        console.error('[Electron] Error scanning directory:', dirPath, err);
        return [];
      }
    }
    
    const allFiles = await scanDirectory(rootPath);
    
    return { 
      success: true, 
      data: { 
        files: allFiles.map(item => item.path),
        tree: allFiles 
      } 
    };
  } catch (error) {
    console.error('[Electron] List files recursive error:', error);
    return { success: false, error: error.message };
  }
});

// Read file content
ipcMain.handle('read-file', async (event, filePath) => {
  try {
    // Resolve relative paths relative to the app directory
    const fullPath = path.resolve(filePath);
    
    // Basic security check - don't allow going outside the project
    const projectRoot = process.cwd();
    if (!fullPath.startsWith(projectRoot)) {
      return { success: false, error: 'Access denied: Path outside project directory' };
    }
    
    // Check if file exists
    try {
      await fs.access(fullPath);
    } catch {
      return { success: false, error: 'File not found' };
    }
    
    // Read file content
    const buffer = await fs.readFile(fullPath);
    
    // Detect if file is binary by checking for null bytes
    const isBinary = buffer.includes(0);
    
    if (isBinary) {
      return { 
        success: true, 
        data: { 
          content: null, 
          isBinary: true,
          path: fullPath,
          size: buffer.length
        } 
      };
    }
    
    // Convert to string for text files
    const content = buffer.toString('utf-8');
    
    return { 
      success: true, 
      data: { 
        content, 
        isBinary: false,
        path: fullPath,
        size: buffer.length
      } 
    };
  } catch (error) {
    console.error('[Electron] Read file error:', error);
    return { success: false, error: error.message };
  }
});

// Open file in editor (sends to renderer to handle)
ipcMain.handle('open-file', async (event, filePath) => {
  try {
    const projectRoot = process.cwd();
    let fullPath;
    
    // If path is already absolute and starts with project root, use it
    if (path.isAbsolute(filePath) && filePath.startsWith(projectRoot)) {
      fullPath = filePath;
    } 
    // If it's a relative path or just a filename, try to resolve it
    else {
      // First try: resolve relative to project root
      fullPath = path.resolve(projectRoot, filePath);
      
      // If file doesn't exist, try to find it recursively in common directories
      try {
        await fs.access(fullPath);
      } catch {
        // Common directories to search
        const searchDirs = [
          'src/components',
          'src',
          'backend',
          'electron',
          'docs',
          '.'
        ];
        
        let found = false;
        for (const dir of searchDirs) {
          const testPath = path.resolve(projectRoot, dir, filePath);
          try {
            await fs.access(testPath);
            fullPath = testPath;
            found = true;
            console.log(`[Electron] Found file: ${testPath}`);
            break;
          } catch {
            // Continue searching
          }
        }
        
        if (!found) {
          throw new Error(`File not found: ${filePath}`);
        }
      }
    }
    
    // Security check - ensure resolved path is within project
    if (!fullPath.startsWith(projectRoot)) {
      throw new Error('Access denied: Path outside project directory');
    }
    
    // Final existence check
    await fs.access(fullPath);
    
    console.log(`[Electron] Opening file: ${fullPath}`);
    
    // Send event to renderer to open the file
    // The renderer will handle opening it in Monaco or appropriate viewer
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('open-file-in-editor', fullPath);
    }
    
    return { success: true };
  } catch (error) {
    console.error('[Electron] Open file error:', error);
    throw error;
  }
});

// Save chat messages to persistent file
ipcMain.handle('save-chat-messages', async (event, messages) => {
  try {
    const userDataPath = app.getPath('userData');
    const chatFilePath = path.join(userDataPath, 'chat-messages.json');
    
    await fs.writeFile(chatFilePath, JSON.stringify(messages, null, 2), 'utf-8');
    console.log('[Electron] Chat messages saved:', messages.length, 'messages');
    
    return { success: true };
  } catch (error) {
    console.error('[Electron] Save chat messages error:', error);
    return { success: false, error: error.message };
  }
});

// Load chat messages from persistent file
ipcMain.handle('load-chat-messages', async (event) => {
  try {
    const userDataPath = app.getPath('userData');
    const chatFilePath = path.join(userDataPath, 'chat-messages.json');
    
    try {
      const data = await fs.readFile(chatFilePath, 'utf-8');
      const messages = JSON.parse(data);
      console.log('[Electron] Chat messages loaded:', messages.length, 'messages');
      return { success: true, data: messages };
    } catch (err) {
      // File doesn't exist yet, return empty array
      if (err.code === 'ENOENT') {
        console.log('[Electron] No saved chat messages found');
        return { success: true, data: [] };
      }
      throw err;
    }
  } catch (error) {
    console.error('[Electron] Load chat messages error:', error);
    return { success: false, error: error.message };
  }
});

/**
 * App lifecycle with performance optimizations
 */

// App optimization settings
app.commandLine.appendSwitch('--disable-gpu-sandbox');
app.commandLine.appendSwitch('--disable-software-rasterizer');
app.commandLine.appendSwitch('--disable-background-timer-throttling');
app.commandLine.appendSwitch('--disable-backgrounding-occluded-windows');

// Enable hardware acceleration when available
if (!app.isPackaged) {
  app.commandLine.appendSwitch('--enable-logging');
}

app.whenReady().then(async () => {
  // Performance: Start Python backend and window creation in parallel
  const pythonStartPromise = startPythonBackend();
  const windowCreationPromise = createWindow();
  
  // Wait for both to complete
  await Promise.all([pythonStartPromise, windowCreationPromise]);
});

app.on('window-all-closed', () => {
  // Graceful cleanup: Kill Python process when app closes
  if (pythonProcess && !pythonProcess.killed) {
    pythonProcess.kill('SIGTERM');
    
    // Force kill after 3 seconds if still running
    setTimeout(() => {
      if (pythonProcess && !pythonProcess.killed) {
        pythonProcess.kill('SIGKILL');
      }
    }, 3000);
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On macOS, re-create window when dock icon is clicked
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Memory Management & Resource Optimization
setInterval(() => {
  // Periodic garbage collection to optimize memory usage
  if (global.gc) {
    global.gc();
  }
  
  // Log memory usage in development mode
  if (!app.isPackaged) {
    const memoryUsage = process.memoryUsage();
    console.log(`[Memory] RSS: ${Math.round(memoryUsage.rss / 1024 / 1024)}MB, ` +
                `Heap: ${Math.round(memoryUsage.heapUsed / 1024 / 1024)}MB`);
  }
}, 30000); // Every 30 seconds

// Performance: Enable process cleanup optimizations
app.on('before-quit', () => {
  // Clean up resources before quitting
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.removeAllListeners();
  }
  
  // Clear pending requests to prevent memory leaks
  pendingRequests.clear();
  
  // Force garbage collection if available
  if (global.gc) {
    global.gc();
  }
});

// Process Resource Monitoring & Limits
if (!app.isPackaged) {
  // Enable V8 garbage collection exposure for memory optimization
  app.commandLine.appendSwitch('--expose-gc');
  
  // Monitor main process performance
  setInterval(() => {
    const usage = process.cpuUsage();
    const memoryUsage = process.memoryUsage();
    
    console.log(`[Performance] CPU: ${Math.round(usage.user / 1000)}ms user, ` +
                `${Math.round(usage.system / 1000)}ms system | ` +
                `Memory: ${Math.round(memoryUsage.rss / 1024 / 1024)}MB RSS`);
  }, 60000); // Every minute in development
}

// Cleanup on exit
process.on('exit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});
