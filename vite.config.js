import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { visualizer } from 'rollup-plugin-visualizer';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // Bundle analyzer - generates stats.html after build
    visualizer({
      filename: 'dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  optimizeDeps: {
    include: ['monaco-editor']
  },
  worker: {
    format: 'es'
  },
  server: {
    port: 5173,
    strictPort: true,
    watch: {
      ignored: [
        '**/backend/venv/**',
        '**/backend/__pycache__/**',
        '**/backend/**/__pycache__/**',
        '**/.venv/**',
        '**/node_modules/**'
      ]
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    // Bundle size optimizations
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          // Vue framework as separate chunk
          'vue-vendor': ['vue'],
          // Future: separate chunks for larger dependencies
        },
        // Optimize chunk file names
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      },
      // Tree shaking optimizations
      treeshake: {
        moduleSideEffects: false,
        propertyReadSideEffects: false,
        tryCatchDeoptimization: false
      }
    },
    // Production optimizations
    minify: 'terser',
    terserOptions: {
      compress: {
        // Remove console.logs in production
        drop_console: true,
        drop_debugger: true,
        // Remove unused code
        pure_funcs: ['console.log', 'console.debug', 'console.info'],
        // Advanced compression
        passes: 2,
        unsafe_arrows: true,
        unsafe_comps: true,
        unsafe_methods: true
      },
      mangle: {
        safari10: true
      },
      format: {
        comments: false
      }
    },
    // Chunk size warning threshold
    chunkSizeWarningLimit: 1000,
    // Target modern browsers for smaller output
    target: 'esnext',
    // Inline small assets
    assetsInlineLimit: 4096,
    // CSS optimizations (using built-in CSS minification)
    cssCodeSplit: true,
    cssMinify: 'lightningcss'
  }
});
