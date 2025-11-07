<template>
  <div class="file-explorer">
    <div class="explorer-header">
      <h3>📁 File Explorer</h3>
      <button @click="refreshFiles" class="refresh-btn" title="Refresh">
        🔄
      </button>
    </div>
    <div class="explorer-content">
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else class="file-tree">
        <FileTreeItem
          v-for="item in fileTree"
          :key="item.path"
          :item="item"
          :depth="0"
          @file-click="handleFileClick"
          @folder-toggle="handleFolderToggle"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue';

// File tree item component
import { defineComponent } from 'vue';

interface FileItem {
  name: string;
  path: string;
  isDirectory: boolean;
  children?: FileItem[];
  expanded?: boolean;
}

// Define emits
const emit = defineEmits(['fileSelected']);

const files = ref<string[]>([]);
const loading = ref(false);
const error = ref('');
const fileTree = ref<FileItem[]>([]);
const fileTreeMap = ref<Map<string, FileItem>>(new Map());

// VS Code style file icons
const getFileIcon = (filename: string, isDirectory: boolean, expanded: boolean = false) => {
  if (isDirectory) return expanded ? '📂' : '📁';
  
  const ext = filename.split('.').pop()?.toLowerCase();
  
  // Programming languages
  if (ext === 'vue') return '�'; // Vue green
  if (ext === 'ts') return '🔷'; // TypeScript blue
  if (ext === 'tsx') return '⚛️'; // React
  if (ext === 'js' || ext === 'mjs' || ext === 'cjs') return '📜';
  if (ext === 'jsx') return '⚛️';
  if (ext === 'py') return '🐍';
  if (ext === 'java') return '☕';
  if (ext === 'cpp' || ext === 'cc' || ext === 'cxx') return '⚙️';
  if (ext === 'c') return '©️';
  if (ext === 'rs') return '🦀'; // Rust
  if (ext === 'go') return '🐹';
  if (ext === 'php') return '🐘';
  if (ext === 'rb') return '💎'; // Ruby
  
  // Web
  if (ext === 'html' || ext === 'htm') return '🌐';
  if (ext === 'css' || ext === 'scss' || ext === 'sass' || ext === 'less') return '🎨';
  
  // Data
  if (ext === 'json') return '📋';
  if (ext === 'xml') return '📰';
  if (ext === 'yaml' || ext === 'yml') return '⚙️';
  if (ext === 'toml') return '⚙️';
  
  // Documents
  if (ext === 'md' || ext === 'markdown') return '📝';
  if (ext === 'txt') return '📄';
  if (ext === 'pdf') return '📕';
  
  // Images
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico'].includes(ext || '')) return '�️';
  
  // Config
  if (filename === 'package.json') return '📦';
  if (filename === 'tsconfig.json') return '🔷';
  if (filename === '.gitignore') return '�';
  if (filename.startsWith('.env')) return '�';
  if (ext === 'config' || filename.endsWith('.config.js') || filename.endsWith('.config.ts')) return '⚙️';
  
  return '📄';
};

// Build tree structure from flat file list (only once, then cache)
const buildFileTree = () => {
  console.log('[FileExplorer] Building tree from', files.value.length, 'files');
  const root: FileItem[] = [];
  const map = new Map<string, FileItem>();
  
  // First pass: create all items
  for (const file of files.value) {
    const isDirectory = file.endsWith('/');
    const cleanPath = file.replace(/\/$/, '');
    const parts = cleanPath.split('/');
    const name = parts[parts.length - 1];
    
    const item: FileItem = {
      name,
      path: file,
      isDirectory,
      children: isDirectory ? [] : undefined,
      expanded: false
    };
    
    map.set(file, item);
  }
  
  // Second pass: build hierarchy
  for (const [path, item] of map.entries()) {
    const cleanPath = path.replace(/\/$/, '');
    const parts = cleanPath.split('/');
    
    if (parts.length === 1) {
      root.push(item);
    } else {
      const parentPath = parts.slice(0, -1).join('/') + '/';
      const parent = map.get(parentPath);
      if (parent && parent.children) {
        parent.children.push(item);
      }
    }
  }
  
  // Sort function: directories first (a-z), then files (a-z)
  const sortItems = (items: FileItem[]) => {
    return items.sort((a, b) => {
      // Directories before files
      if (a.isDirectory !== b.isDirectory) {
        return a.isDirectory ? -1 : 1;
      }
      // Alphabetical within same type
      return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
    });
  };
  
  // Sort root level
  sortItems(root);
  
  // Sort all children recursively
  const sortChildren = (items: FileItem[]) => {
    items.forEach(item => {
      if (item.children) {
        sortItems(item.children);
        sortChildren(item.children);
      }
    });
  };
  sortChildren(root);
  
  console.log('[FileExplorer] Tree built with', root.length, 'root items');
  if (root.length > 0) {
    console.log('[FileExplorer] First root item:', root[0].name, root[0].isDirectory);
  }
  
  fileTree.value = root;
  fileTreeMap.value = map;
};

