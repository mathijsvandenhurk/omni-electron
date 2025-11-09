# Omni UX Redesign Plan
## Van Basis Progress naar VS Code-stijl Streaming Responses

**Created:** 2025-01-XX  
**Status:** Planning Phase  
**Priority:** HIGH - User Dissatisfaction

---

## Executive Summary

### Probleem
Huidige Omni implementatie toont progress met basic visual indicators (spinner + emoji badges), maar gebruiker wil complete UX redesign naar VS Code Copilot-stijl responses met:
- Natuurlijke Nederlandse narratief flow
- Code changes met line numbers (bijv. "ChatPanel.vue+13-1")
- Progress geïntegreerd in lopende tekst
- Probleem → Oplossing → Implementatie structuur
- Success metrics met ✅ checkmarks

### Huidige Performance Bottleneck
Backend maakt **12+ LLM calls** per request:
- 1× planning prompt
- Per tool: 1× next action explanation + 1× result analysis  
- 1× completion summary
- **Resultaat:** 5 tools = 15 LLM calls = 3-5× te traag

### Oplossing
Complete redesign van response generation:
1. **Backend:** Single streaming LLM call met geïntegreerde narrative
2. **Frontend:** Real-time streaming display met embedded code blocks
3. **Protocol:** Event-based streaming voor granular progress updates
4. **Logging:** Structured logging zonder console clutter

### Expected Outcomes
- **Performance:** 3-5× sneller (12 calls → 2-3 calls)
- **UX:** VS Code-stijl natural language responses
- **Maintainability:** Clean logs, duidelijke event protocol
- **Extensibility:** Makkelijk nieuwe response types toevoegen

---

## Research Findings

### 1. VS Code Chat Extension Patterns

**ChatResponseStream API:**
```typescript
const handler: vscode.ChatRequestHandler = async (request, context, stream, token) => {
  // Natural language explanation
  stream.markdown("Ik begrijp de problemen! Laten me deze systematisch oplossen:");
  
  // Progress update
  stream.progress("Reading ChatPanel.vue, lines 440 to 540");
  
  // Code changes
  stream.markdown("```vue\n// ChatPanel.vue+13-1\nconst currentProgress = ref([]);\n```");
  
  // File reference
  stream.reference(fileUri);
  
  // Success summary
  stream.markdown("✅ Wat ik heb opgelost:\n1. Visuele Progress Feedback\n2. Real-time Updates");
};
```

**Key Features:**
- `stream.markdown()` - Incremental text rendering
- `stream.progress()` - Status updates (niet main content)
- `stream.reference()` - File/location links
- `stream.button()` - Actionable commands
- `stream.filetree()` - Directory structure preview

### 2. Anthropic Streaming Architecture

**SSE Event Flow:**
```
event: message_start          → Message initialization
event: content_block_start    → New content block (text/tool_use)
event: content_block_delta    → Incremental content (multiple)
event: content_block_stop     → Block complete
event: message_delta          → Metadata updates (stop_reason, usage)
event: message_stop           → Stream complete
```

**Tool Use Streaming:**
```json
{"type": "content_block_delta", "delta": {"type": "input_json_delta", "partial_json": "{\"location\": \"San Fra"}}
{"type": "content_block_delta", "delta": {"type": "input_json_delta", "partial_json": "ncisco, CA\"}"}}
```

Fine-grained streaming van tool parameters voor real-time feedback.

### 3. Agent Workflow Patterns

**Cursor Cascade:**
- Multi-step planning met contextual awareness
- Scoped changes via natural language
- Real-time execution visibility

**Continue.dev:**
- Background agents voor async operations
- TUI mode voor interactive workflows
- Mission Control voor orchestration

**Windsurf:**
- SWE-1.5 model voor near-SOTA performance
- Supercomplete: Predicts next actions
- In-line commands met follow-ups

### 4. Response Structure Analysis

**User's Preferred Format (from examples):**

```
1. Probleem Analyse
   Ik begrijp de problemen!
   
   Problemen:
   1. [Issue A]
   2. [Issue B]
   3. [Issue C]

