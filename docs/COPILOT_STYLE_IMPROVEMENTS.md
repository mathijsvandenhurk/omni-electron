# Omni Response Style Verbeteringsplan
> Gebaseerd op onderzoek van 10+ bronnen (VS Code Copilot, GitHub Copilot, Cursor, Continue.dev, Aider)

## 📋 Onderzoekssamenvatting

### Geanalyseerde Bronnen
1. **VS Code Copilot Documentation** (3 pagina's)
   - Chat interface design patterns
   - Context systeem (#file, #codebase)
   - Response formatting best practices
   
2. **GitHub Copilot Blog & Docs** (2 sources)
   - Product vision en UX patterns
   - Smart actions en slash commands
   - Inline chat vs sidebar chat

3. **Cursor AI** (2 sources)  
   - Agent mode capabilities
   - Tab autocomplete patterns
   - Codebase understanding

4. **Continue.dev** (2 sources)
   - Context inclusion patterns (@Files, @Terminal)
   - Apply/Insert/Copy actions voor code

5. **Aider CLI** (2 sources)
   - Terminal-based AI coding workflow
   - Git integration patterns
   - Voice-to-code capabilities

### Kerninzichten uit Research

#### 1. Response Formatting 🎨
**Huidige situatie (Omni):**
```
📊 Analyse voltooid!
- Ik heb de bestanden gelezen
- Ik heb de wijzigingen toegepast
- Hot-reload actief

✨ Mijn proces:
1. Eerst heb ik...
2. Daarna heb ik...
3. Tot slot heb ik...
```

**Gewenst (VS Code Copilot style):**
```
Ik heb de authentication flow geanalyseerd. De login functie in `AuthService.ts` 
mist error handling voor network timeouts. Hier is een verbeterde versie die 
reconnection attempts implementeert:

[code block met Apply/Copy buttons]

De nieuwe implementatie gebruikt exponential backoff en logt failures naar 
`ErrorLogger.ts`. Wil je dat ik ook unit tests toevoeg?
```

**Waarom dit beter is:**
- Natuurlijke lopende tekst, geen artificiële structuur
- File references zijn kort en klikbaar (`AuthService.ts`)
- Geen "wat ik gedaan heb" recap aan het eind
- Code blocks hebben interactieve buttons
- Eindigt met relevante follow-up vraag

#### 2. File References 📁
**Probleem:** Omni toont vaak volledige paden
```
/home/mathijs/Desktop/omni-electron/src/components/ChatPanel.vue
```

**Oplossing:** Korte klikbare links zoals VS Code
```
ChatPanel.vue
```
- Klikbaar → opent bestand in editor
- Hover → toont volledig pad als tooltip
- Automatisch gedetecteerd in responses

#### 3. Code Block Interactie 💻
**Current:** Plain text code blocks  
**Needed:** VS Code style actions

```typescript
// Code block header
ChatPanel.vue | TypeScript

[Apply] [Insert at Cursor] [Copy]

export function useChat() {
  // ... code ...
}
```

**Buttons:**
- **Apply**: Vervang huidige bestand/selectie
- **Insert**: Voeg toe op cursor positie  
- **Copy**: Naar clipboard

#### 4. Progress Indicators ⏳
**VS Code pattern:**
```
🤔 Analyzing authentication flow...
📖 Reading AuthService.ts...
🔍 Searching for error handlers...
✏️ Updating error handling...
✅ Applied 3 changes to AuthService.ts
```

**Kenmerken:**
- Emoji voor visuele context
- Korte actie-gerichte zinnen
- Real-time updates tijdens LLM tool calls
- Geen lange uitleg, alleen status

#### 5. Context System 🧠
**VS Code heeft #-mentions:**
- `#file:ChatPanel.vue` - Specifiek bestand
- `#codebase` - Hele workspace search
- `#terminalSelection` - Terminal output
- `@workspace` - Chat participant

**Omni moet implementeren:**
- Visueel tonen welke files in context zijn
- Expandable context indicator component
- Duidelijk maken wat AI "kan zien"

---

## 🎯 Implementatieplan

### Fase 1: Response Format (Week 1) ⭐ PRIORITEIT

#### 1.1 Backend Prompt Engineering
**File:** `backend/main.py`

**Huidige system prompt:**
```python
system_prompt = f"""Je bent Omni - een self-modifying AI...

GEDRAGSREGELS:
- ACTIE EERST: Gebruik direct tools
- Wees specifiek: noem exacte bestanden
- Korte antwoorden: geen lange uitleg
```

**Nieuwe prompt style guidance:**
```python
RESPONSE STYLE:
- Spreek als een natuurlijke assistent, geen lijstjes
- Begin direct met de oplossing of analyse
- Noem bestanden kort: `ChatPanel.vue` ipv volledig pad
- Gebruik emoji's spaarzaam: alleen voor tool actions
- Eindig met relevante follow-up vraag indien passend
- NOOIT een "mijn proces" sectie aan het eind

VOORBEELDEN:

GOED:
"Ik zie dat de login functie in `AuthService.ts` geen timeout handling heeft. 
Hier is een betere versie die reconnection attempts gebruikt..."

FOUT:  
"✅ Analyse voltooid!
- Bestand gelezen
- Probleem gevonden
✨ Mijn proces: Eerst heb ik..."
```

**Taak:**
- [ ] Update system prompt in `backend/main.py`
- [ ] Remove auto-generated process summary
- [ ] Test met 10+ verschillende requests
- [ ] Verify natuurlijke taal output

#### 1.2 Verwijder "Mijn proces" Sectie
**Probleem:** Backend genereert automatisch samenvatting

**Oplossing:**
```python
# backend/main.py - line ~640
# REMOVE this logic:
if tool_results:
    tools_used = ", ".join([t["tool"] for t in tool_results])
    response += f"\n\n✨ Mijn proces:\n"
    response += f"- Gebruikte tools: {tools_used}\n"
    # ...etc
```

**Taak:**
- [ ] Comment out or remove process summary code
- [ ] LLM response should stand on its own
- [ ] If user wants details, they can ask "how did you do that?"

---

### Fase 2: File References (Week 2)

#### 2.1 FileReference Component
**Nieuw bestand:** `src/components/FileReference.vue`

```vue
<template>
  <span 
    class="file-reference"
    @click="openFile"
    @mouseenter="showTooltip = true"
    @mouseleave="showTooltip = false"
    :title="fullPath"
  >
    <span class="file-icon">📄</span>
    <span class="file-name">{{ fileName }}</span>
  </span>
  
  <!-- Tooltip met volledig pad -->
  <Teleport to="body">
    <div v-if="showTooltip" class="file-tooltip" :style="tooltipStyle">
      {{ fullPath }}
      <kbd>Click to open</kbd>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface Props {
  path: string; // Kan kort zijn "ChatPanel.vue" of lang "src/components/ChatPanel.vue"
}

const props = defineProps<Props>();
const showTooltip = ref(false);

const fileName = computed(() => {
  return props.path.split('/').pop() || props.path;
});

const fullPath = computed(() => {
  // Als het al een volledig pad is, gebruik dat
  // Anders, construeer vanuit project root
  if (props.path.startsWith('/') || props.path.includes(':/')) {
    return props.path;
  }
  return `/home/mathijs/Desktop/omni-electron/${props.path}`;
});

const openFile = async () => {
  try {
    await window.electronAPI.openFile(fullPath.value);
  } catch (error) {
    console.error('Failed to open file:', error);
  }
};

// Tooltip positioning logic
const tooltipStyle = computed(() => {
  // Calculate position based on cursor
  return {
    // Will be implemented with mouse position tracking
  };
});
</script>

<style scoped>
.file-reference {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition-fast);
  font-family: var(--font-family-code);
  font-size: var(--font-size-sm);
}

.file-reference:hover {
  background: var(--color-primary-alpha-10);
  color: var(--color-primary);
}

.file-icon {
  font-size: 12px;
}

.file-name {
  font-weight: 500;
}

.file-tooltip {
  position: fixed;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-sm);
  box-shadow: var(--shadow-lg);
  z-index: 9999;
  pointer-events: none;
}

.file-tooltip kbd {
  margin-left: var(--space-2);
  padding: 2px 6px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
}
</style>
```

#### 2.2 Auto-detect File References in Responses
**File:** `src/components/ChatPanel.vue`

Voeg parser toe voor file mentions:

```typescript
// Detect file references in markdown content
function parseFileReferences(content: string): string {
  // Match patterns like:
  // - `ChatPanel.vue`
  // - `src/components/ChatPanel.vue`
  // - ChatPanel.vue (without backticks)
  
  const filePattern = /(?:`)?([a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_-]+)*\.[a-zA-Z0-9]+)(?:`)?/g;
  
  return content.replace(filePattern, (match, filepath) => {
    // Check if it looks like a valid file path
    if (filepath.includes('.')) {
      return `<FileReference path="${filepath}" />`;
    }
    return match;
  });
}
```

**Integratie in markdown renderer:**
```vue
<script setup lang="ts">
import { marked } from 'marked';
import FileReference from './FileReference.vue';

// Configure marked to handle custom elements
const renderer = new marked.Renderer();
renderer.code = (code, language) => {
  // ... existing code block rendering
};

// Custom file reference handling
const parseMessage = (content: string) => {
  // First parse markdown
  let html = marked.parse(content);
  
  // Then detect and wrap file references
  html = parseFileReferences(html);
  
  return html;
};
</script>
```

**Taak:**
- [ ] Create FileReference.vue component
- [ ] Implement auto-detection in ChatPanel.vue
- [ ] Add electronAPI.openFile method if not exists
- [ ] Test with various file path formats
- [ ] Add hover tooltip with full path

---

### Fase 3: Code Block Actions (Week 2-3)

#### 3.1 Enhanced Code Block Component
**Nieuw bestand:** `src/components/CodeBlock.vue`

```vue
<template>
  <div class="code-block-wrapper">
    <!-- Header met filename en actions -->
    <div class="code-header">
      <div class="code-info">
        <FileReference v-if="filename" :path="filename" />
        <span v-if="language" class="language-badge">{{ language }}</span>
      </div>
      
      <div class="code-actions">
        <button 
          @click="applyCode" 
          class="action-btn primary"
          :disabled="!canApply"
          title="Apply to current file or selection"
        >
          <span class="icon">✓</span>
          Apply
        </button>
        
        <button 
          @click="insertCode" 
          class="action-btn"
          title="Insert at cursor position"
        >
          <span class="icon">↓</span>
          Insert
        </button>
        
        <button 
          @click="copyCode" 
          class="action-btn"
          title="Copy to clipboard"
        >
          <span class="icon">📋</span>
          {{ copied ? 'Copied!' : 'Copy' }}
        </button>
      </div>
    </div>
    
    <!-- Code content met syntax highlighting -->
    <pre><code :class="`language-${language}`" v-html="highlightedCode"></code></pre>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import hljs from 'highlight.js';
import FileReference from './FileReference.vue';

interface Props {
  code: string;
  language?: string;
  filename?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  apply: [code: string];
  insert: [code: string];
}>();

const copied = ref(false);

const highlightedCode = computed(() => {
  if (props.language) {
    try {
      return hljs.highlight(props.code, { language: props.language }).value;
    } catch (e) {
      return hljs.highlightAuto(props.code).value;
    }
  }
  return hljs.highlightAuto(props.code).value;
});

const canApply = computed(() => {
  // Can apply if:
  // 1. Filename matches active editor
  // 2. Or there's a selection in active editor
  // Will be implemented with editor state
  return true;
});

const applyCode = async () => {
  emit('apply', props.code);
  
  // Apply logic:
  // If filename matches → replace file content
  // If selection exists → replace selection
  // Otherwise → show dialog to choose file
};

const insertCode = async () => {
  emit('insert', props.code);
  
  // Insert at current cursor position in Monaco editor
};

const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(props.code);
    copied.value = true;
    setTimeout(() => copied.value = false, 2000);
  } catch (error) {
    console.error('Failed to copy:', error);
  }
};
</script>

<style scoped>
.code-block-wrapper {
  margin: var(--space-3) 0;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-bg-secondary);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border-light);
}

.code-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.language-badge {
  padding: 2px 8px;
  background: var(--color-bg-quaternary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-family: var(--font-family-code);
  color: var(--color-text-muted);
}

.code-actions {
  display: flex;
  gap: var(--space-2);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: 4px 12px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: var(--transition-fast);
}

.action-btn:hover:not(:disabled) {
  background: var(--color-bg-secondary);
  border-color: var(--color-primary);
}

.action-btn.primary {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.action-btn.primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon {
  font-size: 14px;
}

pre {
  margin: 0;
  padding: var(--space-4);
  overflow-x: auto;
  background: var(--color-bg-code);
}

code {
  font-family: var(--font-family-code);
  font-size: var(--font-size-code);
  line-height: var(--line-height-code);
}
</style>
```

#### 3.2 Integrate with Markdown Renderer
**File:** `src/components/ChatPanel.vue`

```typescript
import CodeBlock from './CodeBlock.vue';

// Configure marked to use custom code renderer
const renderer = new marked.Renderer();

renderer.code = (code: string, language: string | undefined) => {
  // Extract filename from code fence info if present
  // E.g. ```typescript:ChatPanel.vue
  const [lang, filename] = (language || '').split(':');
  
  return `<CodeBlock 
    code="${escapeHtml(code)}" 
    language="${lang}" 
    ${filename ? `filename="${filename}"` : ''} 
  />`;
};

