// frontend/vite.config.ts
import { defineConfig } from 'vite';
import type {
  ConfigEnv,
  HtmlTagDescriptor,
  IndexHtmlTransformContext,
  PluginOption,
} from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig(({ isSsrBuild }: ConfigEnv) => {
  const appEnvironment =
    process.env.ENVIRONMENT || process.env.VITE_ENVIRONMENT || 'development';
  const disablePwaEnvironments = [
    'development',
    'dev',
    'local',
    'stage',
    'stg',
  ];
  const enablePwa =
    !isSsrBuild && !disablePwaEnvironments.includes(appEnvironment);

  const criticalPathPlugin: PluginOption = !isSsrBuild
    ? {
        name: 'critical-path-optimization',
        enforce: 'post',
        transformIndexHtml: {
          order: 'post',
          handler(
            html: string,
            ctx?: IndexHtmlTransformContext
          ): string | HtmlTagDescriptor[] {
            const bootstrapScript = `<script>(function(){try{var lang=window.__INITIAL_LANGUAGE__||localStorage.getItem('i18nextLng')||'en';document.documentElement.lang=lang.split('-')[0];window.__INITIAL_LANGUAGE__=lang;}catch(_e){document.documentElement.lang='en';window.__INITIAL_LANGUAGE__='en';}})();</script>`;

            html = html.replace(
              /<link rel="modulepreload"[^>]*href="[^"]*sentry-[^"]*\.js"[^>]*>\s*/gi,
              ''
            );

            if (ctx?.bundle) {
              const entryChunk = Object.values(ctx.bundle).find(file => {
                const chunk = file as {
                  type?: string;
                  isEntry?: boolean;
                  fileName?: string;
                };
                return (
                  chunk.type === 'chunk' &&
                  chunk.isEntry === true &&
                  typeof chunk.fileName === 'string' &&
                  chunk.fileName.endsWith('.js')
                );
              }) as { fileName?: string } | undefined;

              if (entryChunk?.fileName) {
                html = html.replace(
                  '</head>',
                  `<link rel="modulepreload" href="/${entryChunk.fileName}" crossorigin>\n</head>`
                );
              }
            }

            html = html.replace('</head>', `${bootstrapScript}\n</head>`);

            if (ctx?.bundle) {
              let cssContent = '';
              for (const [fileName, file] of Object.entries(ctx.bundle)) {
                const asset = file as { type?: string; source?: unknown };
                if (
                  fileName.endsWith('.css') &&
                  asset.type === 'asset' &&
                  typeof asset.source === 'string'
                ) {
                  cssContent += asset.source;
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
      }
    : null;

  return {
    esbuild: {
      target: 'es2022',
    },
    define: {
      'Array.from': 'Array.from',
      __PROJECT_OWNER__: JSON.stringify(
        process.env.PROJECT_OWNER || 'Portfolio Owner'
      ),
    },
    plugins: [
      react(),
      criticalPathPlugin,
      enablePwa &&
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
    ].filter(Boolean),
    css: {
      modules: {
        localsConvention: 'camelCaseOnly',
      },
    },
    ssr: {
      noExternal: ['react-helmet-async'],
    },
    server: {
      host: '0.0.0.0',
      port: Number(process.env.FRONTEND_PORT) || 8080,
      allowedHosts: process.env.ALLOWED_HOSTS
        ? process.env.ALLOWED_HOSTS.split(',').map(h => h.trim())
        : ['portfolio.local', 'localhost'],
      hmr: {
        clientPort: process.env.VITE_ENVIRONMENT === 'stage' ? 8443 : 443,
        protocol: 'wss',
        host:
          process.env.VITE_ENVIRONMENT === 'stage'
            ? process.env.SITE_DOMAIN || 'stage.portfolio.local'
            : 'portfolio.local',
      },
      warmup: {
        clientFiles: ['./src/entry-client.tsx'],
      },
    },
    preview: {
      host: '0.0.0.0',
      port: Number(process.env.FRONTEND_PORT) || 8080,
    },
    build: {
      target: 'es2022',
      outDir: isSsrBuild ? 'dist/server' : 'dist',
      // The local SSR dev container rebuilds on file watch and can overlap
      // client builds briefly. Avoid emptying dist in development to prevent
      // ENOTEMPTY races while keeping production builds clean.
      emptyOutDir:
        appEnvironment === 'development' || appEnvironment === 'dev'
          ? false
          : undefined,
      sourcemap: true,
      rollupOptions: isSsrBuild
        ? undefined
        : {
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
  };
});
