# Chat UI Design Research & Optimalisaties voor Omni

## 📊 Onderzochte Bronnen

1. **GitHub Copilot Chat (VS Code)** - Official Documentation
2. **GitHub Copilot** - Marketing & Features Site  
3. **Cursor IDE** - Product Website & Documentation
4. **GitHub Copilot Marketplace** - VS Code Extension
5. **Laws of UX** - UX Principles & Best Practices
6. **GitHub Copilot Chat Usage Guide** - Complete IDE Documentation
7. **ChatGPT** - OpenAI Interface (limited access)
8. **Claude** - Anthropic Interface (limited access)
9. **VS Code Copilot Series** - YouTube Educational Content
10. **Microsoft Learn** - Visual Studio Copilot Documentation

---

## 🎨 Belangrijkste Design Patterns Gevonden

### 1. **Tekst Styling & Typografie**

#### **VS Code / GitHub Copilot**
- **Font**: System mono font voor code, sans-serif voor tekst
- **Grootte**: 
  - User messages: 13-14px
  - AI responses: 13-14px
  - Code blocks: 12px monospace
  - Hints/labels: 11px
- **Gewicht**: 
  - Normal (400) voor body text
  - Medium (500) voor labels
  - Semi-bold (600) voor headings
- **Contrast**: Hoge leesbaarheid met theme-aware kleuren
- **Line height**: 1.5-1.6 voor tekst, 1.4 voor code

#### **Cursor IDE**
- **Moderne sans-serif** (Inter/SF Pro)
- **Grotere tekst**: 14-15px voor beter lezen
- **Code highlighting**: Syntax highlighting in antwoorden
- **Markdown rendering**: Volledige markdown support met preview

### 2. **Message Flow & Layout**

#### **Conversational Flow Patterns**
```
┌─────────────────────────────────────┐
│  🧑 User Message (Right-aligned)    │
│  - Compact bubble                   │
│  - Subtle background                │
│  - Timestamp bij hover              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  🤖 AI Response (Left-aligned)      │
│  - Full width voor leesbaarheid     │
│  - Sectioned content:               │
│    • Text explanation               │
│    • Code blocks met syntax         │
│    • Action buttons                 │
│  - References/sources expandable    │
└─────────────────────────────────────┘
```

#### **Key Features**:
1. **Progressive Disclosure**
   - Streaming responses (typewriter effect)
   - Expandable sections voor lange antwoorden
   - "Show more" voor code snippets
   - Collapsible references

2. **Visual Hierarchy**
   - Clear separation tussen user/AI
   - Distinct styling voor code vs prose
   - Prominent action buttons
   - Subtle metadata (time, model used)

3. **Spacing**
   - 16-24px tussen messages
   - 8-12px padding binnen messages
   - 4-8px tussen text en code blocks

### 3. **Status Indicators & Feedback**

#### **Loading States**
- **Thinking**: Animated dots of spinner
- **Processing**: Progress indicator met context
- **Streaming**: Cursor aan einde van text
- **Error**: Duidelijke foutmelding met retry optie

#### **VS Code Copilot Patterns**:
```
🔄 "GitHub Copilot is thinking..."
⚡ "Generating code..."
📝 "Applying changes..."
✅ "Done"
❌ "Error: [clear message]"
```

#### **Cursor Patterns**:
```
🧠 "Analyzing your code..."
🔨 "Making edits across 3 files..."
🏃 "Running tests..."
✨ "Task complete!"
```

### 4. **Interactive Elements**

#### **Action Buttons (GitHub Copilot)**
- **Copy Code** - Clipboard icon
- **Insert at Cursor** - Plus icon
- **Apply Changes** - Check icon  
- **Regenerate** - Refresh icon
- **Thumbs Up/Down** - Feedback

#### **Context Management (Cursor)**
- **Add to context**: File/folder selection
- **Remove from context**: X icon
- **Context indicator**: Aantal bestanden/lijnen
- **Smart suggestions**: Auto-detect relevant files

#### **Edit Mode Controls**
- **Accept**: Primary green button
- **Reject**: Secondary red button
- **Modify**: Edit icon voor aanpassingen
- **Split/Merge**: Voor complexe changes

### 5. **Mode Indicators**

Both Copilot and Cursor have clear mode switching:

