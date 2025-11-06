<template>
  <div class="error-message" :class="[`severity-${severity}`]">
    <div class="error-icon">
      {{ errorIcon }}
    </div>
    
    <div class="error-content">
      <h4 class="error-title">{{ title || defaultTitle }}</h4>
      <p class="error-text">{{ message }}</p>
      <div v-if="details" class="error-details">
        <details>
          <summary>Technische details</summary>
          <pre class="details-content">{{ details }}</pre>
        </details>
      </div>
    </div>
    
    <div v-if="showActions" class="error-actions">
      <button v-if="showRetry" @click="retry" class="error-button retry-button">
        <span>🔄</span>
        Opnieuw proberen
      </button>
      <button v-if="showDismiss" @click="dismiss" class="error-button dismiss-button">
        <span>✕</span>
        Sluiten
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type SeverityType = 'error' | 'warning' | 'info';

interface Props {
  title?: string;
  message: string;
  details?: string;
  severity?: SeverityType;
  showRetry?: boolean;
  showDismiss?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  details: '',
  severity: 'error',
  showRetry: true,
  showDismiss: true
});

const emit = defineEmits<{
  retry: [];
  dismiss: [];
}>();

const showActions = computed(() => props.showRetry || props.showDismiss);

const errorIcons: Record<SeverityType, string> = {
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️'
};

const errorIcon = computed(() => errorIcons[props.severity]);

const defaultTitles: Record<SeverityType, string> = {
  error: 'Er is een fout opgetreden',
  warning: 'Waarschuwing',
  info: 'Informatie'
};

const defaultTitle = computed(() => defaultTitles[props.severity]);

const retry = () => {
  emit('retry');
};

const dismiss = () => {
  emit('dismiss');
};
</script>

<style scoped>
.error-message {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-medium);
  background: var(--color-bg-secondary);
  animation: errorSlideIn var(--transition-base) var(--ease-out);
  box-shadow: var(--shadow-md);
}

@keyframes errorSlideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Severity-specific styling */
.severity-error {
  background: var(--color-error-bg);
  border-color: var(--color-error-border);
}

.severity-warning {
  background: var(--color-warning-bg);
  border-color: var(--color-warning-border);
}

.severity-info {
  background: var(--color-info-bg);
  border-color: var(--color-info-border);
}

.error-icon {
  flex-shrink: 0;
  font-size: var(--font-size-2xl);
  line-height: 1;
  margin-top: var(--space-1);
}

.error-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 0; /* Allow text truncation */
}

.error-title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
}

.severity-error .error-title {
  color: var(--color-error);
}

.severity-warning .error-title {
  color: var(--color-warning);
}

.severity-info .error-title {
  color: var(--color-info);
}

.error-text {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  line-height: var(--line-height-normal);
  word-wrap: break-word;
}

.error-details {
  margin-top: var(--space-2);
}

.error-details details {
  cursor: pointer;
}

.error-details summary {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-semibold);
  padding: var(--space-2);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  user-select: none;
}

.error-details summary:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.details-content {
  margin: var(--space-2) 0 0;
  padding: var(--space-3);
  background: var(--color-code-bg);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  font-family: var(--font-family-code);
  font-size: var(--font-size-sm);
  color: var(--color-code-text);
  overflow-x: auto;
  line-height: var(--line-height-code);
  max-height: 200px;
  overflow-y: auto;
}

.error-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex-shrink: 0;
}

.error-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.retry-button {
  background: var(--color-primary);
  color: var(--color-white);
  border-color: var(--color-primary-dark);
}

.retry-button:hover {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.dismiss-button {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

.dismiss-button:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
  border-color: var(--color-border-dark);
}

.error-button:active {
  transform: translateY(0);
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .error-message {
    flex-direction: column;
  }
  
  .error-actions {
    flex-direction: row;
    justify-content: flex-end;
  }
  
  .error-button {
    flex: 1;
  }
}
</style>
