<template>
  <div class="editor-panel">
    <!-- Tab Bar -->
    <TabBar 
      :tabs="openTabs"
      :active-tab-uri="activeTabUri"
      @select-tab="handleSelectTab"
      @close-tab="handleCloseTab"
      @close-other-tabs="handleCloseOtherTabs"
      @close-tabs-to-right="handleCloseTabsToRight"
      @close-all-tabs="handleCloseAllTabs"
    />
    
    <!-- Monaco Editor Container -->
    <div ref="editorContainer" class="monaco-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue';
import * as monaco from 'monaco-editor';
import { useMonacoModels } from '../composables/useMonacoModels';
import { setupMonacoThemes } from '../composables/useMonacoTheme';
import TabBar from './TabBar.vue';

// NOTE: Web workers are DISABLED to fix Electron shared memory crashes
// See setupMonacoEnvironment() for details

// Use model management system
const modelManager = useMonacoModels();

// Theme observer for automatic synchronization
let themeObserver: MutationObserver | null = null;

// Props
interface Props {
  theme?: 'light' | 'dark';
  language?: string;
  readOnly?: boolean;
  modelUri?: string; // Optional: URI for the model to display
}

const props = withDefaults(defineProps<Props>(), {
  theme: 'dark',
  language: 'typescript',
  readOnly: false,
  modelUri: 'file:///welcome.ts'
});

// Emits
const emit = defineEmits<{
  contentChange: [content: string];
  selectionChange: [selection: string];
  modelChange: [model: monaco.editor.ITextModel | null];
}>();

// Refs
const editorContainer = ref<HTMLElement | null>(null);
let editor: monaco.editor.IStandaloneCodeEditor | null = null;

// Tab state - computed from model manager
const openTabs = computed(() => {
  return modelManager.listModels().map(info => ({
    uri: info.uri.toString(),
    isDirty: info.isDirty
  }));
});

const activeTabUri = computed(() => modelManager.getActiveModelUri());

// Configure Monaco Environment - DISABLE WORKERS to fix Electron crash
const setupMonacoEnvironment = () => {
  // Only setup once
  if ((self as any).MonacoEnvironment) {
    return;
  }

  // CRITICAL FIX: Disable web workers to prevent Electron shared memory crashes
  // The error "Creating shared memory in /tmp/.org.chromium.Chromium failed" 
  // is caused by too many workers in Electron's renderer process
  // Running everything in main thread is less performant but STABLE
  (self as any).MonacoEnvironment = {
    getWorker() {
      // Return null to disable workers - run everything in main thread
      return null;
    }
  };
  
  console.log('⚙️ Monaco environment configured (workers DISABLED for Electron stability)');
};

// Configure TypeScript/JavaScript language features
const setupLanguageFeatures = () => {
  // Production-ready TypeScript configuration
  // Based on Theia IDE and VS Code implementations
  monaco.languages.typescript.typescriptDefaults.setCompilerOptions({
    target: monaco.languages.typescript.ScriptTarget.Latest,
    allowNonTsExtensions: true,
    moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
    module: monaco.languages.typescript.ModuleKind.ESNext,
    noEmit: true,
    esModuleInterop: true,
    jsx: monaco.languages.typescript.JsxEmit.React,
    reactNamespace: 'React',
    allowJs: true,
    typeRoots: ['node_modules/@types']
  });

  monaco.languages.typescript.javascriptDefaults.setCompilerOptions({
    target: monaco.languages.typescript.ScriptTarget.Latest,
    allowNonTsExtensions: true,
    moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
    module: monaco.languages.typescript.ModuleKind.ESNext,
    noEmit: true,
    esModuleInterop: true,
    allowJs: true
  });

  // Enable diagnostics for full IntelliSense
  monaco.languages.typescript.typescriptDefaults.setDiagnosticsOptions({
    noSemanticValidation: false,
    noSyntaxValidation: false,
    noSuggestionDiagnostics: false,
    diagnosticCodesToIgnore: []
  });

  monaco.languages.typescript.javascriptDefaults.setDiagnosticsOptions({
    noSemanticValidation: false,
    noSyntaxValidation: false,
    noSuggestionDiagnostics: false
  });

  // Enable eager model sync for better IntelliSense
  monaco.languages.typescript.typescriptDefaults.setEagerModelSync(true);
  monaco.languages.typescript.javascriptDefaults.setEagerModelSync(true);

  console.log('🔧 TypeScript/JavaScript language features configured (full IntelliSense)');
};

