<template>
  <button 
    @click="toggleTheme"
    class="theme-toggle"
    :title="isDark ? 'Schakel naar light mode' : 'Schakel naar dark mode'"
  >
    <span class="theme-icon">{{ isDark ? '☀️' : '🌙' }}</span>
    <span class="theme-label">{{ isDark ? 'Light' : 'Dark' }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const isDark = ref(false);

// Load theme preference from localStorage
const loadTheme = (): boolean => {
  try {
    const saved = localStorage.getItem('omni-theme');
    if (saved) {
      return saved === 'dark';
    }
    // Default to system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  } catch (error) {
    console.warn('Failed to load theme preference:', error);
    return false;
  }
};

// Apply theme to document
const applyTheme = (dark: boolean) => {
  if (dark) {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }
  
  try {
    localStorage.setItem('omni-theme', dark ? 'dark' : 'light');
  } catch (error) {
    console.warn('Failed to save theme preference:', error);
  }
};

const toggleTheme = () => {
  isDark.value = !isDark.value;
  applyTheme(isDark.value);
};

// Initialize theme on mount
onMounted(() => {
  isDark.value = loadTheme();
  applyTheme(isDark.value);
  
  // Listen for system theme changes
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  mediaQuery.addEventListener('change', (e) => {
    isDark.value = e.matches;
    applyTheme(isDark.value);
  });
});
</script>

<style scoped>
.theme-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-xs);
}

.theme-toggle:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.theme-toggle:active {
  transform: translateY(0);
}

.theme-icon {
  font-size: var(--font-size-lg);
  line-height: 1;
  transition: transform var(--transition-base);
}

.theme-toggle:hover .theme-icon {
  transform: rotate(180deg) scale(1.1);
}

.theme-label {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Animation when theme changes */
@keyframes themeChange {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
}

.theme-toggle:active .theme-icon {
  animation: themeChange 0.3s ease-out;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .theme-label {
    display: none;
  }
  
  .theme-toggle {
    padding: var(--space-2);
  }
}
</style>
