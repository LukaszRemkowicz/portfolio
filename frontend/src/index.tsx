import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import App from './App';
import './styles/global/index.css';
import './i18n';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';
import { getEnv } from './utils/env';
import i18n from './i18n';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found');
}
const sentryDsn = getEnv('SENTRY_DSN_FE');
const environment = getEnv('ENVIRONMENT', 'development');

if (sentryDsn && !['development', 'dev'].includes(environment)) {
  let isSentryLoaded = false;
  const initSentry = () => {
    if (isSentryLoaded) return;
    isSentryLoaded = true;
    import('@sentry/react')
      .then(Sentry => {
        if (Sentry && Sentry.init) {
          Sentry.init({
            dsn: sentryDsn,
            // Selective integrations for minimal impact
            defaultIntegrations: false,
            integrations: Sentry.browserTracingIntegration
              ? [Sentry.browserTracingIntegration()]
              : [],
            tracesSampleRate: 0.1,
            environment: environment,
          });
        }
      })
      .catch(err => console.warn('Sentry failed to load:', err));
  };

  // Wait for interaction to completely remove Sentry from page load trace
  const triggerSentry = () => {
    initSentry();
    ['scroll', 'mousemove', 'touchstart', 'keydown'].forEach(e =>
      window.removeEventListener(e, triggerSentry)
    );
  };

  ['scroll', 'mousemove', 'touchstart', 'keydown'].forEach(e =>
    window.addEventListener(e, triggerSentry, { once: true, passive: true })
  );

  // No fallback timeout to ensure it never affects critical page load metrics
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// Invalidate all queries when language changes so all data is refetched in new language
i18n.on('languageChanged', () => {
  queryClient.invalidateQueries();
});

const root = createRoot(rootElement);
root.render(
  <QueryClientProvider client={queryClient}>
    <App />
    {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
  </QueryClientProvider>
);

// Unregister service worker everywhere to rely on Nginx caching
serviceWorkerRegistration.unregister();
