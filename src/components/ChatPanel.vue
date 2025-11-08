<template>
  <div class="chat-panel">
    <div class="chat-header">
      <div class="header-left">
        <h3>Chat met Omni</h3>
        <span v-if="commandHistory.length > 0" class="history-indicator">
          📚 {{ commandHistory.length }}/{{ maxHistorySize }} history
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
              </div>
              <div class="message-content">{{ msg.content }}</div>
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
            </div>
            <div class="message-content">
              <span class="typing-indicator">
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
      <button @click="sendMessage" :disabled="loading || !inputMessage.trim()" class="send-button">
        Send
      </button>
      <button @click="abortRequest" :disabled="!loading" class="abort-button" title="Stop huidige actie">
        ⏹️ Stop
      </button>
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
import { ref, nextTick, watch, onMounted, computed } from 'vue';
import InlineChat from './InlineChat.vue';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Load messages from localStorage on component creation
const loadMessages = (): Message[] => {
  try {
    const saved = localStorage.getItem('omni-chat-messages');
    if (saved) {
      const parsed = JSON.parse(saved);
      return parsed.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }));
    }
  } catch (error) {
    console.warn('Failed to load chat messages from localStorage:', error);
  }
  
  // Default welcome message
  return [{
    role: 'assistant',
    content: 'Hallo! Ik ben Omni, jouw zelfverbeterende AI-assistent. Hoe kan ik je vandaag helpen?',
    timestamp: new Date()
  }];
};

const messages = ref<Message[]>(loadMessages());

// Message archiving (max 20 visible messages)
const MAX_VISIBLE_MESSAGES = 20;
const archivedMessages = ref<Message[]>([]);
const loadingOlder = ref(false);

const hasArchivedMessages = computed(() => archivedMessages.value.length > 0);

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
  
  // Simulate small delay for better UX
  await new Promise(resolve => setTimeout(resolve, 300));
  
  // Load 20 more messages from archive
  const toLoad = Math.min(20, archivedMessages.value.length);
  const loaded = archivedMessages.value.splice(-toLoad, toLoad);
  messages.value.unshift(...loaded);
  
  // Update localStorage
  try {
    localStorage.setItem('omni-chat-archived', JSON.stringify(archivedMessages.value));
    localStorage.setItem('omni-chat-messages', JSON.stringify(messages.value));
  } catch (error) {
    console.warn('Failed to update messages:', error);
  }
  
  loadingOlder.value = false;
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
};