// Initialize editor
const initializeEditor = () => {
  if (!editorContainer.value) {
    console.error('Editor container not found');
    return;
  }

  try {
    // Setup Monaco environment first
    setupMonacoEnvironment();
    
    // Configure language features
    setupLanguageFeatures();

    // Get or create model using model manager
    const welcomeContent = '// Welcome to Omni Code Editor!\n// Powered by Monaco Editor (VS Code)\n\nfunction hello() {\n  console.log("Hello, Omni!");\n}\n';
    const model = modelManager.getOrCreateModel(
      props.modelUri,
      welcomeContent,
      modelManager.detectLanguage(props.modelUri)
    );

    // Create editor instance with the model
    editor = monaco.editor.create(editorContainer.value, {
      model, // Use managed model
      theme: props.theme === 'dark' ? 'vs-dark' : 'vs',
      readOnly: props.readOnly,
      automaticLayout: true,
      fontSize: 14,
      lineHeight: 21,
      fontFamily: 'JetBrains Mono, Fira Code, Monaco, Menlo, Consolas, monospace',
      minimap: {
        enabled: true
      },
      scrollBeyondLastLine: false,
      renderWhitespace: 'selection',
      lineNumbers: 'on',
      folding: true,
      tabSize: 2,
      insertSpaces: true,
      wordWrap: 'off',
      bracketPairColorization: {
        enabled: true
      },
      guides: {
        bracketPairs: true,
        indentation: true
      },
      suggest: {
        preview: true
      },
      quickSuggestions: {
        other: true,
        comments: false,
        strings: false
      }
    });

    // Set as active model
    modelManager.setActiveModel(props.modelUri);

    // Setup custom themes and watch for theme changes
    themeObserver = setupMonacoThemes(editor);

    console.log('✅ Monaco Editor initialized successfully');
    console.log(`📝 Active model: ${props.modelUri}`);
    console.log(`📊 Total models: ${modelManager.getModelCount()}`);
    console.log('🎨 Custom themes applied and watching for changes');

    // Setup event listeners
    setupEventListeners();
  } catch (error) {
    console.error('❌ Failed to initialize Monaco Editor:', error);
  }
};

// Setup event listeners
const setupEventListeners = () => {
  if (!editor) return;

  // Content change event
  editor.onDidChangeModelContent(() => {
    const content = editor?.getValue() || '';
    emit('contentChange', content);
  });

  // Cursor/selection change event
  editor.onDidChangeCursorSelection(() => {
    const selection = editor?.getModel()?.getValueInRange(editor.getSelection()!) || '';
    if (selection) {
      emit('selectionChange', selection);
    }
  });

  // Model change event
  editor.onDidChangeModel(() => {
    const model = editor?.getModel() || null;
    emit('modelChange', model);
  });
};

// Watch theme prop changes (fallback if data-theme not used)
watch(() => props.theme, (newTheme) => {
  if (editor) {
    const monacoTheme = newTheme === 'dark' ? 'omni-dark' : 'omni-light';
    monaco.editor.setTheme(monacoTheme);
  }
});

// Watch language changes
watch(() => props.language, (newLanguage) => {
  if (editor) {
    const model = editor.getModel();
    if (model) {
      monaco.editor.setModelLanguage(model, newLanguage);
    }
  }
});

// Public API methods
const getValue = () => editor?.getValue() || '';
const setValue = (value: string) => editor?.setValue(value);
const getSelection = () => editor?.getModel()?.getValueInRange(editor.getSelection()!) || '';
const focus = () => editor?.focus();

