<template>
  <div class="chat-panel">
    <div class="chat-header">
      <div class="header-left">
        <h3>Chat met Omni</h3>
        <span v-if="commandHistory.length > 0" class="history-indicator">
          📚 {{ commandHistory.length }}/{{ MAX_HISTORY }} history
        </span>
      </div>
      <button @click="clearChat" class="clear-button" title="Wis chat geschiedenis en command history">
        🗑️ Wissen
      </button>
    </div>
    
    <div class="messages" ref="messagesContainer" @scroll="handleScroll">
      <!-- Load Older Messages Button -->
      <div v-if="hasArchivedMessages" class="load-older-container">
        <button 
          v-if="!loadingOlder"
          @click="loadOlderMessages" 
          class="load-older-button"
        >
          📜 Oudere berichten laden? ({{ archivedMessages.length }} berichten gearchiveerd)
        </button>
        <div v-else class="loading-older">
          <span class="spinner-small"></span>
          Laden...
        </div>
      </div>
      
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message"
        :class="msg.role"
      >
        <!-- User messages: simple bubble on the right -->
        <template v-if="msg.role === 'user'">
          <div class="message-header">
            <strong>You</strong>
            <span class="timestamp">{{ formatTime(msg.timestamp) }}</span>
          </div>
          <div class="message-content">{{ msg.content }}</div>
        </template>
        
        <!-- Assistant messages: icon + bubble on the left -->
        <template v-else>
          <div class="message-wrapper">
            <div class="message-icon">🤖</div>
            <div style="flex: 1;">
              <div class="message-header">
                <strong>Omni</strong>
                <span class="timestamp">{{ formatTime(msg.timestamp) }}</span>
                <span v-if="msg.isStreaming" class="streaming-badge">Streaming...</span>
              </div>
              
              <!-- Use StreamingResponse for actively streaming messages -->
              <StreamingResponse
                v-if="msg.requestId && msg.isStreaming"
                :ref="el => registerStreamingRef(el, msg.requestId!)"
                :request-id="msg.requestId"
                :auto-scroll="true"
                @complete="handleStreamComplete"
                @error="handleStreamError"
              />
              
              <!-- For completed messages, show preserved data -->
              <div v-else-if="msg.tools || msg.codeChanges || msg.fileReferences || msg.metadata" class="message-content preserved-response">
                <!-- Narrative content -->
                <div v-if="msg.content" class="narrative-section" v-html="renderMarkdown(msg.content)"></div>
                
                <!-- Tools section -->
                <ToolExecutionTree 
                  v-if="msg.tools && msg.tools.length > 0"
                  :tools="msg.tools"
                  class="tools-section"
                />
                
                <!-- Code changes -->
                <div v-if="msg.codeChanges && msg.codeChanges.length > 0" class="code-changes-section">
                  <h3>Code wijzigingen</h3>
                  <CodeChangeViewer 
                    v-for="(change, idx) in msg.codeChanges"
                    :key="`code-${idx}`"
                    :file-path="change.file"
                    :code="change.code"
                    :language="change.language"
                    :line-range="`${change.lineStart} - ${change.lineEnd}`"
                  />
                </div>
                
                <!-- File references -->
                <div v-if="msg.fileReferences && msg.fileReferences.length > 0" class="file-references">
                  <h3>Bestanden</h3>
                  <FileReference 
                    v-for="(ref, idx) in msg.fileReferences"
                    :key="`ref-${idx}`"
                    :path="ref.path"
                  />
                </div>
                
                <!-- Metadata footer -->
                <div v-if="msg.metadata" class="response-metadata">
                  <span v-if="msg.metadata.duration" class="duration">
                    Duur: {{ formatDuration(msg.metadata.duration) }}
                  </span>
                  <span v-if="msg.metadata.toolsExecuted && msg.metadata.toolsExecuted.length > 0" class="tools-count">
                    Tools: {{ msg.metadata.toolsExecuted.length }}
                  </span>
                  <span v-if="msg.metadata.filesModified && msg.metadata.filesModified.length > 0" class="files-count">
                    Bestanden: {{ msg.metadata.filesModified.length }}
                  </span>
                </div>
              </div>
              
              <!-- Fallback: Old-style content display for backwards compatibility -->
              <div v-else class="message-content">
                <!-- Parse content for file references -->
                <template v-for="(part, i) in parseMessageContent(msg.content)" :key="i">
                  <FileReference v-if="part.type === 'file'" :path="part.value" />
                  <span v-else>{{ part.value }}</span>
                </template>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div v-if="loading" class="message assistant loading">
        <div class="message-wrapper">
          <div class="message-icon">🤖</div>
          <div style="flex: 1;">
            <div class="message-header">
              <strong>Omni</strong>
              <span class="activity-indicator">
                <span class="spinner-dot"></span>
                <span class="activity-text">Bezig...</span>
              </span>
            </div>
            <div class="message-content">
              <!-- Progress messages with spinner -->
              <div v-if="currentProgress.length > 0" class="progress-section">
                <div v-for="(prog, idx) in currentProgress" :key="idx" class="progress-item">
                  <span class="progress-icon">{{ prog.icon }}</span>
                  <span class="progress-text">{{ prog.text }}</span>
                </div>
              </div>
              <!-- Typing indicator only when no progress -->
              <span v-else class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-container">
        <textarea
          ref="inputTextarea"
          v-model="inputMessage"
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.shift.enter.prevent="handleShiftEnter"
          @keydown.up="handleArrowUp"
          @keydown.down="handleArrowDown"
          placeholder="Type a message... (Enter to send, Shift+Enter for new line, ↑↓ voor history)"
          :disabled="loading"
          class="message-input"
          rows="5"
        />
        <button 
          @click="loading ? abortRequest() : sendMessage()" 
          :disabled="!loading && !inputMessage.trim()" 
          class="play-stop-button"
          :class="{ 'stop-mode': loading }"
          :title="loading ? 'Stop huidige actie' : 'Verstuur bericht'"
        >
          <svg v-if="loading" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="4" width="4" height="16" />
            <rect x="14" y="4" width="4" height="16" />
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Inline Chat Component -->
    <InlineChat 
      ref="inlineChatRef"
      @submit="handleInlineChatSubmit"
      @apply="handleInlineChatApply"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted, onBeforeUnmount, computed } from 'vue';