// Handle Apply/Insert events from CodeBlock
const handleApplyCode = async (code: string, filename?: string) => {
  if (filename) {
    // Apply to specific file
    const fullPath = resolveFilePath(filename);
    await window.electronAPI.writeFile(fullPath, code);
    
    // Show toast notification
    showToast(`Applied changes to ${filename}`, 'success');
  } else {
    // Apply to current editor selection
    const activeEditor = tabManager.getActiveTab();
    if (activeEditor && activeEditor.hasSelection()) {
      activeEditor.replaceSelection(code);
    } else {
      // Show file picker dialog
      const targetFile = await showFilePicker();
      if (targetFile) {
        await window.electronAPI.writeFile(targetFile, code);
      }
    }
  }
};

const handleInsertCode = async (code: string) => {
  const activeEditor = tabManager.getActiveTab();
  if (activeEditor) {
    activeEditor.insertAtCursor(code);
  } else {
    showToast('No active editor', 'error');
  }
};
```

**Taak:**
- [ ] Create CodeBlock.vue component
- [ ] Add highlight.js for syntax highlighting
- [ ] Implement Apply logic (replace file/selection)
- [ ] Implement Insert logic (insert at cursor)
- [ ] Implement Copy logic (clipboard)
- [ ] Add filename parsing from code fences
- [ ] Test with Monaco editor integration

---

### Fase 4: Context Indicators (Week 3)

#### 4.1 Context Indicator Component
**Nieuw bestand:** `src/components/ContextIndicator.vue`

```vue
<template>
  <div class="context-indicator" :class="{ expanded: isExpanded }">
    <div class="context-header" @click="toggleExpanded">
      <span class="context-icon">🧠</span>
      <span class="context-label">Context ({{ contextItems.length }} items)</span>
      <span class="expand-icon">{{ isExpanded ? '▼' : '▶' }}</span>
    </div>
    
    <Transition name="expand">
      <div v-if="isExpanded" class="context-list">
        <div 
          v-for="item in contextItems" 
          :key="item.id"
          class="context-item"
        >
          <span class="item-icon">{{ getIcon(item.type) }}</span>
          <FileReference v-if="item.type === 'file'" :path="item.path" />
          <span v-else class="item-name">{{ item.name }}</span>
          <button 
            @click.stop="removeItem(item.id)" 
            class="remove-btn"
            title="Remove from context"
          >
            ×
          </button>
        </div>
        
        <button @click="addContext" class="add-context-btn">
          + Add files or symbols
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import FileReference from './FileReference.vue';

