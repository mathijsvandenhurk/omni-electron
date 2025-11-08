<template>
  <div class="app">
    <header class="app-header">
      <h1>Omni</h1>
      <div class="header-controls">
        <ThemeToggle />
        <button 
          @click="showFileExplorer = !showFileExplorer" 
          class="toggle-btn"
          :class="{ active: showFileExplorer }"
          title="Toggle File Explorer"
        >
          📁 Files
        </button>
        <button 
          @click="showEditor = !showEditor" 
          class="toggle-btn"
          :class="{ active: showEditor }"
          title="Toggle Code Editor"
        >
          📝 Editor
        </button>
        <button 
          @click="showChat = !showChat" 
          class="toggle-btn"
          :class="{ active: showChat }"
          title="Toggle Chat"
        >
          💬 Chat
        </button>
        <button 
          @click="showTerminal = !showTerminal" 
          class="toggle-btn"
          :class="{ active: showTerminal }"
          title="Toggle Terminal"
        >
          🖥️ Terminal
        </button>
        <div class="status-badge" :class="statusClass">
          {{ statusText }}
        </div>
      </div>
    </header>

    <main class="app-main">
      <div class="split-view">
        <!-- Chat Panel (LEFT) -->
        <div 
          v-if="showChat" 
          class="chat-panel"
          :style="{ width: chatPanel.size.value + 'px' }"
        >
          <Suspense>
            <ChatPanel />
            <template #fallback>
              <div class="loading-placeholder">Loading chat...</div>
            </template>
          </Suspense>
        </div>
        
        <!-- Resize Handle for Chat -->
        <div 
          v-if="showChat"
          class="resize-handle resize-handle-vertical"
          @mousedown="chatPanel.startResize"
          :class="{ resizing: chatPanel.isResizing.value }"
        ></div>
        
        <!-- Center Column: Editor + Terminal (MIDDLE) -->
        <div v-if="showEditor || showTerminal" class="center-column">
          <!-- Code Editor Panel -->
          <div 
            v-if="showEditor" 
            class="editor-panel"
            :style="showTerminal ? { height: `calc(100% - ${terminalPanel.size.value}px)` } : {}"
          >
            <Suspense>
              <EditorPanel 
                ref="editorRef"
                :theme="currentTheme"
                @content-change="handleEditorChange"
                @selection-change="handleSelectionChange"
              />
              <template #fallback>
                <div class="loading-placeholder">Loading editor...</div>
              </template>
            </Suspense>
            
            <!-- Loading overlay when opening file -->
            <div v-if="loadingFile" class="file-loading-overlay">
              <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Opening file...</p>
              </div>
            </div>
            
            <!-- Error message when file loading fails -->
            <div v-if="fileError" class="file-error-overlay" @click="fileError = null">
              <div class="error-message">
                <span class="error-icon">⚠️</span>
                <p>{{ fileError }}</p>
                <button @click="fileError = null" class="dismiss-btn">Dismiss</button>
              </div>
            </div>
          </div>
          
          <!-- Resize Handle for Terminal -->
          <div 
            v-if="showEditor && showTerminal"
            class="resize-handle resize-handle-horizontal"
            @mousedown="terminalPanel.startResize"
            :class="{ resizing: terminalPanel.isResizing.value }"
          ></div>
          
          <!-- Terminal Panel (BELOW EDITOR) -->
          <div 
            v-if="showTerminal" 
            class="terminal-panel"
            :style="{ height: terminalPanel.size.value + 'px' }"
          >
            <Suspense>
              <Terminal />
              <template #fallback>
                <div class="loading-placeholder">Loading terminal...</div>
              </template>
            </Suspense>
          </div>
        </div>
        
        <!-- Resize Handle for Files -->
        <div 
          v-if="showFileExplorer"
          class="resize-handle resize-handle-vertical"
          @mousedown="filePanel.startResize"
          :class="{ resizing: filePanel.isResizing.value }"
        ></div>
        
        <!-- File Explorer Panel (RIGHT) -->
        <div 
          v-if="showFileExplorer" 
          class="file-panel"
          :style="{ width: filePanel.size.value + 'px' }"
        >
          <Suspense>
            <FileExplorer @file-selected="handleFileSelected" />
            <template #fallback>
              <div class="loading-placeholder">Loading files...</div>
            </template>
          </Suspense>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, defineAsyncComponent, computed } from 'vue';