import { marked } from 'marked';
import InlineChat from './InlineChat.vue';
import FileReference from './FileReference.vue';
import StreamingResponse from './StreamingResponse.vue';
import ToolExecutionTree from './ToolExecutionTree.vue';
import CodeChangeViewer from './CodeChangeViewer.vue';
import type { OmniEvent } from '../types/events';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  requestId?: string;  // For tracking streaming responses
  isStreaming?: boolean;  // Whether this message is still streaming
  // Streaming response data (preserved after completion)
  tools?: Array<{
    name: string;
    args: any;
    result?: any;
    status: 'pending' | 'running' | 'success' | 'error';
    startTime: number;
    duration?: number;
    error?: string;
  }>;
  codeChanges?: Array<{
    file: string;
    lineStart: number;
    lineEnd: number;
    code: string;
    language: string;
  }>;
  fileReferences?: Array<{
    path: string;
    lineStart?: number;
    lineEnd?: number;
    context?: string;
  }>;
  metadata?: {
    requestId: string;
    duration: number;
    tokensUsed: number;
    toolsExecuted: string[];
    filesModified: string[];
  };
}

// Load messages from persistent storage on component creation
const loadMessages = async (): Promise<Message[]> => {
  try {
    // First try loading from Electron persistent storage
    if (window.electronAPI && window.electronAPI.loadChatMessages) {
      const response = await window.electronAPI.loadChatMessages();
      if (response.success && response.data && response.data.length > 0) {
        return response.data.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
      }
    }
    
    // Fallback: try localStorage (for backwards compatibility)
    const saved = localStorage.getItem('omni-chat-messages');
    
    if (saved) {
      const parsed = JSON.parse(saved);
      // Only return saved messages if array is not empty
      if (parsed && parsed.length > 0) {
        return parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
      }
    }
    
    // Check if there are archived messages - if so, don't show welcome message
    const archivedSaved = localStorage.getItem('omni-chat-archived');
    if (archivedSaved) {
      const archivedParsed = JSON.parse(archivedSaved);
      if (archivedParsed && archivedParsed.length > 0) {
        // Return empty array, archived messages will be shown via loadOlderMessages
        return [];
      }
    }
  } catch (error) {
    console.warn('Failed to load chat messages:', error);
  }
  
  // Default welcome message (only if no messages AND no archived messages)
  return [{
    role: 'assistant',
    content: 'Hallo! Ik ben Omni, jouw zelfverbeterende AI-assistent. Hoe kan ik je vandaag helpen?',
    timestamp: new Date()
  }];
};

const messages = ref<Message[]>([]);

// Streaming support
const streamingResponseRefs = ref<Record<string, any>>({});
const currentRequestId = ref<string | null>(null);

// Function to register StreamingResponse refs
const registerStreamingRef = (el: any, requestId: string) => {
  if (el && requestId) {
    streamingResponseRefs.value[requestId] = el;
  }
};

// Message archiving (max 10 visible messages)
const MAX_VISIBLE_MESSAGES = 10;
const archivedMessages = ref<Message[]>([]);
const loadingOlder = ref(false);
const showLoadOlder = ref(false);

