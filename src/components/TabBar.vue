<template>
  <div class="tab-bar">
    <!-- Scroll left button (shown when overflow) -->
    <button 
      v-if="showScrollButtons && canScrollLeft"
      class="scroll-btn scroll-left"
      @click="scrollTabs('left')"
      title="Scroll left"
    >
      ‹
    </button>

    <!-- Tabs container -->
    <div 
      ref="tabsContainer" 
      class="tabs-container"
      @scroll="updateScrollButtons"
    >
      <div 
        v-for="tab in tabs" 
        :key="tab.uri"
        class="tab"
        :class="{ 
          active: tab.uri === activeTabUri,
          dirty: tab.isDirty
        }"
        @click="selectTab(tab.uri)"
        @contextmenu.prevent="openContextMenu(tab.uri, $event)"
      >
        <!-- File icon (based on language/extension) -->
        <span class="tab-icon">{{ getFileIcon(tab.uri) }}</span>
        
        <!-- File name -->
        <span class="tab-name" :title="tab.uri">
          {{ getFileName(tab.uri) }}
        </span>
        
        <!-- Dirty indicator (unsaved changes) -->
        <span v-if="tab.isDirty" class="tab-dirty">●</span>
        
        <!-- Close button -->
        <button 
          class="tab-close"
          @click.stop="closeTab(tab.uri)"
          title="Close"
        >
          ×
        </button>
      </div>
    </div>

    <!-- Scroll right button (shown when overflow) -->
    <button 
      v-if="showScrollButtons && canScrollRight"
      class="scroll-btn scroll-right"
      @click="scrollTabs('right')"
      title="Scroll right"
    >
      ›
    </button>

    <!-- Context menu -->
    <Teleport to="body">
      <div 
        v-if="contextMenu.visible"
        ref="contextMenuRef"
        class="context-menu"
        :style="{ 
          top: contextMenu.y + 'px', 
          left: contextMenu.x + 'px' 
        }"
      >
        <button @click="closeTab(contextMenu.targetUri!)">Close</button>
        <button @click="closeOtherTabs(contextMenu.targetUri!)">Close Others</button>
        <button @click="closeTabsToRight(contextMenu.targetUri!)">Close to the Right</button>
        <button @click="closeAllTabs()">Close All</button>
        <hr>
        <button v-if="isTabDirty(contextMenu.targetUri!)" disabled>
          Save (Not implemented yet)
        </button>
        <button @click="copyFilePath(contextMenu.targetUri!)">Copy Path</button>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';

// Props
interface Tab {
  uri: string;
  isDirty: boolean;
}

interface Props {
  tabs: Tab[];
  activeTabUri: string | null;
}

const props = defineProps<Props>();

// Emits
const emit = defineEmits<{
  selectTab: [uri: string];
  closeTab: [uri: string];
  closeOtherTabs: [uri: string];
  closeTabsToRight: [uri: string];
  closeAllTabs: [];
}>();

// Refs
const tabsContainer = ref<HTMLElement | null>(null);
const contextMenuRef = ref<HTMLElement | null>(null);
const canScrollLeft = ref(false);
const canScrollRight = ref(false);

// Context menu state
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  targetUri: null as string | null
});

// Computed
const showScrollButtons = computed(() => {
  return canScrollLeft.value || canScrollRight.value;
});

// Methods
const getFileName = (uri: string): string => {
  const parts = uri.split('/');
  const filename = parts[parts.length - 1];
  
  // Truncate long filenames
  if (filename.length > 25) {
    return filename.substring(0, 22) + '...';
  }
  
  return filename;
};

const getFileIcon = (uri: string): string => {
  const ext = uri.split('.').pop()?.toLowerCase() || '';
  
  const iconMap: Record<string, string> = {
    // JavaScript/TypeScript
    'js': '🟨',
    'ts': '🔷',
    'jsx': '⚛️',
    'tsx': '⚛️',
    'vue': '💚',
    
    // Web
    'html': '🌐',
    'css': '🎨',
    'scss': '🎨',
    'json': '📋',
    
    // Python
    'py': '🐍',
    
    // Other
    'md': '📝',
    'txt': '📄',
    'log': '📃',
    'yaml': '⚙️',
    'yml': '⚙️',
    'xml': '📰',
    'sql': '🗄️',
    'sh': '🔧',
    
    // Default
    '': '📄'
  };
  
  return iconMap[ext] || '📄';
};

const selectTab = (uri: string) => {
  console.log('🔍 DEBUG [TabBar.selectTab]: Called with URI:', uri);
  console.log('🔍 DEBUG [TabBar.selectTab]: Current active tab:', props.activeTabUri);
  console.log('🔍 DEBUG [TabBar.selectTab]: Available tabs:', props.tabs.map(t => t.uri));
  console.log('🔍 DEBUG [TabBar.selectTab]: Emitting selectTab event');
  emit('selectTab', uri);
  console.log('🔍 DEBUG [TabBar.selectTab]: Event emitted successfully');
};

