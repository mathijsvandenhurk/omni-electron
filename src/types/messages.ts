/**
 * Enhanced Message Types for Omni
 * 
 * Complete type definitions with structured content preservation
 * Based on research from GitHub Copilot, Cursor, and Windsurf
 */

/**
 * Core structured content that must ALWAYS be preserved
 */
export interface StructuredContent {
  // Narrative text (both raw and rendered)
  narrative: string;              // Plain markdown text
  narrativeHtml?: string;         // Rendered HTML (cached)
  
  // Tool executions (NEVER LOST)
  tools: EnhancedToolExecution[];
  
  // Code changes
  codeChanges: CodeChange[];
  
  // File references (context)
  fileReferences: FileReference[];
  
  // Response metadata
  metadata: MessageMetadata;
}

/**
 * Enhanced tool execution with complete state tracking
 */
export interface EnhancedToolExecution {
  id: string;                     // Unique ID for this execution
  toolName: string;
  args: Record<string, any>;
  
  // Timing
  startTime: number;
  endTime?: number;
  duration?: number;
  
  // Results (PERSISTENT)
  status: 'pending' | 'running' | 'success' | 'error';
  result?: any;
  resultSummary?: string;         // Human-readable summary
  
  // Error handling
  error?: {
    message: string;
    stack?: string;
    retryable: boolean;
  };
  
  // UI state (preserved across reloads)
  isExpanded: boolean;
}

/**
 * Code change information
 */
export interface CodeChange {
  file: string;
  lineStart: number;
  lineEnd: number;
  code: string;
  language: string;
  changeType?: 'add' | 'modify' | 'delete';
}

/**
 * File reference (context used)
 */
export interface FileReference {
  path: string;
  lineStart?: number;
  lineEnd?: number;
  context?: string;
  reason?: string;               // Why this file was referenced
}

/**
 * Message metadata
 */
export interface MessageMetadata {
  duration: number;               // Total duration in ms
  model: string;                  // Model used (e.g., "claude-3-5-sonnet")
  filesModified: string[];        // Files that were changed
  testsRun: boolean;              // Whether tests were executed
  tokensUsed?: number;            // Token count (if available)
}

/**
 * Message state flags
 */
export interface MessageState {
  isStreaming: boolean;           // Currently receiving data
  isComplete: boolean;            // Stream finished successfully
  hasError: boolean;              // Error occurred
  errorMessage?: string;          // Error details
  wasStopped?: boolean;           // User manually stopped the request
}

/**
 * Render cache for performance
 */
export interface RenderCache {
  renderedAt: Date;
  htmlContent: string;
  toolsCount: number;
  codeChangesCount: number;
}

/**
 * Base message interface
 */
export interface BaseMessage {
  id: string;                     // UUID for uniqueness
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;                // Primary content (markdown for assistant)
  timestamp: Date;
  requestId?: string;             // For tracking streaming responses
}

/**
 * User message (simple)
 */
export interface UserMessage extends BaseMessage {
  role: 'user';
}

/**
 * Assistant message (rich structured content)
 */
export interface AssistantMessage extends BaseMessage {
  role: 'assistant';
  
  // Structured content (ALWAYS preserved)
  structuredContent: StructuredContent;
  
  // State management
  state: MessageState;
  
  // Performance optimization
  _cached?: RenderCache;
}

/**
 * Tool execution message (for backwards compatibility)
 */
export interface ToolMessage extends BaseMessage {
  role: 'tool';
  toolName: string;
  toolArgs?: Record<string, any>;
  status: 'calling' | 'done' | 'error';
  result?: any;
  duration?: number;
  error?: string;
}

/**
 * System message
 */
export interface SystemMessage extends BaseMessage {
  role: 'system';
}

/**
 * Union type for all messages
 */
export type OmniMessage = UserMessage | AssistantMessage | ToolMessage | SystemMessage;

/**
 * Message thread for organizing conversations
 */
export interface MessageThread {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: OmniMessage[];
  context: {
    workingFiles: string[];
    projectPath: string;
  };
}

/**
 * Streaming context for active message construction
 */
export interface StreamContext {
  requestId: string;
  buffer: string;                 // Accumulating narrative
  structuredData: {
    tools: EnhancedToolExecution[];
    codeChanges: CodeChange[];
    fileReferences: FileReference[];
  };
  startTime: number;
}

/**
 * Storage options
 */
export interface StorageOptions {
  maxMessages?: number;           // Max messages to keep in memory
  archiveThreshold?: number;      // Archive messages older than N
  enableCache?: boolean;          // Enable render caching
}

/**
 * Type guards
 */
export function isUserMessage(msg: OmniMessage): msg is UserMessage {
  return msg.role === 'user';
}

export function isAssistantMessage(msg: OmniMessage): msg is AssistantMessage {
  return msg.role === 'assistant';
}

export function isToolMessage(msg: OmniMessage): msg is ToolMessage {
  return msg.role === 'tool';
}

export function isSystemMessage(msg: OmniMessage): msg is SystemMessage {
  return msg.role === 'system';
}

/**
 * Migration helper for old message format
 */
export function migrateOldMessage(oldMsg: any): OmniMessage {
  if (oldMsg.role === 'user') {
    return {
      id: oldMsg.id || generateId(),
      role: 'user',
      content: oldMsg.content || '',
      timestamp: new Date(oldMsg.timestamp || Date.now()),
      requestId: oldMsg.requestId
    };
  }
  
  if (oldMsg.role === 'assistant') {
    return {
      id: oldMsg.id || generateId(),
      role: 'assistant',
      content: oldMsg.content || '',
      timestamp: new Date(oldMsg.timestamp || Date.now()),
      requestId: oldMsg.requestId,
      structuredContent: {
        narrative: oldMsg.content || '',
        narrativeHtml: undefined,
        tools: (oldMsg.tools || []).map((t: any) => ({
          id: generateId(),
          toolName: t.name || 'unknown',
          args: t.args || {},
          startTime: t.startTime || Date.now(),
          endTime: t.endTime,
          duration: t.duration,
          status: t.status || 'success',
          result: t.result,
          resultSummary: undefined,
          error: t.error ? { message: t.error, retryable: false } : undefined,
          isExpanded: false
        })),
        codeChanges: oldMsg.codeChanges || [],
        fileReferences: oldMsg.fileReferences || [],
        metadata: {
          duration: oldMsg.metadata?.duration || 0,
          model: oldMsg.metadata?.model || 'unknown',
          filesModified: oldMsg.metadata?.filesModified || [],
          testsRun: oldMsg.metadata?.testsRun || false,
          tokensUsed: oldMsg.metadata?.tokensUsed
        }
      },
      state: {
        isStreaming: oldMsg.isStreaming || false,
        isComplete: true,
        hasError: false
      }
    };
  }
  
  // Tool message
  if (oldMsg.role === 'tool') {
    return {
      id: oldMsg.id || generateId(),
      role: 'tool',
      content: '',
      timestamp: new Date(oldMsg.timestamp || Date.now()),
      requestId: oldMsg.requestId,
      toolName: oldMsg.toolName || 'unknown',
      toolArgs: oldMsg.toolArgs,
      status: oldMsg.status || 'done',
      result: oldMsg.result,
      duration: oldMsg.duration,
      error: oldMsg.error
    };
  }
  
  // Fallback
  return {
    id: generateId(),
    role: 'system',
    content: 'Invalid message format',
    timestamp: new Date()
  };
}

/**
 * Generate unique ID
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
