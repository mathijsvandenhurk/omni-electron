import { ref, onUnmounted } from 'vue';

export interface ResizeOptions {
  minSize: number;
  maxSize: number;
  defaultSize: number;
  direction: 'horizontal' | 'vertical';
  invertDelta?: boolean; // For panels on the right or bottom that grow in opposite direction
  onResize?: (size: number) => void;
}

export function useResizable(
  options: ResizeOptions
) {
  const size = ref(options.defaultSize);
  const isResizing = ref(false);
  
  let startPosition = 0;
  let startSize = 0;

  const startResize = (event: MouseEvent) => {
    event.preventDefault();
    isResizing.value = true;
    
    startPosition = options.direction === 'horizontal' ? event.clientX : event.clientY;
    startSize = size.value;
    
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', stopResize);
    document.body.style.cursor = options.direction === 'horizontal' ? 'col-resize' : 'row-resize';
    document.body.style.userSelect = 'none';
  };

  const onMouseMove = (event: MouseEvent) => {
    if (!isResizing.value) return;
    
    const currentPosition = options.direction === 'horizontal' ? event.clientX : event.clientY;
    let delta = currentPosition - startPosition;
    
    // Invert delta for panels that grow in opposite direction (right/bottom panels)
    if (options.invertDelta) {
      delta = -delta;
    }
    
    let newSize = startSize + delta;
    
    // Apply min/max constraints
    newSize = Math.max(options.minSize, Math.min(options.maxSize, newSize));
    
    size.value = newSize;
    
    if (options.onResize) {
      options.onResize(newSize);
    }
  };

  const stopResize = () => {
    isResizing.value = false;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', stopResize);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  };

  onUnmounted(() => {
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', stopResize);
  });

  return {
    size,
    isResizing,
    startResize
  };
}