const closeTab = (uri: string) => {
  emit('closeTab', uri);
  closeContextMenu();
};

const closeOtherTabs = (uri: string) => {
  emit('closeOtherTabs', uri);
  closeContextMenu();
};

const closeTabsToRight = (uri: string) => {
  emit('closeTabsToRight', uri);
  closeContextMenu();
};

const closeAllTabs = () => {
  emit('closeAllTabs');
  closeContextMenu();
};

const isTabDirty = (uri: string): boolean => {
  const tab = props.tabs.find(t => t.uri === uri);
  return tab?.isDirty || false;
};

const copyFilePath = (uri: string) => {
  navigator.clipboard.writeText(uri);
  closeContextMenu();
};

const scrollTabs = (direction: 'left' | 'right') => {
  if (!tabsContainer.value) return;
  
  const scrollAmount = 200;
  const currentScroll = tabsContainer.value.scrollLeft;
  
  if (direction === 'left') {
    tabsContainer.value.scrollTo({
      left: currentScroll - scrollAmount,
      behavior: 'smooth'
    });
  } else {
    tabsContainer.value.scrollTo({
      left: currentScroll + scrollAmount,
      behavior: 'smooth'
    });
  }
};

const updateScrollButtons = () => {
  if (!tabsContainer.value) return;
  
  const { scrollLeft, scrollWidth, clientWidth } = tabsContainer.value;
  
  canScrollLeft.value = scrollLeft > 0;
  canScrollRight.value = scrollLeft < scrollWidth - clientWidth - 1;
};

const openContextMenu = (uri: string, event: MouseEvent) => {
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    targetUri: uri
  };
};

const closeContextMenu = () => {
  contextMenu.value.visible = false;
};

// Close context menu on click outside
const handleClickOutside = (event: MouseEvent) => {
  if (contextMenu.value.visible && contextMenuRef.value) {
    if (!contextMenuRef.value.contains(event.target as Node)) {
      closeContextMenu();
    }
  }
};

// Watch for tab changes to update scroll buttons
watch(() => props.tabs.length, async () => {
  await nextTick();
  updateScrollButtons();
});

// Lifecycle
onMounted(() => {
  updateScrollButtons();
  window.addEventListener('click', handleClickOutside);
  
  // Update scroll buttons on window resize
  window.addEventListener('resize', updateScrollButtons);
  
  // Observe container size changes
  if (tabsContainer.value) {
    const resizeObserver = new ResizeObserver(updateScrollButtons);
    resizeObserver.observe(tabsContainer.value);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener('click', handleClickOutside);
  window.removeEventListener('resize', updateScrollButtons);
});
</script>

<style scoped>
.tab-bar {
  display: flex;
  align-items: center;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
  height: 40px;
  user-select: none;
}

.tabs-container {
  flex: 1;
  display: flex;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.tabs-container::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.tab {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  min-width: 120px;
  max-width: 200px;
  background: var(--color-bg-tertiary);
  border-right: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: background var(--transition-fast);
  flex-shrink: 0;
}

.tab:hover {
  background: var(--color-bg-hover);
}

.tab.active {
  background: var(--color-bg-primary);
  border-bottom: 2px solid var(--color-primary);
}

.tab.dirty .tab-name {
  font-style: italic;
}

.tab-icon {
  font-size: 16px;
  line-height: 1;
  flex-shrink: 0;
}

.tab-name {
  flex: 1;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tab-dirty {
  color: var(--color-warning);
  font-size: 18px;
  line-height: 1;
  flex-shrink: 0;
}

.tab-close {
  display: none;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.tab:hover .tab-close {
  display: flex;
}

.tab-close:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.scroll-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 40px;
  border: none;
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-size: 20px;
  cursor: pointer;
  transition: background var(--transition-fast);
  flex-shrink: 0;
}

.scroll-btn:hover {
  background: var(--color-bg-hover);
}

.scroll-left {
  border-right: 1px solid var(--color-border-light);
}

.scroll-right {
  border-left: 1px solid var(--color-border-light);
}

/* Context Menu */
.context-menu {
  position: fixed;
  z-index: 10000;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-medium);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  padding: var(--space-2) 0;
  min-width: 180px;
}

.context-menu button {
  display: block;
  width: 100%;
  padding: var(--space-2) var(--space-4);
  border: none;
  background: transparent;
  color: var(--color-text-primary);
  text-align: left;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.context-menu button:hover:not(:disabled) {
  background: var(--color-bg-hover);
}

.context-menu button:disabled {
  color: var(--color-text-muted);
  cursor: not-allowed;
}

.context-menu hr {
  margin: var(--space-2) 0;
  border: none;
  border-top: 1px solid var(--color-border-light);
}
</style>