interface ContextItem {
  id: string;
  type: 'file' | 'selection' | 'symbol';
  name: string;
  path?: string;
}

interface Props {
  items: ContextItem[];
}

const props = defineProps<Props>();
const emit = defineEmits<{
  add: [];
  remove: [id: string];
}>();

const isExpanded = ref(false);

const contextItems = computed(() => props.items);

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value;
};

const getIcon = (type: string) => {
  const icons = {
    file: '📄',
    selection: '✂️',
    symbol: '🔤'
  };
  return icons[type as keyof typeof icons] || '📎';
};

const removeItem = (id: string) => {
  emit('remove', id);
};

const addContext = () => {
  emit('add');
};
</script>

<style scoped>
.context-indicator {
  margin: var(--space-3) 0;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
}

.context-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  cursor: pointer;
  user-select: none;
  transition: var(--transition-fast);
}

.context-header:hover {
  background: var(--color-bg-tertiary);
}

.context-icon {
  font-size: 16px;
}

.context-label {
  flex: 1;
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.expand-icon {
  font-size: 10px;
  color: var(--color-text-muted);
}

.context-list {
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--color-border-light);
}

.context-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2);
  border-radius: var(--radius-sm);
  transition: var(--transition-fast);
}

.context-item:hover {
  background: var(--color-bg-tertiary);
}

