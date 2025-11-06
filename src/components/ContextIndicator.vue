<template>
  <div class="context-indicator" :class="{ collapsed: isCollapsed }">
    <div class="context-header" @click="toggleCollapse">
      <div class="header-left">
        <span class="context-icon">📁</span>
        <span class="context-title">Context</span>
        <span class="file-count">{{ files.length }}</span>
      </div>
      <button class="collapse-button" :title="isCollapsed ? 'Uitklappen' : 'Inklappen'">
        {{ isCollapsed ? '▼' : '▲' }}
      </button>
    </div>
    
    <transition name="slide">
      <div v-if="!isCollapsed" class="context-content">
        <div v-if="files.length === 0" class="empty-state">
          <span class="empty-icon">📄</span>
          <p class="empty-text">Geen bestanden in context</p>
          <button @click="addFile" class="add-button-empty">
            <span>➕</span>
            Bestand toevoegen
          </button>
        </div>
        
        <div v-else class="file-list">
          <div
            v-for="file in files"
            :key="file.path"
            class="file-item"
          >
            <div class="file-info">
              <span class="file-icon">{{ getFileIcon(file.path) }}</span>
              <div class="file-details">
                <span class="file-name">{{ getFileName(file.path) }}</span>
                <span class="file-path">{{ getFilePath(file.path) }}</span>
              </div>
            </div>
            <button 
              @click="removeFile(file.path)"
              class="remove-button"
              title="Verwijder uit context"
            >
              ✕
            </button>
          </div>
        </div>
        
        <button v-if="files.length > 0" @click="addFile" class="add-button">
          <span>➕</span>
          Bestand toevoegen
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface ContextFile {
  path: string;
  name?: string;
}

interface Props {
  files: ContextFile[];
  collapsed?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false
});

const emit = defineEmits<{
  'add-file': [];
  'remove-file': [path: string];
}>();

const isCollapsed = ref(props.collapsed);

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value;
};

const addFile = () => {
  emit('add-file');
};

const removeFile = (path: string) => {
  emit('remove-file', path);
};

const getFileName = (path: string): string => {
  return path.split('/').pop() || path;
};

const getFilePath = (path: string): string => {
  const parts = path.split('/');
  parts.pop(); // Remove filename
  return parts.join('/') || '/';
};

const getFileIcon = (path: string): string => {
  const ext = path.split('.').pop()?.toLowerCase();
  const iconMap: Record<string, string> = {
    'js': '🟨',
    'ts': '🔷',
    'vue': '💚',
    'py': '🐍',
    'html': '🌐',
    'css': '🎨',
    'json': '📦',
    'md': '📝',
    'txt': '📄',
    'sh': '⚡'
  };
  return iconMap[ext || ''] || '📄';
};
</script>

<style scoped>
.context-indicator {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all var(--transition-base);
}

.context-indicator:hover {
  border-color: var(--color-border-medium);
  box-shadow: var(--shadow-sm);
}

.context-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
  user-select: none;
  transition: background var(--transition-fast);
}

.context-header:hover {
  background: var(--color-bg-hover);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.context-icon {
  font-size: var(--font-size-lg);
  line-height: 1;
}

.context-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.file-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 var(--space-2);
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.collapse-button {
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  padding: var(--space-1);
  transition: all var(--transition-fast);
}

.collapse-button:hover {
  color: var(--color-text-primary);
  transform: scale(1.2);
}

.context-content {
  border-top: 1px solid var(--color-border-light);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-6) var(--space-4);
  gap: var(--space-3);
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-text {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  margin: 0;
}

.file-list {
  display: flex;
  flex-direction: column;
  max-height: 300px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
  transition: background var(--transition-fast);
  animation: fileSlideIn var(--transition-base) var(--ease-out);
}

@keyframes fileSlideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.file-item:hover {
  background: var(--color-bg-hover);
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 0; /* Allow text truncation */
}

.file-icon {
  font-size: var(--font-size-lg);
  line-height: 1;
  flex-shrink: 0;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0; /* Allow text truncation */
}

.file-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-path {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-button {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--color-text-muted);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--font-size-sm);
  transition: all var(--transition-fast);
}

.remove-button:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
  transform: scale(1.1);
}

.add-button,
.add-button-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
  border: none;
  border-top: 1px solid var(--color-border-light);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-fast);
}

.add-button-empty {
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-md);
  margin: 0 var(--space-4) var(--space-4);
  width: auto;
}

.add-button:hover,
.add-button-empty:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

/* Slide transition */
.slide-enter-active,
.slide-leave-active {
  transition: all var(--transition-base);
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}

.slide-enter-to,
.slide-leave-from {
  max-height: 500px;
  opacity: 1;
}
</style>