const hasArchivedMessages = computed(() => archivedMessages.value.length > 0 && showLoadOlder.value);

// Archive old messages when exceeding limit
const archiveOldMessages = () => {
  if (messages.value.length > MAX_VISIBLE_MESSAGES) {
    const toArchive = messages.value.length - MAX_VISIBLE_MESSAGES;
    const archived = messages.value.splice(0, toArchive);
    archivedMessages.value.push(...archived);
    
    // Save archived messages to localStorage
    try {
      localStorage.setItem('omni-chat-archived', JSON.stringify(archivedMessages.value));
    } catch (error) {
      console.warn('Failed to save archived messages:', error);
    }
  }
};

// Load archived messages from localStorage
const loadArchivedMessages = () => {
  try {
    const saved = localStorage.getItem('omni-chat-archived');
    if (saved) {
      archivedMessages.value = JSON.parse(saved).map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }));
    }
  } catch (error) {
    console.warn('Failed to load archived messages:', error);
  }
};

// Load older messages when button is clicked
const loadOlderMessages = async () => {
  if (archivedMessages.value.length === 0) return;
  
  loadingOlder.value = true;
  
  // Save current scroll height before adding messages
  const oldScrollHeight = messagesContainer.value?.scrollHeight || 0;
  
  // Simulate small delay for better UX
  await new Promise(resolve => setTimeout(resolve, 300));
  
  // Load 10 more messages from archive
  const toLoad = Math.min(10, archivedMessages.value.length);
  const loaded = archivedMessages.value.splice(-toLoad, toLoad);
  messages.value.unshift(...loaded);
  
  // Hide the load button after loading
  showLoadOlder.value = false;
  
  // Update localStorage
  try {
    localStorage.setItem('omni-chat-archived', JSON.stringify(archivedMessages.value));
    localStorage.setItem('omni-chat-messages', JSON.stringify(messages.value));
  } catch (error) {
    console.warn('Failed to update messages:', error);
  }
  
  loadingOlder.value = false;
  
  // Restore scroll position after DOM updates
  // The new messages increase the scroll height, so we need to adjust
  await nextTick();
  if (messagesContainer.value) {
    const newScrollHeight = messagesContainer.value.scrollHeight;
    const heightDifference = newScrollHeight - oldScrollHeight;
    // Maintain relative scroll position by adding the height difference
    messagesContainer.value.scrollTop += heightDifference;
  }
};

// Scroll tracking
const userScrolledUp = ref(false);
const isNearBottom = () => {
  if (!messagesContainer.value) return true;
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value;
  return scrollHeight - scrollTop - clientHeight < 100; // Within 100px of bottom
};

const handleScroll = () => {
  userScrolledUp.value = !isNearBottom();
  
  // Show "Load older" button when user scrolls up and there are archived messages
  if (userScrolledUp.value && archivedMessages.value.length > 0) {
    showLoadOlder.value = true;
  }
};

// Save messages to localStorage when they change
watch(messages, (newMessages) => {
  try {
    // Don't save if we only have the default welcome message and no archived messages
    // This prevents overwriting existing chat history on component reload
    if (newMessages.length === 1 && 
        newMessages[0].role === 'assistant' && 
        newMessages[0].content.includes('Hallo! Ik ben Omni') &&
        archivedMessages.value.length === 0) {
      return;
    }
    
    localStorage.setItem('omni-chat-messages', JSON.stringify(newMessages));
  } catch (error) {
    console.warn('Failed to save chat messages to localStorage:', error);
  }
}, { deep: true });

// HMR detection and preservation
if ((import.meta as any).hot) {
  onMounted(async () => {
  // HMR preservation logic
  });
}

// Load messages and archived messages on mount
onMounted(async () => {
  // Clean up any existing listeners first (important for HMR)
  if (window.electronAPI?.removeChatEventListener) {
    window.electronAPI.removeChatEventListener();
  }
  
  // Setup streaming event listener
  setupStreamingListener();
  
  // Load messages from persistent storage
  const loadedMessages = await loadMessages();
  // Use splice to maintain array reference for Vue reactivity
  messages.value.splice(0, messages.value.length, ...loadedMessages);
  
  // Load archived messages
  loadArchivedMessages();
  
  // If we have archived messages but no visible messages, load the most recent 10
  if (archivedMessages.value.length > 0 && messages.value.length === 0) {
    const toLoad = Math.min(10, archivedMessages.value.length);
    const loaded = archivedMessages.value.splice(-toLoad, toLoad);
    messages.value.push(...loaded);
    
    // Update localStorage
    try {
      localStorage.setItem('omni-chat-archived', JSON.stringify(archivedMessages.value));
      localStorage.setItem('omni-chat-messages', JSON.stringify(messages.value));
    } catch (error) {
      console.warn('Failed to restore messages from archive:', error);
    }
  }
  
  // Archive old messages if we loaded more than MAX_VISIBLE_MESSAGES
  if (messages.value.length > MAX_VISIBLE_MESSAGES) {
    archiveOldMessages();
  }
  
  // Scroll to bottom on initial load (instant, no animation)
  // Use setTimeout to ensure DOM is fully rendered
  setTimeout(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  }, 0);
});

