/**
 * Omni Streaming Event Protocol
 * 
 * Type definitions for streaming events between backend and frontend.
 * All events follow a consistent structure for type safety and validation.
 */

/**
 * Base event structure
 */
export interface BaseEvent {
  type: string;
  timestamp: number;
  requestId: string;
}

/**
 * Response lifecycle events
 */
export interface ResponseStartEvent extends BaseEvent {
  type: 'response_start';
  data: {
    requestId: string;
    timestamp: number;
  };
}

export interface ResponseCompleteEvent extends BaseEvent {
  type: 'response_complete';
  data: {
    metadata: ResponseMetadata;
  };
}

export interface ResponseMetadata {
  requestId: string;
  duration: number;
  tokensUsed: number;
  toolsExecuted: string[];
  filesModified: string[];
}

/**
 * Narrative streaming events
 */
export interface NarrativeChunkEvent extends BaseEvent {
  type: 'narrative_chunk';
  data: {
    text: string;
    isMarkdown: boolean;
  };
}

/**
 * Progress update events
 */
export interface ProgressUpdateEvent extends BaseEvent {
  type: 'progress_update';
  data: {
    step: string;
    details?: string;
    percentage?: number;
  };
}

/**
 * Tool execution events
 */
export interface ToolStartEvent extends BaseEvent {
  type: 'tool_start';
  data: {
    name: string;
    args: Record<string, any>;
    timestamp: number;
  };
}

export interface ToolResultEvent extends BaseEvent {
  type: 'tool_result';
  data: {
    name: string;
    result: any;
    status: 'success' | 'error';
    duration: number;
    error?: string;
  };
}

export interface ToolExecution {
  name: string;
  args: Record<string, any>;
  status: 'pending' | 'running' | 'success' | 'error';
  result?: any;
  error?: string;
  startTime: number;
  duration?: number;
}

/**
 * Code change events
 */
export interface CodeChangeEvent extends BaseEvent {
  type: 'code_change';
  data: {
    file: string;
    lineStart: number;
    lineEnd: number;
    code: string;
    language: string;
  };
}

/**
 * File reference events
 */
export interface FileReferenceEvent extends BaseEvent {
  type: 'file_reference';
  data: {
    path: string;
    lineStart?: number;
    lineEnd?: number;
    context?: string;
  };
}

/**
 * Error events
 */
export interface ErrorEvent extends BaseEvent {
  type: 'error';
  data: {
    message: string;
    code: string;
    recoverable: boolean;
    details?: any;
  };
}

/**
 * Union type of all possible events
 */
export type OmniEvent =
  | ResponseStartEvent
  | ResponseCompleteEvent
  | NarrativeChunkEvent
  | ProgressUpdateEvent
  | ToolStartEvent
  | ToolResultEvent
  | CodeChangeEvent
  | FileReferenceEvent
  | ErrorEvent;

/**
 * Type guards for event discrimination
 */
export function isResponseStartEvent(event: OmniEvent): event is ResponseStartEvent {
  return event.type === 'response_start';
}

export function isResponseCompleteEvent(event: OmniEvent): event is ResponseCompleteEvent {
  return event.type === 'response_complete';
}

export function isNarrativeChunkEvent(event: OmniEvent): event is NarrativeChunkEvent {
  return event.type === 'narrative_chunk';
}

export function isProgressUpdateEvent(event: OmniEvent): event is ProgressUpdateEvent {
  return event.type === 'progress_update';
}

export function isToolStartEvent(event: OmniEvent): event is ToolStartEvent {
  return event.type === 'tool_start';
}

export function isToolResultEvent(event: OmniEvent): event is ToolResultEvent {
  return event.type === 'tool_result';
}

export function isCodeChangeEvent(event: OmniEvent): event is CodeChangeEvent {
  return event.type === 'code_change';
}

export function isFileReferenceEvent(event: OmniEvent): event is FileReferenceEvent {
  return event.type === 'file_reference';
}

export function isErrorEvent(event: OmniEvent): event is ErrorEvent {
  return event.type === 'error';
}

/**
 * Event validation
 */
export function validateEvent(event: any): event is OmniEvent {
  if (!event || typeof event !== 'object') {
    return false;
  }

  if (!event.type || typeof event.type !== 'string') {
    return false;
  }

  if (!event.timestamp || typeof event.timestamp !== 'number') {
    return false;
  }

  if (!event.requestId || typeof event.requestId !== 'string') {
    return false;
  }

  if (!event.data || typeof event.data !== 'object') {
    return false;
  }

  return true;
}
