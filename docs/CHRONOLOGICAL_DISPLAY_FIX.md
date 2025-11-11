# Chronological Display Fix - Implementation Plan

## Probleem

De chat UI toont tools **gegroepeerd** onderaan het assistant message, niet **interleaved** met de uitleg:

**Huidige weergave:**
```
Omni: "Ik ga eerst package.json lezen en dan de dependencies analyseren"
Tool Uitvoeringen (5)
  ✓ list_files - VOLTOOID
  ✓ list_files - VOLTOOID  
  ✓ list_files - VOLTOOID
```

**Gewenste weergave (zoals VS Code Copilot):**
```
Omni: "Laat me eerst kijken naar de huidige styling"
  
  🔧 list_files in src/components
     Status: Voltooid (0.12s)
     Result: ChatPanel.vue, EditorPanel.vue, ...

Omni: "Ik zie dat de chat interface margin-left heeft"

  🔧 grep_search voor "margin-left"  
     Status: Voltooid (0.08s)
     Result: 3 matches gevonden

Omni: "Laat me die aanpassen zodat..."
```

## Root Cause

De `StreamingResponse.vue` component **buffert** alle tools en toont ze als één `<ToolExecutionTree>` sectie NA de narrative text:

```vue
<!-- StreamingResponse.vue line 12-24 -->
<div v-if="narrative" class="narrative-content"></div>

<!-- Tools worden HIER gegroepeerd getoond -->
<ToolExecutionTree 
  v-if="tools.length > 0"
  :tools="tools"
  class="tools-section"
/>
```

## Onderzoek Bevindingen

### Continue.dev Pattern
- **Separate message per tool**: Elk tool call krijgt eigen message bubble
- **Interleaved display**: Tools verschijnen tussen narrative chunks
- **Source**: `gui/src/pages/gui/Chat.tsx` lines 405-436

### AutoGPT Pattern  
- **ToolResponseMessage component**: Dedicated component voor tool results
- **Chronological rendering**: Each message (text or tool) rendered in order received
- **Source**: `frontend/src/app/(platform)/chat/components/ToolResponseMessage/`

### VS Code Copilot Pattern
- **Agent mode**: "Copilot streams the edits in the editor"
- **Real-time display**: Tools execute and display immediately, not batched
- **Source**: VS Code docs on Copilot agent mode

## Solution Architecture

### 1. Backend Change (Already Done ✅)
Backend executes tools **during streaming** in `content_block_stop` event:

```python
# backend/main.py line ~680-710
elif event_type == 'content_block_stop':
    if current_tool_use:
        # Execute IMMEDIATELY during streaming
        handler.emit_tool_start(tool_name, tool_args)
        result = self._execute_tool(tool_name, tool_args)  
        handler.emit_tool_result(tool_name, result, status='success', duration=...)
```

### 2. Frontend Change (To Implement)

**Problem**: `StreamingResponse` buffers tools in array, displays after text
**Solution**: Create separate message entries for each tool

#### Option A: Message-per-Tool Pattern (Recommended)
Match Continue.dev/AutoGPT pattern - create separate message for each tool:

```typescript
// In ChatPanel.vue
messages = [
  { role: 'assistant', content: 'Laat me dat opzoeken...', timestamp: ... },
  { role: 'tool', toolName: 'list_files', status: 'calling', timestamp: ... },
  { role: 'tool', toolName: 'list_files', status: 'done', result: {...}, timestamp: ... },
  { role: 'assistant', content: 'Ik zie dat...', timestamp: ... },
  { role: 'tool', toolName: 'grep_search', status: 'calling', timestamp: ... },
  { role: 'tool', toolName: 'grep_search', status: 'done', result: {...}, timestamp: ... },
]
```

#### Option B: Interleaved Chunks Pattern  
Keep single assistant message but interleave chunks:

```typescript
{
  role: 'assistant',
  chunks: [
    { type: 'text', content: 'Laat me...' },
    { type: 'tool', toolName: 'list_files', ... },
    { type: 'text', content: 'Ik zie...' },
    { type: 'tool', toolName: 'grep_search', ... }
  ]
}
```

**Recommendation**: Option A is better because:
- Matches industry standard (Continue.dev, AutoGPT, Cursor)
- Easier to implement (no complex chunk management)
- Better for future features (tool retry, individual timestamps)

### 3. Implementation Steps