```
┌────────────────────────────────────┐
│ [ Ask ] [ Edit ] [ Agent ]         │  ← Mode selector
│                                    │
│ 📁 Working Set: 3 files            │  ← Context
│                                    │
│ 🎯 Current Task: Refactor auth     │  ← State
└────────────────────────────────────┘
```

**Modes explained**:
- **Ask**: Q&A, geen code changes
- **Edit**: Gerichte edits met approve/reject
- **Agent**: Autonome multi-step tasks

---

## 🚀 Optimalisaties voor Omni

### **PRIORITEIT 1: Immediate Improvements**

#### 1. **Typography Overhaul**
```css
/* Huidige Omni (vermoedelijk) */
font-size: 14px;
line-height: 1.4;

/* → Nieuwe Omni */
--font-size-base: 14px;
--font-size-large: 15px;
--font-size-small: 13px;
--font-size-code: 12px;

--line-height-text: 1.6;
--line-height-code: 1.4;
--line-height-tight: 1.3;

/* Font families */
--font-family-text: -apple-system, BlinkMacSystemFont, 
                     'Segoe UI', 'Roboto', sans-serif;
--font-family-code: 'Fira Code', 'JetBrains Mono', 
                     'Consolas', monospace;
```

#### 2. **Message Layout Redesign**
```
Huidige layout (1-kolom):
┌──────────────────────────────┐
│ User: Hello                  │
│ AI: Response here            │
└──────────────────────────────┘

→ Nieuwe layout (bubble chat):
┌──────────────────────────────┐
│              ┌──────────────┐│
│              │ User: Hello  ││  ← Right-aligned
│              └──────────────┘│
│                              │
│ ┌────────────────────────┐  │
│ │ 🤖 AI Response         │  │  ← Left-aligned, with icon
│ │ Here is my answer...   │  │
│ │                        │  │
│ │ ```python              │  │  ← Code block with actions
│ │ def example():         │  │
│ │   pass                 │  │
│ │ ```                    │  │
│ │ [Copy] [Insert] [✓]   │  │  ← Action buttons
│ └────────────────────────┘  │
└──────────────────────────────┘
```

#### 3. **Progress Indicators**
```vue
<!-- Status component -->
<div class="ai-status" v-if="isProcessing">
  <div class="status-icon">
    <LoadingSpinner />
  </div>
  <div class="status-text">
    {{ currentStatus }}
  </div>
  <div class="status-progress" v-if="progress">
    <ProgressBar :value="progress" />
  </div>
</div>

<!-- States -->
thinking → "Analyzing your code..."
generating → "Generating response..."
streaming → [typewriter effect]
complete → "✓ Done"
error → "⚠ Something went wrong: [message]"
```

#### 4. **Code Block Improvements**
```vue
<template>
  <div class="code-block">
    <div class="code-header">
      <span class="language-badge">{{ language }}</span>
      <div class="code-actions">
        <button @click="copyCode" title="Copy">
          <CopyIcon />
        </button>
        <button @click="insertCode" title="Insert">
          <InsertIcon />
        </button>
        <button @click="applyDiff" v-if="isDiff" title="Apply">
          <CheckIcon />
        </button>
      </div>
    </div>
    <pre><code :class="`language-${language}`">{{ code }}</code></pre>
  </div>
</template>

<style scoped>
.code-block {
  border-radius: 8px;
  background: var(--color-code-bg);
  border: 1px solid var(--color-code-border);
  margin: 12px 0;
  overflow: hidden;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-code-header);
  border-bottom: 1px solid var(--color-code-border);
}

.language-badge {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.code-actions {
  display: flex;
  gap: 4px;
}

.code-actions button {
  padding: 4px 8px;
  border-radius: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s, background 0.2s;
}

.code-actions button:hover {
  opacity: 1;
  background: var(--color-hover);
}

pre {
  margin: 0;
  padding: 12px;
  overflow-x: auto;
  font-family: var(--font-family-code);
  font-size: var(--font-size-code);
  line-height: var(--line-height-code);
}
</style>
```

### **PRIORITEIT 2: Enhanced UX Features**

#### 5. **Streaming Response Animation**
```typescript
// Typewriter effect voor streaming
function streamResponse(text: string, onChunk: (chunk: string) => void) {
  let index = 0;
  const chunkSize = 3; // Characters per frame
  const delay = 16; // ~60fps
  
  const interval = setInterval(() => {
    if (index >= text.length) {
      clearInterval(interval);
      return;
    }
    
    const chunk = text.slice(index, index + chunkSize);
    onChunk(chunk);
    index += chunkSize;
  }, delay);
}
```

