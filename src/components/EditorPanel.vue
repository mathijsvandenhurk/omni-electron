<template>
  <div class="editor-panel">
    <TabBar 
      v-if="openTabs.length > 0"
      :tabs="openTabs"
      :activeTabUri="activeTabUri"
      @select-tab="handleSelectTab"
      @close-tab="handleCloseTab"
      @close-other-tabs="handleCloseOtherTabs"
      @close-tabs-to-right="handleCloseTabsToRight"
      @close-all-tabs="handleCloseAllTabs"
    />
    <div v-if="openTabs.length === 0" class="empty-state">
      <div class="empty-state-content">
        <span class="empty-state-icon">📝</span>
        <h3>No files open</h3>
        <p>Open a file from the file explorer to start editing</p>
      </div>
    </div>
    <div v-show="openTabs.length > 0" ref="editorContainer" class="codemirror-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { EditorView, keymap, lineNumbers, highlightActiveLineGutter } from '@codemirror/view';
import { EditorState, Compartment } from '@codemirror/state';
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands';
import { bracketMatching, syntaxHighlighting, defaultHighlightStyle, foldGutter, foldKeymap } from '@codemirror/language';
import { autocompletion, closeBrackets } from '@codemirror/autocomplete';
import { oneDark } from '@codemirror/theme-one-dark';
import { javascript } from '@codemirror/lang-javascript';
import { html } from '@codemirror/lang-html';
import { css } from '@codemirror/lang-css';
import { json } from '@codemirror/lang-json';
import { markdown } from '@codemirror/lang-markdown';
import { python } from '@codemirror/lang-python';
import { useCodeMirrorModels } from '../composables/useCodeMirrorModels';
import TabBar from './TabBar.vue';

const modelManager = useCodeMirrorModels();
const themeCompartment = new Compartment();
const languageCompartment = new Compartment();

interface Props {
  theme?: 'light' | 'dark';
}

const props = withDefaults(defineProps<Props>(), {
  theme: 'dark'
});

const emit = defineEmits<{
  contentChange: [content: string];
  selectionChange: [selection: string];
}>();

const editorContainer = ref<HTMLElement | null>(null);
let editorView: EditorView | null = null;

const openTabs = computed(() => modelManager.listModels().map(info => ({
  uri: info.uri,
  isDirty: info.isDirty
})));

const activeTabUri = computed(() => modelManager.getActiveModelUri());

const getLanguageExtension = (uri: string) => {
  const ext = uri.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'js':
    case 'jsx':
      return javascript();
    case 'ts':
    case 'tsx':
      return javascript({ typescript: true });
    case 'html':
      return html();
    case 'css':
      return css();
    case 'json':
      return json();
    case 'md':
      return markdown();
    case 'py':
      return python();
    default:
      return javascript();
  }
};

const createEditorTheme = (isDark: boolean) => isDark ? oneDark : [];

const initializeEditor = () => {
  if (!editorContainer.value) return;
  
  // Start with an empty editor - no welcome file
  const startState = EditorState.create({
    doc: '',
    extensions: [
      lineNumbers(),
      highlightActiveLineGutter(),
      history(),
      foldGutter(),
      syntaxHighlighting(defaultHighlightStyle),
      bracketMatching(),
      closeBrackets(),
      autocompletion(),
      keymap.of([...defaultKeymap, ...historyKeymap, ...foldKeymap, indentWithTab]),
      themeCompartment.of(createEditorTheme(props.theme === 'dark')),
      languageCompartment.of(javascript()),
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          const uri = modelManager.getActiveModelUri();
          if (uri) {
            const content = update.state.doc.toString();
            modelManager.updateModelContent(uri, content);
            emit('contentChange', content);
          }
        }
      })
    ]
  });

  editorView = new EditorView({
    state: startState,
    parent: editorContainer.value
  });
};