2. Oplossing
   Laten me deze systematisch oplossen:
   
   [Strategy explanation]

3. Implementatie
   Read [file], lines [X] to [Y]
   
   ```language
   // [file]+[line]-[count]
   [code snippet]
   ```

4. Success Summary
   ✅ Wat ik heb opgelost:
   1. [Achievement 1]
   2. [Achievement 2]
   
   Performance: [metrics]
```

---

## Proposed Architecture

### Event Protocol

**Backend → Frontend Events:**

```typescript
// Event Types
type OmniEvent = 
  | { type: 'response_start'; data: { requestId: string; timestamp: number } }
  | { type: 'narrative_chunk'; data: { text: string; isMarkdown: boolean } }
  | { type: 'progress_update'; data: { step: string; details?: string } }
  | { type: 'tool_start'; data: { name: string; args: Record<string, any> } }
  | { type: 'tool_result'; data: { name: string; result: any; status: 'success' | 'error' } }
  | { type: 'code_change'; data: { file: string; lineRange: string; code: string; language: string } }
  | { type: 'file_reference'; data: { path: string; lineStart?: number; lineEnd?: number } }
  | { type: 'response_complete'; data: { metadata: ResponseMetadata } }
  | { type: 'error'; data: { message: string; code: string; recoverable: boolean } };

interface ResponseMetadata {
  requestId: string;
  duration: number;
  tokensUsed: number;
  toolsExecuted: string[];
  filesModified: string[];
}
```

### Backend Redesign (Python)

**Current Flow (12 LLM calls):**
```
User Request
  → Planning LLM Call
  → For each tool:
      → Next Action Explanation LLM Call
      → Tool Execution
      → Result Analysis LLM Call
  → Completion Summary LLM Call
  → Send Response
```

**New Flow (2-3 LLM calls):**
```
User Request
  → Single Streaming LLM Call with System Prompt voor VS Code-stijl
      → Stream narrative chunks real-time
      → On tool_use block: execute tool
      → Stream tool results terug naar LLM
      → Continue streaming narrative
  → Stream Complete event
```

**Implementation Approach:**

```python
async def handle_chat_streaming(request: dict, ws_connection):
    """Stream responses in VS Code style"""
    
    # Emit start event
    await emit_event(ws_connection, {
        'type': 'response_start',
        'data': {'requestId': request['id'], 'timestamp': time.time()}
    })
    
    # Prepare streaming LLM request
    messages = build_conversation_history(request)
    system_prompt = get_vs_code_style_prompt()  # Dutch narrative instructions
    
    # Stream from Anthropic
    async with anthropic.messages.stream(
        model="claude-sonnet-4-20250514",
        messages=messages,
        system=system_prompt,
        tools=get_available_tools(),
        max_tokens=4096,
    ) as stream:
        async for event in stream:
            if event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    # Stream narrative text
                    await emit_event(ws_connection, {
                        'type': 'narrative_chunk',
                        'data': {'text': event.delta.text, 'isMarkdown': True}
                    })
                    
                elif event.delta.type == "input_json_delta":
                    # Tool parameter streaming (optional: show progress)
                    pass
                    
            elif event.type == "content_block_stop":
                # Check if tool use block completed
                if event.content_block.type == "tool_use":
                    tool_name = event.content_block.name
                    tool_args = event.content_block.input
                    
                    # Emit tool start
                    await emit_event(ws_connection, {
                        'type': 'tool_start',
                        'data': {'name': tool_name, 'args': tool_args}
                    })
                    
                    # Execute tool
                    try:
                        result = await execute_tool(tool_name, tool_args)
                        
                        # Emit tool result
                        await emit_event(ws_connection, {
                            'type': 'tool_result',
                            'data': {'name': tool_name, 'result': result, 'status': 'success'}
                        })
                        
                        # Continue streaming with tool result
                        # (Anthropic will generate next narrative based on result)
                        
                    except Exception as e:
                        await emit_event(ws_connection, {
                            'type': 'tool_result',
                            'data': {'name': tool_name, 'result': str(e), 'status': 'error'}
                        })
    
    # Emit completion
    await emit_event(ws_connection, {
        'type': 'response_complete',
        'data': {
            'metadata': {
                'requestId': request['id'],
                'duration': time.time() - start_time,
                'tokensUsed': stream.usage.output_tokens,
                'toolsExecuted': executed_tools,
                'filesModified': modified_files
            }
        }
    })
