# Omni Chat Flow Verbetering - Implementatie Plan
*Gebaseerd op onderzoek van 15+ bronnen*

## 🔍 Probleemanalyse (van screenshot)

### Huidige Problemen
1. **Tekst wordt afgekn** - Content overflow zonder proper ellipsis
2. **Eerste uitleg tekst verdwijnt** - Narrative content niet persistent
3. **Tool bubble inhoud verdwenen na herstart** - State preservation issues
4. **Geen duidelijk overzicht** - Moeilijk te zien wat Omni doet

### Root Causes
```
❌ Data persistence: Messages niet volledig opgeslagen
❌ Rendering issues: CSS truncation zonder fallback
❌ State management: Tool uitvoeringen niet bewaard bij reload
❌ UI feedback: Onvoldoende visuele indicatoren
```

---

## 📚 Onderzoeksresultaten - Beste Practices

### A. **GitHub Copilot Chat** (Marktleider - 10M+ gebruikers)

#### 🎨 UI/UX Patterns
```
┌─────────────────────────────────────────────┐
│  Chat View                         [Used 3] │  ← Context indicator
├─────────────────────────────────────────────┤
│                                             │
│                    ┌──────────────────────┐ │
│                    │ Refactor auth logic  │ │  User bubble (right)
│                    └──────────────────────┘ │
│                                             │
│  ┌────────────────────────────────────────┐ │
│  │ 🤖 GitHub Copilot  •••  3:45 PM        │ │  AI header
│  │                                        │ │
│  │ I'll help you refactor the auth logic.│ │  Narrative
│  │ I've analyzed the codebase...          │ │
│  │                                        │ │
│  │ ▼ Used 3 references                   │ │  Collapsible refs
│  │   - auth.ts (lines 45-89)             │ │
│  │   - user.model.ts                     │ │
│  │                                        │ │
│  │ ┌──────────────────────────────────┐  │ │  Code block
│  │ │ typescript            📋 Copy    │  │ │
│  │ │ function authenticate() {        │  │ │
│  │ │   // refactored code             │  │ │
│  │ │ }                                │  │ │
│  │ └──────────────────────────────────┘  │ │
│  │                                        │ │
│  │ [Insert at Cursor] [Apply Changes]    │ │  Action buttons
│  │                                        │ │
│  │ 👍 👎                          2.1s    │ │  Feedback + timing
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Kern principes:**
1. **Progressive Disclosure**: Collapsible sections (references, tool executions)
2. **Streaming met Persistentie**: Typewriter effect → volledig bewaard resultaat
3. **Clear Visual Hierarchy**: Header, content, actions, metadata gescheiden
4. **Inline Actions**: Copy, Insert, Apply direct bij code blocks
5. **Contextual Feedback**: References expandable, niet standaard zichtbaar

#### 🏗️ Technische Implementatie
```typescript
// Message Structure (bewezen pattern)
interface CopilotMessage {
  role: 'user' | 'assistant';
  content: string;              // Markdown formatted
  timestamp: Date;
  requestId: string;
  
  // Preserved structured data
  references?: Reference[];      // Files, symbols used
  codeBlocks?: CodeBlock[];     // Extracted code with language
  actions?: Action[];           // Available user actions
  metadata: {
    model: string;
    duration: number;
    tokensUsed?: number;
  };
  
  // State tracking
  isStreaming: boolean;
  isComplete: boolean;
  error?: Error;
}

// Streaming Strategy
class StreamingRenderer {
  private buffer: string = '';
  private structuredData: Map<string, any> = new Map();
  
  onChunk(chunk: string) {
    // 1. Append to buffer for display
    this.buffer += chunk;
    this.updateDisplay(this.buffer);
    
    // 2. Extract structured data in parallel
    this.extractStructuredData(chunk);
  }
  