#### Step 1: Modify Event Handling in ChatPanel
```vue
// ChatPanel.vue - setupStreamingListener
const handleToolStart = (event: ToolStartEvent) => {
  // Create NEW message for tool
  messages.value.push({
    role: 'tool',
    toolName: event.data.name,
    toolArgs: event.data.args,
    status: 'calling',
    timestamp: new Date(),
    requestId: event.requestId
  });
};

const handleToolResult = (event: ToolResultEvent) => {
  // Find the tool message and update it
  const toolMsg = messages.value.findLast(
    msg => msg.role === 'tool' && 
           msg.toolName === event.data.name &&
           msg.status === 'calling'
  );
  if (toolMsg) {
    toolMsg.status = event.data.status;
    toolMsg.result = event.data.result;
    toolMsg.duration = event.data.duration;
  }
};

const handleNarrativeChunk = (event: NarrativeChunkEvent) => {
  // Find CURRENT streaming assistant message or create new one
  let assistantMsg = messages.value.findLast(
    msg => msg.role === 'assistant' && msg.isStreaming
  );
  
  if (!assistantMsg) {
    assistantMsg = {
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      requestId: event.requestId
    };
    messages.value.push(assistantMsg);
  }
  
  assistantMsg.content += event.data.text;
};
```

#### Step 2: Create ToolMessage Component
New component to display individual tool executions:

```vue
<!-- ToolMessage.vue -->
<template>
  <div class="tool-message" :class="statusClass">
    <div class="tool-header">
      <span class="tool-icon">🔧</span>
      <strong>{{ displayName }}</strong>
      <span class="tool-status">{{ statusText }}</span>
      <span v-if="duration" class="tool-duration">({{ duration.toFixed(2) }}s)</span>
    </div>
    
    <div v-if="showArgs" class="tool-args">
      <pre>{{ JSON.stringify(toolArgs, null, 2) }}</pre>
    </div>
    
    <div v-if="status === 'done' && result" class="tool-result">
      <pre>{{ formatResult(result) }}</pre>
    </div>
  </div>
</template>
```

#### Step 3: Update ChatPanel Template
```vue
<div v-for="(msg, index) in messages" :key="index" class="message">
  <!-- User messages -->
  <template v-if="msg.role === 'user'">
    ...
  </template>
  
  <!-- Assistant text messages -->
  <template v-else-if="msg.role === 'assistant'">
    <div class="message-bubble">
      <div v-html="renderMarkdown(msg.content)"></div>
    </div>
  </template>
  
  <!-- Tool execution messages (NEW) -->
  <template v-else-if="msg.role === 'tool'">
    <ToolMessage 
      :tool-name="msg.toolName"
      :tool-args="msg.toolArgs"
      :status="msg.status"
      :result="msg.result"
      :duration="msg.duration"
    />
  </template>
</div>
```

## Testing Scenarios

1. **Multi-tool sequence**
   ```
   User: "Lees package.json en vertel me de dependencies"
   
   Expected:
   - Omni: "Laat me eerst kijken..."
   - 🔧 list_files (voltooid)
   - Omni: "Ik zie package.json, ik ga het lezen"  
   - 🔧 read_file (voltooid)
   - Omni: "De dependencies zijn: react, vue, ..."
   ```

2. **Tool during narrative**
   ```
   User: "Zoek naar TODO comments"
   
   Expected:
   - Omni: "Ik ga zoeken..."
   - 🔧 grep_search (running...)
   - 🔧 grep_search (voltooid - 15 matches)
   - Omni: "Ik heb 15 TODO's gevonden in..."
   ```

3. **Error handling**
   ```
   Expected:
   - Omni: "Laat me dat file lezen"
   - 🔧 read_file (error - file not found)
   - Omni: "Het bestand bestaat niet. Wil je..."
   ```

## Benefits

1. **Industry Standard**: Matches VS Code, Continue.dev, Cursor, AutoGPT
2. **Better UX**: Users see tools execute in context with explanation
3. **Debugging**: Easier to see exactly when tools ran and what they returned
4. **Performance**: Tools run earlier (don't wait for all text)
5. **Flexibility**: Can add tool retry, individual timestamps, etc.

## Migration Notes

- Old saved messages in localStorage won't have interleaved format
- Need to handle backward compatibility
- StreamingResponse component can be simplified (no tool buffering needed)

## Status

- [x] Backend implementation (chronological tool execution)
- [ ] Frontend message structure change
- [ ] ToolMessage component
- [ ] ChatPanel template update
- [ ] Testing with multi-tool scenarios
- [ ] Documentation update

## References

- Continue.dev: `gui/src/pages/gui/Chat.tsx` - Separate TimelineItems per message
- AutoGPT: `frontend/src/app/(platform)/chat/components/` - Dedicated tool components
- VS Code: Copilot agent mode documentation
- Anthropic: Streaming with tools - natural chronological support
