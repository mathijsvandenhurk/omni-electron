<template>
  <div class="file-explorer">
    <div class="explorer-header">
      <h3>📁 File Explorer</h3>
      <button @click="refreshFiles" class="refresh-btn" title="Refresh">
        🔄
      </button>
    </div>
    <div class="explorer-content">
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else class="file-tree">
        <div v-for="file in files" :key="file" class="file-item" @click="selectFile(file)">
          <span class="file-icon">{{ getFileIcon(file) }}</span>
          <span class="file-name">{{ file }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const files = ref<string[]>([]);
const loading = ref(false);
const error = ref('');

const getFileIcon = (filename: string) => {
  if (filename.endsWith('/')) return '📁';
  if (filename.endsWith('.vue')) return '🖼️';
  if (filename.endsWith('.ts') || filename.endsWith('.js')) return '📜';
  if (filename.endsWith('.py')) return '🐍';
  if (filename.endsWith('.json')) return '📋';
  if (filename.endsWith('.css')) return '🎨';
  return '📄';
};

const loadFiles = async () => {
  loading.value = true;
  error.value = '';
  try {
    const response = await window.electronAPI.listFiles('.');
    if (response.success) {
      files.value = response.data?.files || [];
    } else {
      error.value = response.error || 'Failed to load files';
    }
  } catch (err: any) {
    error.value = err.message || 'Unknown error';
  } finally {
    loading.value = false;
  }
};

const refreshFiles = () => {
  loadFiles();
};

const selectFile = (file: string) => {
  console.log('Selected file:', file);
  // TODO: Add file preview or edit functionality
};

onMounted(() => {
  loadFiles();
});
</script>

<style scoped>
.file-explorer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  border-right: 1px solid #3e3e42;
}

.explorer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #252526;
  border-bottom: 1px solid #3e3e42;
}

.explorer-header h3 {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #ffffff;
}

.refresh-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.refresh-btn:hover {
  opacity: 1;
}

.explorer-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.loading, .error {
  padding: 1rem;
  text-align: center;
  color: #858585;
  font-size: 0.875rem;
}

.error {
  color: #ef4444;
}

.file-tree {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 0.875rem;
}

.file-item:hover {
  background: #2d2d30;
}

.file-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.file-name {
  color: #d4d4d4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>