// Open a file in the editor (create/switch model)
const openFile = (uri: string, content: string, language?: string) => {
  console.log('🔍 DEBUG [openFile]: Called with URI:', uri, 'Content length:', content.length);
  
  if (!editor) {
    console.error('❌ Editor not initialized');
    return;
  }
  console.log('🔍 DEBUG [openFile]: Editor exists');

  try {
    // Detect language if not provided
    console.log('🔍 DEBUG [openFile]: Detecting language');
    const detectedLanguage = language || modelManager.detectLanguage(uri);
    console.log('🔍 DEBUG [openFile]: Language detected:', detectedLanguage);

    // Get or create model
    console.log('🔍 DEBUG [openFile]: Getting or creating model');
    const model = modelManager.getOrCreateModel(uri, content, detectedLanguage);
    console.log('🔍 DEBUG [openFile]: Model obtained:', model ? 'success' : 'failed');

    // Set model in editor
    console.log('🔍 DEBUG [openFile]: Setting model in editor');
    editor.setModel(model);
    console.log('🔍 DEBUG [openFile]: Model set successfully');
    
    // Update active model
    console.log('🔍 DEBUG [openFile]: Setting active model');
    modelManager.setActiveModel(uri);
    console.log('🔍 DEBUG [openFile]: Active model set successfully');

    console.log(`📂 Opened file: ${uri} (${detectedLanguage})`);
    console.log(`📊 Total models: ${modelManager.getModelCount()}`);
  } catch (error) {
    console.error('❌ Error opening file:', error);
    console.error('❌ Error stack:', error instanceof Error ? error.stack : 'No stack trace');
    throw error; // Re-throw so FileExplorer can show error
  }
};

// Tab event handlers
const handleSelectTab = (uri: string) => {
  console.log('🔍 DEBUG: handleSelectTab called with URI:', uri);
  
  if (!editor) {
    console.warn('⚠️ Cannot select tab: editor not initialized');
    return;
  }
  console.log('🔍 DEBUG: Editor exists');
  
  try {
    console.log('🔍 DEBUG: Calling modelManager.getModel()');
    const model = modelManager.getModel(uri);
    console.log('🔍 DEBUG: Model retrieved:', model ? 'exists' : 'null');
    
    if (!model) {
      console.warn(`⚠️ Model not found for URI: ${uri}`);
      return;
    }
    
    console.log('🔍 DEBUG: Getting current model from editor');
    const currentModel = editor.getModel();
    console.log('🔍 DEBUG: Current model URI:', currentModel?.uri.toString());
    console.log('🔍 DEBUG: New model URI:', model.uri.toString());
    
    // Only switch if it's a different model
    if (currentModel?.uri.toString() !== model.uri.toString()) {
      console.log('🔍 DEBUG: Models are different, switching...');
      
      // Save view state of current model before switching
      const viewState = currentModel ? editor.saveViewState() : null;
      console.log('🔍 DEBUG: Saved view state:', viewState ? 'success' : 'none');
      
      // Check if new model is disposed
      if (model.isDisposed()) {
        console.error('❌ Model is disposed, cannot switch:', uri);
        return;
      }
      console.log('🔍 DEBUG: Model is not disposed, proceeding');
      
      // CRITICAL: Set model to null first to clear internal state
      console.log('🔍 DEBUG: Setting model to null');
      editor.setModel(null);
      
      // Use requestAnimationFrame to ensure DOM is updated
      requestAnimationFrame(() => {
        try {
          console.log('🔍 DEBUG: In requestAnimationFrame, setting new model');
          
          // Double-check editor still exists
          if (!editor) {
            console.error('❌ Editor was disposed between frames');
            return;
          }
          
          // Double-check model is still valid
          if (!model.isDisposed()) {
            editor.setModel(model);
            console.log('🔍 DEBUG: Model set successfully');
            
            // Restore view state if needed (optional)
            // editor.restoreViewState(viewState);
            
            modelManager.setActiveModel(uri);
            console.log(`� Switched to tab: ${uri}`);
          } else {
            console.error('❌ Model was disposed between frames');
          }
        } catch (innerError) {
          console.error('❌ Error in requestAnimationFrame:', innerError);
        }
      });
    } else {
      console.log('🔍 DEBUG: Same model, no switch needed');
      modelManager.setActiveModel(uri);
    }
  } catch (error) {
    console.error('❌ Error switching tab:', error);
    console.error('❌ Error stack:', error instanceof Error ? error.stack : 'No stack trace');
    console.error('❌ Error details:', {
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : String(error)
    });
  }
};

