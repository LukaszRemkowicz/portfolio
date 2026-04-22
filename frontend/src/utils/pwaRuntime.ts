const STALE_CHUNK_RELOAD_KEY = 'portfolio:stale-chunk-reload';
const SW_UPDATE_RELOAD_KEY = 'portfolio:sw-update-reload';
const STALE_CHUNK_PATTERNS = [
  /Failed to fetch dynamically imported module/i,
  /Importing a module script failed/i,
  /ChunkLoadError/i,
  /Loading chunk [\w-]+ failed/i,
];

function matchesStaleChunkError(value: unknown): boolean {
  if (value instanceof Error) {
    return STALE_CHUNK_PATTERNS.some(
      pattern => pattern.test(value.message) || pattern.test(value.stack || '')
    );
  }

  if (typeof value === 'string') {
    return STALE_CHUNK_PATTERNS.some(pattern => pattern.test(value));
  }

  return false;
}

function triggerReloadOnce(storageKey: string): void {
  const currentUrl = window.location.href;

  if (sessionStorage.getItem(storageKey) === currentUrl) {
    return;
  }

  sessionStorage.setItem(storageKey, currentUrl);
  window.location.reload();
}

function installStaleChunkRecovery(): void {
  window.addEventListener(
    'error',
    event => {
      if (matchesStaleChunkError(event.error || event.message)) {
        triggerReloadOnce(STALE_CHUNK_RELOAD_KEY);
      }
    },
    true
  );

  window.addEventListener('unhandledrejection', event => {
    if (matchesStaleChunkError(event.reason)) {
      triggerReloadOnce(STALE_CHUNK_RELOAD_KEY);
    }
  });
}

async function enablePwaRuntime(): Promise<void> {
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    triggerReloadOnce(SW_UPDATE_RELOAD_KEY);
  });

  try {
    const registration =
      (await navigator.serviceWorker.getRegistration('/')) ||
      (await navigator.serviceWorker.register('/sw.js'));

    const activateUpdatedWorker = () => {
      sessionStorage.removeItem(SW_UPDATE_RELOAD_KEY);
      registration.waiting?.postMessage({ type: 'SKIP_WAITING' });
    };

    if (registration.waiting) {
      activateUpdatedWorker();
    }

    registration.addEventListener('updatefound', () => {
      const installingWorker = registration.installing;
      if (!installingWorker) {
        return;
      }

      installingWorker.addEventListener('statechange', () => {
        if (
          installingWorker.state === 'installed' &&
          navigator.serviceWorker.controller
        ) {
          activateUpdatedWorker();
        }
      });
    });

    void registration.update();
  } catch (error) {
    console.error('Failed to register service worker', error);
  }
}

function clearReloadGuardsOnSuccessfulLoad(): void {
  window.addEventListener('pageshow', () => {
    window.setTimeout(() => {
      sessionStorage.removeItem(STALE_CHUNK_RELOAD_KEY);
      sessionStorage.removeItem(SW_UPDATE_RELOAD_KEY);
    }, 10000);
  });
}

export function initPwaRuntime(environment: string): void {
  installStaleChunkRecovery();
  clearReloadGuardsOnSuccessfulLoad();

  if (['development', 'dev', 'local'].includes(environment)) {
    return;
  }

  if (!('serviceWorker' in navigator)) {
    return;
  }

  void enablePwaRuntime();
}
