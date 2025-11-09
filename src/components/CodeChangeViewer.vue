<template>
  <div class="code-change-viewer" :class="{ collapsed: isCollapsed }">
    <!-- Header -->
    <div class="code-header" @click="toggleCollapse">
      <div class="header-left">
        <span class="collapse-icon">{{ isCollapsed ? '▶' : '▼' }}</span>
        <span class="file-icon">{{ getFileIcon(filePath) }}</span>
        <span class="file-path">{{ filePath }}</span>
        <span v-if="lineRange" class="line-range">{{ formatLineRange(lineRange) }}</span>
      </div>
      <div class="header-right">
        <span v-if="operation" class="operation-badge" :class="`operation-${operation}`">
          {{ operationLabel(operation) }}
        </span>
        <button 
          class="copy-button" 
          @click.stop="copyCode"
          :title="copySuccess ? 'Gekopieerd!' : 'Kopieer code'"
        >
          {{ copySuccess ? '✓' : '📋' }}
        </button>
      </div>
    </div>

    <!-- Code content -->
    <div v-if="!isCollapsed" class="code-content">
      <pre class="line-numbers"><code v-html="highlightedCode" :class="`language-${language}`"></code></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import Prism from 'prismjs';

// Import common language components
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-markup'; // HTML
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-markdown';

// Import VS Code Dark theme
import 'prismjs/themes/prism-tomorrow.css';

interface Props {
  // Support both old and new prop names for compatibility
  file?: string;
  filePath?: string;
  lineStart?: number;
  lineEnd?: number;
  lineRange?: string;
  code: string;
  language?: string;
  operation?: 'create' | 'modify' | 'delete';
  initialCollapsed?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  language: 'text',
  operation: 'modify',
  initialCollapsed: false
});

// State
const isCollapsed = ref(props.initialCollapsed);
const copySuccess = ref(false);

// Computed for backwards compatibility
const filePath = computed(() => props.filePath || props.file || '');
const lineRange = computed(() => {
  if (props.lineRange) return props.lineRange;
  if (props.lineStart && props.lineEnd) {
    return `${props.lineStart} - ${props.lineEnd}`;
  }
  return '';
});

// Computed
const highlightedCode = computed(() => {
  try {
    // Get the appropriate Prism grammar
    const grammar = Prism.languages[props.language || 'text'] || Prism.languages.text;
    
    // Highlight the code
    const highlighted = Prism.highlight(props.code, grammar, props.language || 'text');
    
    // Add line numbers if lineRange is provided
    if (lineRange.value) {
      return addLineNumbers(highlighted, lineRange.value);
    }
    
    return highlighted;
  } catch (err) {
    console.error('Syntax highlighting error:', err);
    return escapeHtml(props.code);
  }
});

// Methods
function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value;
}

function copyCode() {
  navigator.clipboard.writeText(props.code).then(() => {
    copySuccess.value = true;
    setTimeout(() => {
      copySuccess.value = false;
    }, 2000);
  }).catch(err => {
    console.error('Copy failed:', err);
  });
}

function getFileIcon(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase();
  
  const iconMap: Record<string, string> = {
    'js': '📜',
    'ts': '📘',
    'jsx': '⚛️',
    'tsx': '⚛️',
    'vue': '💚',
    'py': '🐍',
    'json': '📋',
    'html': '🌐',
    'css': '🎨',
    'scss': '🎨',
    'md': '📝',
    'txt': '📄',
    'sh': '⚡',
    'yml': '⚙️',
    'yaml': '⚙️'
  };
  
  return iconMap[ext || ''] || '📄';
}

function formatLineRange(range: string): string {
  return `lines ${range}`;
}

function operationLabel(op: string): string {
  const labels: Record<string, string> = {
    'create': 'Nieuw',
    'modify': 'Gewijzigd',
    'delete': 'Verwijderd'
  };
  return labels[op] || op;
}

function addLineNumbers(html: string, lineRange: string): string {
  // Parse line range (e.g., "125 - 127" or "125")
  const parts = lineRange.split('-').map(s => parseInt(s.trim()));
  const startLine = parts[0] || 1;
  
  // Split highlighted HTML into lines
  const lines = html.split('\n');
  
  // Add line numbers to each line
  return lines.map((line, index) => {
    const lineNum = startLine + index;
    return `<span class="line-number">${lineNum}</span>${line}`;
  }).join('\n');
}

function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
</script>

