<template>
  <Teleport to="body">
    <div 
      v-if="isVisible" 
      class="inline-chat-overlay"
      @click.self="handleOverlayClick"
    >
      <div class="inline-chat-container" ref="containerRef">
        <div class="inline-chat-header">
          <div class="header-title">
            <span class="icon">💬</span>
            <span>Inline Chat</span>
            <span v-if="hasSelection" class="context-badge">{{ selectionLines }} lines selected</span>
          </div>
          <button @click="close" class="close-button" title="Close (Esc)">
            <span>✕</span>
          </button>
        </div>

        <div class="inline-chat-body">
          <!-- Selected code preview (if any) -->
          <div v-if="selectedCode" class="code-preview">
            <div class="preview-header">
              <span>📄 Selected Code</span>
              <button @click="clearSelection" class="clear-selection-btn">Clear</button>
            </div>
            <pre class="code-content"><code>{{ selectedCode }}</code></pre>
          </div>

          <!-- Input area -->
          <div class="input-section">
            <textarea
              ref="inputRef"
              v-model="prompt"
              @keydown.enter.exact.prevent="handleSubmit"
              @keydown.escape="close"
              @keydown.meta.enter="handleSubmit"
              @keydown.ctrl.enter="handleSubmit"
              placeholder="Ask a question or describe what you want to do... (⌘/Ctrl+Enter to submit, Esc to close)"
              class="inline-input"
              rows="3"
            />
            
            <!-- Quick actions -->
            <div class="quick-actions">
              <button 
                v-for="action in quickActions" 
                :key="action.id"
                @click="applyQuickAction(action)"
                class="quick-action-btn"
                :title="action.description"
              >
                {{ action.icon }} {{ action.label }}
              </button>
            </div>
          </div>

          <!-- Response area (when AI is responding) -->
          <div v-if="isProcessing || response" class="response-section">
            <div v-if="isProcessing" class="processing-indicator">
              <span class="spinner"></span>
              <span>{{ processingStatus }}</span>
            </div>
            
            <div v-if="response" class="response-content">
              <div class="response-header">
                <span>🤖 Omni</span>
                <div class="response-actions">
                  <button 
                    v-if="hasCodeChanges" 
                    @click="applyChanges" 
                    class="action-btn primary"
                    title="Apply changes to editor"
                  >
                    ✓ Apply
                  </button>
                  <button 
                    v-if="hasCodeChanges" 
                    @click="previewDiff" 
                    class="action-btn"
                    title="Preview diff"
                  >
                    👁️ Preview
                  </button>
                  <button @click="copyResponse" class="action-btn" title="Copy response">
                    📋 Copy
                  </button>
                  <button @click="clearResponse" class="action-btn" title="Clear response">
                    🗑️ Clear
                  </button>
                </div>
              </div>
              <div class="response-text" v-html="formattedResponse"></div>
            </div>
          </div>

          <!-- Diff preview (when viewing changes) -->
          <div v-if="showDiff" class="diff-preview">
            <div class="diff-header">
              <span>📝 Proposed Changes</span>
              <div class="diff-actions">
                <button @click="acceptDiff" class="action-btn primary">✓ Accept</button>
                <button @click="rejectDiff" class="action-btn">✕ Reject</button>
              </div>
            </div>
            <div class="diff-content">
              <div class="diff-line" v-for="(line, index) in diffLines" :key="index" :class="line.type">
                <span class="line-number">{{ line.number }}</span>
                <span class="line-content">{{ line.content }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer with shortcuts -->
        <div class="inline-chat-footer">
          <div class="shortcuts">
            <span class="shortcut"><kbd>⌘</kbd>+<kbd>Enter</kbd> Submit</span>
            <span class="shortcut"><kbd>Esc</kbd> Close</span>
            <span v-if="hasCodeChanges" class="shortcut"><kbd>⌘</kbd>+<kbd>K</kbd> Apply</span>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue';

// Props
interface Props {
  initialSelection?: string;
  filePath?: string;
}

const props = withDefaults(defineProps<Props>(), {
  initialSelection: '',
  filePath: ''
});

// Emits
const emit = defineEmits<{
  close: [];
  apply: [changes: string];
  submit: [prompt: string, selection?: string];
}>();

// Refs
const isVisible = ref(false);
const prompt = ref('');
const selectedCode = ref(props.initialSelection);
const response = ref('');
const isProcessing = ref(false);
const processingStatus = ref('Thinking...');
const showDiff = ref(false);
const diffLines = ref<Array<{ type: string; number: number; content: string }>>([]);
const containerRef = ref<HTMLElement>();
const inputRef = ref<HTMLTextAreaElement>();

// Computed
const hasSelection = computed(() => selectedCode.value.length > 0);
const selectionLines = computed(() => selectedCode.value.split('\n').length);
const hasCodeChanges = computed(() => response.value.includes('```') || showDiff.value);

const formattedResponse = computed(() => {
  // Simple markdown-like formatting
  let html = response.value
    .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
  return html;
});

// Quick actions
const quickActions = ref([
  { id: 'explain', icon: '📖', label: 'Explain', description: 'Explain the selected code' },
  { id: 'fix', icon: '🔧', label: 'Fix', description: 'Fix issues in the code' },
  { id: 'optimize', icon: '⚡', label: 'Optimize', description: 'Optimize the code' },
  { id: 'test', icon: '🧪', label: 'Add Tests', description: 'Generate test cases' },
  { id: 'document', icon: '📝', label: 'Document', description: 'Add documentation' }
]);

// Methods
const open = () => {
  isVisible.value = true;
  nextTick(() => {
    inputRef.value?.focus();
  });
};

const close = () => {
  isVisible.value = false;
  prompt.value = '';
  response.value = '';
  showDiff.value = false;
  emit('close');
};

const handleOverlayClick = () => {
  // Optional: close on overlay click
  // close();
};

const clearSelection = () => {
  selectedCode.value = '';
};

const handleSubmit = async () => {
  if (!prompt.value.trim() || isProcessing.value) return;

  isProcessing.value = true;
  processingStatus.value = 'Thinking...';

  try {
    emit('submit', prompt.value, selectedCode.value);
    
    // Simulate AI response (in real implementation, this would be an API call)
    await new Promise(resolve => setTimeout(resolve, 1000));
    processingStatus.value = 'Generating response...';
    
    await new Promise(resolve => setTimeout(resolve, 1500));
    response.value = 'This is a simulated response. In production, this would be the actual AI response.';
    
  } catch (error) {
    console.error('Error processing inline chat:', error);
    response.value = '❌ Error: Failed to process your request.';
  } finally {
    isProcessing.value = false;
  }
};

const applyQuickAction = (action: typeof quickActions.value[0]) => {
  const templates: Record<string, string> = {
    explain: 'Explain this code in detail',
    fix: 'Find and fix any issues in this code',
    optimize: 'Optimize this code for better performance',
    test: 'Generate comprehensive test cases for this code',
    document: 'Add clear documentation and comments to this code'
  };
  
  prompt.value = templates[action.id] || action.label;
  handleSubmit();
};

const applyChanges = () => {
  // Extract code from response
  const codeMatch = response.value.match(/```(?:\w+)?\n([\s\S]*?)```/);
  if (codeMatch) {
    emit('apply', codeMatch[1]);
    close();
  }
};

const previewDiff = () => {
  // Generate diff preview
  showDiff.value = true;
  
  // Simulate diff lines (in production, would be actual diff)
  diffLines.value = [
    { type: 'unchanged', number: 1, content: 'function example() {' },
    { type: 'removed', number: 2, content: '  const old = "old code";' },
    { type: 'added', number: 2, content: '  const new = "new code";' },
    { type: 'unchanged', number: 3, content: '  return new;' },
    { type: 'unchanged', number: 4, content: '}' }
  ];
};

const acceptDiff = () => {
  applyChanges();
};

const rejectDiff = () => {
  showDiff.value = false;
};

const copyResponse = () => {
  navigator.clipboard.writeText(response.value);
  // Could add a toast notification here
};

const clearResponse = () => {
  response.value = '';
  showDiff.value = false;
};

// Keyboard shortcut handling
const handleKeyDown = (e: KeyboardEvent) => {
  // Cmd/Ctrl + I to toggle
  if ((e.metaKey || e.ctrlKey) && e.key === 'i') {
    e.preventDefault();
    if (isVisible.value) {
      close();
    } else {
      open();
    }
  }
  
  // Cmd/Ctrl + K to apply changes (when visible)
  if (isVisible.value && (e.metaKey || e.ctrlKey) && e.key === 'k' && hasCodeChanges.value) {
    e.preventDefault();
    applyChanges();
  }
};

// Lifecycle
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
  if (props.initialSelection) {
    selectedCode.value = props.initialSelection;
  }
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});

