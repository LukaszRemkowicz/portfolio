/**
 * Registers the service worker for the application.
 *
 * This function handles the service worker lifecycle:
 * 1. Only runs in production environments to avoid HMR interference.
 * 2. Checks browser support for Service Workers.
 * 3. Registers /service-worker.js after the window has fully loaded.
 * 4. Monitors for background updates and handles precaching states.
 *    - Logs when content is first cached for offline use.
 *    - Logs when new content is available but waiting for a refresh.
 */
export function register() {
  if (process.env.NODE_ENV === 'production' && 'serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      const swUrl = '/service-worker.js';
      navigator.serviceWorker
        .register(swUrl)
        .then(registration => {
          registration.onupdatefound = () => {
            const installingWorker = registration.installing;
            if (installingWorker == null) {
              return;
            }
            installingWorker.onstatechange = () => {
              if (installingWorker.state === 'installed') {
                if (navigator.serviceWorker.controller) {
                  // At this point, the updated precached content has been fetched,
                  // but the previous service worker will still serve the older
                  // content until all client tabs are closed.
                  console.log('New content is available; please refresh.');
                } else {
                  // At this point, everything has been precached.
                  // It's the perfect time to display a
                  // "Content is cached for offline use." message.
                  console.log('Content is cached for offline use.');
                }
              }
            };
          };
        })
        .catch(error => {
          console.error('Error during service worker registration:', error);
        });
    });
  }
}

/**
 * Unregisters any active service worker registration.
 *
 * Useful for cleanup or forcing the browser to stop using a previously
 * installed service worker for the current domain.
 * Waits for the service worker to be 'ready' before calling unregister().
 */
export function unregister() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then(registration => {
        registration.unregister();
      })
      .catch(error => {
        console.error(error.message);
      });
  }
}