```

**System Prompt Update:**

```python
VS_CODE_STYLE_PROMPT = """
Je bent Omni, een AI coding assistant geïntegreerd in een VS Code-stijl interface.

RESPONSE STYLE:
- Gebruik natuurlijke Nederlandse taal
- Begin met probleem analyse: "Ik begrijp de situatie!"
- Gebruik gestructureerde secties met headers
- Toon progress embedded in narrative: "Laten me eerst [file] checken..."
- Bij code changes: specifieke line numbers vermelden

FORMATTING:
- Markdown voor structure (headers, lists, code blocks)
- Code blocks format: 
  ```language
  // [filename]+[startLine]-[lineCount]
  [code]
  ```
- Success summaries met ✅ bullets
- File references: `[filepath]` of `[filepath]:[line]`

WORKFLOW:
1. Probleem Analyse - Begrijp user's request, break down in sub-issues
2. Oplossing - Explain strategy systematically
3. Implementatie - Show actual changes with line numbers
4. Verificatie - Confirm changes work
5. Summary - Bullet lijst met achievements + metrics

TOOLS:
- Gebruik tools transparently, vertel user wat je doet
- "Laten me [filename] lezen..." voor read_file
- "Ik ga [change] maken in [file]..." voor replace_string
- Show progress naturally in narrative, niet als separate messages

TONE:
- Professioneel maar vriendelijk
- Enthousiast bij successes ("Perfect!", "Gelukt!")
- Empathisch bij problems ("Ik begrijp het probleem", "Dat is vervelend")
- Clear explanations zonder jargon waar mogelijk

Voorbeelden in conversation history tonen exact gewenste stijl.
"""
```

### Frontend Redesign (Vue 3)

**New Components:**

**1. StreamingResponse.vue** - Main container voor streaming responses
```vue
<template>
  <div class="streaming-response">
    <!-- Narrative chunks (markdown) -->
    <div class="narrative-content" v-html="renderedMarkdown"></div>
    
    <!-- Tool executions (collapsible tree) -->
    <ToolExecutionTree 
      v-if="toolExecutions.length > 0"
      :executions="toolExecutions"
    />
    
    <!-- Code changes (syntax highlighted) -->
    <CodeChangeViewer
      v-for="change in codeChanges"
      :key="change.file"
      :file="change.file"
      :lineRange="change.lineRange"
      :code="change.code"
      :language="change.language"
    />
    
    <!-- Completion metadata -->
    <ResponseMetadata 
      v-if="metadata"
      :metadata="metadata"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { marked } from 'marked';
import ToolExecutionTree from './ToolExecutionTree.vue';
import CodeChangeViewer from './CodeChangeViewer.vue';
import ResponseMetadata from './ResponseMetadata.vue';

const narrativeBuffer = ref('');
const toolExecutions = ref<ToolExecution[]>([]);
const codeChanges = ref<CodeChange[]>([]);
const metadata = ref<ResponseMetadata | null>(null);

const renderedMarkdown = computed(() => {
  return marked.parse(narrativeBuffer.value);
});