// Cleanup on unmount (for proper component lifecycle)
onBeforeUnmount(() => {
  if (window.electronAPI?.removeChatEventListener) {
    window.electronAPI.removeChatEventListener();
  }
  // Clear global handler reference
  globalEventHandler = null;
});

const inputMessage = ref('');
const loading = ref(false);
const messagesContainer = ref<HTMLElement | null>(null);
const inputTextarea = ref<HTMLTextAreaElement | null>(null);

// Command history management
const commandHistory = ref<string[]>([]);
const historyIndex = ref(-1);
const MAX_HISTORY = 20;

// Load command history from localStorage with validation
const loadCommandHistory = (): string[] => {
  try {
    const saved = localStorage.getItem('omni-command-history');
    if (!saved) return [];
    
    const parsed = JSON.parse(saved);
    // Validate: must be array of strings
    if (!Array.isArray(parsed)) return [];
    
    const validated = parsed.filter(item => typeof item === 'string' && item.trim().length > 0);
    return validated.slice(0, MAX_HISTORY); // Ensure max limit
  } catch (error) {
    console.warn('Failed to load command history:', error);
    return [];
  }
};

// Save command history to localStorage with validation
const saveCommandHistory = (history: string[]) => {
  try {
    // Validate before saving
    const validated = history
      .filter(item => typeof item === 'string' && item.trim().length > 0)
      .slice(0, MAX_HISTORY);
    
    localStorage.setItem('omni-command-history', JSON.stringify(validated));
  } catch (error) {
    console.warn('Failed to save command history:', error);
  }
};

// Initialize command history
commandHistory.value = loadCommandHistory();

// Watch messages and auto-save to both localStorage AND persistent storage whenever they change
watch(messages, async (newMessages) => {
  try {
    // Convert messages to plain objects (serialize Date objects to strings)
    const serializedMessages = newMessages.map(msg => ({
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp instanceof Date ? msg.timestamp.toISOString() : msg.timestamp
    }));
    
    // Save to localStorage for quick access
    localStorage.setItem('omni-chat-messages', JSON.stringify(serializedMessages));
    
    // Save to persistent storage (survives app restarts)
    if (window.electronAPI && window.electronAPI.saveChatMessages) {
      await window.electronAPI.saveChatMessages(serializedMessages);
    }
  } catch (error) {
    console.warn('Failed to save messages:', error);
  }
}, { deep: true });

// Add command to history
const addToHistory = (command: string) => {
  const trimmedCommand = command.trim();
  if (trimmedCommand && commandHistory.value[0] !== trimmedCommand) {
    commandHistory.value.unshift(trimmedCommand);
    
    // Limit history size
    if (commandHistory.value.length > MAX_HISTORY) {
      commandHistory.value = commandHistory.value.slice(0, MAX_HISTORY);
    }
    
    saveCommandHistory(commandHistory.value);
  }
  historyIndex.value = -1; // Reset to latest
};

// Navigate through history
const navigateHistory = (direction: 'up' | 'down') => {
  if (commandHistory.value.length === 0) {
    return;
  }
  
  if (direction === 'up') {
    if (historyIndex.value < commandHistory.value.length - 1) {
      historyIndex.value++;
      inputMessage.value = commandHistory.value[historyIndex.value];
    }
  } else if (direction === 'down') {
    if (historyIndex.value > 0) {
      historyIndex.value--;
      inputMessage.value = commandHistory.value[historyIndex.value];
    } else if (historyIndex.value === 0) {
      historyIndex.value = -1;
      inputMessage.value = '';
    }
  }
};

