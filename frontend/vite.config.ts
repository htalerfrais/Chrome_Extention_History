import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './', // Force relative paths for Chrome extension
  build: {
    outDir: '../extension/dashboard-assets',
    emptyOutDir: true, // Clean output directory before build
    rollupOptions: {
      output: {
        // Generate single files for Chrome extension
        entryFileNames: 'index.js',
        chunkFileNames: 'chunk-[name].js',
        assetFileNames: 'assets/[name].[ext]',
        // Avoid code splitting for Chrome extension compatibility
        manualChunks: undefined,
      },
    },
    // Chrome extension CSP compatibility
    target: 'es2017',
    minify: false, // Keep readable for debugging
  },
  define: {
    // Define global for Chrome extension environment
    global: 'globalThis',
  },
})
