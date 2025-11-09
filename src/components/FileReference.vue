<template>
  <span 
    class="file-reference" 
    @click="openFile"
    :title="fullPath"
    role="button"
    tabindex="0"
    @keydown.enter="openFile"
  >
    <span class="file-icon">📄</span>
    <span class="file-name">{{ fileName }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  path: string
}

const props = defineProps<Props>()

// Extract just the filename from the path
const fileName = computed(() => {
  const parts = props.path.split('/')
  return parts[parts.length - 1]
})

// Get the full path (for now just return as-is, could resolve relative paths later)
const fullPath = computed(() => {
  return props.path
})

// Open file in editor using electron API
const openFile = async () => {
  try {
    // Check if electronAPI exists (we're in Electron context)
    if (window.electronAPI && window.electronAPI.openFile) {
      await window.electronAPI.openFile(fullPath.value)
    } else {
      console.warn('electronAPI.openFile not available')
      // Fallback: copy path to clipboard
      await navigator.clipboard.writeText(fullPath.value)
      console.info('File path copied to clipboard:', fullPath.value)
    }
  } catch (error) {
    console.error('Error opening file:', error)
  }
}
</script>

<style scoped>
.file-reference {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 4px;
  color: #60a5fa;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.file-reference:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
  color: #93c5fd;
  transform: translateY(-1px);
}

.file-reference:active {
  transform: translateY(0);
}

.file-icon {
  font-size: 0.9em;
  line-height: 1;
}

.file-name {
  font-weight: 500;
  line-height: 1;
}

/* Keyboard focus indicator */
.file-reference:focus {
  outline: 2px solid rgba(59, 130, 246, 0.5);
  outline-offset: 2px;
}

.file-reference:focus:not(:focus-visible) {
  outline: none;
}
</style>