.item-icon {
  font-size: 14px;
}

.item-name {
  flex: 1;
  font-size: var(--font-size-sm);
  font-family: var(--font-family-code);
}

.remove-btn {
  padding: 2px 8px;
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  transition: var(--transition-fast);
}

.remove-btn:hover {
  color: var(--color-danger);
}

.add-context-btn {
  width: 100%;
  margin-top: var(--space-2);
  padding: var(--space-2);
  background: var(--color-bg-tertiary);
  border: 1px dashed var(--color-border-medium);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: var(--font-size-sm);
  transition: var(--transition-fast);
}

.add-context-btn:hover {
  background: var(--color-bg-quaternary);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.expand-enter-active,
.expand-leave-active {
  transition: all var(--transition-normal);
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.expand-enter-to,
.expand-leave-from {
  max-height: 500px;
  opacity: 1;
}
</style>
```

#### 4.2 Add to Chat Input Area
**File:** `src/components/ChatPanel.vue`

```vue
<template>
  <div class="chat-panel">
    <!-- ... existing messages ... -->
    
    <!-- Chat input section -->
    <div class="chat-input-section">
      <!-- Context indicator above input -->
      <ContextIndicator 
        :items="activeContextItems"
        @add="showContextPicker"
        @remove="removeContextItem"
      />
      
      <div class="input-wrapper">
        <textarea
          v-model="inputMessage"
          @keydown.enter.exact.prevent="sendMessage"
          placeholder="Ask Omni anything... (Attach files with drag & drop)"
          @drop.prevent="handleFileDrop"
          @dragover.prevent
        />
        
        <div class="input-actions">
          <button @click="attachFiles" class="attach-btn" title="Attach files">
            📎
          </button>
          <button @click="sendMessage" :disabled="!inputMessage.trim()">
            Send
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import ContextIndicator from './ContextIndicator.vue';

const activeContextItems = ref<ContextItem[]>([]);

const showContextPicker = async () => {
  // Show file picker dialog
  const files = await window.electronAPI.showOpenDialog({
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'All Files', extensions: ['*'] }
    ]
  });
  
  if (files) {
    files.forEach(filepath => {
      activeContextItems.value.push({
        id: generateId(),
        type: 'file',
        name: filepath.split('/').pop() || filepath,
        path: filepath
      });
    });
  }
};

const removeContextItem = (id: string) => {
  activeContextItems.value = activeContextItems.value.filter(item => item.id !== id);
};

const handleFileDrop = (event: DragEvent) => {
  const files = Array.from(event.dataTransfer?.files || []);
  
  files.forEach(file => {
    activeContextItems.value.push({
      id: generateId(),
      type: 'file',
      name: file.name,
      path: file.path // Electron provides file.path
    });
  });
};

const sendMessage = async () => {
  // Include context items in request
  const contextPaths = activeContextItems.value
    .filter(item => item.type === 'file')
    .map(item => item.path);
  
  const response = await window.electronAPI.chat(inputMessage.value, {
    context_files: contextPaths
  });
  
  // Clear context after sending
  activeContextItems.value = [];
};
</script>
```

**Backend support:**
```python
# backend/main.py
def chat(self, params: dict) -> dict:
    message = params.get("message", "").strip()
    context_files = params.get("context_files", [])
    
    # Read context files and add to prompt
    context_content = ""
    for filepath in context_files:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
                context_content += f"\n\n<FILE path='{filepath}'>\n{content}\n</FILE>"
    
    # Add to system prompt or user message
    enhanced_message = f"{context_content}\n\nUser request: {message}"
    # ... rest of chat logic
```

**Taak:**
- [ ] Create ContextIndicator.vue component
- [ ] Add drag & drop support for files
- [ ] Implement file picker dialog
- [ ] Update backend to accept context_files parameter
- [ ] Test with multiple files in context
- [ ] Show active context in UI

---

### Fase 5: Streaming & Follow-ups (Week 4)

#### 5.1 Streaming Responses
**Backend:** Implement SSE (Server-Sent Events)

```python
# backend/main.py
from flask import Response, stream_with_context

