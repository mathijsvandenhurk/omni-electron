<template>
  <div class="tool-message" :class="[statusClass, { 'tool-expanded': isExpanded }]">
    <div class="tool-header" @click="toggleExpanded">
      <div class="tool-info">
        <span class="tool-icon">{{ statusIcon }}</span>
        <strong class="tool-name">{{ displayName }}</strong>
        <span class="tool-status" :class="`status-${status}`">{{ statusText }}</span>
        <span v-if="duration && status === 'done'" class="tool-duration">
          {{ duration.toFixed(2) }}s
        </span>
      </div>
      <button class="expand-button" :aria-label="isExpanded ? 'Collapse' : 'Expand'">
        {{ isExpanded ? '▼' : '▶' }}
      </button>
    </div>
    
    <!-- Expandable content -->
    <div v-if="isExpanded" class="tool-details">
      <!-- Arguments -->
      <div v-if="toolArgs && Object.keys(toolArgs).length > 0" class="tool-section">
        <h4>Parameters:</h4>
        <pre class="tool-code">{{ JSON.stringify(toolArgs, null, 2) }}</pre>
      </div>
      
      <!-- Result -->
      <div v-if="status === 'done' && result" class="tool-section">
        <h4>Result:</h4>
        <pre class="tool-code">{{ formatResult(result) }}</pre>
      </div>
      
      <!-- Error -->
      <div v-if="status === 'error' && error" class="tool-section tool-error">
        <h4>Error:</h4>
        <div class="error-message">{{ error }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface Props {
  toolName: string;
  toolArgs?: Record<string, any>;
  status: 'calling' | 'done' | 'error';
  result?: any;
  duration?: number;
  error?: string;
}

const props = defineProps<Props>();

const isExpanded = ref(false);

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value;
};

// Map tool names to friendly display names
const toolDisplayNames: Record<string, string> = {
  'list_files': 'List Files',
  'read_file': 'Read File', 
  'write_file': 'Write File',
  'grep_search': 'Search Files',
  'replace_in_file': 'Replace in File',
  'apply_diff': 'Apply Changes',
  'execute_command': 'Execute Command',
  'semantic_search': 'Semantic Search',
};

const displayName = computed(() => {
  return toolDisplayNames[props.toolName] || props.toolName;
});

const statusClass = computed(() => {
  return `tool-status-${props.status}`;
});

const statusIcon = computed(() => {
  switch (props.status) {
    case 'calling':
      return '⏳';
    case 'done':
      return '✓';
    case 'error':
      return '⚠️';
    default:
      return '🔧';
  }
});

const statusText = computed(() => {
  switch (props.status) {
    case 'calling':
      return 'Running...';
    case 'done':
      return 'Completed';
    case 'error':
      return 'Error';
    default:
      return '';
  }
});

const formatResult = (result: any): string => {
  if (typeof result === 'string') {
    // Truncate very long strings
    return result.length > 500 ? result.substring(0, 500) + '...' : result;
  }
  return JSON.stringify(result, null, 2);
};
</script>

<style scoped>
.tool-message {
  margin: 8px 0;
  padding: 8px 12px;
  border-left: 3px solid var(--tool-border-color, #6366f1);
  background: var(--tool-bg, rgba(99, 102, 241, 0.05));
  border-radius: 4px;
  font-size: 0.9em;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tool-message:hover {
  background: var(--tool-bg-hover, rgba(99, 102, 241, 0.1));
}

/* Status-specific styling */
.tool-status-calling {
  border-left-color: #f59e0b;
  background: rgba(245, 158, 11, 0.05);
}

.tool-status-calling:hover {
  background: rgba(245, 158, 11, 0.1);
}

.tool-status-done {
  border-left-color: #10b981;
  background: rgba(16, 185, 129, 0.05);
}

.tool-status-done:hover {
  background: rgba(16, 185, 129, 0.1);
}

.tool-status-error {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.tool-status-error:hover {
  background: rgba(239, 68, 68, 0.1);
}

.tool-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.tool-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.tool-icon {
  font-size: 1.1em;
}

.tool-name {
  font-weight: 600;
  color: var(--text-primary);
}

.tool-status {
  font-size: 0.85em;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.status-calling {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.status-done {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.status-error {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.tool-duration {
  font-size: 0.85em;
  color: var(--text-secondary);
  font-style: italic;
}

.expand-button {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  font-size: 0.8em;
  transition: transform 0.2s ease;
}

.tool-expanded .expand-button {
  transform: rotate(0deg);
}

.tool-details {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
}

.tool-section {
  margin-bottom: 12px;
}

.tool-section:last-child {
  margin-bottom: 0;
}

.tool-section h4 {
  margin: 0 0 6px 0;
  font-size: 0.85em;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tool-code {
  background: var(--code-bg, rgba(0, 0, 0, 0.05));
  border: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
  border-radius: 4px;
  padding: 8px;
  overflow-x: auto;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.85em;
  line-height: 1.4;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.tool-error {
  color: #ef4444;
}

.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 4px;
  padding: 8px;
  font-size: 0.9em;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .tool-message {
    background: rgba(99, 102, 241, 0.1);
  }
  
  .tool-message:hover {
    background: rgba(99, 102, 241, 0.15);
  }
  
  .tool-status-calling {
    background: rgba(245, 158, 11, 0.1);
  }
  
  .tool-status-done {
    background: rgba(16, 185, 129, 0.1);
  }
  
  .tool-status-error {
    background: rgba(239, 68, 68, 0.1);
  }
  
  .tool-code {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
  }
}
</style>
