import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';
import { resolve } from 'path';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    tsconfigPaths(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['telescope.png', 'logo.png', 'robots.txt', 'sitemap.xml'],
      manifest: {
        short_name: 'Portfolio',
        name: 'Łukasz Remkowicz - Software Developer & Astrophotographer',
        description:
          'Portfolio landing page with astrophotography gallery, built with React, TypeScript, and Zustand.',
        icons: [
          {
            src: 'telescope.png',
            sizes: '64x64 32x32 24x24 16x16',
            type: 'image/png',
          },
          {
            src: 'telescope.png',
            type: 'image/png',
            sizes: '192x192',
            purpose: 'any maskable',
          },
          {
            src: 'telescope.png',
            type: 'image/png',
            sizes: '512x512',
          },
        ],
        start_url: '.',
        display: 'standalone',
        theme_color: '#02040a',
        background_color: '#02040a',
      },
    }),
  ],
  define: {
    // Inject process.env vars into import.meta.env for frontend access
    // Force empty API_URL to ensure we use valid relative paths for the proxy
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.API_URL),
    'import.meta.env.VITE_GA_TRACKING_ID': JSON.stringify(
      process.env.GA_TRACKING_ID
    ),
    'import.meta.env.VITE_ENABLE_GA': JSON.stringify(process.env.ENABLE_GA),
    'process.env.VITE_API_URL': JSON.stringify(process.env.API_URL),
    'process.env.VITE_GA_TRACKING_ID': JSON.stringify(
      process.env.GA_TRACKING_ID
    ),
    'process.env.VITE_ENABLE_GA': JSON.stringify(process.env.ENABLE_GA),
  },
  // dev settings
  server: {
    host: '0.0.0.0', // Needed for Docker
    port: 3000,
    open: false, // Don't open browser in Docker
    allowedHosts: ['portfolio.local', 'localhost', '127.0.0.1'],
    proxy: {
      '/v1': {
        target: 'http://portfolio-be:8000',
        changeOrigin: true,
        secure: false,
        headers: {
          Host: new URL(process.env.API_URL || 'http://localhost').host,
        },
      },
      '/api': {
        target: 'http://portfolio-be:8000',
        changeOrigin: true,
        secure: false,
        headers: {
          Host: new URL(process.env.API_URL || 'http://localhost').host,
        },
      },
      '/media': {
        target: 'http://portfolio-be:8000',
        changeOrigin: true,
        secure: false,
        headers: {
          Host: new URL(process.env.API_URL || 'http://localhost').host,
        },
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
});
