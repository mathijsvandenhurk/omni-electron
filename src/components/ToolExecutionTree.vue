<template>
  <div class="tool-execution-tree">
    <h3 class="tree-header">
      <span class="header-icon">🔧</span>
      <span>Tool Uitvoeringen</span>
      <span class="tool-count">({{ tools.length }})</span>
    </h3>

    <div class="tree-content">
      <div 
        v-for="(tool, index) in tools" 
        :key="index"
        class="tool-item"
        :class="{ expanded: expandedTools.has(index) }"
      >
        <!-- Tool header -->
        <div class="tool-header" @click="toggleTool(index)">
          <div class="header-left">
            <span class="expand-icon">{{ expandedTools.has(index) ? '▼' : '▶' }}</span>
            <span class="status-icon" :class="`status-${tool.status}`">
              {{ getStatusIcon(tool.status) }}
            </span>
            <span class="tool-name">{{ tool.name }}</span>
            <span v-if="tool.duration" class="tool-duration">
              {{ formatDuration(tool.duration) }}
            </span>
          </div>
          <div class="header-right">
            <span class="status-badge" :class="`status-${tool.status}`">
              {{ getStatusLabel(tool.status) }}
            </span>
          </div>
        </div>

        <!-- Tool details (expandable) -->
        <div v-if="expandedTools.has(index)" class="tool-details">
          <!-- Arguments -->
          <div v-if="tool.args && Object.keys(tool.args).length > 0" class="detail-section">
            <div class="section-header">
              <span class="section-icon">📥</span>
              <span class="section-title">Argumenten</span>
            </div>
            <div class="section-content">
              <pre class="json-content">{{ formatJson(tool.args) }}</pre>
            </div>
          </div>

          <!-- Result -->
          <div v-if="tool.result !== undefined" class="detail-section">
            <div class="section-header">
              <span class="section-icon">{{ tool.status === 'success' ? '📤' : '⚠️' }}</span>
              <span class="section-title">{{ tool.status === 'success' ? 'Resultaat' : 'Fout' }}</span>
            </div>
            <div class="section-content">
              <pre class="json-content" :class="{ error: tool.status === 'error' }">{{ formatResult(tool.result) }}</pre>
            </div>
          </div>

          <!-- Timing info -->
          <div v-if="tool.startTime" class="detail-section timing-section">
            <div class="timing-info">
              <span class="timing-label">Start:</span>
              <span class="timing-value">{{ formatTimestamp(tool.startTime) }}</span>
            </div>
            <div v-if="tool.duration" class="timing-info">
              <span class="timing-label">Duur:</span>
              <span class="timing-value">{{ formatDuration(tool.duration) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import type { ToolExecution } from '../types/events';

interface Props {
  tools: ToolExecution[];
  defaultExpanded?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  defaultExpanded: false
});

// State
const expandedTools = ref<Set<number>>(new Set());

// Function to expand all tools if defaultExpanded is true
function initializeExpanded() {
  if (props.defaultExpanded && props.tools.length > 0) {
    // Expand ALL tools, not just the first one
    expandedTools.value.clear();
    for (let i = 0; i < props.tools.length; i++) {
      expandedTools.value.add(i);
    }
  }
}

// Initialize on mount
onMounted(() => {
  initializeExpanded();
});

// Watch for changes in tools or defaultExpanded prop
watch([() => props.tools, () => props.defaultExpanded], () => {
  initializeExpanded();
}, { immediate: true });

// Methods
function toggleTool(index: number) {
  if (expandedTools.value.has(index)) {
    expandedTools.value.delete(index);
  } else {
    expandedTools.value.add(index);
  }
}

function getStatusIcon(status: string): string {
  const icons: Record<string, string> = {
    'running': '⏳',
    'success': '✅',
    'error': '❌'
  };
  return icons[status] || '❓';
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    'running': 'Actief',
    'success': 'Voltooid',
    'error': 'Mislukt'
  };
  return labels[status] || status;
}

function formatJson(obj: any): string {
  try {
    return JSON.stringify(obj, null, 2);
  } catch (err) {
    return String(obj);
  }
}

function formatResult(result: any): string {
  if (typeof result === 'string') {
    return result;
  }
  return formatJson(result);
}