const loadFiles = async () => {
  loading.value = true;
  error.value = '';
  try {
    console.log('[FileExplorer] Loading files recursively from "."');
    const response = await (window.electronAPI as any).listFilesRecursive('.', {
      maxDepth: 10,
      excludePatterns: ['node_modules', '__pycache__', '.DS_Store', 'Thumbs.db']
    });
    console.log('[FileExplorer] Response:', response);
    if (response.success) {
      files.value = response.data?.files || [];
      console.log('[FileExplorer] Loaded files:', files.value.length, 'files');
      console.log('[FileExplorer] First 10 files:', files.value.slice(0, 10));
      
      // Build tree once after loading
      buildFileTree();
    } else {
      error.value = response.error || 'Failed to load files';
      console.error('[FileExplorer] Error:', error.value);
    }
  } catch (err: any) {
    error.value = err.message || 'Unknown error';
    console.error('[FileExplorer] Exception:', err);
  } finally {
    loading.value = false;
  }
};

const refreshFiles = () => {
  loadFiles();
};

const handleFileClick = (path: string) => {
  emit('fileSelected', path);
};

const handleFolderToggle = (path: string) => {
  console.log('[FileExplorer] Toggling folder:', path);
  
  // Find item in map and toggle its expanded state
  const item = fileTreeMap.value.get(path);
  if (item && item.isDirectory) {
    item.expanded = !item.expanded;
    // Force Vue reactivity update
    fileTree.value = [...fileTree.value];
  }
};

onMounted(() => {
  loadFiles();
});

// File tree item component using render function (no template compiler needed)
const FileTreeItem: any = defineComponent({
  name: 'FileTreeItem',
  props: {
    item: {
      type: Object as () => FileItem,
      required: true
    },
    depth: {
      type: Number,
      required: true
    }
  },
  emits: ['file-click', 'folder-toggle'],
  setup(props, { emit }) {
    const handleClick = () => {
      if (props.item.isDirectory) {
        emit('folder-toggle', props.item.path);
      } else {
        emit('file-click', props.item.path);
      }
    };
    
    return { handleClick, getFileIcon };
  },
  render() {
    const { item, depth, handleClick } = this as any;
    const paddingLeft = `${depth * 16 + 8}px`;
    
    // Recursive children
    const children = item.isDirectory && item.expanded && item.children
      ? item.children.map((child: FileItem) =>
          h(FileTreeItem, {
            key: child.path,
            item: child,
            depth: depth + 1,
            'onFile-click': (path: string) => this.$emit('file-click', path),
            'onFolder-toggle': (path: string) => this.$emit('folder-toggle', path)
          })
        )
      : [];
    
    return h('div', { class: 'tree-item-wrapper' }, [
      h('div', {
        class: 'file-item',
        style: { paddingLeft },
        onClick: handleClick
      }, [
        item.isDirectory
          ? h('span', { class: 'expand-icon' }, item.expanded ? '▾' : '▸')
          : h('span', { class: 'expand-icon-placeholder' }),
        h('span', { class: 'file-icon' }, getFileIcon(item.name, item.isDirectory, item.expanded)),
        h('span', { class: 'file-name' }, item.name)
      ]),
      ...children
    ]);
  }
});
</script>

<style scoped>
.file-explorer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
}

.explorer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.explorer-header h3 {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.refresh-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
  opacity: 0.7;
  transition: opacity 0.2s;
  color: var(--text-primary);
}

.refresh-btn:hover {
  opacity: 1;
}

.explorer-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.loading, .error {
  padding: 1rem;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.error {
  color: var(--color-error);
}

.file-tree {
  display: flex;
  flex-direction: column;
  user-select: none;
}

.tree-item-wrapper {
  display: flex;
  flex-direction: column;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  transition: background 0.15s;
  font-size: 0.875rem;
  white-space: nowrap;
  min-height: 22px;
}

.file-item:hover {
  background: var(--bg-hover);
}

.expand-icon {
  width: 16px;
  flex-shrink: 0;
  font-size: 0.75rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.expand-icon-placeholder {
  width: 16px;
  flex-shrink: 0;
}

.file-icon {
  font-size: 1rem;
  flex-shrink: 0;
  width: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-name {
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Scrollbar styling */
.explorer-content::-webkit-scrollbar {
  width: 10px;
}

.explorer-content::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

.explorer-content::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 5px;
}

.explorer-content::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}
</style>