// Handle streaming events from backend
function handleStreamEvent(event: OmniEvent) {
  switch (event.type) {
    case 'narrative_chunk':
      narrativeBuffer.value += event.data.text;
      break;
      
    case 'tool_start':
      toolExecutions.value.push({
        name: event.data.name,
        args: event.data.args,
        status: 'running',
        startTime: Date.now()
      });
      break;
      
    case 'tool_result':
      const execution = toolExecutions.value.find(e => e.name === event.data.name);
      if (execution) {
        execution.status = event.data.status;
        execution.result = event.data.result;
        execution.duration = Date.now() - execution.startTime;
      }
      break;
      
    case 'code_change':
      codeChanges.value.push({
        file: event.data.file,
        lineRange: event.data.lineRange,
        code: event.data.code,
        language: event.data.language
      });
      break;
      
    case 'response_complete':
      metadata.value = event.data.metadata;
      break;
  }
}
</script>
```

**2. CodeChangeViewer.vue** - Display code changes met line numbers
```vue
<template>
  <div class="code-change-viewer">
    <div class="code-header">
      <span class="file-icon">📄</span>
      <span class="file-path">{{ file }}</span>
      <span class="line-range">{{ lineRange }}</span>
      <button @click="copyCode" class="copy-btn">📋 Copy</button>
    </div>
    
    <div class="code-content">
      <pre><code :class="`language-${language}`" v-html="highlightedCode"></code></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import Prism from 'prismjs';

interface Props {
  file: string;
  lineRange: string;  // e.g., "+13-5" (start line 13, 5 lines)
  code: string;
  language: string;
}

const props = defineProps<Props>();

const highlightedCode = computed(() => {
  return Prism.highlight(props.code, Prism.languages[props.language], props.language);
});

function copyCode() {
  navigator.clipboard.writeText(props.code);
}
</script>

<style scoped>
.code-change-viewer {
  margin: 12px 0;
  border: 1px solid var(--vscode-panel-border);
  border-radius: 6px;
  overflow: hidden;
}

.code-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--vscode-editor-background);
  border-bottom: 1px solid var(--vscode-panel-border);
  font-size: 12px;
}

.file-path {
  font-family: var(--vscode-editor-font-family);
  flex: 1;
}

.line-range {
  color: var(--vscode-descriptionForeground);
  font-family: monospace;
}

.code-content {
  background: var(--vscode-editor-background);
  overflow-x: auto;
}