const handleCloseTab = (uri: string) => {
  const tabs = openTabs.value;
  const currentIndex = tabs.findIndex(t => t.uri === uri);
  
  // Check if we need to switch tabs BEFORE disposing
  const shouldSwitchTab = uri === activeTabUri.value && tabs.length > 1;
  let nextTabUri: string | null = null;
  
  if (shouldSwitchTab) {
    // Calculate next tab to switch to BEFORE disposing
    const nextIndex = currentIndex < tabs.length - 1 ? currentIndex : currentIndex - 1;
    if (nextIndex >= 0 && tabs[nextIndex] && tabs[nextIndex].uri !== uri) {
      nextTabUri = tabs[nextIndex].uri;
    }
  }
  
  // Switch to next tab BEFORE disposing the current one
  if (nextTabUri && editor) {
    const nextModel = modelManager.getModel(nextTabUri);
    if (nextModel) {
      editor.setModel(nextModel);
      modelManager.setActiveModel(nextTabUri);
    }
  }
  
  // Now dispose the model
  modelManager.disposeModel(uri);
  
  // If last tab closed, clear editor
  if (tabs.length === 1 && editor) {
    editor.setModel(null);
  }
  
  console.log(`❌ Closed tab: ${uri}`);
};

const handleCloseOtherTabs = (uri: string) => {
  const allTabs = openTabs.value;
  allTabs.forEach(tab => {
    if (tab.uri !== uri) {
      modelManager.disposeModel(tab.uri);
    }
  });
  
  // Switch to the kept tab
  handleSelectTab(uri);
  console.log(`❌ Closed other tabs, kept: ${uri}`);
};

const handleCloseTabsToRight = (uri: string) => {
  const allTabs = openTabs.value;
  const index = allTabs.findIndex(t => t.uri === uri);
  
  if (index >= 0) {
    const tabsToClose = allTabs.slice(index + 1);
    tabsToClose.forEach(tab => {
      modelManager.disposeModel(tab.uri);
    });
    console.log(`❌ Closed ${tabsToClose.length} tabs to the right`);
  }
};

const handleCloseAllTabs = () => {
  const count = openTabs.value.length;
  modelManager.disposeAllModels();
  editor?.setModel(null);
  console.log(`❌ Closed all ${count} tabs`);
};

// Get model manager (for external access)
const getModelManager = () => modelManager;

// Get current model info
const getCurrentModelInfo = () => {
  const uri = modelManager.getActiveModelUri();
  return uri ? modelManager.getModelInfo(uri) : null;
};

// Expose methods to parent
defineExpose({
  getValue,
  setValue,
  getSelection,
  focus,
  openFile,
  getModelManager,
  getCurrentModelInfo
});

// Lifecycle hooks
onMounted(() => {
  console.log('EditorPanel mounting...');
  // Small delay to ensure DOM is ready
  setTimeout(() => {
    initializeEditor();
  }, 100);
});

onBeforeUnmount(() => {
  console.log('EditorPanel unmounting, disposing editor...');
  
  // Disconnect theme observer
  if (themeObserver) {
    themeObserver.disconnect();
    themeObserver = null;
    console.log('🎨 Theme observer disconnected');
  }
  
  if (editor) {
    editor.dispose();
    editor = null;
  }
  
  // Note: We don't dispose models here - they're managed globally
  // and may be used by other editor instances or tabs
  console.log(`📊 Remaining models: ${modelManager.getModelCount()}`);
});
</script>

<style scoped>
.editor-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
}

.monaco-container {
  flex: 1;
  width: 100%;
  overflow: hidden;
}
</style>
