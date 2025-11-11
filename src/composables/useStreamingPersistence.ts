/**
 * Streaming Persistence Composable
 * 
 * Bridges streaming events to persistent storage
 * Ensures NO data is lost during streaming
 */

import { ref } from 'vue';
import type { OmniEvent } from '../types/events';
import type {
  StreamContext,
  EnhancedToolExecution,
  CodeChange,
  FileReference,
  AssistantMessage
} from '../types/messages';
import { messageStorage } from '../services/messageStorage';
import { marked } from 'marked';

/**
 * Generate unique ID
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Summarize tool result for display
 */
function summarizeResult(result: any): string {
  if (!result) return 'No output';
  
  if (typeof result === 'string') {
    // Truncate long strings
    return result.length > 200 ? result.substring(0, 200) + '...' : result;
  }
  
  if (typeof result === 'object') {
    // For objects, show key info
    const keys = Object.keys(result);
    if (keys.length === 0) return 'Empty object';
    if (keys.length <= 3) {
      return JSON.stringify(result, null, 2);
    }
    return `Object with ${keys.length} properties: ${keys.slice(0, 3).join(', ')}...`;
  }
  
  return String(result);
}

/**
 * Debounced save function
 */
function createDebouncedSave(delay = 300) {
  let timeoutId: NodeJS.Timeout | null = null;
  let pendingContext: StreamContext | null = null;

  return {
    save: (context: StreamContext) => {
      pendingContext = context;
      
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      timeoutId = setTimeout(async () => {
        if (pendingContext) {
          // Save intermediate state (for recovery)
          try {
            localStorage.setItem(
              `omni-stream-${pendingContext.requestId}`,
              JSON.stringify(pendingContext)
            );
          } catch (error) {
            console.error('[StreamingPersistence] Failed to save intermediate state:', error);
          }
        }
        timeoutId = null;
      }, delay);
    },
    
    flush: async (context: StreamContext) => {
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
      // Clean up intermediate state
      try {
        localStorage.removeItem(`omni-stream-${context.requestId}`);
      } catch (error) {
        console.error('[StreamingPersistence] Failed to clean up intermediate state:', error);
      }
    }
  };
}

/**
 * Composable for streaming persistence
 */