import { useSystem } from './composables/useSystem';
import { useResizable } from './composables/useResizable';
import ThemeToggle from './components/ThemeToggle.vue';

// Lazy load components for better startup performance
const ChatPanel = defineAsyncComponent(() => import('./components/ChatPanel.vue'));
const Terminal = defineAsyncComponent(() => import('./components/Terminal.vue'));
const FileExplorer = defineAsyncComponent(() => import('./components/FileExplorer.vue'));
const EditorPanel = defineAsyncComponent(() => import('./components/EditorPanel.vue'));

// Use Clean Architecture system composable
const { statusText, statusClass } = useSystem();

// Panel visibility controls
const showFileExplorer = ref(false);
const showEditor = ref(true); // Editor shown by default
const showChat = ref(true); // Chat shown by default
const showTerminal = ref(true); // Terminal shown by default

// Editor ref for API access
const editorRef = ref<InstanceType<typeof EditorPanel> | null>(null);

// Theme sync with data-theme attribute
const currentTheme = computed(() => {
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
});

// File loading state
const loadingFile = ref(false);
const fileError = ref<string | null>(null);

// Resizable panels
const chatPanel = useResizable({
  minSize: 300,
  maxSize: 600,
  defaultSize: 400,
  direction: 'horizontal'
});

const filePanel = useResizable({
  minSize: 200,
  maxSize: 400,
  defaultSize: 250,
  direction: 'horizontal'
});

const terminalPanel = useResizable({
  minSize: 150,
  maxSize: 500,
  defaultSize: 300,
  direction: 'vertical'
});

// File selection handler - opens file in editor
const handleFileSelected = async (filePath: string) => {
  console.log('📂 Opening file:', filePath);
  
  // Skip if it's a directory
  if (filePath.endsWith('/')) {
    console.log('⚠️ Skipping directory:', filePath);
    return;
  }
  
  // Skip if editor is not visible
  if (!showEditor.value) {
    console.log('⚠️ Editor is not visible, showing it...');
    showEditor.value = true;
    // Wait a bit for editor to mount
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  // Skip if editor is not ready
  if (!editorRef.value) {
    console.error('❌ Editor ref not available');
    fileError.value = 'Editor is not ready yet';
    return;
  }
  
  loadingFile.value = true;
  fileError.value = null;
  
  try {
    // Read file content via Electron API
    const response = await (window.electronAPI as any).readFile(filePath);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to read file');
    }
    
    const content = response.data?.content || '';
    const isBinary = response.data?.isBinary || false;
    
    // Handle binary files
    if (isBinary) {
      console.log('⚠️ Binary file detected:', filePath);
      fileError.value = 'Cannot open binary file in text editor';
      return;
    }
    
    // Create URI for the file (use file:// protocol for real files)
    const fileUri = `file:///${filePath}`;
    
    console.log('✅ File loaded, opening in editor:', fileUri);
    
    // Open file in editor (will create new tab or switch to existing)
    editorRef.value.openFile(fileUri, content);
    
    console.log('✅ File opened successfully:', filePath);
    
  } catch (err: any) {
    console.error('❌ Error opening file:', err);
    fileError.value = err.message || 'Failed to open file';
  } finally {
    loadingFile.value = false;
  }
};

// Editor event handlers
const handleEditorChange = (content: string) => {
  console.log('Editor content changed:', content.length, 'characters');
};

const handleSelectionChange = (selection: string) => {
  if (selection) {
    console.log('Selection changed:', selection.substring(0, 50) + '...');
  }
};
</script>

<style scoped>
.app {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-6);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-sm);
  z-index: 100;
}

.app-header h1 {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.header-controls {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.toggle-btn {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-md);
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toggle-btn:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border-dark);
  transform: translateY(-1px);
}

