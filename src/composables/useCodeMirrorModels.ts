import { ref } from 'vue';

/**
 * Model information structure
 */
export interface ModelInfo {
  uri: string;
  content: string;
  isDirty: boolean;
  originalContent: string;
}

/**
 * Composable for managing CodeMirror editor models
 * Simplified version without Monaco dependencies
 */
export function useCodeMirrorModels() {
  // Store all models
  const models = ref<Map<string, ModelInfo>>(new Map());
  
  // Track active model URI
  const activeModelUri = ref<string | null>(null);

  /**
   * Create a new model
   */
  const createModel = (uri: string, content: string): ModelInfo => {
    // Check if model already exists
    if (models.value.has(uri)) {
      console.warn(`⚠️ Model already exists: ${uri}`);
      return models.value.get(uri)!;
    }

    const modelInfo: ModelInfo = {
      uri,
      content,
      isDirty: false,
      originalContent: content
    };

    models.value.set(uri, modelInfo);
    console.log(`✅ Model created: ${uri}`);
    
    return modelInfo;
  };

  /**
   * Get a model by URI
   */
  const getModel = (uri: string): ModelInfo | undefined => {
    return models.value.get(uri);
  };

  /**
   * Update model content
   */
  const updateModelContent = (uri: string, content: string): void => {
    const model = models.value.get(uri);
    if (!model) {
      console.warn(`⚠️ Cannot update non-existent model: ${uri}`);
      return;
    }

    model.content = content;
    model.isDirty = content !== model.originalContent;
  };

  /**
   * Mark model as saved (resets dirty state)
   */
  const markModelAsSaved = (uri: string): void => {
    const model = models.value.get(uri);
    if (!model) {
      console.warn(`⚠️ Cannot mark non-existent model as saved: ${uri}`);
      return;
    }

    model.originalContent = model.content;
    model.isDirty = false;
    console.log(`💾 Model marked as saved: ${uri}`);
  };

  /**
   * Dispose a model
   */
  const disposeModel = (uri: string): void => {
    const model = models.value.get(uri);
    if (!model) {
      console.warn(`⚠️ Cannot dispose non-existent model: ${uri}`);
      return;
    }

    models.value.delete(uri);
    
    // If this was the active model, clear active model
    if (activeModelUri.value === uri) {
      activeModelUri.value = null;
    }
    
    console.log(`🗑️ Model disposed: ${uri}`);
  };

  /**
   * List all models
   */
  const listModels = (): ModelInfo[] => {
    return Array.from(models.value.values());
  };

  /**
   * Get active model URI
   */
  const getActiveModelUri = (): string | null => {
    return activeModelUri.value;
  };

  /**
   * Set active model
   */
  const setActiveModel = (uri: string): void => {
    if (!models.value.has(uri)) {
      console.warn(`⚠️ Cannot set non-existent model as active: ${uri}`);
      return;
    }
    
    activeModelUri.value = uri;
  };

  /**
   * Check if model is dirty
   */
  const isModelDirty = (uri: string): boolean => {
    const model = models.value.get(uri);
    return model?.isDirty ?? false;
  };

  return {
    createModel,
    getModel,
    updateModelContent,
    markModelAsSaved,
    disposeModel,
    listModels,
    getActiveModelUri,
    setActiveModel,
    isModelDirty
  };
}