#### 6. **Smart Context Display**
```vue
<template>
  <div class="context-indicator">
    <div class="context-header">
      <FileIcon />
      <span>Context ({{ fileCount }} files)</span>
      <button @click="toggleExpanded">
        <ChevronIcon :expanded="isExpanded" />
      </button>
    </div>
    
    <transition name="slide">
      <div v-if="isExpanded" class="context-files">
        <div v-for="file in contextFiles" :key="file.path" 
             class="context-file">
          <FileIcon :type="file.type" />
          <span class="file-path">{{ file.relativePath }}</span>
          <span class="file-lines">{{ file.lines }} lines</span>
          <button @click="removeFile(file)" class="remove-btn">
            <XIcon />
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>
```

#### 7. **Mode Switching UI**
```vue
<template>
  <div class="mode-selector">
    <button 
      v-for="mode in modes" 
      :key="mode.id"
      @click="selectMode(mode)"
      :class="['mode-button', { active: currentMode === mode.id }]">
      <component :is="mode.icon" />
      <span>{{ mode.label }}</span>
    </button>
  </div>
</template>

<script setup>
const modes = [
  { id: 'ask', label: 'Ask', icon: ChatIcon },
  { id: 'edit', label: 'Edit', icon: EditIcon },
  { id: 'agent', label: 'Agent', icon: SparklesIcon }
];
</script>

<style scoped>
.mode-selector {
  display: flex;
  gap: 8px;
  padding: 8px;
  background: var(--color-bg-secondary);
  border-radius: 8px;
  margin-bottom: 16px;
}

.mode-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.mode-button:hover {
  background: var(--color-hover);
  color: var(--color-text-primary);
}

.mode-button.active {
  background: var(--color-primary);
  color: white;
}
</style>
```

### **PRIORITEIT 3: Advanced Features**

#### 8. **References & Sources**
```vue
<template>
  <div class="message-footer">
    <button @click="toggleReferences" class="references-toggle">
      <InfoIcon />
      Used {{ referenceCount }} references
      <ChevronIcon :expanded="showReferences" />
    </button>
    
    <transition name="expand">
      <div v-if="showReferences" class="references-list">
        <div v-for="ref in references" :key="ref.id" class="reference-item">
          <FileIcon :type="ref.type" />
          <span class="ref-path">{{ ref.path }}</span>
          <span class="ref-lines">Lines {{ ref.startLine }}-{{ ref.endLine }}</span>
          <button @click="openReference(ref)" class="open-btn">
            <ExternalLinkIcon />
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>
```

#### 9. **Error Handling & Retry**
```vue
<template>
  <div v-if="error" class="error-message">
    <div class="error-icon">
      <AlertIcon />
    </div>
    <div class="error-content">
      <h4>{{ error.title }}</h4>
      <p>{{ error.message }}</p>
      <div class="error-actions">
        <button @click="retry" class="retry-btn">
          <RetryIcon />
          Try Again
        </button>
        <button @click="dismiss" class="dismiss-btn">
          Dismiss
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.error-message {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: 8px;
  margin: 12px 0;
}

.error-icon {
  flex-shrink: 0;
  color: var(--color-error);
}

.error-content h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-error);
}

.error-content p {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.error-actions {
  display: flex;
  gap: 8px;
}
</style>
```

#### 10. **Keyboard Shortcuts**
```typescript
// Handig voor power users
const shortcuts = {
  'Ctrl/Cmd + Enter': 'Send message',
  'Ctrl/Cmd + K': 'Clear chat',
  'Ctrl/Cmd + /': 'Toggle command palette',
  'Ctrl/Cmd + Shift + C': 'Copy last code block',
  'Escape': 'Cancel current operation',
  'Ctrl/Cmd + ↑': 'Previous message in history',
  'Ctrl/Cmd + ↓': 'Next message in history'
};
```

---

## 🎯 UX Principles Applied

### **1. Jakob's Law**
> Users prefer your site to work like other sites they know

**Implementatie**: Gebruik bekende chat patterns (bubbles, timestamps, user right/AI left)

### **2. Aesthetic-Usability Effect**
> Users perceive attractive design as more usable