.toggle-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary-dark);
  color: var(--color-white);
}

.status-badge {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.status-badge.ready {
  background: var(--color-success-bg);
  color: var(--color-success);
  border: 1px solid var(--color-success-border);
}

.status-badge.loading {
  background: var(--color-warning-bg);
  color: var(--color-warning);
  border: 1px solid var(--color-warning-border);
}

.status-badge.error {
  background: var(--color-error-bg);
  color: var(--color-error);
  border: 1px solid var(--color-error-border);
}

.app-main {
  flex: 1;
  overflow: hidden;
  display: flex;
  gap: 0;
}

.split-view {
  display: flex;
  width: 100%;
  height: 100%;
  gap: 0;
}

/* Chat Panel (LEFT SIDE) */
.chat-panel {
  background: var(--color-bg-primary);
  border-right: 1px solid var(--color-border-light);
  overflow: hidden;
  flex-shrink: 0;
}

/* Center Column: Editor + Terminal (MIDDLE) */
.center-column {
  flex: 1;
  min-width: 400px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Code Editor Panel (TOP OF CENTER COLUMN) */
.editor-panel {
  background: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border-light);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative; /* For overlay positioning */
  flex-shrink: 0;
}

/* Terminal Panel (BOTTOM OF CENTER COLUMN) */
.terminal-panel {
  background: var(--color-bg-primary);
  border-right: 1px solid var(--color-border-light);
  overflow: hidden;
  flex-shrink: 0;
}

/* File Explorer Panel (RIGHT SIDE) */
.file-panel {
  background: var(--color-bg-secondary);
  overflow-y: auto;
  flex-shrink: 0;
}

/* Resize Handles */
.resize-handle {
  flex-shrink: 0;
  background: var(--color-border-light);
  transition: background-color var(--transition-fast);
  z-index: 10;
  position: relative;
}

.resize-handle-vertical {
  width: 4px;
  cursor: col-resize;
  min-width: 4px;
  max-width: 4px;
}

.resize-handle-horizontal {
  height: 4px;
  cursor: row-resize;
  min-height: 4px;
  max-height: 4px;
}

.resize-handle:hover,
.resize-handle.resizing {
  background: var(--color-primary);
}

.resize-handle-vertical:hover::after,
.resize-handle-vertical.resizing::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 3px;
  height: 40px;
  background: var(--color-primary-dark);
  border-radius: var(--radius-full);
  pointer-events: none;
}

.resize-handle-horizontal:hover::after,
.resize-handle-horizontal.resizing::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 3px;
  background: var(--color-primary-dark);
  border-radius: var(--radius-full);
  pointer-events: none;
}
.file-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-in;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  color: var(--color-text-primary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-border-medium);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-spinner p {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
}

/* File error overlay */
.file-error-overlay {
  position: absolute;
  top: var(--space-4);
  right: var(--space-4);
  z-index: 1000;
  animation: slideInRight 0.3s ease-out;
}

.error-message {
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  max-width: 300px;
  box-shadow: var(--shadow-lg);
}

.error-icon {
  font-size: 2rem;
}

.error-message p {
  margin: 0;
  color: var(--color-error);
  font-size: var(--font-size-sm);
  text-align: center;
  word-break: break-word;
}

.dismiss-btn {
  padding: var(--space-2) var(--space-4);
  background: var(--color-error);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.dismiss-btn:hover {
  background: var(--color-error-dark);
  transform: translateY(-1px);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* File loading overlay */
.file-loading-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-muted);
  font-style: italic;
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .split-view {
    flex-direction: column;
  }
  
  .chat-panel,
  .file-panel {
    width: 100% !important;
    max-width: 100%;
    height: 300px;
    border-right: none;
    border-bottom: 1px solid var(--color-border-light);
  }
  
  .center-column {
    min-width: 100%;
  }
  
  .terminal-panel {
    height: 200px !important;
    border-right: none;
  }
  
  .resize-handle {
    display: none;
  }
}
</style>
