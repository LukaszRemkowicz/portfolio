// frontend/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  css: {
    modules: {
      localsConvention: 'camelCaseOnly',
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: ['portfolio.local', 'localhost'],
    // HMR must go through Nginx reverse-proxy (wss://portfolio.local)
    hmr: {
      clientPort: 443,
      protocol: 'wss',
      host: 'portfolio.local',
    },
    warmup: {
      clientFiles: ['./src/index.tsx'],
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
        },
      },
    },
  },
});