**Implementatie**: 
- Smooth animations
- Proper spacing
- Consistent styling
- Modern icons

### **3. Doherty Threshold**
> Response time < 400ms keeps users engaged

**Implementatie**:
- Instant typing feedback
- Progressive loading
- Streaming responses
- Optimistic UI updates

### **4. Miller's Law**
> Users can keep 7±2 items in working memory

**Implementatie**:
- Chunk long responses
- Collapsible sections
- Clear visual hierarchy
- Progressive disclosure

### **5. Hick's Law**
> More choices = more decision time

**Implementatie**:
- Limited action buttons (max 3-4)
- Context-aware actions
- Smart defaults
- Hidden advanced options

### **6. Peak-End Rule**
> Users judge experience by peaks and ending

**Implementatie**:
- Smooth completion animations
- Success celebrations
- Clear task completion
- Helpful error recovery

---

## 📐 Design System Recommendations

### **Color Palette**
```css
:root {
  /* Primary */
  --color-primary: #0066ff;
  --color-primary-hover: #0052cc;
  --color-primary-active: #004099;
  
  /* Semantic */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;
  
  /* Text */
  --color-text-primary: #111827;
  --color-text-secondary: #6b7280;
  --color-text-muted: #9ca3af;
  
  /* Backgrounds */
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f9fafb;
  --color-bg-tertiary: #f3f4f6;
  
  /* Borders */
  --color-border-light: #e5e7eb;
  --color-border-medium: #d1d5db;
  --color-border-dark: #9ca3af;
  
  /* Code */
  --color-code-bg: #1e1e1e;
  --color-code-text: #d4d4d4;
  --color-code-border: #333333;
}

/* Dark mode variants */
[data-theme="dark"] {
  --color-text-primary: #f9fafb;
  --color-text-secondary: #d1d5db;
  --color-text-muted: #9ca3af;
  
  --color-bg-primary: #111827;
  --color-bg-secondary: #1f2937;
  --color-bg-tertiary: #374151;
  
  --color-border-light: #374151;
  --color-border-medium: #4b5563;
  --color-border-dark: #6b7280;
}
```

### **Spacing Scale**
```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
}
```

### **Border Radius**
```css
:root {
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-full: 9999px;
}
```

### **Shadows**
```css
:root {
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
}
```

