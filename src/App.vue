<template>
  <div class="app">
    <header class="app-header">
      <h1>Omni</h1>
      <div class="header-controls">
        <button 
          @click="showFileExplorer = !showFileExplorer" 
          class="toggle-btn"
          :class="{ active: showFileExplorer }"
        >
          📁 Files
        </button>
        <div class="status-badge" :class="statusClass">
          {{ statusText }}
        </div>
      </div>
    </header>

    <main class="app-main">
      <div class="split-view">
        <!-- File Explorer (conditionally loaded) -->
        <div v-if="showFileExplorer" class="file-panel">
          <Suspense>
            <FileExplorer />
            <template #fallback>
              <div class="loading-placeholder">Loading files...</div>
            </template>
          </Suspense>
        </div>
        
        <div class="left-panel">
          <Suspense>
            <ChatPanel />
            <template #fallback>
              <div class="loading-placeholder">Loading chat...</div>
            </template>
          </Suspense>
        </div>
        
        <div class="right-panel">
          <Suspense>
            <Terminal />
            <template #fallback>
              <div class="loading-placeholder">Loading terminal...</div>
            </template>
          </Suspense>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, defineAsyncComponent } from 'vue';
import { useSystem } from './composables/useSystem';

// Lazy load components for better startup performance
const ChatPanel = defineAsyncComponent(() => import('./components/ChatPanel.vue'));
const Terminal = defineAsyncComponent(() => import('./components/Terminal.vue'));
const FileExplorer = defineAsyncComponent(() => import('./components/FileExplorer.vue'));

// Use Clean Architecture system composable
const { statusText, statusClass } = useSystem();
const showFileExplorer = ref(false);
</script>

<style scoped>
.app {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #d4d4d4;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #252526;
  border-bottom: 1px solid #3e3e42;
}

.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #ffffff;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.toggle-btn {
  padding: 0.375rem 0.75rem;
  border: 1px solid #3e3e42;
  border-radius: 6px;
  background: #2d2d30;
  color: #d4d4d4;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  background: #3e3e42;
  border-color: #555;
}

.toggle-btn.active {
  background: #0e639c;
  border-color: #0e639c;
  color: white;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-badge.ready {
  background: #10b981;
  color: white;
}

.status-badge.loading {
  background: #f59e0b;
  color: white;
}

.status-badge.error {
  background: #ef4444;
  color: white;
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
}

.file-panel {
  width: 250px;
  min-width: 200px;
  max-width: 300px;
  background: #252526;
  border-right: 1px solid #3e3e42;
}

.left-panel {
  flex: 1;
  min-width: 0;
  border-right: 1px solid #3e3e42;
}

.right-panel {
  width: 500px;
  min-width: 300px;
  max-width: 50%;
  background: #1e1e1e;
}

.loading-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #888;
  font-style: italic;
}
</style>