// Expose methods to parent
defineExpose({
  open,
  close
});
</script>

<style scoped>
/* Overlay */
.inline-chat-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.15s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Container */
.inline-chat-container {
  width: min(90vw, 800px);
  max-height: 90vh;
  background: var(--color-bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-2xl);
  border: 1px solid var(--color-border-medium);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.2s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Header */
.inline-chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
}

.header-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.header-title .icon {
  font-size: var(--font-size-lg);
}

.context-badge {
  padding: var(--space-1) var(--space-2);
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.close-button {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-button:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

/* Body */
.inline-chat-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* Code Preview */
.code-preview {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border-light);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.clear-selection-btn {
  padding: var(--space-1) var(--space-2);
  background: transparent;
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.clear-selection-btn:hover {
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
}

.code-content {
  padding: var(--space-3);
  margin: 0;
  font-family: var(--font-family-code);
  font-size: var(--font-size-code);
  line-height: var(--line-height-code);
  color: var(--color-text-primary);
  overflow-x: auto;
  max-height: 200px;
}

/* Input Section */
.input-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.inline-input {
  width: 100%;
  padding: var(--space-3);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-family: var(--font-family-text);
  line-height: var(--line-height-normal);
  resize: vertical;
  min-height: 80px;
  transition: all var(--transition-fast);
}

.inline-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.inline-input::placeholder {
  color: var(--color-text-muted);
}

/* Quick Actions */
.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.quick-action-btn {
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-action-btn:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-1px);
}

/* Response Section */
.response-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.processing-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  color: var(--color-text-secondary);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border-medium);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.response-content {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.response-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3);
  background: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border-light);
  font-weight: var(--font-weight-semibold);
}