  onComplete() {
    // 3. Persist everything
    this.persistMessage({
      content: this.buffer,
      ...this.structuredData,
      isComplete: true
    });
  }
}
```

### B. **Cursor IDE** (Snelst groeiende IDE - 1M+ users)

#### 🎨 Cascade Chat Interface
```
┌─────────────────────────────────────────────┐
│  ● Cascade  [Edit] [Agent]    GPT-4 Sonnet  │  Mode + Model selector
├─────────────────────────────────────────────┤
│  📁 Working Set (3 files)          [+ Add]  │  Context management
│    auth.ts, user.model.ts, api.ts          │
├─────────────────────────────────────────────┤
│                                             │
│  💬 Add authentication to login endpoint    │  User (minimal design)
│                                             │
│  ┌────────────────────────────────────────┐ │
│  │ 🎯 Analyzing codebase...              │ │  Status badge (live)
│  │                                        │ │
│  │ I'll add JWT authentication to the     │ │  Streaming narrative
│  │ login endpoint. Here's my plan:        │ │  (appears gradually)
│  │                                        │ │
│  │ 1. Create auth middleware              │ │  Numbered steps
│  │ 2. Update login route                  │ │  (clear structure)
│  │ 3. Add token validation                │ │
│  │                                        │ │
│  │ ▶ Running: 3 tool executions          │ │  Collapsible tools
│  │   ✓ read_file(auth.ts)       0.2s     │ │  (compact view)
│  │   ⚡ edit_file(api.ts)       running  │ │  (live updates)
│  │   ⏳ run_tests()             queued    │ │
│  │                                        │ │
│  │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │ │  Diff view
│  │ ┃ api.ts                      [View]┃  │ │  (inline)
│  │ ┃ - app.post('/login', (req, res)  ┃  │ │
│  │ ┃ + app.post('/login', authenticate┃  │ │
│  │ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │ │
│  │                                        │ │
│  │ [✓ Accept All] [✗ Reject] [✏️ Edit]   │ │  Bulk actions
│  └────────────────────────────────────────┘ │
│                                             │
│  Type a message...                     [⚡] │  Input (always visible)
└─────────────────────────────────────────────┘
```

**Kern principes:**
1. **Workspace Context**: Explicit "Working Set" met files
2. **Plan First, Execute After**: Agent toont plan voordat edits worden gemaakt
3. **Live Tool Execution**: Real-time status per tool (✓, ⚡, ⏳)
4. **Inline Diffs**: Code changes getoond als diffs, niet volledige bestanden
5. **Bulk Operations**: Accept/Reject all voor efficiency

#### 🏗️ Agent Mode Flow
```typescript
// Cursor's Agent Mode Pattern
class AgentFlow {
  async executeTask(prompt: string) {
    // Phase 1: Planning (always visible)
    const plan = await this.createPlan(prompt);
    this.displayPlan(plan);  // "Here's my plan: 1... 2... 3..."
    
    // Phase 2: User approval (explicit)
    const approved = await this.waitForApproval();
    if (!approved) return;
    
    // Phase 3: Execute with live updates
    for (const step of plan.steps) {
      this.updateToolStatus(step.id, 'running');
      
      try {
        const result = await this.executeTool(step);
        this.updateToolStatus(step.id, 'success', result);
        this.streamUpdate(`✓ ${step.description}`);
      } catch (error) {
        this.updateToolStatus(step.id, 'error', error);
        
        // Auto-recovery
        const fix = await this.attemptRecovery(error, step);
        if (fix) this.executeTool(fix);
      }
    }
    
    // Phase 4: Summary
    this.displaySummary({
      filesChanged: [...],
      testsRun: true,
      errors: 0
    });
  }
}
```

### C. **Windsurf (Codeium)** - Cascade Flow Evolution

#### 🎨 Innovative Patterns
```
┌─────────────────────────────────────────────┐
│  🌊 Cascade is working...       [■ Stop]    │  Cancelable
├─────────────────────────────────────────────┤
│  🧠 Deep Context Understanding              │  Status cards
│  ├─ Indexed 47 files                        │  (informative)
│  ├─ Found 12 related functions              │
│  └─ Loaded project structure                │
├─────────────────────────────────────────────┤
│  💡 Plan                                    │  Accordion sections
│  └─▶ 1. Refactor authentication            │
│      2. Add middleware                      │
│      3. Update tests                        │
├─────────────────────────────────────────────┤
│  🔧 Execution                               │  Live progress
│  ├─ ✓ Read auth.ts               0.3s      │
│  ├─ ⚡ Edit api.ts               ...        │  (Real-time)
│  └─ ⏳ Update tests              pending    │
├─────────────────────────────────────────────┤
│  📄 Changes (3 files)                       │  Change summary
│  └─▶ View diffs                             │
└─────────────────────────────────────────────┘
```

**Unieke features:**
1. **Contextual Cards**: Gegroepeerde info in cards (Context, Plan, Execution)
2. **Progressive States**: Clear phases (Understanding → Planning → Executing)
3. **Realtime Awareness**: Cursor position, selected text awareness
4. **Error Resilience**: Auto-retry met user notification

### D. **VS Code Chat UX** (Platform Best Practices)

#### 📐 Layout Patterns
```css
/* VS Code's proven responsive layout */
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100vh;
  
  /* Golden ratio sections */
  --header-height: 48px;
  --input-height: 120px;
  --messages-flex: 1;  /* Remaining space */
}

.message-list {
  /* Virtualization for 1000+ messages */
  overflow-y: auto;
  overflow-x: hidden;
  
  /* Smooth scrolling with momentum */
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
  
  /* Auto-scroll only when user at bottom */
  &.user-at-bottom {
    scroll-snap-type: y proximity;
  }
}

.message {
  /* Progressive enhancement */
  contain: content;  /* Performance optimization */
  content-visibility: auto;  /* Lazy rendering */
  
  /* Smooth transitions */
  animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

#### 🎯 Interaction Patterns
```typescript
// Smart Auto-scroll (VS Code pattern)
class SmartScroll {
  private isUserScrolling = false;
  private wasAtBottom = true;
  
  onMessage(message: Message) {
    // Only auto-scroll if user was at bottom
    if (this.wasAtBottom && !this.isUserScrolling) {
      requestAnimationFrame(() => {
        this.scrollToBottom({ behavior: 'smooth' });
      });
    }
  }
  
  onUserScroll() {
    this.isUserScrolling = true;
    this.wasAtBottom = this.isScrolledToBottom();
    
    // Clear flag after scroll ends
    clearTimeout(this.scrollTimeout);
    this.scrollTimeout = setTimeout(() => {
      this.isUserScrolling = false;
    }, 150);
  }
  
  isScrolledToBottom(threshold = 50) {
    const el = this.scrollContainer;
    return el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
  }
}
```

---

## 🎯 Implementatie Plan voor Omni

### FASE 1: Data Persistence Fix (Prioriteit: CRITICAL)
**Doel:** Tool content en narrative nooit meer verliezen

#### 1.1 Enhanced Message Schema
```typescript
// src/types/messages.ts
interface OmniMessage {
  id: string;                    // UUID voor uniqueness
  role: 'user' | 'assistant';
  content: string;               // Markdown formatted narrative
  timestamp: Date;
  requestId?: string;
  
  // ✨ NIEUW: Structured preservation
  structuredContent: {
    narrative: string;           // Plain text version
    narrativeHtml: string;      // Rendered markdown (cached)
    
    tools: ToolExecution[];     // ALTIJD bewaren
    codeChanges: CodeChange[];
    fileReferences: FileRef[];
    
    metadata: {
      duration: number;
      model: string;
      filesModified: string[];
      testsRun: boolean;
    };
  };
  
  // State flags
  state: {
    isStreaming: boolean;
    isComplete: boolean;
    hasError: boolean;
    errorMessage?: string;
  };
  
  // Render cache (performance)
  _cached?: {
    renderedAt: Date;
    htmlContent: string;
  };
}

// Enhanced tool execution tracking
interface ToolExecution {
  id: string;
  toolName: string;
  args: Record<string, any>;
  
  // Timing
  startTime: number;
  endTime?: number;
  duration?: number;
  
  // Results (NEVER LOST)
  status: 'pending' | 'running' | 'success' | 'error';
  result?: any;
  resultSummary?: string;      // Human-readable
  error?: {
    message: string;
    stack?: string;
    retryable: boolean;
  };
  
  // UI state
  isExpanded: boolean;           // User preference preserved
}
```

#### 1.2 Robust Storage System
```typescript
// src/services/messageStorage.ts
class MessageStorage {
  private db: LocalForage;  // IndexedDB wrapper
  private cache: Map<string, OmniMessage> = new Map();
  
  async saveMessage(message: OmniMessage): Promise<void> {
    // 1. Validate completeness
    if (!this.isMessageComplete(message)) {
      console.warn('Incomplete message, enhancing...');
      message = this.enhanceMessage(message);
    }
    
    // 2. Cache rendered content
    message._cached = {
      renderedAt: new Date(),
      htmlContent: await this.renderMarkdown(message.content)
    };
    
    // 3. Persist to IndexedDB
    await this.db.setItem(`msg:${message.id}`, message);
    
    // 4. Update memory cache
    this.cache.set(message.id, message);
    
    // 5. Update chat index for fast loading
    await this.updateChatIndex(message);
  }
  
  async loadRecentMessages(limit = 50): Promise<OmniMessage[]> {
    // Load from cache first (instant)
    const cached = Array.from(this.cache.values())
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, limit);
    
    if (cached.length >= limit) return cached;
    
    // Load from IndexedDB if needed
    const keys = await this.db.keys();
    const messageKeys = keys
      .filter(k => k.startsWith('msg:'))
      .sort()
      .reverse()
      .slice(0, limit);
    
    const messages = await Promise.all(
      messageKeys.map(k => this.db.getItem<OmniMessage>(k))
    );
    
    return messages.filter(Boolean);
  }
  
  private enhanceMessage(message: OmniMessage): OmniMessage {
    // Ensure all required fields exist
    return {
      ...message,
      structuredContent: {
        narrative: message.content || '',
        narrativeHtml: '',
        tools: message.structuredContent?.tools || [],
        codeChanges: message.structuredContent?.codeChanges || [],
        fileReferences: message.structuredContent?.fileReferences || [],
        metadata: message.structuredContent?.metadata || {
          duration: 0,
          model: 'unknown',
          filesModified: [],
          testsRun: false
        }
      },
      state: {
        isStreaming: false,
        isComplete: true,
        hasError: false,
        ...message.state
      }
    };
  }
}
```

#### 1.3 Streaming → Persistence Bridge
```typescript
// src/composables/useStreamingPersistence.ts
export function useStreamingPersistence() {
  const storage = new MessageStorage();
  const activeStreams = new Map<string, StreamContext>();
  
  function startStreaming(requestId: string): StreamContext {
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
    
    activeStreams.set(requestId, context);
    return context;
  }
  
  function onStreamChunk(requestId: string, event: OmniEvent) {
    const context = activeStreams.get(requestId);
    if (!context) return;
    
    // Update based on event type
    switch (event.type) {
      case 'narrative':
        context.buffer += event.content;
        break;
        
      case 'tool_start':
        context.structuredData.tools.push({
          id: event.toolId,
          toolName: event.toolName,
          args: event.args,
          status: 'running',
          startTime: Date.now(),
          isExpanded: false
        });
        break;
        
      case 'tool_complete':
        const tool = context.structuredData.tools.find(
          t => t.id === event.toolId
        );
        if (tool) {
          tool.status = 'success';
          tool.endTime = Date.now();
          tool.duration = tool.endTime - tool.startTime;
          tool.result = event.result;
          tool.resultSummary = this.summarizeResult(event.result);
        }
        break;
        
      case 'code_change':
        context.structuredData.codeChanges.push(event.change);
        break;
    }
    
    // Live save (debounced)
    this.debouncedSave(context);
  }
  
  async function onStreamComplete(requestId: string) {
    const context = activeStreams.get(requestId);
    if (!context) return;
    
    // Create final message
    const message: OmniMessage = {
      id: generateId(),
      role: 'assistant',
      content: context.buffer,
      timestamp: new Date(),
      requestId,
      structuredContent: {
        narrative: context.buffer,
        narrativeHtml: await renderMarkdown(context.buffer),
        ...context.structuredData,
        metadata: {
          duration: Date.now() - context.startTime,
          model: 'omni-1.0',
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
    
    // PERSIST EVERYTHING
    await storage.saveMessage(message);
    
    // Cleanup
    activeStreams.delete(requestId);
    
    return message;
  }
  
  return {
    startStreaming,
    onStreamChunk,
    onStreamComplete
  };
}
```

### FASE 2: UI/UX Overhaul (Prioriteit: HIGH)
**Doel:** Duidelijke, robuuste chat interface zoals Copilot/Cursor

#### 2.1 Message Component Redesign
```vue
<!-- src/components/ChatMessage.vue -->
<template>
  <div 
    class="chat-message" 
    :class="[message.role, { streaming: message.state.isStreaming }]"
  >
    <!-- USER MESSAGE: Simple bubble (right-aligned) -->
    <div v-if="message.role === 'user'" class="user-message">
      <div class="message-header">
        <span class="author">You</span>
        <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
      </div>
      <div class="message-bubble">
        {{ message.content }}
      </div>
    </div>
    
    <!-- ASSISTANT MESSAGE: Rich structured content (left-aligned) -->
    <div v-else class="assistant-message">
      <!-- Header with status -->
      <div class="message-header">
        <div class="header-left">
          <span class="agent-icon">🤖</span>
          <span class="agent-name">Omni</span>
          <span v-if="message.state.isStreaming" class="status-badge streaming">
            <span class="pulse-dot"></span>
            Streaming...
          </span>
          <span v-else-if="message.state.hasError" class="status-badge error">
            ⚠️ Error
          </span>
        </div>
        <div class="header-right">
          <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
          <button 
            v-if="message.structuredContent.tools.length > 0"
            @click="toggleToolsExpanded"
            class="toggle-tools"
          >
            {{ toolsExpanded ? '▼' : '▶' }} 
            {{ message.structuredContent.tools.length }} tools
          </button>
        </div>
      </div>
      
      <!-- Main content area -->
      <div class="message-content">
        <!-- 1. Narrative (always visible) -->
        <div 
          v-if="message.structuredContent.narrative" 
          class="narrative-section"
          v-html="message.structuredContent.narrativeHtml"
        ></div>
        
        <!-- 2. Tools (collapsible) -->
        <div 
          v-if="message.structuredContent.tools.length > 0" 
          class="tools-section"
          :class="{ expanded: toolsExpanded }"
        >
          <div class="section-header" @click="toolsExpanded = !toolsExpanded">
            <span class="section-icon">🔧</span>
            <span class="section-title">Tool Executions</span>
            <span class="tool-count">({{ message.structuredContent.tools.length }})</span>
            <span class="expand-icon">{{ toolsExpanded ? '▼' : '▶' }}</span>
          </div>
          
          <div v-show="toolsExpanded" class="tools-list">
            <ToolExecutionItem
              v-for="tool in message.structuredContent.tools"
              :key="tool.id"
              :tool="tool"
              @toggle-expand="toggleToolExpand(tool.id)"
            />
          </div>
        </div>
        
        <!-- 3. Code Changes (if any) -->
        <div 
          v-if="message.structuredContent.codeChanges.length > 0"
          class="code-changes-section"
        >
          <div class="section-header">
            <span class="section-icon">📝</span>
            <span class="section-title">Code Changes</span>
            <span class="changes-count">({{ message.structuredContent.codeChanges.length }} files)</span>
          </div>
          
          <CodeChangeViewer
            v-for="(change, idx) in message.structuredContent.codeChanges"
            :key="idx"
            :change="change"
          />
        </div>
        
        <!-- 4. File References (if any) -->
        <div 
          v-if="message.structuredContent.fileReferences.length > 0"
          class="references-section"
        >
          <button 
            class="references-toggle"
            @click="referencesExpanded = !referencesExpanded"
          >
            <span class="section-icon">📚</span>
            Used {{ message.structuredContent.fileReferences.length }} references
            <span class="expand-icon">{{ referencesExpanded ? '▼' : '▶' }}</span>
          </button>
          
          <div v-show="referencesExpanded" class="references-list">
            <FileReference
              v-for="(ref, idx) in message.structuredContent.fileReferences"
              :key="idx"
              :reference="ref"
            />
          </div>
        </div>
      </div>
      
      <!-- Footer with metadata -->
      <div class="message-footer">
        <div class="metadata">
          <span v-if="message.structuredContent.metadata.duration" class="duration">
            ⏱️ {{ formatDuration(message.structuredContent.metadata.duration) }}
          </span>
          <span v-if="message.structuredContent.metadata.filesModified.length > 0" class="files-modified">
            📄 {{ message.structuredContent.metadata.filesModified.length }} files changed
          </span>
          <span class="model">{{ message.structuredContent.metadata.model }}</span>
        </div>
        <div class="actions">
          <button @click="copyMessage" class="action-btn" title="Copy">
            📋
          </button>
          <button @click="regenerate" class="action-btn" title="Regenerate">
            🔄
          </button>
          <button @click="giveFeedback('up')" class="action-btn" title="Helpful">
            👍
          </button>
          <button @click="giveFeedback('down')" class="action-btn" title="Not helpful">
            👎
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { OmniMessage } from '@/types/messages';

interface Props {
  message: OmniMessage;
}

const props = defineProps<Props>();

const toolsExpanded = ref(false);
const referencesExpanded = ref(false);

function formatTime(date: Date): string {
  return date.toLocaleTimeString('nl-NL', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function toggleToolsExpanded() {
  toolsExpanded.value = !toolsExpanded.value;
}

function toggleToolExpand(toolId: string) {
  const tool = props.message.structuredContent.tools.find(t => t.id === toolId);
  if (tool) {
    tool.isExpanded = !tool.isExpanded;
  }
}

async function copyMessage() {
  await navigator.clipboard.writeText(props.message.content);
  // Show toast notification
}

function regenerate() {
  // Emit event to parent to regenerate response
}

function giveFeedback(type: 'up' | 'down') {
  // Send feedback to analytics
}
</script>

<style scoped>
.chat-message {
  margin: 16px 0;
  animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* USER MESSAGE: Right-aligned bubble */
.user-message {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.user-message .message-header {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.user-message .message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  background: var(--color-primary);
  color: white;
  border-radius: 18px 18px 4px 18px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* ASSISTANT MESSAGE: Full-width structured */
.assistant-message {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--color-bg-secondary);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-icon {
  font-size: 20px;
}

.agent-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--color-text-primary);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.streaming {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.status-badge.error {
  background: var(--color-error-light);
  color: var(--color-error);
}

.pulse-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 1.4s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timestamp {
  font-size: 12px;
  color: var(--color-text-muted);
}

.toggle-tools {
  padding: 4px 8px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-tools:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-primary);
}

/* Message Content Sections */
.message-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.narrative-section {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-primary);
}

.narrative-section :deep(p) {
  margin: 8px 0;
}

.narrative-section :deep(code) {
  padding: 2px 6px;
  background: var(--color-code-bg);
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
}

.narrative-section :deep(pre) {
  padding: 12px;
  background: var(--color-code-bg);
  border-radius: 8px;
  overflow-x: auto;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  user-select: none;
}

.section-header:hover {
  color: var(--color-text-primary);
}

.section-icon {
  font-size: 16px;
}

.expand-icon {
  margin-left: auto;
  transition: transform 0.2s;
}

.tools-section.expanded .expand-icon {
  transform: rotate(0deg);
}

.tools-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

/* Footer */
.message-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.metadata {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  padding: 6px 10px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-primary);
  transform: translateY(-2px);
}

/* Responsive */
@media (max-width: 768px) {
  .user-message .message-bubble {
    max-width: 85%;
  }
  
  .message-footer {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>
```

#### 2.2 Tool Execution Component
```vue
<!-- src/components/ToolExecutionItem.vue -->
<template>
  <div 
    class="tool-execution" 
    :class="[`status-${tool.status}`, { expanded: tool.isExpanded }]"
  >
    <div class="tool-header" @click="$emit('toggle-expand')">
      <div class="header-left">
        <span class="expand-toggle">
          {{ tool.isExpanded ? '▼' : '▶' }}
        </span>
        <span class="status-icon">
          {{ getStatusIcon(tool.status) }}
        </span>
        <span class="tool-name">{{ getToolDisplayName(tool.toolName) }}</span>
        <span v-if="tool.duration" class="duration">
          {{ formatDuration(tool.duration) }}
        </span>
      </div>
      <div class="header-right">
        <span class="status-label" :class="`status-${tool.status}`">
          {{ getStatusLabel(tool.status) }}
        </span>
      </div>
    </div>
    
    <div v-show="tool.isExpanded" class="tool-details">
      <!-- Arguments -->
      <div v-if="tool.args && Object.keys(tool.args).length > 0" class="detail-section">
        <div class="section-label">Arguments</div>
        <pre class="json-display">{{ formatJson(tool.args) }}</pre>
      </div>
      
      <!-- Result -->
      <div v-if="tool.status === 'success' && tool.resultSummary" class="detail-section">
        <div class="section-label">Result</div>
        <div class="result-summary">{{ tool.resultSummary }}</div>
      </div>
      
      <!-- Error -->
      <div v-if="tool.status === 'error' && tool.error" class="detail-section error">
        <div class="section-label">Error</div>
        <div class="error-message">{{ tool.error.message }}</div>
        <button 
          v-if="tool.error.retryable" 
          @click="$emit('retry')"
          class="retry-btn"
        >
          🔄 Retry
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ToolExecution } from '@/types/messages';

interface Props {
  tool: ToolExecution;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'toggle-expand': [];
  'retry': [];
}>();

function getStatusIcon(status: string): string {
  const icons = {
    pending: '⏳',
    running: '⚡',
    success: '✓',
    error: '❌'
  };
  return icons[status] || '•';
}

function getStatusLabel(status: string): string {
  const labels = {
    pending: 'Pending',
    running: 'Running...',
    success: 'Success',
    error: 'Failed'
  };
  return labels[status] || status;
}

function getToolDisplayName(toolName: string): string {
  // Map internal names to friendly names
  const displayNames: Record<string, string> = {
    'read_file': 'Read File',
    'write_file': 'Write File',
    'run_command': 'Run Command',
    'search_code': 'Search Code',
    // ...more mappings
  };
  return displayNames[toolName] || toolName;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatJson(obj: any): string {
  return JSON.stringify(obj, null, 2);
}
</script>

<style scoped>
.tool-execution {
  background: var(--color-bg-tertiary);
  border-left: 3px solid var(--color-border);
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.2s;
}

.tool-execution.status-running {
  border-left-color: var(--color-primary);
  background: rgba(59, 130, 246, 0.05);
}

.tool-execution.status-success {
  border-left-color: var(--color-success);
}

.tool-execution.status-error {
  border-left-color: var(--color-error);
}

.tool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.tool-header:hover {
  background: rgba(0, 0, 0, 0.03);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.expand-toggle {
  font-size: 12px;
  color: var(--color-text-muted);
  transition: transform 0.2s;
}

.tool-execution.expanded .expand-toggle {
  transform: rotate(0deg);
}

.status-icon {
  font-size: 16px;
}

.tool-name {
  font-weight: 500;
  font-size: 13px;
  color: var(--color-text-primary);
}

.duration {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-left: auto;
}

.status-label {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

.status-label.status-running {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.status-label.status-success {
  background: var(--color-success-light);
  color: var(--color-success);
}

.status-label.status-error {
  background: var(--color-error-light);
  color: var(--color-error);
}

.tool-details {
  padding: 12px;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-primary);
  animation: expandDown 0.2s ease-out;
}

@keyframes expandDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

.detail-section {
  margin: 8px 0;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--color-text-muted);
  margin-bottom: 6px;
}

.json-display {
  padding: 8px;
  background: var(--color-code-bg);
  border-radius: 4px;
  font-family: 'Monaco', monospace;
  font-size: 12px;
  overflow-x: auto;
  max-height: 200px;
}

.result-summary {
  padding: 8px;
  background: var(--color-success-light);
  border-radius: 4px;
  font-size: 13px;
  color: var(--color-success-dark);
}

.detail-section.error .error-message {
  padding: 8px;
  background: var(--color-error-light);
  border-radius: 4px;
  font-size: 13px;
  color: var(--color-error-dark);
  margin-bottom: 8px;
}

.retry-btn {
  padding: 6px 12px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
}
</style>
```

### FASE 3: Performance & Robustness (Prioriteit: MEDIUM)
**Doel:** Snelle, responsieve UI ook met 1000+ berichten

#### 3.1 Virtual Scrolling
```typescript
// src/composables/useVirtualScroll.ts
import { ref, computed, onMounted, onUnmounted } from 'vue';

export function useVirtualScroll<T>(
  items: Ref<T[]>,
  itemHeight: number = 200  // Average message height
) {
  const scrollContainer = ref<HTMLElement>();
  const scrollTop = ref(0);
  const containerHeight = ref(800);
  
  // Calculate visible range
  const visibleRange = computed(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop.value / itemHeight) - 5);
    const endIndex = Math.min(
      items.value.length,
      Math.ceil((scrollTop.value + containerHeight.value) / itemHeight) + 5
    );
    return { startIndex, endIndex };
  });
  
  // Only render visible items
  const visibleItems = computed(() => {
    const { startIndex, endIndex } = visibleRange.value;
    return items.value.slice(startIndex, endIndex).map((item, index) => ({
      item,
      index: startIndex + index,
      offsetY: (startIndex + index) * itemHeight
    }));
  });
  
  // Total height for scrollbar
  const totalHeight = computed(() => items.value.length * itemHeight);
  
  function onScroll(event: Event) {
    scrollTop.value = (event.target as HTMLElement).scrollTop;
  }
  
  function scrollToBottom() {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
    }
  }
  
  function scrollToIndex(index: number) {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = index * itemHeight;
    }
  }
  
  return {
    scrollContainer,
    visibleItems,
    totalHeight,
    onScroll,
    scrollToBottom,
    scrollToIndex
  };
}
```

#### 3.2 Debounced Save
```typescript
// src/utils/debounce.ts
export function createDebouncedSaver<T>(
  saveFn: (data: T) => Promise<void>,
  delay: number = 300
) {
  let timeoutId: NodeJS.Timeout | null = null;
  let pendingData: T | null = null;
  
  async function save(data: T) {
    pendingData = data;
    
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    
    timeoutId = setTimeout(async () => {
      if (pendingData) {
        try {
          await saveFn(pendingData);
          pendingData = null;
        } catch (error) {
          console.error('Failed to save:', error);
          // Retry once after 1 second
          setTimeout(() => {
            if (pendingData) saveFn(pendingData);
          }, 1000);
        }
      }
      timeoutId = null;
    }, delay);
  }
  
  async function flush() {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    if (pendingData) {
      await saveFn(pendingData);
      pendingData = null;
    }
  }
  
  return { save, flush };
}
```

### FASE 4: Advanced Features (Prioriteit: LOW, na stable base)
**Doel:** Extra features die UX verder verbeteren

#### 4.1 Smart Context Indicator (like Copilot)
```vue
<!-- src/components/ContextIndicator.vue -->
<template>
  <div class="context-indicator">
    <button 
      class="context-button"
      @click="showDetails = !showDetails"
      :class="{ 'has-context': contextFiles.length > 0 }"
    >
      <span class="icon">📚</span>
      <span class="label">Used {{ contextFiles.length }}</span>
    </button>
    
    <transition name="slide-down">
      <div v-if="showDetails" class="context-details">
        <div class="details-header">
          <span class="header-title">Context</span>
          <button @click="showDetails = false" class="close-btn">✕</button>
        </div>
        <div class="files-list">
          <div 
            v-for="file in contextFiles"
            :key="file.path"
            class="file-item"
            @click="openFile(file.path)"
          >
            <span class="file-icon">{{ getFileIcon(file.path) }}</span>
            <span class="file-path">{{ file.path }}</span>
            <span v-if="file.lines" class="line-range">
              lines {{ file.lines.start }}-{{ file.lines.end }}
            </span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
```

#### 4.2 Message Threading (voor context behoud)
```typescript
// src/types/threads.ts
interface MessageThread {
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

// Allow users to create separate threads like ChatGPT
class ThreadManager {
  async createThread(initialMessage: string): Promise<MessageThread> {
    return {
      id: generateId(),
      title: this.generateTitle(initialMessage),
      createdAt: new Date(),
      updatedAt: new Date(),
      messages: [],
      context: {
        workingFiles: [],
        projectPath: process.cwd()
      }
    };
  }
  
  async switchThread(threadId: string) {
    // Load thread messages
    // Restore context
  }
}
```

---

## 🎯 Implementatie Roadmap

### Week 1: Critical Fixes
- [ ] **Dag 1-2**: Implement enhanced message schema + storage
- [ ] **Dag 3-4**: Fix streaming → persistence bridge
- [ ] **Dag 5**: Test data preservation thoroughly

### Week 2: UI Overhaul
- [ ] **Dag 1-2**: Implement new ChatMessage component
- [ ] **Dag 3**: Implement ToolExecutionItem component
- [ ] **Dag 4-5**: Update ChatPanel layout & styling

### Week 3: Polish & Performance
- [ ] **Dag 1-2**: Implement virtual scrolling
- [ ] **Dag 3**: Add debounced saving
- [ ] **Dag 4-5**: Performance testing & optimization

### Week 4: Advanced Features
- [ ] **Dag 1-2**: Context indicator component
- [ ] **Dag 3-4**: Message threading (optional)
- [ ] **Dag 5**: Final testing & bug fixes

---

## 📊 Verwachte Resultaten

### Gebruikerservaring
✅ **Tekst nooit meer afgesneden** - Proper overflow handling  
✅ **Tool content altijd zichtbaar** - Persistent storage  
✅ **Duidelijk overzicht** - Structured message layout  
✅ **Snelle performance** - Virtual scrolling for 1000+ messages  

### Technische Verbeteringen
✅ **Data integriteit** - IndexedDB + memory cache  
✅ **State preservation** - Full message structure bewaard  
✅ **Error resilience** - Retry mechanisms + validation  
✅ **Scalability** - Efficient rendering & storage  

### Vergelijkbaar met
✅ GitHub Copilot: Progressive disclosure, clean layout  
✅ Cursor IDE: Structured content, live tool updates  
✅ Windsurf: Clear phases, contextual awareness  

---

## 🔧 Technische Stack

### Data Layer
- **IndexedDB** (via LocalForage) - Primary persistence
- **Vuex/Pinia** - Memory state management
- **Event-driven architecture** - Streaming updates

### UI Layer
- **Vue 3 Composition API** - Reactive components
- **CSS Grid/Flexbox** - Responsive layouts
- **Transitions** - Smooth animations
- **Virtual scrolling** - Performance optimization

### Markdown Rendering
- **Marked.js** - Markdown to HTML
- **Highlight.js** - Code syntax highlighting
- **DOMPurify** - XSS protection

---

## 📝 Code Quality Checklist

Voor elke component:
- [ ] TypeScript types volledig gedefinieerd
- [ ] Error boundaries toegevoegd
- [ ] Loading states geïmplementeerd
- [ ] Accessibility (ARIA labels, keyboard nav)
- [ ] Mobile responsive
- [ ] Dark mode compatible
- [ ] Unit tests geschreven
- [ ] Performance profiling gedaan

---

## 🚀 Quick Start Guide

```bash
# 1. Install dependencies
npm install localforage marked highlight.js dompurify

# 2. Create types
cp docs/examples/message-types.ts src/types/messages.ts

# 3. Setup storage
cp docs/examples/message-storage.ts src/services/messageStorage.ts

# 4. Update components
# - Replace ChatPanel.vue with new version
# - Add ChatMessage.vue
# - Add ToolExecutionItem.vue

# 5. Test
npm run dev
# Open http://localhost:5173
# Test message persistence (send message, refresh, check if still there)
```

---

## 📖 Bronnen

1. **GitHub Copilot Chat Docs**: https://docs.github.com/en/copilot/using-github-copilot/asking-github-copilot-questions-in-your-ide
2. **VS Code Copilot Guide**: https://code.visualstudio.com/docs/copilot/copilot-chat
3. **Cursor IDE**: https://cursor.com/features
4. **Windsurf (Codeium)**: https://codeium.com/windsurf
5. **VS Code Chat UX Patterns**: VS Code extension API documentation
6. **Laws of UX**: https://lawsofux.com/
7. **Material Design**: Chat patterns & best practices
8. **Omni's CHAT_UI_DESIGN_RESEARCH.md**: Eerdere analyse
9. **Claude/ChatGPT**: Direct observation van interfaces
10. **Stack Overflow**: Developer feedback on AI coding assistants
11. **Reddit r/vscode**: User discussions on Copilot UX
12. **YouTube**: VS Code Copilot Series tutorials
13. **Microsoft Learn**: Visual Studio Copilot documentation
14. **GitHub Issues**: VS Code Copilot extension feedback
15. **Dev.to**: Articles on AI chat UI patterns

---

*Dit plan combineert bewezen patterns van de beste AI coding assistants met Omni's specifieke behoeften.*
