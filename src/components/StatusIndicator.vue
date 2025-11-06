<template>
  <div class="status-indicator" :class="[`status-${status}`, { inline }]">
    <div class="status-icon">
      <!-- Animated spinner for active states -->
      <div v-if="isActiveStatus" class="spinner" :class="`spinner-${status}`">
        <div class="spinner-ring"></div>
      </div>
      
      <!-- Static icons for complete/error states -->
      <span v-else class="status-emoji">{{ statusIcon }}</span>
    </div>
    
    <div class="status-content">
      <span class="status-message">{{ statusMessage }}</span>
      <span v-if="detail" class="status-detail">{{ detail }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type StatusType = 'thinking' | 'generating' | 'streaming' | 'complete' | 'error';

interface Props {
  status: StatusType;
  message?: string;
  detail?: string;
  inline?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  message: '',
  detail: '',
  inline: false
});

// Active statuses show spinner
const isActiveStatus = computed(() => {
  return ['thinking', 'generating', 'streaming'].includes(props.status);
});

// Status icons for complete/error states
const statusIcons: Record<StatusType, string> = {
  thinking: '🤔',
  generating: '⚡',
  streaming: '💬',
  complete: '✅',
  error: '❌'
};

const statusIcon = computed(() => statusIcons[props.status]);

// Default messages per status
const defaultMessages: Record<StatusType, string> = {
  thinking: 'Aan het nadenken...',
  generating: 'Genereren...',
  streaming: 'Antwoord streamen...',
  complete: 'Klaar',
  error: 'Er is een fout opgetreden'
};

const statusMessage = computed(() => {
  return props.message || defaultMessages[props.status];
});
</script>

<style scoped>
.status-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  animation: statusFadeIn var(--transition-base) var(--ease-out);
}

.status-indicator.inline {
  display: inline-flex;
  padding: var(--space-2) var(--space-3);
}

@keyframes statusFadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.status-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-emoji {
  font-size: var(--font-size-lg);
  line-height: 1;
}

/* Spinner animations */
.spinner {
  width: 100%;
  height: 100%;
  position: relative;
}

.spinner-ring {
  width: 100%;
  height: 100%;
  border: 2px solid var(--color-border-light);
  border-radius: 50%;
  border-top-color: var(--color-primary);
  animation: spinRotate 0.8s linear infinite;
}

.spinner-thinking .spinner-ring {
  border-top-color: var(--color-info);
  animation-duration: 1s;
}

.spinner-generating .spinner-ring {
  border-top-color: var(--color-warning);
  animation-duration: 0.6s;
}

.spinner-streaming .spinner-ring {
  border-top-color: var(--color-success);
  animation-duration: 1.2s;
  animation-timing-function: ease-in-out;
}

@keyframes spinRotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Additional pulse effect for active statuses */
.status-thinking,
.status-generating,
.status-streaming {
  animation: statusPulse 2s ease-in-out infinite;
}

@keyframes statusPulse {
  0%, 100% {
    box-shadow: 0 0 0 0 var(--color-primary-light);
  }
  50% {
    box-shadow: 0 0 0 4px transparent;
  }
}

.status-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0; /* Allow text truncation */
}

.status-message {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
}

.status-detail {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-tight);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Status-specific styling */
.status-thinking {
  background: var(--color-info-bg);
  border-color: var(--color-info-border);
}

.status-thinking .status-message {
  color: var(--color-info);
}

.status-generating {
  background: var(--color-warning-bg);
  border-color: var(--color-warning-border);
}

.status-generating .status-message {
  color: var(--color-warning);
}

.status-streaming {
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
}

.status-streaming .status-message {
  color: var(--color-success);
}

.status-complete {
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
}

.status-complete .status-message {
  color: var(--color-success);
}

.status-error {
  background: var(--color-error-bg);
  border-color: var(--color-error-border);
}

.status-error .status-message {
  color: var(--color-error);
}

/* Inline variant adjustments */
.status-indicator.inline .status-icon {
  width: 20px;
  height: 20px;
}

.status-indicator.inline .status-emoji {
  font-size: var(--font-size-base);
}

.status-indicator.inline .status-message {
  font-size: var(--font-size-sm);
}

.status-indicator.inline .status-detail {
  font-size: var(--font-size-xs);
}
</style>