.code-content pre {
  margin: 0;
  padding: 12px;
  font-family: var(--vscode-editor-font-family);
  font-size: 13px;
  line-height: 1.6;
}
</style>
```

**3. ToolExecutionTree.vue** - Collapsible tree van tool executions
```vue
<template>
  <div class="tool-execution-tree">
    <div class="tree-header">
      <span class="tree-icon">🔧</span>
      <span>Tool Executions ({{ executions.length }})</span>
    </div>
    
    <div class="tree-items">
      <div 
        v-for="(exec, index) in executions" 
        :key="index"
        class="tree-item"
        :class="exec.status"
      >
        <div class="item-header" @click="toggleExpand(index)">
          <span class="status-icon">{{ getStatusIcon(exec.status) }}</span>
          <span class="tool-name">{{ exec.name }}</span>
          <span v-if="exec.duration" class="duration">{{ exec.duration }}ms</span>
          <span class="expand-icon">{{ expandedItems.has(index) ? '▼' : '▶' }}</span>
        </div>
        
        <div v-if="expandedItems.has(index)" class="item-details">
          <div class="args-section">
            <strong>Arguments:</strong>
            <pre>{{ JSON.stringify(exec.args, null, 2) }}</pre>
          </div>
          
          <div v-if="exec.result" class="result-section">
            <strong>Result:</strong>
            <pre>{{ JSON.stringify(exec.result, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface ToolExecution {
  name: string;
  args: Record<string, any>;
  status: 'running' | 'success' | 'error';
  result?: any;
  startTime: number;
  duration?: number;
}

interface Props {
  executions: ToolExecution[];
}

defineProps<Props>();

const expandedItems = ref<Set<number>>(new Set());

function toggleExpand(index: number) {
  if (expandedItems.value.has(index)) {
    expandedItems.value.delete(index);
  } else {
    expandedItems.value.add(index);
  }
}

function getStatusIcon(status: string): string {
  switch (status) {
    case 'running': return '⏳';
    case 'success': return '✅';
    case 'error': return '❌';
    default: return '⏺';
  }
}
</script>
```

**4. ChatPanel.vue Updates** - Integrate streaming components
```vue
<template>
  <div class="chat-panel">
    <div class="messages-container" ref="messagesContainer">
      <div 
        v-for="message in messages" 
        :key="message.id"
        class="message"
        :class="message.role"
      >
        <template v-if="message.role === 'user'">
          <div class="message-content">{{ message.content }}</div>
        </template>
        
        <template v-else>
          <StreamingResponse 
            :events="message.events"
            :isComplete="message.isComplete"
          />
        </template>
      </div>
    </div>
    
    <ChatInput @send="handleSendMessage" />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';
import StreamingResponse from './StreamingResponse.vue';
import ChatInput from './ChatInput.vue';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content?: string;
  events?: OmniEvent[];
  isComplete: boolean;
}

const messages = ref<Message[]>([]);
const messagesContainer = ref<HTMLElement | null>(null);

// Handle incoming events from backend via IPC
window.electronAPI.onChatEvent((event: OmniEvent) => {
  const currentMessage = messages.value[messages.value.length - 1];
  
  if (event.type === 'response_start') {
    // Create new assistant message
    messages.value.push({
      id: event.data.requestId,
      role: 'assistant',
      events: [],
      isComplete: false
    });
  } else if (event.type === 'response_complete') {
    currentMessage.isComplete = true;
  } else {
    // Add event to current message
    currentMessage.events?.push(event);
  }
  
  // Auto-scroll to bottom
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
});

async function handleSendMessage(content: string) {
  // Add user message
  messages.value.push({
    id: generateId(),
    role: 'user',
    content,
    isComplete: true
  });
  
  // Send to backend
  await window.electronAPI.sendChatMessage({ content });
}
</script>
```

### IPC Protocol (Electron)

**electron/main.js updates:**

```javascript
const { ipcMain } = require('electron');
const { PythonShell } = require('python-shell');

// WebSocket connection naar Python backend
let pythonProcess = null;
let activeStreams = new Map();

ipcMain.handle('chat:send', async (event, message) => {
  const requestId = generateRequestId();
  
  // Start streaming van Python backend
  const stream = pythonProcess.sendRequest({
    type: 'chat',
    id: requestId,
    content: message.content,
    history: message.history
  });
  
  activeStreams.set(requestId, stream);
  
  // Forward events naar renderer
  stream.on('event', (omniEvent) => {
    event.sender.send('chat:event', omniEvent);
  });
  
  stream.on('complete', () => {
    activeStreams.delete(requestId);
  });
  
  stream.on('error', (error) => {
    event.sender.send('chat:event', {
      type: 'error',
      data: {
        message: error.message,
        code: error.code,
        recoverable: true
      }
    });
    activeStreams.delete(requestId);
  });
  
  return { requestId };
});

// Cancel streaming request
ipcMain.handle('chat:cancel', async (event, requestId) => {
  const stream = activeStreams.get(requestId);
  if (stream) {
    stream.cancel();
    activeStreams.delete(requestId);
  }
});
```

**electron/preload.js updates:**

```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  sendChatMessage: (message) => ipcRenderer.invoke('chat:send', message),
  
  cancelChatMessage: (requestId) => ipcRenderer.invoke('chat:cancel', requestId),
  
  onChatEvent: (callback) => {
    ipcRenderer.on('chat:event', (event, omniEvent) => callback(omniEvent));
  }
});
```

---

## Console Logging Strategy

### Current Issues
- Old debug logs scattered throughout codebase
- No structured logging format
- Mix of console.log, console.error, console.warn
- Hard to trace requests through system
- No log levels

### Proposed Solution

**Backend (Python):**
```python
import logging
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage examples
logger.info("chat_request_received", request_id=request_id, content_length=len(content))
logger.debug("tool_execution_started", tool_name="read_file", file_path=path)
logger.error("tool_execution_failed", tool_name="read_file", error=str(e), request_id=request_id)
```

**Frontend (TypeScript):**
```typescript
// src/utils/logger.ts
enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

