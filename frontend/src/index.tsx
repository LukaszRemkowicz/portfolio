// frontend/src/index.tsx
import { createRoot } from 'react-dom/client';
import * as Sentry from '@sentry/react';
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

// Initialize Sentry
const sentryDsn = getEnv('SENTRY_DSN_FE');
if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    tracesSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    environment: getEnv('ENVIRONMENT', 'development'),
  });
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