def chat_stream(self, params: dict):
    """Stream chat responses token by token"""
    message = params.get("message", "").strip()
    
    def generate():
        # Start with progress updates
        yield f"data: {json.dumps({'type': 'progress', 'content': '🤔 Analyzing...'})}\n\n"
        
        # Tool execution
        for tool_result in self.execute_tools(message):
            yield f"data: {json.dumps({'type': 'tool', 'data': tool_result})}\n\n"
        
        # Stream LLM response
        full_prompt = self.build_prompt(message)
        
        for chunk in self.llm.generate_stream(full_prompt):
            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
        
        # Send completion
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')
```

**Frontend:** EventSource voor streaming

```typescript
// src/composables/useStreamingChat.ts
export function useStreamingChat() {
  const sendMessage = async (message: string) => {
    const assistantMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date()
    };
    messages.value.push(assistantMessage);
    
    const eventSource = new EventSource(`http://localhost:5000/chat-stream?message=${encodeURIComponent(message)}`);
    
    eventSource.addEventListener('message', (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'progress') {
        // Update progress indicator
        progress.value = data.content;
      } else if (data.type === 'tool') {
        // Show tool execution
        logToolExecution(data.data);
      } else if (data.type === 'content') {
        // Append to message content (streaming!)
        assistantMessage.content += data.content;
      } else if (data.type === 'done') {
        eventSource.close();
        loading.value = false;
      }
    });
    
    eventSource.onerror = () => {
      eventSource.close();
      loading.value = false;
    };
  };
  
  return { sendMessage };
}
```

#### 5.2 Follow-up Questions
**Backend:** Generate after response

```python
def generate_followups(self, message: str, response: str, tool_results: list) -> list[str]:
    """Generate 2-3 relevant follow-up questions"""
    
    prompt = f"""Based on this conversation:
User: {message}
Assistant: {response}

Generate 2-3 short follow-up questions the user might want to ask next.
Format: Just the questions, one per line.
"""
    
    followup_text = self.llm.generate(prompt, max_tokens=150, temperature=0.7)
    followups = [q.strip() for q in followup_text.split('\n') if q.strip()]
    
    return followups[:3]  # Max 3
```

**Frontend:** Show as chips

```vue
<template>
  <div class="message assistant">
    <div class="message-content">{{ message.content }}</div>
    
    <!-- Follow-up questions -->
    <div v-if="message.followups?.length" class="followups">
      <span class="followups-label">Continue with:</span>
      <button
        v-for="(question, i) in message.followups"
        :key="i"
        @click="askFollowup(question)"
        class="followup-chip"
      >
        {{ question }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.followups {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border-light);
}

.followups-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-right: var(--space-2);
}

.followup-chip {
  padding: 6px 12px;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: var(--transition-fast);
}

.followup-chip:hover {
  background: var(--color-primary-alpha-10);
  border-color: var(--color-primary);
  color: var(--color-primary);
}
</style>
```

**Taak:**
- [ ] Implement SSE streaming in backend
- [ ] Create useStreamingChat composable
- [ ] Add character-by-character rendering
- [ ] Implement follow-up generation
- [ ] Display follow-ups as clickable chips
- [ ] Test streaming with slow connections

---

### Fase 6: Slash Commands (Week 4)

#### 6.1 Command Parser
**File:** `src/composables/useSlashCommands.ts`

```typescript
export interface SlashCommand {
  name: string;
  description: string;
  icon: string;
  handler: (args: string) => Promise<void>;
}

export function useSlashCommands() {
  const commands: SlashCommand[] = [
    {
      name: 'fix',
      description: 'Fix issues in the selected code',
      icon: '🔧',
      handler: async (args) => {
        const selection = await getActiveSelection();
        const prompt = `Fix issues in this code:\n\n${selection}\n\n${args}`;
        return sendMessage(prompt);
      }
    },
    {
      name: 'explain',
      description: 'Explain the selected code',
      icon: '📖',
      handler: async (args) => {
        const selection = await getActiveSelection();
        const prompt = `Explain this code:\n\n${selection}\n\n${args}`;
        return sendMessage(prompt);
      }
    },
    {
      name: 'optimize',
      description: 'Optimize code performance',
      icon: '⚡',
      handler: async (args) => {
        const selection = await getActiveSelection();
        const prompt = `Optimize this code for performance:\n\n${selection}\n\n${args}`;
        return sendMessage(prompt);
      }
    },
    {
      name: 'test',
      description: 'Generate unit tests',
      icon: '🧪',
      handler: async (args) => {
        const selection = await getActiveSelection();
        const prompt = `Generate comprehensive unit tests for:\n\n${selection}\n\n${args}`;
        return sendMessage(prompt);
      }
    },
    {
      name: 'doc',
      description: 'Add documentation',
      icon: '📝',
      handler: async (args) => {
        const selection = await getActiveSelection();
        const prompt = `Add detailed documentation to:\n\n${selection}\n\n${args}`;
        return sendMessage(prompt);
      }
    }
  ];
  
  const parseCommand = (input: string): { command: SlashCommand | null; args: string } => {
    if (!input.startsWith('/')) {
      return { command: null, args: input };
    }
    
    const parts = input.slice(1).split(' ');
    const commandName = parts[0];
    const args = parts.slice(1).join(' ');
    
    const command = commands.find(c => c.name === commandName);
    
    return { command: command || null, args };
  };
  
  return {
    commands,
    parseCommand
  };
}
```

#### 6.2 Command Suggestions UI
**File:** `src/components/CommandSuggestions.vue`

```vue
<template>
  <Transition name="slide-up">
    <div v-if="show && suggestions.length" class="command-suggestions">
      <div
        v-for="(cmd, i) in suggestions"
        :key="cmd.name"
        class="suggestion-item"
        :class="{ active: i === activeIndex }"
        @click="selectCommand(cmd)"
        @mouseenter="activeIndex = i"
      >
        <span class="suggestion-icon">{{ cmd.icon }}</span>
        <div class="suggestion-info">
          <div class="suggestion-name">/{{ cmd.name }}</div>
          <div class="suggestion-description">{{ cmd.description }}</div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { SlashCommand } from '@/composables/useSlashCommands';