// Smooth typewriter effect using requestAnimationFrame (~60fps)
const typewriterEffect = async (text: string, onUpdate: (partialText: string) => void): Promise<void> => {
  return new Promise((resolve) => {
    const charsPerFrame = 2; // Characters to add per frame (adjustable for speed)
    const targetFPS = 60;
    const frameInterval = 1000 / targetFPS;
    
    let currentIndex = 0;
    let lastFrameTime = performance.now();
    
    const animate = async (currentTime: number) => {
      const elapsed = currentTime - lastFrameTime;
      
      if (elapsed >= frameInterval) {
        lastFrameTime = currentTime;
        currentIndex = Math.min(currentIndex + charsPerFrame, text.length);
        
        onUpdate(text.substring(0, currentIndex));
        await nextTick();
        
        if (currentIndex < text.length) {
          requestAnimationFrame(animate);
        } else {
          resolve();
        }
      } else {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  });
};

// Activity tracking voor timeout management
const lastProgressTime = ref(Date.now());
const progressUpdates = ref<string[]>([]);
const currentProgress = ref<Array<{ icon: string; text: string }>>([]);

// Parse progress message to extract icon and text
const parseProgressMessage = (msg: string): { icon: string; text: string } => {
  // Match emoji at start of string
  const emojiMatch = msg.match(/^([\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}])\s*/u);
  if (emojiMatch) {
    return {
      icon: emojiMatch[1],
      text: msg.substring(emojiMatch[0].length)
    };
  }
  return { icon: '⚙️', text: msg };
};

// Setup progress listener
if (window.electronAPI?.onChatProgress) {
  window.electronAPI.onChatProgress(async (progressMessage: string) => {
    // Update activity timestamp
    lastProgressTime.value = Date.now();
    
    // Store progress update
    progressUpdates.value.push(progressMessage);
    
    // Add to visual progress list (keep last 5 items)
    const parsed = parseProgressMessage(progressMessage);
    currentProgress.value.push(parsed);
    if (currentProgress.value.length > 5) {
      currentProgress.value.shift(); // Remove oldest
    }
    
    // Find the last assistant message and show progress IMMEDIATELY
    const lastMsg = messages.value[messages.value.length - 1];
    if (lastMsg && lastMsg.role === 'assistant' && loading.value) {
      // PERMANENTLY add progress - never replace, always append
      if (!lastMsg.content.endsWith('\n')) {
        lastMsg.content += '\n';
      }
      lastMsg.content += `${progressMessage}\n`;
      
      await nextTick();
      scrollToBottom();
    }
  });
}

const sendMessage = async () => {
  const message = inputMessage.value.trim();
  if (!message || loading.value) return;

  // Add to command history
  addToHistory(message);

  // Add user message
  messages.value.push({
    role: 'user',
    content: message,
    timestamp: new Date()
  });

  inputMessage.value = '';
  loading.value = true;
  
  // Clear previous progress
  currentProgress.value = [];
  progressUpdates.value = [];

  // Archive old messages if needed (before adding new response)
  archiveOldMessages();

  // Scroll to bottom and reset scroll tracking
  userScrolledUp.value = false;
  await nextTick();
  scrollToBottom();

  // Generate unique request ID
  const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  currentRequestId.value = requestId;

  // Add placeholder for assistant message with streaming support
  const assistantMessageIndex = messages.value.length;
  messages.value.push({
    role: 'assistant',
    content: '',
    timestamp: new Date(),
    requestId: requestId,
    isStreaming: true
  });

  try {
    // Call backend - streaming events will be handled by onChatEvent listener
    // Pass requestId so backend uses the same ID as frontend
    const response: any = await window.electronAPI.chat(message, requestId);

    if (!response.success) {
      // Handle error response
      console.error('[ChatPanel] Chat error:', response.error);
      const lastMsg = messages.value[assistantMessageIndex];
      lastMsg.content = `Error: ${response.error || 'Unknown error'}`;
      lastMsg.isStreaming = false;
      loading.value = false;
    }
    // If success, leave loading=true and let stream events handle completion
  } catch (error: any) {
    console.error('[ChatPanel] Chat error:', error);
    
    // Handle exception
    const lastMsg = messages.value[assistantMessageIndex];
    lastMsg.content = `Error: ${error?.message || 'Unknown error'}`;
    lastMsg.isStreaming = false;
    loading.value = false;
  }
  // Don't set loading=false here - let stream complete event handle it
  
  await nextTick();
  scrollToBottom();
};

// Streaming event handlers
const handleStreamComplete = (requestId: string) => {
  // Find message and mark as complete
  const message = messages.value.find(m => m.requestId === requestId);
  if (message) {
    message.isStreaming = false;
    
    // Get ALL data from StreamingResponse and save it to the message
    const responseRef = streamingResponseRefs.value[requestId];
    if (responseRef && responseRef.getAllData) {
      const allData = responseRef.getAllData();
      
      // Save all the data to the message for persistence
      message.content = allData.narrative || '';
      message.tools = allData.tools;
      message.codeChanges = allData.codeChanges;
      message.fileReferences = allData.fileReferences;
      message.metadata = allData.metadata;
      
      // Watcher will automatically save messages when content changes
    }
  }
  
  loading.value = false;
  currentRequestId.value = null;
  scrollToBottom();
};

const handleStreamError = (error: any) => {
  console.error('[ChatPanel] Stream error:', error);
  
  // CRITICAL: Preserve data before marking as complete
  // Find the message that was streaming
  const lastMsg = messages.value[messages.value.length - 1];
  if (lastMsg && lastMsg.role === 'assistant' && lastMsg.requestId) {
    // Get ALL data from StreamingResponse BEFORE marking as complete
    const responseRef = streamingResponseRefs.value[lastMsg.requestId];
    if (responseRef && responseRef.getAllData) {
      const allData = responseRef.getAllData();
      
      // Save all the data to the message for persistence
      lastMsg.content = allData.narrative || '';
      lastMsg.tools = allData.tools;
      lastMsg.codeChanges = allData.codeChanges;
      lastMsg.fileReferences = allData.fileReferences;
      lastMsg.metadata = allData.metadata;
    }
    
    // NOW mark as complete
    lastMsg.isStreaming = false;
  }
  
  loading.value = false;
};

// Global event handler reference (singleton pattern for HMR compatibility)
// This ensures we don't create multiple listeners during hot reload
let globalEventHandler: ((event: OmniEvent) => void) | null = null;

// Setup streaming event listener
const setupStreamingListener = () => {
  if (window.electronAPI?.onChatEvent) {
    // Remove old handler if it exists (hot reload cleanup)
    if (globalEventHandler) {
      // Note: Electron IPC doesn't provide removeListener, but we can overwrite
    }
    
    // Create new handler
    globalEventHandler = (event: OmniEvent) => {
      // Forward ALL events to the StreamingResponse component
      // (including response_complete, which triggers the @complete event)
      const responseRef = streamingResponseRefs.value[event.requestId];
      if (responseRef && responseRef.handleEvent) {
        responseRef.handleEvent(event);
      } else {
        console.warn('[ChatPanel] No StreamingResponse ref found for:', event.requestId);
      }
    };
    
    // Register the handler
    window.electronAPI.onChatEvent(globalEventHandler);
  } else {
    console.warn('[ChatPanel] onChatEvent API not available');
  }
};

const scrollToBottom = (force = false, instant = false) => {
  if (messagesContainer.value && (force || !userScrolledUp.value)) {
    if (instant) {
      // Instant scroll without animation (for initial load)
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    } else {
      // Smooth scroll
      messagesContainer.value.scrollTo({
        top: messagesContainer.value.scrollHeight,
        behavior: 'smooth'
      });
    }
  }
};

const abortRequest = () => {
  // Set loading to false to stop the current request
  loading.value = false;
  
  // Add a system message indicating the request was stopped
  const lastMsg = messages.value[messages.value.length - 1];
  if (lastMsg && lastMsg.role === 'assistant') {
    lastMsg.content += '\n\n⚠️ Request gestopt door gebruiker.';
  }
};

const clearChat = () => {
  const welcomeMessage: Message = {
    role: 'assistant',
    content: 'Hallo! Ik ben Omni, jouw zelfverbeterende AI-assistent. Hoe kan ik je vandaag helpen?',
    timestamp: new Date()
  };
  // Use splice to maintain array reference for Vue reactivity
  messages.value.splice(0, messages.value.length, welcomeMessage);
  localStorage.removeItem('omni-chat-messages');
  
  // Clear archived messages
  archivedMessages.value.splice(0, archivedMessages.value.length);
  localStorage.removeItem('omni-chat-archived');
  
  // NOTE: We DO NOT clear command history - it's useful to keep it like a terminal
  // Users can still use ↑↓ arrows to recall previous commands even after clearing chat
};

// InlineChat handlers
const inlineChatRef = ref();

const handleInlineChatSubmit = async (prompt: string, selection?: string) => {
  // Add user message to chat
  const userMessage: Message = {
    role: 'user',
    content: selection ? `\`\`\`\n${selection}\n\`\`\`\n\n${prompt}` : prompt,
    timestamp: new Date()
  };
  messages.value.push(userMessage);

  // Trigger API call similar to sendMessage
  loading.value = true;
  
  // Add placeholder for assistant message
  const assistantMessageIndex = messages.value.length;
  messages.value.push({
    role: 'assistant',
    content: '',
    timestamp: new Date()
  });

  await nextTick();
  scrollToBottom();

  try {
    const startTime = Date.now();
    const response: any = await Promise.race([
      window.electronAPI.chat(selection ? `${selection}\n\n${prompt}` : prompt),
      new Promise((_, reject) => {
        const checkTimeout = () => {
          const elapsed = Date.now() - startTime;
          const sinceProgress = Date.now() - lastProgressTime.value;
          
          if (elapsed > 180000 && sinceProgress > 45000) {
            reject(new Error(`Request timeout after ${Math.round(elapsed/1000)}s`));
          } else {
            setTimeout(checkTimeout, 10000);
          }
        };
        setTimeout(checkTimeout, 10000);
      })
    ]);

    if (response.success) {
      // Use typewriter effect
      await typewriterEffect(
        response.message,
        (partialText) => {
          messages.value[assistantMessageIndex].content = partialText;
        }
      );
      
      await nextTick();
      scrollToBottom();
    } else {
      messages.value[assistantMessageIndex].content = `❌ Fout: ${response.error}`;
    }
  } catch (error) {
    console.error('Inline chat error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    messages.value[assistantMessageIndex].content = `❌ Fout: ${errorMessage}`;
  } finally {
    loading.value = false;
  }
};

const handleInlineChatApply = (changes: string) => {
  console.log('Inline chat apply:', changes);
  // Here you would integrate with editor/code application logic
  // For now, just add as a message
  const message: Message = {
    role: 'assistant',
    content: `✅ Changes applied:\n\`\`\`\n${changes}\n\`\`\``,
    timestamp: new Date()
  };
  messages.value.push(message);
};

const handleShiftEnter = () => {
  // Get current cursor position
  const textarea = inputTextarea.value;
  if (textarea) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    
    // Insert newline at cursor position
    const value = inputMessage.value;
    inputMessage.value = value.substring(0, start) + '\n' + value.substring(end);
    
    // Restore cursor position after the newline
    nextTick(() => {
      textarea.selectionStart = textarea.selectionEnd = start + 1;
      textarea.focus();
    });
  }
};

const handleArrowUp = (event: KeyboardEvent) => {
  const textarea = inputTextarea.value;
  if (textarea) {
    // Only navigate history if cursor is at the first line
    const cursorPos = textarea.selectionStart;
    const textBeforeCursor = inputMessage.value.substring(0, cursorPos);
    const isFirstLine = !textBeforeCursor.includes('\n');
    
    if (isFirstLine) {
      event.preventDefault();
      navigateHistory('up');
    }
  }
};

const handleArrowDown = (event: KeyboardEvent) => {
  const textarea = inputTextarea.value;
  if (textarea) {
    // Only navigate history if cursor is at the last line  
    const cursorPos = textarea.selectionStart;
    const textAfterCursor = inputMessage.value.substring(cursorPos);
    const isLastLine = !textAfterCursor.includes('\n');
    
    if (isLastLine) {
      event.preventDefault();
      navigateHistory('down');
    }
  }
};

const formatTime = (date: Date) => {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

const formatDuration = (ms: number): string => {
  if (ms < 1000) {
    return `${ms}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  } else {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}m ${seconds}s`;
  }
};

const renderMarkdown = (text: string): string => {
  try {
    return marked(text) as string;
  } catch (err) {
    console.error('Markdown parsing error:', err);
    return text;
  }
};

/**
 * Parse message content into text and file reference parts
 * Returns an array of parts with type 'text' or 'file'
 */
interface MessagePart {
  type: 'text' | 'file';
  value: string;
}

const parseMessageContent = (content: string): MessagePart[] => {
  const parts: MessagePart[] = [];
  
  // Pattern to match file references with common extensions
  // Matches: filename.ext, path/to/file.ext, `filename.ext`
  const filePattern = /(?:^|\s)(`?([a-zA-Z0-9_\-]+(?:\/[a-zA-Z0-9_\-]+)*\.(vue|ts|js|jsx|tsx|py|css|html|json|md|txt))`?)(?=\s|$|[,.:!?])/gi;
  
  let lastIndex = 0;
  let match;
  
  while ((match = filePattern.exec(content)) !== null) {
    // Add text before the file reference
    if (match.index > lastIndex) {
      const textBefore = content.substring(lastIndex, match.index);
      if (textBefore) {
        parts.push({ type: 'text', value: textBefore });
      }
    }
    
    // Add the file reference (remove backticks if present)
    const filePath = match[2];
    parts.push({ type: 'file', value: filePath });
    
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (lastIndex < content.length) {
    parts.push({ type: 'text', value: content.substring(lastIndex) });
  }
  
  // If no file references found, return the whole content as text
  if (parts.length === 0) {
    parts.push({ type: 'text', value: content });
  }
  
  return parts;
};
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: var(--color-bg-primary);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
  border-bottom: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-sm);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.chat-header h3 {
  margin: 0;
  color: var(--color-white);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
}

.history-indicator {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  background: var(--color-bg-tertiary);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border-light);
}

.clear-button {
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.clear-button:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border-dark);
  transform: translateY(-1px);
}