export function useStreamingPersistence() {
  const activeStreams = ref<Map<string, StreamContext>>(new Map());
  const debouncedSave = createDebouncedSave();

  /**
   * Start a new streaming session
   */
  function startStreaming(requestId: string): StreamContext {
    console.log('[StreamingPersistence] 🚀 Starting stream:', requestId);
    
    const context: StreamContext = {
      requestId,
      buffer: '',
      structuredData: {
        tools: [],
        codeChanges: [],
        fileReferences: []
      },
      startTime: Date.now()
    };

    activeStreams.value.set(requestId, context);
    
    // Check for recovery state
    try {
      const recovered = localStorage.getItem(`omni-stream-${requestId}`);
      if (recovered) {
        const recoveredContext = JSON.parse(recovered);
        console.log('[StreamingPersistence] 🔄 Recovered state for:', requestId);
        return { ...context, ...recoveredContext };
      }
    } catch (error) {
      console.warn('[StreamingPersistence] Failed to recover state:', error);
    }

    return context;
  }

  /**
   * Handle streaming event and update context
   */
  function onStreamChunk(requestId: string, event: OmniEvent) {
    const context = activeStreams.value.get(requestId);
    if (!context) {
      console.warn('[StreamingPersistence] ⚠️ No context for requestId:', requestId);
      return;
    }

    // Update based on event type
    switch (event.type) {
      case 'narrative_chunk':
        context.buffer += event.data.text;
        break;

      case 'tool_start':
        {
          const toolExecution: EnhancedToolExecution = {
            id: generateId(),
            toolName: event.data.name,
            args: event.data.args,
            startTime: event.data.timestamp,
            status: 'running',
            isExpanded: false
          };
          context.structuredData.tools.push(toolExecution);
          console.log('[StreamingPersistence] 🔧 Tool started:', toolExecution.toolName);
        }
        break;

      case 'tool_result':
        {
          // Find and update the running tool
          const tool = context.structuredData.tools.find(
            t => t.toolName === event.data.name && t.status === 'running'
          );
          
          if (tool) {
            tool.status = event.data.status;
            tool.endTime = Date.now();
            tool.duration = event.data.duration;
            tool.result = event.data.result;
            tool.resultSummary = summarizeResult(event.data.result);
            
            if (event.data.error) {
              tool.error = {
                message: event.data.error,
                retryable: false
              };
            }
            
            console.log('[StreamingPersistence] ✅ Tool completed:', tool.toolName, tool.status);
          } else {
            console.warn('[StreamingPersistence] ⚠️ Could not find running tool:', event.data.name);
          }
        }
        break;

      case 'code_change':
        {
          const codeChange: CodeChange = {
            file: event.data.file,
            lineStart: event.data.lineStart,
            lineEnd: event.data.lineEnd,
            code: event.data.code,
            language: event.data.language
          };
          context.structuredData.codeChanges.push(codeChange);
          console.log('[StreamingPersistence] 📝 Code change:', codeChange.file);
        }
        break;

      case 'file_reference':
        {
          const fileRef: FileReference = {
            path: event.data.path,
            lineStart: event.data.lineStart,
            lineEnd: event.data.lineEnd,
            context: event.data.context
          };
          context.structuredData.fileReferences.push(fileRef);
          console.log('[StreamingPersistence] 📚 File reference:', fileRef.path);
        }
        break;

      case 'error':
        console.error('[StreamingPersistence] ❌ Error event:', event.data.message);
        break;
    }

    // Debounced save for recovery
    debouncedSave.save(context);
  }

  /**
   * Complete streaming and persist final message
   */
  async function onStreamComplete(requestId: string): Promise<AssistantMessage | null> {
    const context = activeStreams.value.get(requestId);
    if (!context) {
      console.error('[StreamingPersistence] ❌ No context to complete:', requestId);
      return null;
    }

    console.log('[StreamingPersistence] 🏁 Completing stream:', requestId);

    try {
      // Render markdown HTML
      let narrativeHtml = '';
      try {
        narrativeHtml = await marked.parse(context.buffer, {
          gfm: true,
          breaks: true
        });
      } catch (error) {
        console.error('[StreamingPersistence] Failed to render markdown:', error);
        narrativeHtml = context.buffer;
      }

      // Create complete assistant message
      const message: AssistantMessage = {
        id: generateId(),
        role: 'assistant',
        content: context.buffer,
        timestamp: new Date(),
        requestId,
        structuredContent: {
          narrative: context.buffer,
          narrativeHtml,
          tools: context.structuredData.tools,
          codeChanges: context.structuredData.codeChanges,
          fileReferences: context.structuredData.fileReferences,
          metadata: {
            duration: Date.now() - context.startTime,
            model: 'omni-1.0', // TODO: Get from backend
            filesModified: context.structuredData.codeChanges.map(c => c.file),
            testsRun: context.structuredData.tools.some(t => t.toolName === 'run_tests')
          }
        },
        state: {
          isStreaming: false,
          isComplete: true,
          hasError: false
        }
      };

      // PERSIST TO STORAGE (critical!)
      await messageStorage.saveMessage(message);
      console.log('[StreamingPersistence] ✅ Message persisted:', message.id);

      // Clean up
      activeStreams.value.delete(requestId);
      await debouncedSave.flush(context);

      return message;
    } catch (error) {
      console.error('[StreamingPersistence] ❌ Failed to complete stream:', error);
      
      // Try emergency save to localStorage
      try {
        const emergency = {
          requestId,
          context,
          timestamp: new Date(),
          error: String(error)
        };
        localStorage.setItem(`omni-emergency-${requestId}`, JSON.stringify(emergency));
        console.log('[StreamingPersistence] 🆘 Emergency save successful');
      } catch (emergencyError) {
        console.error('[StreamingPersistence] 🆘 Emergency save failed:', emergencyError);
      }

      return null;
    }
  }

  /**
   * Handle streaming error
   */
  async function onStreamError(requestId: string, error: any): Promise<void> {
    const context = activeStreams.value.get(requestId);
    if (!context) return;

    console.error('[StreamingPersistence] ❌ Stream error:', requestId, error);

    try {
      // Create error message
      const message: AssistantMessage = {
        id: generateId(),
        role: 'assistant',
        content: context.buffer || 'An error occurred during streaming.',
        timestamp: new Date(),
        requestId,
        structuredContent: {
          narrative: context.buffer || 'An error occurred.',
          tools: context.structuredData.tools,
          codeChanges: context.structuredData.codeChanges,
          fileReferences: context.structuredData.fileReferences,
          metadata: {
            duration: Date.now() - context.startTime,
            model: 'omni-1.0',
            filesModified: [],
            testsRun: false
          }
        },
        state: {
          isStreaming: false,
          isComplete: false,
          hasError: true,
          errorMessage: error.message || String(error)
        }
      };

      // Save error message
      await messageStorage.saveMessage(message);
      console.log('[StreamingPersistence] ✅ Error message persisted');
    } catch (saveError) {
      console.error('[StreamingPersistence] ❌ Failed to save error message:', saveError);
    } finally {
      // Clean up
      activeStreams.value.delete(requestId);
      await debouncedSave.flush(context);
    }
  }

  /**
   * Get current streaming context (for debugging)
   */
  function getContext(requestId: string): StreamContext | undefined {
    return activeStreams.value.get(requestId);
  }

  /**
   * Cancel streaming
   */
  async function cancelStreaming(requestId: string): Promise<void> {
    const context = activeStreams.value.get(requestId);
    if (!context) return;

    console.log('[StreamingPersistence] 🛑 Canceling stream:', requestId);
    
    // Clean up
    activeStreams.value.delete(requestId);
    await debouncedSave.flush(context);
  }

  return {
    startStreaming,
    onStreamChunk,
    onStreamComplete,
    onStreamError,
    getContext,
    cancelStreaming,
    activeStreams: activeStreams.value
  };
}