interface Props {
  show: boolean;
  query: string;
  commands: SlashCommand[];
}

const props = defineProps<Props>();
const emit = defineEmits<{
  select: [command: SlashCommand];
}>();

const activeIndex = ref(0);

const suggestions = computed(() => {
  const query = props.query.toLowerCase().replace('/', '');
  return props.commands.filter(cmd => 
    cmd.name.toLowerCase().includes(query)
  );
});

watch(() => props.query, () => {
  activeIndex.value = 0;
});

const selectCommand = (cmd: SlashCommand) => {
  emit('select', cmd);
};

// Keyboard navigation
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'ArrowDown') {
    event.preventDefault();
    activeIndex.value = (activeIndex.value + 1) % suggestions.value.length;
  } else if (event.key === 'ArrowUp') {
    event.preventDefault();
    activeIndex.value = activeIndex.value === 0 
      ? suggestions.value.length - 1 
      : activeIndex.value - 1;
  } else if (event.key === 'Enter' && suggestions.value[activeIndex.value]) {
    event.preventDefault();
    selectCommand(suggestions.value[activeIndex.value]);
  }
};

defineExpose({ handleKeyDown });
</script>

<style scoped>
.command-suggestions {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  margin-bottom: var(--space-2);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  z-index: 100;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  cursor: pointer;
  transition: var(--transition-fast);
}

.suggestion-item:hover,
.suggestion-item.active {
  background: var(--color-bg-tertiary);
}

.suggestion-icon {
  font-size: 20px;
}

.suggestion-info {
  flex: 1;
}

.suggestion-name {
  font-family: var(--font-family-code);
  font-weight: 600;
  color: var(--color-primary);
}

.suggestion-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all var(--transition-fast);
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
```

#### 6.3 Integrate in Chat Input
**File:** `src/components/ChatPanel.vue`

```vue
<template>
  <div class="input-wrapper">
    <CommandSuggestions
      :show="showCommandSuggestions"
      :query="inputMessage"
      :commands="slashCommands"
      @select="handleCommandSelect"
      ref="commandSuggestionsRef"
    />
    
    <textarea
      v-model="inputMessage"
      @input="handleInput"
      @keydown="handleKeyDown"
      placeholder="Type / for commands, or just ask anything..."
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useSlashCommands } from '@/composables/useSlashCommands';
import CommandSuggestions from './CommandSuggestions.vue';

const { commands: slashCommands, parseCommand } = useSlashCommands();
const inputMessage = ref('');
const commandSuggestionsRef = ref<InstanceType<typeof CommandSuggestions>>();

const showCommandSuggestions = computed(() => {
  return inputMessage.value.startsWith('/') && 
         inputMessage.value.length > 1 &&
         !inputMessage.value.includes(' ');
});

const handleInput = () => {
  // Update suggestions visibility
};

const handleKeyDown = (event: KeyboardEvent) => {
  if (showCommandSuggestions.value) {
    // Delegate to CommandSuggestions component
    commandSuggestionsRef.value?.handleKeyDown(event);
  } else if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
};

const handleCommandSelect = (command: SlashCommand) => {
  inputMessage.value = `/${command.name} `;
  // Focus back on textarea
};

const sendMessage = async () => {
  const { command, args } = parseCommand(inputMessage.value);
  
  if (command) {
    // Execute command handler
    await command.handler(args);
  } else {
    // Send regular message
    await window.electronAPI.chat(inputMessage.value);
  }
  
  inputMessage.value = '';
};
</script>
```

**Taak:**
- [ ] Create useSlashCommands composable
- [ ] Build CommandSuggestions component
- [ ] Implement keyboard navigation (↑↓ Enter)
- [ ] Add command handlers for /fix, /explain, etc.
- [ ] Test with different commands
- [ ] Add visual feedback for command execution

---

## 📊 Prioritering & Planning

### Week 1: Foundation 🏗️
**Focus:** Response formatting & file references  
**Effort:** 15-20 uur

**Deliverables:**
- [x] Updated system prompt (natuurlijke taal)
- [x] Verwijderd "Mijn proces" sectie
- [x] FileReference.vue component
- [x] Auto-detect file mentions in responses
- [x] Hover tooltips met volledige paden

**Succes criteria:**
- Responses lezen als natuurlijke conversatie
- File namen zijn klikbaar en openen in editor
- Geen artificiële structuur meer in antwoorden

---

### Week 2: Interactivity 🎛️
**Focus:** Code blocks & context  
**Effort:** 20-25 uur

**Deliverables:**
- [x] CodeBlock.vue met Apply/Insert/Copy buttons
- [x] Syntax highlighting (highlight.js)
- [x] ContextIndicator.vue component
- [x] Drag & drop file attachment
- [x] Backend context_files parameter

**Succes criteria:**
- Code blocks hebben werkende action buttons
- Apply/Insert werken correct in Monaco editor
- Context indicator toont actieve bestanden
- Drag & drop voegt bestanden toe aan context

---

### Week 3: Polish & Advanced 💎
**Focus:** Streaming & follow-ups  
**Effort:** 20-25 uur

**Deliverables:**
- [x] SSE streaming implementation
- [x] Character-by-character rendering
- [x] Follow-up question generation
- [x] Follow-up chips UI
- [x] Progress indicators met emoji's

**Succes criteria:**
- Responses streamen real-time
- Follow-ups zijn relevant en klikbaar
- Progress updates zijn duidelijk en informatief
- Alles voelt smooth en responsive

---

### Week 4: Power Features ⚡
**Focus:** Slash commands  
**Effort:** 15-20 uur

**Deliverables:**
- [x] useSlashCommands composable
- [x] CommandSuggestions component
- [x] /fix, /explain, /optimize, /test, /doc commands
- [x] Keyboard navigation (↑↓ Enter)

**Succes criteria:**
- Commands autocomplete bij typen /
- Keyboard navigation werkt soepel
- Commands genereren relevante prompts
- Suggesti UI ziet er professioneel uit

---

## 🎨 Design Tokens Referentie

### Typography
```css
--font-family-base: 'Inter', -apple-system, system-ui, sans-serif;
--font-family-code: 'Fira Code', 'Consolas', monospace;