.clear-button:active {
  transform: translateY(0);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: 100%;
  /* scroll-behavior removed - controlled via JS for instant vs smooth */
}

.load-older-container {
  display: flex;
  justify-content: center;
  padding: var(--space-4) 0;
  margin-bottom: var(--space-2);
}

.load-older-button {
  padding: var(--space-3) var(--space-5);
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.load-older-button:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-primary);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.loading-older {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.spinner-small {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border-medium);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.message {
  display: flex;
  flex-direction: column;
  animation: messageSlideIn var(--transition-base) var(--ease-out);
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* User messages - right aligned with subtle background */
.message.user {
  align-items: flex-end;
}

.message.user .message-content {
  max-width: var(--chat-message-max-width, 70%);
  padding: var(--space-3) var(--space-4);
  background: rgba(59, 130, 246, 0.1);
  color: var(--color-text-primary);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg);
  border: 1px solid var(--color-primary-border);
  box-shadow: var(--shadow-sm);
}

/* Assistant messages - left aligned, full width with icon */
.message.assistant {
  align-items: flex-start;
}

.message.assistant .message-wrapper {
  display: flex;
  gap: var(--space-3);
  width: 100%;
  max-width: var(--chat-message-max-width, 100%);
}

.message.assistant .message-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-lg);
  color: var(--color-white);
  box-shadow: var(--shadow-sm);
}