// Save messages to localStorage when they change
watch(messages, (newMessages) => {
  try {
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

// Load archived messages on mount
onMounted(() => {
  loadArchivedMessages();
  // Scroll to bottom on initial load
  nextTick(() => {
    scrollToBottom();
  });
});

const inputMessage = ref('');
const loading = ref(false);
const messagesContainer = ref<HTMLElement | null>(null);
const inputTextarea = ref<HTMLTextAreaElement | null>(null);

// Command history management
const commandHistory = ref<string[]>([]);
const historyIndex = ref(-1);
const maxHistorySize = 30;

// Load command history from localStorage
const loadCommandHistory = (): string[] => {
  try {
    const saved = localStorage.getItem('omni-command-history');
    return saved ? JSON.parse(saved) : [];
  } catch (error) {
    console.warn('Failed to load command history:', error);
    return [];
  }
};

// Save command history to localStorage
const saveCommandHistory = (history: string[]) => {
  try {
    localStorage.setItem('omni-command-history', JSON.stringify(history));
  } catch (error) {
    console.warn('Failed to save command history:', error);
  }
};

// Initialize command history
commandHistory.value = loadCommandHistory();

// Add command to history
const addToHistory = (command: string) => {
  const trimmedCommand = command.trim();
  if (trimmedCommand && commandHistory.value[0] !== trimmedCommand) {
    commandHistory.value.unshift(trimmedCommand);
    
    // Limit history size
    if (commandHistory.value.length > maxHistorySize) {
      commandHistory.value = commandHistory.value.slice(0, maxHistorySize);
    }
    
    saveCommandHistory(commandHistory.value);
  }
  historyIndex.value = -1; // Reset to latest
};

// Navigate through history
const navigateHistory = (direction: 'up' | 'down') => {
  if (commandHistory.value.length === 0) return;
  
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

// Setup progress listener
if (window.electronAPI?.onChatProgress) {
  window.electronAPI.onChatProgress(async (progressMessage: string) => {
    // Update activity timestamp
    lastProgressTime.value = Date.now();
    
    // Store progress update
    progressUpdates.value.push(progressMessage);
    
    // Find the last assistant message and show progress IMMEDIATELY
    const lastMsg = messages.value[messages.value.length - 1];
    if (lastMsg && lastMsg.role === 'assistant' && loading.value) {
      // PERMANENTLY add progress - never replace, always append
      if (!lastMsg.content.endsWith('\n')) {
        lastMsg.content += '\n';
      }
      lastMsg.content += `**${progressMessage}**\n`;
      
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

  // Archive old messages if needed (before adding new response)
  archiveOldMessages();

  // Scroll to bottom and reset scroll tracking
  userScrolledUp.value = false;
  await nextTick();
  scrollToBottom();

  // Add placeholder for assistant message
  const assistantMessageIndex = messages.value.length;
  messages.value.push({
    role: 'assistant',
    content: '',
    timestamp: new Date()
  });

  let responseStarted = false;

  try {
    // Call Python backend via Electron IPC met verbeterde timeout handling
    const startTime = Date.now();
    const response: any = await Promise.race([
      window.electronAPI.chat(message),
      new Promise((_, reject) => {
        // Slimme timeout die checkt voor recente progress
        const checkTimeout = () => {
          const elapsed = Date.now() - startTime;
          const sinceProgress = Date.now() - lastProgressTime.value;
          
          // Alleen timeout na 3 minuten met geen progress voor 45 seconden
          if (elapsed > 180000 && sinceProgress > 45000) {
            reject(new Error(`Request timeout after ${Math.round(elapsed/1000)}s (no progress for ${Math.round(sinceProgress/1000)}s)`));
          } else {
            setTimeout(checkTimeout, 10000); // Check every 10 seconds
          }
        };
        setTimeout(checkTimeout, 10000);
      })
    ]);

    if (response.success) {
      const fullText = response.data?.answer || 'No response';
      responseStarted = true;
      
      // Get existing progress content
      const lastMsg = messages.value[assistantMessageIndex];
      const existingProgress = lastMsg.content;
      
      // Add separator between progress and final response if there's progress
      const separator = existingProgress ? '\n\n---\n\n**Final Response:**\n\n' : '';
      
      // Use typewriter effect for the final response
      await typewriterEffect(fullText, (partialText: string) => {
        messages.value[assistantMessageIndex].content = existingProgress + separator + partialText;
        scrollToBottom();
      });
    } else {
      // For errors, also preserve existing progress
      const lastMsg = messages.value[assistantMessageIndex];
      const existingProgress = lastMsg.content;
      const separator = existingProgress ? '\n\n---\n\n' : '';
      messages.value[assistantMessageIndex].content = existingProgress + separator + `Error: ${response.error || 'Unknown error'}`;
    }
  } catch (error: any) {
    console.error('Chat error:', error);
    
    // Better error handling with context  
    let errorMessage = `Error: ${error?.message || 'Unknown error'}`;
    if (error.message?.includes('timeout')) {
      if (responseStarted) {
        errorMessage = `⚠️ Response was taking too long, but Omni may still be working in the background. Try asking "What's your status?" in a few moments.`;
      } else {
        errorMessage = `⚠️ Request timeout - this usually means Omni is working on a complex task. The backend is still running and may complete soon.`;
      }
    }
    
    // Preserve existing progress in error case too
    const lastMsg = messages.value[assistantMessageIndex];
    const existingProgress = lastMsg.content;
    const separator = existingProgress ? '\n\n---\n\n' : '';
    messages.value[assistantMessageIndex].content = existingProgress + separator + errorMessage;
  } finally {
    loading.value = false;
    await nextTick();
    scrollToBottom();
  }
};

const scrollToBottom = (force = false) => {
  if (messagesContainer.value && (force || !userScrolledUp.value)) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
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
  messages.value = [welcomeMessage];
  localStorage.removeItem('omni-chat-messages');
  
  // Clear archived messages
  archivedMessages.value = [];
  localStorage.removeItem('omni-chat-archived');
  
  // Also clear command history
  commandHistory.value = [];
  historyIndex.value = -1;
  localStorage.removeItem('omni-command-history');
};

// InlineChat handlers
const inlineChatRef = ref();

const handleInlineChatSubmit = async (prompt: string, selection?: string) => {
  console.log('Inline chat submit:', { prompt, selection });
  
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
  scroll-behavior: smooth;
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
  background: var(--color-primary-light);
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

.input-area {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  border-top: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-inner);
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