class Logger {
  private level: LogLevel;
  
  constructor(level: LogLevel = LogLevel.INFO) {
    this.level = level;
  }
  
  debug(message: string, context?: Record<string, any>) {
    if (this.level <= LogLevel.DEBUG) {
      console.debug('[Omni DEBUG]', message, context);
    }
  }
  
  info(message: string, context?: Record<string, any>) {
    if (this.level <= LogLevel.INFO) {
      console.info('[Omni INFO]', message, context);
    }
  }
  
  warn(message: string, context?: Record<string, any>) {
    if (this.level <= LogLevel.WARN) {
      console.warn('[Omni WARN]', message, context);
    }
  }
  
  error(message: string, context?: Record<string, any>) {
    if (this.level <= LogLevel.ERROR) {
      console.error('[Omni ERROR]', message, context);
    }
  }
}

export const logger = new Logger(
  import.meta.env.DEV ? LogLevel.DEBUG : LogLevel.INFO
);

// Usage
logger.info('Chat message sent', { requestId, contentLength: content.length });
logger.error('Stream interrupted', { requestId, error: error.message });
```

**Electron Main Process:**
```javascript
const log = require('electron-log');

// Configure electron-log
log.transports.file.level = 'info';
log.transports.console.level = 'debug';

// Usage
log.info('[IPC] Chat request received', { requestId });
log.error('[IPC] Stream error', { requestId, error: error.message });
```

### Migration Steps
1. Search all `console.log` statements in codebase
2. Replace with appropriate logger calls
3. Remove debug logs that are no longer needed
4. Add correlation IDs (requestId) to all logs
5. Document logging conventions in README

---

## Implementation Timeline

### Phase 1: Backend Streaming (Week 1)
**Days 1-2:** Event protocol design + backend refactoring
- [ ] Define event types (TypeScript + Python types)
- [ ] Implement `emit_event()` helper in Python
- [ ] Update system prompt voor VS Code-stijl
- [ ] Refactor `handle_chat()` naar streaming architecture
- [ ] Test with simple text responses (no tools)

**Days 3-4:** Tool execution streaming
- [ ] Integrate tool execution in streaming flow
- [ ] Emit tool_start / tool_result events
- [ ] Handle tool errors gracefully
- [ ] Test with single tool execution
- [ ] Test with multi-tool execution

**Day 5:** Structured logging
- [ ] Audit all console.log statements
- [ ] Implement structlog in Python backend
- [ ] Add correlation IDs to logs
- [ ] Test log output readability

### Phase 2: Frontend Components (Week 2)
**Days 1-2:** Core streaming components
- [ ] Create StreamingResponse.vue
- [ ] Implement markdown rendering (marked.js)
- [ ] Create CodeChangeViewer.vue with syntax highlighting
- [ ] Create ToolExecutionTree.vue
- [ ] Create ResponseMetadata.vue

**Days 3-4:** ChatPanel integration
- [ ] Update ChatPanel.vue voor streaming events
- [ ] Implement IPC event handlers
- [ ] Add auto-scrolling tijdens streaming
- [ ] Handle error states
- [ ] Add loading states

**Day 5:** Styling + polish
- [ ] VS Code theme matching
- [ ] Animations voor state transitions
- [ ] Responsive layout
- [ ] Dark/light mode support (if needed)

### Phase 3: IPC Protocol (Week 3)
**Days 1-2:** Electron IPC updates
- [ ] Update electron/main.js voor streaming
- [ ] Implement WebSocket/IPC bridge naar Python
- [ ] Add stream cancellation support
- [ ] Handle connection interruptions
- [ ] Test reconnection logic

**Days 3-4:** Frontend logger
- [ ] Implement Logger class in TypeScript
- [ ] Replace all console.* calls
- [ ] Add structured logging
- [ ] Test log output in dev/prod modes

**Day 5:** Integration testing
- [ ] E2E test: Simple question
- [ ] E2E test: Multi-tool request
- [ ] E2E test: Error scenarios
- [ ] E2E test: Network interruption
- [ ] E2E test: Large response

### Phase 4: Performance & Polish (Week 4)
**Days 1-2:** Performance optimization
- [ ] Measure response times (old vs new)
- [ ] Profile frontend rendering
- [ ] Optimize markdown parsing
- [ ] Tune streaming buffer sizes
- [ ] Benchmark tool execution overhead

**Days 3-4:** User testing + iteration
- [ ] User acceptance testing
- [ ] Gather feedback on response style
- [ ] Adjust narrative phrasing
- [ ] Fine-tune timing/animations
- [ ] Polish edge cases

**Day 5:** Documentation
- [ ] Update README with new architecture
- [ ] Document event protocol
- [ ] Create developer guide
- [ ] Add troubleshooting section
- [ ] Update MIGRATION_STATUS.md

---

## Success Metrics

### Performance
- [ ] Response time improved by 3-5× (target: <2s for simple requests)
- [ ] LLM calls reduced from 12+ to 2-3
- [ ] Streaming latency <100ms per chunk
- [ ] No UI freezing during streaming

### UX
- [ ] Responses match VS Code Copilot style
- [ ] Code changes clearly visible with line numbers
- [ ] Progress naturally integrated in narrative
- [ ] No console log clutter
- [ ] Smooth streaming without flicker

### Code Quality
- [ ] All console.log replaced with structured logging
- [ ] Event protocol fully typed (TypeScript + Python)
- [ ] Unit tests for streaming components
- [ ] Integration tests for full flow
- [ ] Documentation complete

### User Satisfaction
- [ ] User approves new response style
- [ ] Narrative tone feels natural
- [ ] Information density is appropriate
- [ ] Error messages are helpful
- [ ] Performance is noticeably better

---

## Risk Mitigation

### Technical Risks

**Risk:** Streaming interruptions (network issues)
- **Mitigation:** Implement reconnection logic, buffer partial responses, show error state
- **Fallback:** Degrade to non-streaming mode if connection unstable

**Risk:** Frontend rendering performance with large responses
- **Mitigation:** Virtual scrolling for long conversations, lazy rendering of code blocks
- **Fallback:** Pagination or "load more" for very long responses

**Risk:** Markdown parsing edge cases
- **Mitigation:** Robust parser (marked.js), sanitize HTML output, handle incomplete blocks
- **Fallback:** Show raw text if parsing fails

**Risk:** IPC protocol version mismatch
- **Mitigation:** Version protocol, handle backward compatibility
- **Fallback:** Show error message suggesting restart

### UX Risks

**Risk:** Narrative tone feels unnatural or too verbose
- **Mitigation:** User testing early, iterate on phrasing, allow customization
- **Fallback:** Provide "concise mode" toggle

**Risk:** Code blocks too large, cluttering conversation
- **Mitigation:** Collapsible sections, show first N lines with "expand"
- **Fallback:** Link to open in editor instead of inline display

**Risk:** Too much information overwhelming user
- **Mitigation:** Hide tool execution details by default, expandable tree
- **Fallback:** Settings voor detail level (minimal/standard/verbose)

### Process Risks

**Risk:** Implementation takes longer than 4 weeks
- **Mitigation:** Incremental rollout, MVP first (text streaming only)
- **Fallback:** Phase 1 & 2 minimum, Phase 3 & 4 as enhancements

**Risk:** Breaking existing functionality
- **Mitigation:** Feature flag for new vs old mode, thorough testing
- **Fallback:** Easy rollback via git, keep old code commented out initially

---

## Next Steps

1. **User Approval** - Presenteer dit plan, get feedback op:
   - Overall approach (streaming architecture)
   - Response style examples (Dutch narrative)
   - Timeline (4 weeks realistic?)
   - Priority (any features moet worden vervroegd/uitgesteld?)

2. **Quick Prototype** - Als approved, maak minimal prototype:
   - Backend: Simple streaming text response (no tools)
   - Frontend: StreamingResponse component with markdown
   - Test end-to-end flow
   - Gather feedback on feel/timing

3. **Phase 1 Kickoff** - Start backend streaming implementation
   - Setup structured logging first (foundation)
   - Implement event protocol
   - Refactor handle_chat() function
   - Extensive testing

4. **Iterative Development** - Weekly demos + feedback loops
   - Week 1: Backend streaming working
   - Week 2: Frontend components functional
   - Week 3: Full integration complete
   - Week 4: Polish + performance optimization

---

## Appendix: Example Response

**User Request:** "Fix the bug where messages aren't loading"

**Old Omni Response (current):**
```
🤔 Planning...
[Visual spinner]
• Reading ChatPanel.vue
• Analyzing code
• Implementing fix
• Testing solution

