import type { VitePWAOptions } from 'vite-plugin-pwa';

export function createPwaOptions(
  appEnvironment: string,
  projectOwner = 'Portfolio Owner'
): Partial<VitePWAOptions> {
  const owner = projectOwner || 'Portfolio Owner';

  return {
    registerType: 'autoUpdate',
    injectRegister: false,
    workbox: {
      cleanupOutdatedCaches: true,
      clientsClaim: true,
      skipWaiting: true,
      navigateFallback: '',
      globIgnores: ['**/index.html'],
    },
    includeAssets: ['favicon.ico', 'robots.txt', 'logo192.png', 'logo512.png'],
    manifest: {
      short_name: owner,
      name: `${owner} - Portfolio & Astrophotography`,
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
    devOptions: {
      enabled: ['development', 'dev', 'local'].includes(appEnvironment),
    },
  };
}
