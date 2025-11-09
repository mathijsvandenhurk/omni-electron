<template>
  <div class="streaming-response" ref="containerRef">
    <!-- Response metadata header -->
    <div v-if="metadata" class="response-metadata">
      <span class="timestamp">Start: {{ formatTimestamp(metadata.requestId) }}</span>
      <span v-if="isComplete && metadata.duration" class="duration">
        {{ formatDuration(metadata.duration) }}
      </span>
    </div>

    <!-- Narrative content with markdown rendering -->
    <div 
      v-if="narrative" 
      class="narrative-content"
      ref="narrativeContentRef"
    ></div>

    <!-- Tool executions tree -->
    <ToolExecutionTree 
      v-if="tools.length > 0"
      :tools="tools"
      class="tools-section"
    />

    <!-- Code changes viewer -->
    <div v-if="codeChanges.length > 0" class="code-changes-section">
      <h3>Code wijzigingen</h3>
      <CodeChangeViewer 
        v-for="(change, index) in codeChanges"
        :key="`code-${index}`"
        :file-path="change.file"
        :code="change.code"
        :language="change.language"
        :line-range="`${change.lineStart} - ${change.lineEnd}`"
      />
    </div>

    <!-- File references -->
    <div v-if="fileReferences.length > 0" class="file-references">
      <h3>Bestanden</h3>
      <div 
        v-for="(ref, index) in fileReferences"
        :key="`ref-${index}`"
        class="file-reference"
        @click="openFile(ref.path)"
      >
        <span class="file-icon">📄</span>
        <span class="file-path">{{ ref.path }}</span>
        <span v-if="ref.lineStart && ref.lineEnd" class="line-range">
          lines {{ ref.lineStart }}-{{ ref.lineEnd }}
        </span>
      </div>
    </div>

    <!-- Error display -->
    <div v-if="error" class="error-container">
      <span class="error-icon">⚠️</span>
      <div class="error-content">
        <div class="error-message">{{ error.message }}</div>
        <div v-if="error.details" class="error-details">
          {{ JSON.stringify(error.details, null, 2) }}
        </div>
      </div>
    </div>

    <!-- Streaming indicator -->
    <div ref="streamingIndicatorRef" class="streaming-indicator" style="display: none;">
      <span class="pulse-dot"></span>
      <span class="streaming-text">Streaming...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';
import { marked } from 'marked';
import type { 
  OmniEvent, 
  ResponseMetadata,
  ToolExecution
} from '../types/events';
import CodeChangeViewer from './CodeChangeViewer.vue';
import ToolExecutionTree from './ToolExecutionTree.vue';

// Local interfaces for component state
interface CodeChange {
  file: string;
  lineStart: number;
  lineEnd: number;
  code: string;
  language: string;
}

interface FileReference {
  path: string;
  lineStart?: number;
  lineEnd?: number;
  context?: string;
}

interface ErrorInfo {
  message: string;
  code?: string;
  details?: any;
}

// Props
interface Props {
  requestId: string;
  autoScroll?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  autoScroll: true
});

// Emits
const emit = defineEmits<{
  complete: [requestId: string];
  error: [error: ErrorInfo];
}>();

// State
const containerRef = ref<HTMLElement | null>(null);
const narrativeContentRef = ref<HTMLElement | null>(null);
const streamingIndicatorRef = ref<HTMLElement | null>(null);
const narrative = ref<string>('');
const metadata = ref<ResponseMetadata | null>(null);
const tools = ref<ToolExecution[]>([]);
const codeChanges = ref<CodeChange[]>([]);
const fileReferences = ref<FileReference[]>([]);
const error = ref<ErrorInfo | null>(null);
const isStreaming = ref<boolean>(false);
const isComplete = ref<boolean>(false);

// Markdown buffer for incomplete blocks
const markdownBuffer = ref<string>('');

// Configure marked for safe HTML and code highlighting
marked.setOptions({
  breaks: true,
  gfm: true
});