### **Transitions**
```css
:root {
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## ✅ Implementation Checklist

### **Phase 1: Foundation** (Week 1)
- [ ] Implement new typography system
- [ ] Update color palette & design tokens
- [ ] Create message bubble components
- [ ] Add basic animations & transitions
- [ ] Implement code block component with actions

### **Phase 2: Core Features** (Week 2)
- [ ] Add streaming response support
- [ ] Implement mode selector (Ask/Edit/Agent)
- [ ] Create progress indicators
- [ ] Add context file management
- [ ] Build error handling UI

### **Phase 3: Polish** (Week 3)
- [ ] Add references/sources display
- [ ] Implement keyboard shortcuts
- [ ] Add smooth scrolling behavior
- [ ] Create loading skeletons
- [ ] Add accessibility improvements (ARIA labels, focus management)

### **Phase 4: Advanced** (Week 4)
- [ ] Add message history navigation
- [ ] Implement slash commands UI
- [ ] Add file attachment preview
- [ ] Create diff viewer for code changes
- [ ] Add export conversation feature

---

## 📚 Key Takeaways

### **What Makes Great AI Chat UI?**

1. **Clarity**: Altijd duidelijk wat er gebeurt
2. **Control**: Gebruiker heeft controle over acties
3. **Feedback**: Immediate response op alle acties
4. **Context**: Duidelijk welke context gebruikt wordt
5. **Efficiency**: Snelle workflows, keyboard shortcuts
6. **Beauty**: Esthetisch aantrekkelijk, modern design
7. **Consistency**: Gedrag is voorspelbaar en consistent
8. **Forgiveness**: Fouten zijn makkelijk te herstellen

### **Common Anti-Patterns to Avoid**

❌ **Blocking UI tijdens processing**
✅ Show progress, allow cancellation

❌ **Unclear loading states**
✅ Specific status messages ("Analyzing...", "Generating...")

❌ **No context visibility**
✅ Show which files are being used

❌ **Poor error messages**
✅ Clear explanation + recovery action

❌ **Overwhelming choices**
✅ Smart defaults, progressive disclosure

❌ **Inconsistent styling**
✅ Design system, reusable components

❌ **No keyboard support**
✅ Full keyboard navigation

❌ **Inaccessible UI**
✅ ARIA labels, screen reader support

---

## 🔍 Competitor Feature Comparison

| Feature | Copilot | Cursor | Current Omni | Target Omni |
|---------|---------|---------|--------------|-------------|
| Streaming responses | ✅ | ✅ | ❓ | ✅ |
| Mode switching | ✅ | ✅ | ❌ | ✅ |
| Code actions | ✅ | ✅ | ❓ | ✅ |
| Context management | ✅ | ✅ | ❌ | ✅ |
| References/sources | ✅ | ✅ | ❌ | ✅ |
| Error recovery | ✅ | ✅ | ❓ | ✅ |
| Keyboard shortcuts | ✅ | ✅ | ❌ | ✅ |
| File attachments | ✅ | ✅ | ❓ | ✅ |
| Diff viewer | ✅ | ✅ | ❌ | ✅ |
| Dark mode | ✅ | ✅ | ❓ | ✅ |

---

## 🎬 Next Steps

1. **Review** dit document met het team
2. **Prioritize** features op basis van impact vs effort
3. **Design** mockups voor key screens
4. **Prototype** één complete flow
5. **Test** met gebruikers
6. **Iterate** op basis van feedback
7. **Implement** gefaseerd volgens checklist

---

## 📊 Implementation Progress

### Status Overview
**Started**: November 6, 2025  
**Current Phase**: Testing & Validation  
**Overall Progress**: 11/12 tasks (92%)

### Task Status

#### ✅ Completed (11)
1. **Design System: CSS design tokens bestand** - Created complete design system with 300+ lines of CSS custom properties
2. **Typography: Update globale font styling** - Updated src/style.css with design system typography, colors, and utilities
3. **Chat Messages: Redesign message bubble component** - Implemented bubble-style UI with user messages right-aligned and AI messages with icon
4. **Code Blocks: Creëer CodeBlock component** - Created reusable CodeBlock.vue with language badges and action buttons
5. **Progress Indicators: StatusIndicator component** - Created StatusIndicator.vue with animated spinners for all states
6. **Streaming: Typewriter effect** - Implemented smooth 60fps typewriter effect using requestAnimationFrame
7. **Mode Selector: ModeSelector component** - Created mode selector for Ask/Edit/Agent modes with animations
8. **Context Management: ContextIndicator component** - Built expandable context indicator with file list management
9. **Error Handling: ErrorMessage component** - Created error display component with retry/dismiss actions
10. **Dark Mode: Theme switching** - Implemented ThemeToggle component with localStorage persistence and system preference detection
11. **Animations: Smooth transitions** - All components use design system transitions with consistent timing

#### 🔄 In Progress (1)
12. **Testing: Comprehensive testing** - Testing all new UI components and fixing any issues

#### 📋 Todo (0)
*All tasks completed!*
7. Mode Selector: ModeSelector component
8. Context Management: ContextIndicator component
9. Error Handling: ErrorMessage component
10. Dark Mode: Theme switching
11. Animations: Smooth transitions
12. Testing: Comprehensive testing

### Recent Updates
- **[2025-11-06 12:15]** Task 11 completed - All animations implemented via design system
- **[2025-11-06 12:10]** Task 10 completed - ThemeToggle component created with dark mode support
- **[2025-11-06 12:05]** Task 9 completed - ErrorMessage component with severity levels
- **[2025-11-06 12:00]** Task 8 completed - ContextIndicator with expandable file list
- **[2025-11-06 11:55]** Task 7 completed - ModeSelector for Ask/Edit/Agent modes
- **[2025-11-06 11:52]** Task 6 completed - Smooth 60fps typewriter effect implemented
- **[2025-11-06 11:50]** Task 5 completed - StatusIndicator with animated spinners
- **[2025-11-06 11:45]** Task 4 completed - CodeBlock component created
- **[2025-11-06 11:40]** Tasks 2-3 completed - Typography and chat bubbles

---

**Document Status**: ✅ Complete (Research) | 🔄 In Progress (Implementation)  
**Last Updated**: November 6, 2025  
**Author**: AI Research Assistant  
**Version**: 1.0
