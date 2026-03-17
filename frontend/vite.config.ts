// frontend/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  esbuild: {
    target: 'es2022',
  },
  define: {
    'Array.from': 'Array.from',
  },
  plugins: [
    react(),
    {
      // Optimize the critical rendering path by inlining CSS and removing non-essential preloads
      name: 'critical-path-optimization',
      enforce: 'post',
      transformIndexHtml: {
        order: 'post',
        handler(html, ctx) {
          // Remove non-critical Sentry preloads
          html = html.replace(
            /<link rel="modulepreload"[^>]*href="[^"]*sentry-[^"]*\.js"[^>]*>\s*/gi,
            ''
          );

          // Inline character-critical CSS directly into the HTML to eliminate render-blocking stylesheet requests
          if (ctx.bundle) {
            let cssContent = '';
            for (const [fileName, file] of Object.entries(ctx.bundle)) {
              if (
                fileName.endsWith('.css') &&
                file.type === 'asset' &&
                typeof file.source === 'string'
              ) {
                cssContent += file.source;
                html = html.replace(
                  new RegExp(
                    `<link[^>]*href="[^"]*${fileName}"[^>]*>\\s*`,
                    'g'
                  ),
                  ''
                );
              }
            }
            if (cssContent) {
              const headEndIndex = html.indexOf('</head>');
              if (headEndIndex !== -1) {
                html =
                  html.slice(0, headEndIndex) +
                  `<style>${cssContent}</style>\n` +
                  html.slice(headEndIndex);
              }
            }
          }
          return html;
        },
      },
    },
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'script-defer',
      includeAssets: [
        'favicon.ico',
        'robots.txt',
        'logo192.png',
        'logo512.png',
      ],
      manifest: {
        short_name: process.env.PROJECT_OWNER,
        name: `${process.env.PROJECT_OWNER} - Portfolio & Astrophotography`,
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
    port: Number(process.env.FRONTEND_PORT) || 8080,
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
    port: Number(process.env.FRONTEND_PORT) || 8080,
  },
  build: {
    target: 'es2022',
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/@sentry')) {
            return 'sentry';
          }
          if (
            id.includes('node_modules/react') ||
            id.includes('node_modules/react-dom') ||
            id.includes('node_modules/react-router-dom')
          ) {
            return 'vendor';
          }
        },
      },
    },
  },
});