// Function to manually update narrative DOM (bypasses Vue's batching)
function updateNarrativeDOM() {
  if (narrativeContentRef.value && narrative.value) {
    try {
      const html = marked.parse(narrative.value) as string;
      narrativeContentRef.value.innerHTML = html;
    } catch (err) {
      console.error('Markdown parsing error:', err);
      narrativeContentRef.value.textContent = narrative.value;
    }
  }
}

// Function to manually show/hide streaming indicator (bypasses Vue's batching)
function updateStreamingIndicator(show: boolean) {
  if (streamingIndicatorRef.value) {
    streamingIndicatorRef.value.style.display = show ? 'flex' : 'none';
  }
}

// Methods
function handleEvent(event: OmniEvent) {
  console.log('[StreamingResponse] 🔥 handleEvent called:', event.type, 'narrative length:', narrative.value.length);
  
  switch (event.type) {
    case 'response_start':
      isStreaming.value = true;
      isComplete.value = false;
      error.value = null;
      // Initialize metadata with requestId
      metadata.value = {
        requestId: event.data.requestId,
        duration: 0,
        tokensUsed: 0,
        toolsExecuted: [],
        filesModified: []
      };
      // Show streaming indicator immediately
      updateStreamingIndicator(true);
      console.log('[StreamingResponse] ✅ response_start handled, isStreaming:', isStreaming.value);
      break;

    case 'narrative_chunk':
      // Append narrative chunk
      narrative.value += event.data.text;
      markdownBuffer.value += event.data.text;
      console.log('[StreamingResponse] 📝 narrative_chunk added:', event.data.text.length, 'chars, total now:', narrative.value.length);
      
      // Force immediate DOM update (bypasses Vue's batching)
      updateNarrativeDOM();
      
      if (props.autoScroll) {
        nextTick(() => scrollToBottom());
      }
      break;

    case 'progress_update':
      // Could show progress indicator in future
      break;

    case 'tool_start':
      // Add tool execution (in-progress state)
      tools.value.push({
        name: event.data.name,
        args: event.data.args,
        status: 'running',
        startTime: event.data.timestamp
      });
      
      if (props.autoScroll) {
        nextTick(() => scrollToBottom());
      }
      break;

    case 'tool_result':
      // Update tool execution with result
      const toolIndex = tools.value.findIndex(
        t => t.name === event.data.name && t.status === 'running'
      );
      
      if (toolIndex !== -1) {
        tools.value[toolIndex] = {
          ...tools.value[toolIndex],
          result: event.data.result,
          status: event.data.status,
          duration: event.data.duration,
          error: event.data.error
        };
      }
      break;

    case 'code_change':
      codeChanges.value.push({
        file: event.data.file,
        lineStart: event.data.lineStart,
        lineEnd: event.data.lineEnd,
        code: event.data.code,
        language: event.data.language
      });
      
      if (props.autoScroll) {
        nextTick(() => scrollToBottom());
      }
      break;

    case 'file_reference':
      fileReferences.value.push({
        path: event.data.path,
        lineStart: event.data.lineStart,
        lineEnd: event.data.lineEnd,
        context: event.data.context
      });
      break;

    case 'error':
      error.value = {
        message: event.data.message,
        code: event.data.code,
        details: event.data.details
      };
      isStreaming.value = false;
      // Hide streaming indicator on error
      updateStreamingIndicator(false);
      emit('error', error.value);
      break;

    case 'response_complete':
      console.log('[StreamingResponse] 🏁 response_complete, setting isStreaming=false');
      isStreaming.value = false;
      isComplete.value = true;
      if (event.data.metadata) {
        metadata.value = event.data.metadata;
      }
      
      // Final DOM update
      updateNarrativeDOM();
      
      // Hide streaming indicator immediately
      updateStreamingIndicator(false);
      
      emit('complete', props.requestId);
      console.log('[StreamingResponse] ✅ Complete event emitted, isStreaming:', isStreaming.value);
      break;
  }
}

function scrollToBottom() {
  if (containerRef.value) {
    containerRef.value.scrollIntoView({ 
      behavior: 'smooth', 
      block: 'end' 
    });
  }
}