--font-size-xs: 11px;
--font-size-sm: 13px;
--font-size-base: 14px;
--font-size-lg: 16px;
--font-size-xl: 18px;

--line-height-tight: 1.4;
--line-height-normal: 1.6;
--line-height-relaxed: 1.8;
--line-height-code: 1.5;
```

### Colors (VS Code Dark Theme)
```css
--color-bg-primary: #1e1e1e;
--color-bg-secondary: #252526;
--color-bg-tertiary: #2d2d30;
--color-bg-quaternary: #3e3e42;
--color-bg-code: #1e1e1e;

--color-text-primary: #cccccc;
--color-text-secondary: #9d9d9d;
--color-text-muted: #6a6a6a;

--color-border-light: #3e3e42;
--color-border-medium: #525252;

--color-primary: #007acc;
--color-primary-hover: #1c97ea;
--color-primary-alpha-10: rgba(0, 122, 204, 0.1);

--color-success: #4ec9b0;
--color-warning: #ce9178;
--color-danger: #f48771;
```

### Spacing
```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
```

### Border Radius
```css
--radius-sm: 3px;
--radius-md: 6px;
--radius-lg: 8px;
--radius-full: 9999px;
```

### Transitions
```css
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);
```

### Shadows
```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
--shadow-md: 0 2px 4px rgba(0, 0, 0, 0.3);
--shadow-lg: 0 4px 8px rgba(0, 0, 0, 0.3);
--shadow-xl: 0 8px 16px rgba(0, 0, 0, 0.4);
```

---

## ✅ Testing Checklist

### Response Formatting
- [ ] Responses gebruik natuurlijke lopende tekst
- [ ] Geen artificiële lijstjes of structuur
- [ ] Emoji's alleen voor tool actions
- [ ] "Mijn proces" sectie is verwijderd
- [ ] Eindigt met relevante follow-up vraag

### File References
- [ ] Korte bestandsnamen worden gedetecteerd
- [ ] Hover tooltip toont volledig pad
- [ ] Click opent bestand in correcte tab
- [ ] Styling past bij design system
- [ ] Werkt in markdown en plain text

### Code Blocks
- [ ] Syntax highlighting werkt correct
- [ ] Apply button vervangt bestand/selectie
- [ ] Insert button voegt toe op cursor positie
- [ ] Copy button kopieert naar clipboard
- [ ] Filename wordt getoond in header
- [ ] Language badge is zichtbaar

### Context Indicator
- [ ] Toont aantal actieve context items
- [ ] Expandable/collapsible werkt
- [ ] Files kunnen verwijderd worden
- [ ] Drag & drop voegt bestanden toe
- [ ] Context wordt meegestuurd in request

### Streaming
- [ ] Characters verschijnen progressief
- [ ] Progress updates komen real-time
- [ ] Tool executions worden getoond
- [ ] Geen lag of stuttering
- [ ] Error handling werkt correct

### Follow-ups
- [ ] 2-3 relevante vragen worden gegenereerd
- [ ] Chips zijn klikbaar
- [ ] Click vult input field
- [ ] Styling is consistent
- [ ] Werkt op mobiel formaat

### Slash Commands
- [ ] / trigger toont suggestions
- [ ] Keyboard navigation (↑↓) werkt
- [ ] Enter selecteert command
- [ ] Commands genereren correcte prompts
- [ ] Tooltip toont beschrijving

---

## 🚀 Quick Start Implementatie

```bash
# 1. Installeer dependencies
npm install highlight.js marked

# 2. Create nieuwe components
touch src/components/FileReference.vue
touch src/components/CodeBlock.vue
touch src/components/ContextIndicator.vue
touch src/components/CommandSuggestions.vue

# 3. Create composables
touch src/composables/useSlashCommands.ts
touch src/composables/useStreamingChat.ts

# 4. Update backend
# Edit backend/main.py → update system_prompt
# Remove "Mijn proces" generation code

# 5. Test met voorbeelden
# - "Fix the bug in AuthService.ts"
# - "Explain how the routing works"
# - "/optimize this code"
# - Drag & drop een bestand
```

---

## 📚 Referenties & Inspiratie

### Exact Voorbeelden uit Research

#### VS Code Copilot Chat Response
```
To add authentication to your Express app, you'll need middleware that 
validates JWT tokens. Here's a secure implementation:

[CodeBlock: middleware/auth.js with Apply/Insert/Copy buttons]

This middleware checks the Authorization header, verifies the JWT, and 
attaches the user to the request. Make sure to add it to protected routes 
in `routes/api.js`.