const handleSelectTab = (uri: string) => {
  if (!editorView) return;
  const model = modelManager.getModel(uri);
  if (!model) return;
  
  editorView.dispatch({
    changes: { from: 0, to: editorView.state.doc.length, insert: model.content },
    effects: languageCompartment.reconfigure(getLanguageExtension(uri))
  });
  
  modelManager.setActiveModel(uri);
};

const handleCloseTab = (uri: string) => {
  const models = modelManager.listModels();
  
  // Dispose the model
  modelManager.disposeModel(uri);
  
  // If this was the last tab, clear the editor
  if (models.length === 1) {
    if (editorView) {
      editorView.dispatch({
        changes: { from: 0, to: editorView.state.doc.length, insert: '' }
      });
    }
    return;
  }
  
  // Switch to another tab
  const currentIndex = models.findIndex(m => m.uri === uri);
  const remaining = modelManager.listModels();
  if (remaining.length > 0) {
    handleSelectTab(remaining[Math.min(currentIndex, remaining.length - 1)].uri);
  }
};

const handleCloseOtherTabs = (uri: string) => {
  modelManager.listModels().forEach(m => {
    if (m.uri !== uri) modelManager.disposeModel(m.uri);
  });
  handleSelectTab(uri);
};

const handleCloseTabsToRight = (uri: string) => {
  const models = modelManager.listModels();
  const idx = models.findIndex(m => m.uri === uri);
  for (let i = idx + 1; i < models.length; i++) {
    modelManager.disposeModel(models[i].uri);
  }
};

const handleCloseAllTabs = () => {
  // Dispose all models
  modelManager.listModels().forEach(m => modelManager.disposeModel(m.uri));
  
  // Clear the editor
  if (editorView) {
    editorView.dispatch({
      changes: { from: 0, to: editorView.state.doc.length, insert: '' }
    });
  }
};

const openFile = (uri: string, content: string) => {
  let model = modelManager.getModel(uri);
  if (!model) {
    model = modelManager.createModel(uri, content);
  }
  handleSelectTab(uri);
};

watch(() => props.theme, (newTheme) => {
  if (editorView) {
    editorView.dispatch({
      effects: themeCompartment.reconfigure(createEditorTheme(newTheme === 'dark'))
    });
  }
});

onMounted(() => initializeEditor());
onBeforeUnmount(() => {
  if (editorView) {
    editorView.destroy();
    editorView = null;
  }
});

defineExpose({ openFile });
</script>

<style scoped>
.editor-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.codemirror-container {
  flex: 1;
  overflow: auto;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
}

.empty-state-content {
  text-align: center;
  color: var(--text-secondary);
}

.empty-state-icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
}

.empty-state p {
  font-size: 1rem;
  margin: 0;
  color: var(--text-secondary);
}

.codemirror-container :deep(.cm-editor) {
  height: 100%;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
}

.codemirror-container :deep(.cm-content) {
  caret-color: var(--accent-primary, #007acc);
}

.codemirror-container :deep(.cm-cursor, .cm-dropCursor) {
  border-left: 2px solid var(--accent-primary, #007acc);
}

.codemirror-container :deep(.cm-focused .cm-cursor) {
  border-left-width: 2px;
}

.codemirror-container :deep(.cm-gutters) {
  background: var(--bg-secondary);
}

/* Selection styling */
.codemirror-container :deep(.cm-selectionBackground) {
  background: var(--accent-primary, #007acc) !important;
  opacity: 0.3;
}

.codemirror-container :deep(.cm-focused .cm-selectionBackground) {
  background: var(--accent-primary, #007acc) !important;
  opacity: 0.4;
}

/* Active line */
.codemirror-container :deep(.cm-activeLine) {
  background: var(--bg-tertiary, rgba(255, 255, 255, 0.05));
}

.codemirror-container :deep(.cm-activeLineGutter) {
  background: var(--bg-tertiary, rgba(255, 255, 255, 0.05));
}
</style>