function formatTimestamp(_requestId: string): string {
  // Simple timestamp display
  return new Date().toLocaleTimeString('nl-NL', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  });
}

function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  } else {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}m ${seconds}s`;
  }
}

function openFile(filePath: string) {
  // Use Electron IPC to open file
  if (window.electronAPI?.openFile) {
    window.electronAPI.openFile(filePath);
  }
}

// Expose methods for parent component
defineExpose({
  handleEvent,
  getNarrative: () => narrative.value,
  clear: () => {
    narrative.value = '';
    metadata.value = null;
    tools.value = [];
    codeChanges.value = [];
    fileReferences.value = [];
    error.value = null;
    isStreaming.value = false;
    isComplete.value = false;
    markdownBuffer.value = '';
  }
});
</script>

<style scoped>
.streaming-response {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: var(--vscode-editor-background, #1e1e1e);
  color: var(--vscode-editor-foreground, #d4d4d4);
  border-radius: 6px;
  max-width: 100%;
}

/* Metadata header */
.response-metadata {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--vscode-descriptionForeground, #858585);
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--vscode-panel-border, #2d2d2d);
}

.timestamp {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
}

.model {
  color: var(--vscode-textLink-foreground, #4fc1ff);
}

.duration {
  margin-left: auto;
}

/* Narrative content */
.narrative-content {
  line-height: 1.6;
  color: var(--vscode-editor-foreground, #d4d4d4);
}

.narrative-content :deep(p) {
  margin: 0.5rem 0;
}

.narrative-content :deep(code) {
  background: var(--vscode-textCodeBlock-background, #2d2d2d);
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  font-size: 0.9em;
}

.narrative-content :deep(pre) {
  background: var(--vscode-textCodeBlock-background, #2d2d2d);
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.narrative-content :deep(pre code) {
  background: none;
  padding: 0;
}

.narrative-content :deep(h1),
.narrative-content :deep(h2),
.narrative-content :deep(h3) {
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  color: var(--vscode-textLink-foreground, #4fc1ff);
}

.narrative-content :deep(ul),
.narrative-content :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 2rem;
}

.narrative-content :deep(li) {
  margin: 0.25rem 0;
}

.narrative-content :deep(a) {
  color: var(--vscode-textLink-foreground, #4fc1ff);
  text-decoration: none;
}

.narrative-content :deep(a:hover) {
  text-decoration: underline;
}

/* Code changes section */
.code-changes-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.code-changes-section h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: var(--vscode-textLink-foreground, #4fc1ff);
}

/* File references */
.file-references {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-references h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: var(--vscode-textLink-foreground, #4fc1ff);
}

.file-reference {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--vscode-list-hoverBackground, #2a2d2e);
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.file-reference:hover {
  background: var(--vscode-list-activeSelectionBackground, #37373d);
}

.file-icon {
  font-size: 1rem;
}

.file-path {
  flex: 1;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  font-size: 0.9rem;
}

.line-range {
  color: var(--vscode-descriptionForeground, #858585);
  font-size: 0.85rem;
}

/* Error display */
.error-container {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--vscode-inputValidation-errorBackground, #5a1d1d);
  border: 1px solid var(--vscode-inputValidation-errorBorder, #be1100);
  border-radius: 4px;
}

.error-icon {
  font-size: 1.25rem;
}

.error-content {
  flex: 1;
}

.error-message {
  font-weight: 600;
  color: var(--vscode-errorForeground, #f48771);
  margin-bottom: 0.25rem;
}

.error-details {
  font-size: 0.9rem;
  color: var(--vscode-descriptionForeground, #858585);
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  white-space: pre-wrap;
}

/* Streaming indicator */
.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  color: var(--vscode-descriptionForeground, #858585);
  font-size: 0.9rem;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: var(--vscode-textLink-foreground, #4fc1ff);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

.streaming-text {
  font-style: italic;
}

/* Tools section spacing */
.tools-section {
  margin-top: 0.5rem;
}
</style>
