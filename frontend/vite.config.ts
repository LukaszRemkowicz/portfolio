// frontend/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: [
        'favicon.ico',
        'robots.txt',
        'logo192.png',
        'logo512.png',
      ],
      manifest: {
        short_name: 'Łukasz Remkowicz',
        name: 'Łukasz Remkowicz - Portfolio & Astrophotography',
        icons: [
          {
            src: 'favicon.ico',
            sizes: '64x64 32x32 24x24 16x16',
            type: 'image/x-icon',
          },
          {
            src: 'logo192.png',
            type: 'image/png',
            sizes: '192x192',
          },
          {
            src: 'logo512.png',
            type: 'image/png',
            sizes: '512x512',
          },
        ],
        start_url: '/',
        display: 'standalone',
        theme_color: '#02040a',
        background_color: '#02040a',
      },
    }),
  ],
  css: {
    modules: {
      localsConvention: 'camelCaseOnly',
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: process.env.ALLOWED_HOSTS
      ? process.env.ALLOWED_HOSTS.split(',').map(h => h.trim())
      : ['portfolio.local', 'localhost'],
    // HMR config
    hmr: {
      clientPort: process.env.VITE_ENVIRONMENT === 'stage' ? 8443 : 443,
      protocol: 'wss',
      host:
        process.env.VITE_ENVIRONMENT === 'stage'
          ? process.env.SITE_DOMAIN || 'stage.portfolio.local'
          : 'portfolio.local',
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