.response-actions {
  display: flex;
  gap: var(--space-2);
}

.action-btn {
  padding: var(--space-1) var(--space-3);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.action-btn.primary {
  background: var(--color-primary);
  color: var(--color-white);
  border-color: var(--color-primary);
}

.action-btn.primary:hover {
  background: var(--color-primary-dark);
}

.response-text {
  padding: var(--space-3);
  color: var(--color-text-primary);
  line-height: var(--line-height-normal);
}

.response-text :deep(.code-block) {
  background: var(--color-bg-tertiary);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  margin: var(--space-2) 0;
  overflow-x: auto;
}

.response-text :deep(.inline-code) {
  background: var(--color-bg-tertiary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: var(--font-family-code);
  font-size: 0.9em;
}

/* Diff Preview */
.diff-preview {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.diff-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3);
  background: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border-light);
  font-weight: var(--font-weight-semibold);
}

.diff-actions {
  display: flex;
  gap: var(--space-2);
}

.diff-content {
  padding: var(--space-2);
  font-family: var(--font-family-code);
  font-size: var(--font-size-code);
  line-height: var(--line-height-code);
  overflow-x: auto;
}

.diff-line {
  display: flex;
  padding: 2px var(--space-2);
}

.diff-line.added {
  background: rgba(34, 197, 94, 0.1);
  color: var(--color-success);
}

.diff-line.removed {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-error);
}

.diff-line.unchanged {
  color: var(--color-text-secondary);
}

.line-number {
  min-width: 40px;
  text-align: right;
  margin-right: var(--space-3);
  color: var(--color-text-muted);
}

/* Footer */
.inline-chat-footer {
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-secondary);
  border-top: 1px solid var(--color-border-light);
}

.shortcuts {
  display: flex;
  gap: var(--space-4);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.shortcut {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.shortcut kbd {
  padding: 2px 6px;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-sm);
  font-family: var(--font-family-code);
  font-size: var(--font-size-xs);
  box-shadow: 0 1px 0 var(--color-border-medium);
}
</style>
