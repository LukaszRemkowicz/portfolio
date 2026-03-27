// frontend/src/utils/initClientServices.ts
//
// Browser-only startup work extracted from index.tsx.
// This file must NEVER be imported in any server (SSR) path.

import { getEnv } from './env';

function initSentry(dsn: string, environment: string): void {
  if (!dsn || ['development', 'dev'].includes(environment)) return;

  let isSentryLoaded = false;

  const loadSentry = () => {
    if (isSentryLoaded) return;
    isSentryLoaded = true;

    import('@sentry/react')
      .then(Sentry => {
        if (Sentry?.init) {
          Sentry.init({
            dsn,
            defaultIntegrations: false,
            integrations: Sentry.browserTracingIntegration
              ? [Sentry.browserTracingIntegration()]
              : [],
            tracesSampleRate: 0.1,
            environment,
          });
        }
      })
      .catch(err => console.warn('Sentry failed to load:', err));
  };

  const interactionEvents = [
    'scroll',
    'mousemove',
    'touchstart',
    'keydown',
  ] as const;

  const triggerSentry = () => {
    loadSentry();
    interactionEvents.forEach(e =>
      window.removeEventListener(e, triggerSentry)
    );
  };

  interactionEvents.forEach(e =>
    window.addEventListener(e, triggerSentry, { once: true, passive: true })
  );
}

export function initClientServices(): void {
  const sentryDsn = getEnv('SENTRY_DSN_FE');
  const environment = getEnv('ENVIRONMENT', 'development');

  initSentry(sentryDsn, environment);
}
