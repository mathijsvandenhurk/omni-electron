<template>
  <div class="code-block">
    <!-- Header with language badge and actions -->
    <div class="code-header">
      <div class="code-language">
        <span class="language-icon">{{ languageIcon }}</span>
        <span class="language-name">{{ language }}</span>
      </div>
      <div class="code-actions">
        <button 
          @click="copyCode" 
          class="code-action-btn"
          :class="{ copied: isCopied }"
          :title="isCopied ? 'Gekopieerd!' : 'Kopieer code'"
        >
          {{ isCopied ? '✓' : '📋' }}
          <span class="action-label">{{ isCopied ? 'Gekopieerd' : 'Kopieer' }}</span>
        </button>
        <button 
          v-if="showInsert"
          @click="insertCode" 
          class="code-action-btn"
          title="Voeg code in op cursor positie"
        >
          ➕
          <span class="action-label">Invoegen</span>
        </button>
        <button 
          v-if="showApply"
          @click="applyCode" 
          class="code-action-btn"
          title="Vervang geselecteerde code"
        >
          ✏️
          <span class="action-label">Toepassen</span>
        </button>
      </div>
    </div>
    
    <!-- Code content -->
    <div class="code-content">
      <pre><code>{{ code }}</code></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface Props {
  code: string;
  language?: string;
  showInsert?: boolean;
  showApply?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  language: 'text',
  showInsert: false,
  showApply: false
});

const emit = defineEmits<{
  copy: [code: string];
  insert: [code: string];
  apply: [code: string];
}>();

const isCopied = ref(false);

// Language icon mapping
const languageIcons: Record<string, string> = {
  javascript: '🟨',
  typescript: '🔷',
  python: '🐍',
  vue: '💚',
  html: '🌐',
  css: '🎨',
  json: '📦',
  markdown: '📝',
  bash: '⚡',
  shell: '⚡',
  text: '📄'
};

const languageIcon = computed(() => {
  const lang = props.language.toLowerCase();
  return languageIcons[lang] || languageIcons.text;
});

const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(props.code);
    isCopied.value = true;
    emit('copy', props.code);
    
    // Reset after 2 seconds
    setTimeout(() => {
      isCopied.value = false;
    }, 2000);
  } catch (error) {
    console.error('Failed to copy code:', error);
  }
};

const insertCode = () => {
  emit('insert', props.code);
};

const applyCode = () => {
  emit('apply', props.code);
};
</script>

<style scoped>
.code-block {
  margin: var(--space-3) 0;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--color-border-medium);
  background: var(--color-code-bg);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition-fast);
}

.code-block:hover {
  box-shadow: var(--shadow-md);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border-light);
  min-height: var(--code-header-height, 40px);
}

.code-language {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
}

.language-icon {
  font-size: var(--font-size-base);
}

.language-name {
  text-transform: capitalize;
}

.code-actions {
  display: flex;
  gap: var(--space-2);
}

.code-action-btn {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.code-action-btn:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-1px);
}

.code-action-btn:active {
  transform: translateY(0);
}

.code-action-btn.copied {
  background: var(--color-success-bg);
  color: var(--color-success);
  border-color: var(--color-success-border);
}

.action-label {
  font-size: var(--font-size-xs);
}

.code-content {
  overflow-x: auto;
  background: var(--color-code-bg);
}

.code-content pre {
  margin: 0;
  padding: var(--code-padding, var(--space-4));
  font-family: var(--font-family-code);
  font-size: var(--font-size-code);
  line-height: var(--line-height-code);
  color: var(--color-code-text);
  background: transparent;
}

.code-content code {
  font-family: inherit;
  font-size: inherit;
  color: inherit;
  background: transparent;
  padding: 0;
  border-radius: 0;
}

/* Scrollbar styling for code blocks */
.code-content::-webkit-scrollbar {
  height: 8px;
}

.code-content::-webkit-scrollbar-track {
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
}

.code-content::-webkit-scrollbar-thumb {
  background: var(--color-border-medium);
  border-radius: var(--radius-sm);
}

.code-content::-webkit-scrollbar-thumb:hover {
  background: var(--color-border-dark);
}

/* Animation for copy feedback */
@keyframes copySuccess {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.code-action-btn.copied {
  animation: copySuccess 0.3s ease-out;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .action-label {
    display: none;
  }
  
  .code-action-btn {
    padding: var(--space-1);
  }
}
</style>