I've fixed the bug. The issue was...
[Markdown explanation]
```

**New Omni Response (target):**
```markdown
Ik begrijp het probleem! De berichten laden niet omdat de persistence layer
niet correct geïnitialiseerd wordt.

## Probleem Analyse

Laten me eerst ChatPanel.vue checken...

Read ChatPanel.vue, lines 120 to 180

Ik zie het probleem:
1. `loadMessages()` wordt niet called in `onMounted`
2. File path verkeerd: `chat-messages.txt` ipv `chat-messages.json`
3. Error handling mist voor file read failures

## Oplossing

Ik ga drie dingen fixen:

🔧 Tool: read_file
   File: src/components/ChatPanel.vue
   Lines: 120-180
   Status: ✅ Success (342ms)

```vue
// ChatPanel.vue+125-3
onMounted(async () => {
  await loadMessages();  // ✅ Added
  scrollToBottom();
});
```

🔧 Tool: replace_string_in_file
   File: src/components/ChatPanel.vue  
   Lines: 145-147
   Status: ✅ Success (89ms)

```typescript
// ChatPanel.vue+145-1
const messagesPath = path.join(userData, 'chat-messages.json');  // Fixed extension
```

Perfect! Laten me de changes testen...

🔧 Tool: run_tests
   Test Suite: ChatPanel.spec.ts
   Status: ✅ Success - All 12 tests passed (1.2s)