.message.assistant .message-content {
  flex: 1;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  border-radius: var(--radius-sm) var(--radius-lg) var(--radius-lg) var(--radius-lg);
  border: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-xs);
}

.message.loading .message-content {
  opacity: 0.7;
  background: var(--color-bg-tertiary);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
  font-size: var(--font-size-sm);
}

.message-header strong {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.streaming-badge {
  font-size: var(--font-size-xs);
  color: var(--color-primary);
  background: var(--color-primary-bg);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  border: 1px solid var(--color-primary-border);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.timestamp {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.message-content {
  line-height: var(--line-height-normal);
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: var(--font-size-base);
}

/* Enhanced typing indicator */
.typing-indicator {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-2) 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: typing 1.4s ease-in-out infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

/* Progress section styles */
.progress-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-2) 0;
  font-size: var(--font-size-sm);
}

.progress-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2);
  background: rgba(59, 130, 246, 0.05);
  border-left: 2px solid var(--color-primary);
  border-radius: var(--radius-md);
  animation: slideInLeft 0.3s ease-out;
}

.progress-icon {
  font-size: 1.2em;
  flex-shrink: 0;
}

.progress-text {
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.activity-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
}

.spinner-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border: 2px solid var(--color-primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.activity-text {
  font-weight: var(--font-weight-medium);
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.input-area {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  border-top: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-inner);
}

.input-container {
  position: relative;
  display: flex;
  align-items: flex-end;
}

.input-buttons {
  display: flex;
  gap: var(--space-2);
  align-self: flex-start;
}

.message-input {
  flex: 1;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-lg);
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-family: var(--font-family-text);
  line-height: var(--line-height-normal);
  min-height: calc(var(--chat-input-height) - var(--space-6));
  max-height: 200px;
  height: auto;
  resize: vertical;
  overflow-y: auto;
  overflow-x: hidden;
  transition: all var(--transition-fast);
}