<style scoped>
.code-change-viewer {
  border: 1px solid var(--vscode-panel-border, #2d2d2d);
  border-radius: 6px;
  overflow: hidden;
  background: var(--vscode-editor-background, #1e1e1e);
  transition: all 0.2s ease;
}

.code-change-viewer:hover {
  border-color: var(--vscode-focusBorder, #007fd4);
}

/* Header */
.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--vscode-editorGroupHeader-tabsBackground, #252526);
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.code-header:hover {
  background: var(--vscode-list-hoverBackground, #2a2d2e);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  min-width: 0;
}

.collapse-icon {
  font-size: 0.75rem;
  color: var(--vscode-descriptionForeground, #858585);
  transition: transform 0.2s;
}

.file-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.file-path {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  font-size: 0.9rem;
  color: var(--vscode-editor-foreground, #d4d4d4);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.line-range {
  font-size: 0.85rem;
  color: var(--vscode-descriptionForeground, #858585);
  flex-shrink: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.operation-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.operation-create {
  background: var(--vscode-gitDecoration-addedResourceForeground, #81b88b);
  color: var(--vscode-editor-background, #1e1e1e);
}

.operation-modify {
  background: var(--vscode-gitDecoration-modifiedResourceForeground, #e2c08d);
  color: var(--vscode-editor-background, #1e1e1e);
}

.operation-delete {
  background: var(--vscode-gitDecoration-deletedResourceForeground, #c74e39);
  color: var(--vscode-editor-foreground, #d4d4d4);
}

.copy-button {
  padding: 0.25rem 0.5rem;
  background: var(--vscode-button-secondaryBackground, #3a3d41);
  color: var(--vscode-button-secondaryForeground, #d4d4d4);
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.copy-button:hover {
  background: var(--vscode-button-secondaryHoverBackground, #45494e);
}

.copy-button:active {
  transform: scale(0.95);
}

/* Code content */
.code-content {
  padding: 1rem;
  background: var(--vscode-editor-background, #1e1e1e);
  overflow-x: auto;
}

.line-numbers {
  margin: 0;
  padding: 0;
  counter-reset: line;
}

.line-numbers code {
  display: block;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Consolas', monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  tab-size: 4;
  -moz-tab-size: 4;
}

/* Line number styling */
.line-numbers :deep(.line-number) {
  display: inline-block;
  width: 3em;
  text-align: right;
  margin-right: 1em;
  padding-right: 0.5em;
  color: var(--vscode-editorLineNumber-foreground, #858585);
  border-right: 1px solid var(--vscode-panel-border, #2d2d2d);
  user-select: none;
}

/* Prism theme overrides for VS Code style */
.code-content :deep(.token.comment),
.code-content :deep(.token.prolog),
.code-content :deep(.token.doctype),
.code-content :deep(.token.cdata) {
  color: var(--vscode-comments, #6a9955);
}

.code-content :deep(.token.punctuation) {
  color: var(--vscode-editor-foreground, #d4d4d4);
}

.code-content :deep(.token.property),
.code-content :deep(.token.tag),
.code-content :deep(.token.boolean),
.code-content :deep(.token.number),
.code-content :deep(.token.constant),
.code-content :deep(.token.symbol),
.code-content :deep(.token.deleted) {
  color: var(--vscode-variable, #9cdcfe);
}

.code-content :deep(.token.selector),
.code-content :deep(.token.attr-name),
.code-content :deep(.token.string),
.code-content :deep(.token.char),
.code-content :deep(.token.builtin),
.code-content :deep(.token.inserted) {
  color: var(--vscode-string, #ce9178);
}

.code-content :deep(.token.operator),
.code-content :deep(.token.entity),
.code-content :deep(.token.url),
.code-content :deep(.language-css .token.string),
.code-content :deep(.style .token.string) {
  color: var(--vscode-keyword, #569cd6);
}

.code-content :deep(.token.atrule),
.code-content :deep(.token.attr-value),
.code-content :deep(.token.keyword) {
  color: var(--vscode-keyword, #c586c0);
}

.code-content :deep(.token.function),
.code-content :deep(.token.class-name) {
  color: var(--vscode-function, #dcdcaa);
}

.code-content :deep(.token.regex),
.code-content :deep(.token.important),
.code-content :deep(.token.variable) {
  color: var(--vscode-variable, #9cdcfe);
}

/* Collapsed state */
.collapsed .code-content {
  display: none;
}
</style>
