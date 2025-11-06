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
import ThemeToggle from './components/ThemeToggle.vue';

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
}

.file-panel {
  width: 250px;
  min-width: 200px;
  max-width: 300px;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border-light);
}

.left-panel {
  flex: 1;
  min-width: 0;
  border-right: 1px solid var(--color-border-light);
}

.right-panel {
  width: 500px;
  min-width: 300px;
  max-width: 50%;
  background: var(--color-bg-primary);
}

.loading-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-muted);
  font-style: italic;
}
</style>
