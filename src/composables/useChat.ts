/**
 * Chat Composable - Presentation Layer
 * Vue composition API for chat functionality using Clean Architecture
 */

import { ref, onUnmounted } from 'vue';
import { ChatUseCases } from '../core/usecases';
import { ElectronChatRepository } from '../infrastructure/ElectronChatRepository';
import { MessageProgress } from '../core/entities/Message';

// Create global chat use cases instance
const chatRepository = new ElectronChatRepository();
const chatUseCases = new ChatUseCases(chatRepository);

export function useChat() {
  const messages = ref<string[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const progress = ref<string>('');

  // Send message function
  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    isLoading.value = true;
    error.value = null;
    progress.value = '';
    
    // Add user message
    messages.value.push(`User: ${message}`);

    try {
      const result = await chatUseCases.sendMessage(message);
      
      if (result.success && result.data) {
        messages.value.push(`Assistant: ${result.data}`);
      } else {
        error.value = result.error || 'Failed to send message';
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
    } finally {
      isLoading.value = false;
      progress.value = '';
    }
  };

  // Get available models
  const getModels = async () => {
    const result = await chatUseCases.getAvailableModels();
    return result.success ? result.data || [] : [];
  };

  // Setup progress listening
  const setupProgressListener = () => {
    chatUseCases.onMessageProgress((progressData: MessageProgress) => {
      progress.value = progressData.content;
    });
  };

  // Cleanup on component unmount
  onUnmounted(() => {
    chatUseCases.removeProgressListener();
  });

  return {
    messages,
    isLoading,
    error,
    progress,
    sendMessage,
    getModels,
    setupProgressListener
  };
}