.message-input::placeholder {
  color: var(--color-text-muted);
}

.message-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.message-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--color-bg-tertiary);
}

.send-button {
  padding: var(--space-3) var(--space-6);
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-sm);
}

.send-button:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.send-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--color-bg-tertiary);
  color: var(--color-text-muted);
}

.abort-button {
  padding: var(--space-3) var(--space-4);
  background: var(--color-error);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-sm);
}

.abort-button:hover:not(:disabled) {
  background: var(--color-error-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.abort-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}

.abort-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--color-bg-tertiary);
  color: var(--color-text-muted);
}

/* Preserved response (completed streaming messages) */
.preserved-response {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
}

.preserved-response .narrative-section {
  line-height: 1.6;
  color: var(--color-text-primary);
}

.preserved-response .narrative-section :deep(p) {
  margin: 0.5rem 0;
}

.preserved-response .narrative-section :deep(code) {
  background: var(--color-bg-tertiary);
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  font-size: 0.9em;
}

.preserved-response .tools-section,
.preserved-response .code-changes-section,
.preserved-response .file-references {
  margin-top: 0.5rem;
}

.preserved-response .response-metadata {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border);
  margin-top: 0.5rem;
}

.preserved-response h3 {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .message.user .message-content,
  .message.assistant .message-wrapper {
    max-width: 90%;
  }
  
  .messages {
    padding: var(--space-4) var(--space-2);
  }
}
</style>
