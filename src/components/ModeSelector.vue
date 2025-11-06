<template>
  <div class="mode-selector">
    <button
      v-for="mode in modes"
      :key="mode.value"
      @click="selectMode(mode.value)"
      :class="['mode-button', { active: modelValue === mode.value }]"
      :title="mode.description"
    >
      <span class="mode-icon">{{ mode.icon }}</span>
      <span class="mode-label">{{ mode.label }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
type ModeType = 'ask' | 'edit' | 'agent';

interface ModeOption {
  value: ModeType;
  label: string;
  icon: string;
  description: string;
}

interface Props {
  modelValue: ModeType;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:modelValue': [value: ModeType];
}>();

const modes: ModeOption[] = [
  {
    value: 'ask',
    label: 'Ask',
    icon: '💬',
    description: 'Stel vragen en krijg antwoorden'
  },
  {
    value: 'edit',
    label: 'Edit',
    icon: '✏️',
    description: 'Bewerk en verfijn code'
  },
  {
    value: 'agent',
    label: 'Agent',
    icon: '🤖',
    description: 'Autonome agent mode met zelfverbetering'
  }
];

const selectMode = (mode: ModeType) => {
  emit('update:modelValue', mode);
};
</script>

<style scoped>
.mode-selector {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-2);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
}

.mode-button {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-primary);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;
}

/* Hover effect */
.mode-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-primary-light);
  opacity: 0;
  transition: opacity var(--transition-fast);
  z-index: 0;
}

.mode-button:hover::before {
  opacity: 0.1;
}

.mode-button:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.mode-button:active {
  transform: translateY(0);
}

/* Active state */
.mode-button.active {
  background: var(--color-primary);
  color: var(--color-white);
  border-color: var(--color-primary-dark);
  box-shadow: var(--shadow-sm);
}

.mode-button.active::before {
  opacity: 0;
}

.mode-button.active:hover {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.mode-icon {
  font-size: var(--font-size-xl);
  line-height: 1;
  position: relative;
  z-index: 1;
  transition: transform var(--transition-fast);
}

.mode-button:hover .mode-icon {
  transform: scale(1.1);
}

.mode-button.active .mode-icon {
  transform: scale(1.15);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.mode-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  line-height: 1;
  position: relative;
  z-index: 1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Pulse animation for active mode */
@keyframes modePulse {
  0%, 100% {
    box-shadow: 0 0 0 0 var(--color-primary);
  }
  50% {
    box-shadow: 0 0 0 4px transparent;
  }
}

.mode-button.active {
  animation: modePulse 2s ease-in-out infinite;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .mode-selector {
    gap: var(--space-1);
  }
  
  .mode-button {
    padding: var(--space-2) var(--space-3);
  }
  
  .mode-icon {
    font-size: var(--font-size-lg);
  }
  
  .mode-label {
    font-size: var(--font-size-xs);
  }
}
</style>