## ✅ Wat ik heb opgelost

1. **Messages Loading** - `loadMessages()` now called on mount
2. **File Path Bug** - Fixed extension: `.txt` → `.json`
3. **Error Handling** - Added try/catch voor file operations

Performance: 3 files read, 2 edits, 12 tests passed in 1.5s
```

**Key Differences:**
- ✅ Natural flowing narrative in Dutch
- ✅ Progress embedded in text ("Laten me eerst checken...")
- ✅ Code blocks with file + line numbers
- ✅ Tool execution visible maar not intrusive
- ✅ Clear problem → solution → verification flow
- ✅ Success summary with checkmarks + metrics
- ✅ Conversational tone ("Perfect!", "Ik zie het probleem")

---

## Questions for User

1. **Response Tone** - Is het voorbeeld hierboven qua tone correct? Te informeel? Te formeel?

2. **Detail Level** - Hoeveel tool execution details wil je zien? Collapsed by default ok?

3. **Code Display** - Line numbers format ok? ("+125-3" means start line 125, 3 lines)

4. **Performance Priority** - Is 3-5× speedup genoeg, of moet het sneller?

5. **Timeline** - 4 weeks realistisch? MVP eerder mogelijk (text streaming only, tools later)?

6. **Existing Features** - Zijn er features in current Omni die we MOETEN behouden?

7. **Testing** - Wil je een prototype zien voordat we full implementation starten?

---

**Document Status:** DRAFT - Awaiting User Feedback
**Last Updated:** 2025-01-XX
**Next Review:** After user approval