Would you like me to show how to integrate this with your existing routes?
```

**Waarom goed:**
- Natuurlijke conversatie toon
- Kort file reference zonder volledig pad
- Code block met actions
- Eindigt met relevante follow-up

#### GitHub Copilot Inline Chat
```
🔍 Analyzing authentication flow...
📖 Reading AuthService.ts...
✏️ Applying security improvements...
✅ Updated 3 files

I've added rate limiting and input validation to prevent brute force attacks. 
The changes are in `AuthService.ts`, `middleware/rateLimiter.ts`, and updated 
tests in `__tests__/auth.test.ts`.
```

**Waarom goed:**
- Progress indicators met emoji's
- Beknopte actie-beschrijvingen
- Meerdere file references
- Geen lange uitleg tenzij gevraagd

#### Cursor Agent Mode
```
Let me implement the user profile feature. I'll need to:

[Automatically reads UserController.ts, UserModel.ts, routes/user.js]

I've created a complete profile system with avatar upload, bio editing, 
and privacy settings. The implementation includes input validation and 
database migrations. Check the new files:

• UserProfile.ts - Profile data model
• ProfileController.ts - CRUD operations  
• profile.migration.sql - Database schema

[Apply All Changes button]

Want me to add profile image optimization too?
```

**Waarom goed:**
- Autonome tool gebruik
- Overzicht van wat gemaakt is
- Bullet points alleen voor opsommingen
- Grote "Apply All" actie
- Natural follow-up vraag

---

## 🎯 Success Metrics

**Pre-implementation (huidige staat):**
- Response stijl: Gestructureerd met lijsten (50% natuurlijk)
- File references: Volledige paden (0% klikbaar)
- Code blocks: Plain text (0% interactief)
- Context awareness: Geen visuele indicators (20% duidelijk)
- Tool feedback: OK maar verbose (60% natuurlijk)

**Post-implementation (doel):**
- Response stijl: Vloeiende tekst (95% natuurlijk)
- File references: Korte klikbare links (100% klikbaar)
- Code blocks: Met Apply/Insert/Copy (100% interactief)
- Context awareness: Duidelijke indicators (90% duidelijk)
- Tool feedback: Beknopte emoji updates (90% natuurlijk)

**User satisfaction KPI's:**
- Tijd om code toe te passen: -70% (met Apply button)
- Aantal clicks om bestand te openen: -80% (klikbare refs)
- Begrip van AI proces: +60% (context indicators)
- Gebruiksgemak slash commands: +90% (autocomplete)
- Perceived response quality: +50% (natuurlijke taal)

---

## 🔄 Iteratie & Feedback Loop

**Week 1 Demo:**
- Toon nieuwe response format
- Test file references met echte bestanden
- Verzamel feedback op natuurlijke taal

**Week 2 Demo:**
- Demonstreer Apply/Insert/Copy
- Test context indicators
- Evalueer interactivity

**Week 3 Demo:**
- Live streaming demo
- Follow-ups gebruiken
- Performance check

**Week 4 Demo:**
- Slash commands showcase
- Volledige workflow demo
- User acceptance testing

**Feedback verzamelen:**
1. Screen recordings van gebruikssessies
2. Snelheid metingen (tijd tot actie)
3. User survey (5-punts Likert scale)
4. A/B test oude vs nieuwe stijl

---

## 🎓 Lessen uit Research

### Wat werkt NIET
❌ **Lange gestructureerde responses** - VS Code gebruikt korte paragrafen  
❌ **Volledige file paden** - Niemand toont `/home/user/...`  
❌ **Process recaps** - "Eerst deed ik X, toen Y" voegt geen waarde toe  
❌ **Te veel emoji's** - Alleen voor tool actions, niet decoratief  
❌ **Starre formatting** - Natural language > bullet points  

### Wat werkt WEL
✅ **Conversational tone** - Als je met een collega praat  
✅ **Actie-gerichte progress** - "Reading X..." not "Ik ben bezig met..."  
✅ **Interactieve elementen** - Buttons > instructies typen  
✅ **Context transparency** - Toon wat AI ziet  
✅ **Smart defaults** - Slash commands > lange prompts  

### Verrassende Inzichten
🤔 **Aider CLI is heel minimalistisch** - Terminal-only, geen fancy UI  
💡 **Cursor focust op autonomie** - Agent mode doet meeste werk zelf  
⚡ **Continue.dev heeft beste context system** - @mentions zijn intuïtief  
🎨 **VS Code's design is super consistent** - Alles voelt "native"  
🔮 **Streaming is verwachting** - Users willen real-time feedback  

---

## 📝 Conclusie

Dit plan combineert de beste UX patterns van marktleiders (VS Code Copilot, 
Cursor, Continue.dev, Aider) met Omni's bestaande architectuur. Implementatie 
in 4 weken levert een dramatische verbetering in gebruikservaring:

**Kern voordelen:**
1. 🗣️ **Natuurlijker** - Responses voelen als echte conversatie
2. ⚡ **Sneller** - Direct actions via Apply/Copy/Insert buttons
3. 🎯 **Duidelijker** - File references en context zichtbaar
4. 💪 **Krachtiger** - Slash commands voor common tasks
5. ✨ **Professioneler** - Consistent design system

De implementatie is incremental zodat elke week direct waarde levert. 
Begin met Week 1 (response format) omdat dat de meeste impact heeft op 
dagelijks gebruik.

**Next steps:**
1. Review dit plan met stakeholders
2. Maak todo's aan in project management
3. Start Week 1 implementatie
4. Ship early & often! 🚀
