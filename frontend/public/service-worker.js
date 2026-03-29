//  TODO: TEMPORARY legacy migration worker for clients still registered to
// /service-worker.js from the old PWA path. Remove this file after the
// transition window ends and old clients have had time to clean up.
self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    (async () => {
      const cacheKeys = await caches.keys();
      await Promise.all(cacheKeys.map(cacheKey => caches.delete(cacheKey)));

      await self.clients.claim();
      await self.registration.unregister();

      const clients = await self.clients.matchAll({
        type: 'window',
        includeUncontrolled: true,
      });

      for (const client of clients) {
        client.navigate(client.url);
      }
    })()
  );
});