function formatTimestamp(timestamp: number | string): string {
  const date = typeof timestamp === 'number' ? new Date(timestamp) : new Date(timestamp);
  const time = date.toLocaleTimeString('nl-NL', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
  const ms = String(date.getMilliseconds()).padStart(3, '0');
  return `${time}.${ms}`;
}

function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(2)}s`;
  } else {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(1);
    return `${minutes}m ${seconds}s`;
  }
}
</script>

<style scoped>
.tool-execution-tree {
  background: var(--vscode-editor-background, #1e1e1e);
  border: 1px solid var(--vscode-panel-border, #2d2d2d);
  border-radius: 6px;
  overflow: hidden;
}

/* Header */
.tree-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  margin: 0;
  background: var(--vscode-editorGroupHeader-tabsBackground, #252526);
  color: var(--vscode-editor-foreground, #d4d4d4);
  font-size: 0.95rem;
  font-weight: 600;
  border-bottom: 1px solid var(--vscode-panel-border, #2d2d2d);
}

.header-icon {
  font-size: 1.1rem;
}

.tool-count {
  color: var(--vscode-descriptionForeground, #858585);
  font-weight: normal;
  font-size: 0.9rem;
}

/* Tree content */
.tree-content {
  padding: 0.5rem;
}

/* Tool item */
.tool-item {
  margin-bottom: 0.5rem;
  border: 1px solid var(--vscode-panel-border, #2d2d2d);
  border-radius: 4px;
  background: var(--vscode-list-inactiveSelectionBackground, #37373d);
  transition: all 0.2s ease;
}

.tool-item:hover {
  border-color: var(--vscode-focusBorder, #007fd4);
}

.tool-item.expanded {
  background: var(--vscode-editor-background, #1e1e1e);
}

/* Tool header */
.tool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  cursor: pointer;
  user-select: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  min-width: 0;
}

.expand-icon {
  font-size: 0.7rem;
  color: var(--vscode-descriptionForeground, #858585);
  transition: transform 0.2s;
}

.tool-item.expanded .expand-icon {
  transform: rotate(0deg);
}

.status-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.status-icon.status-running {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

.tool-name {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  font-size: 0.9rem;
  color: var(--vscode-textLink-foreground, #4fc1ff);
  font-weight: 500;
}

.tool-duration {
  font-size: 0.85rem;
  color: var(--vscode-descriptionForeground, #858585);
  font-family: monospace;
}

.header-right {
  display: flex;
  align-items: center;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.status-running {
  background: var(--vscode-editorWarning-foreground, #cca700);
  color: var(--vscode-editor-background, #1e1e1e);
}

.status-badge.status-success {
  background: var(--vscode-testing-iconPassed, #73c991);
  color: var(--vscode-editor-background, #1e1e1e);
}

.status-badge.status-error {
  background: var(--vscode-testing-iconFailed, #f48771);
  color: var(--vscode-editor-background, #1e1e1e);
}

/* Tool details */
.tool-details {
  padding: 0 0.75rem 0.75rem 0.75rem;
  border-top: 1px solid var(--vscode-panel-border, #2d2d2d);
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 1000px;
  }
}

.detail-section {
  margin-top: 0.75rem;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.section-icon {
  font-size: 0.9rem;
}

.section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--vscode-descriptionForeground, #858585);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-content {
  background: var(--vscode-textCodeBlock-background, #2d2d2d);
  border-radius: 4px;
  padding: 0.75rem;
  overflow-x: auto;
}

.json-content {
  margin: 0;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Consolas', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--vscode-editor-foreground, #d4d4d4);
  white-space: pre-wrap;
  word-break: break-word;
}

.json-content.error {
  color: var(--vscode-errorForeground, #f48771);
}

/* Timing section */
.timing-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding-top: 0.5rem;
  border-top: 1px dashed var(--vscode-panel-border, #2d2d2d);
}

.timing-info {
  display: flex;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.timing-label {
  color: var(--vscode-descriptionForeground, #858585);
  min-width: 4rem;
}

.timing-value {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  color: var(--vscode-editor-foreground, #d4d4d4);
}
</style>
