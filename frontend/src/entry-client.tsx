// frontend/src/entry-client.tsx
//
// Client-side entrypoint.
// Hydrates (or mounts) the React tree after SSR HTML is delivered.
// This is the ONLY file allowed to import browser-only code at the top level.

import { createRoot, hydrateRoot } from 'react-dom/client';
import { QueryClient } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrowserRouter } from 'react-router-dom';
import './i18n.client';
import i18n from './i18n.client';
import { setLanguageGetter } from './api/api';
import { initClientServices } from './utils/initClientServices';
import AppShell from './AppShell';
import App from './App';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// Wire language getter so axios interceptor reads live i18n language
setLanguageGetter(() => i18n.language || 'en');

// Invalidate all queries on language change so server-translated data is re-fetched
i18n.on('languageChanged', () => {
  queryClient.invalidateQueries();
});

// Initialise browser-only services (Sentry lazy-load + SW unregister)
initClientServices();

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Root element not found');

const tree = (
  <AppShell queryClient={queryClient} i18nInstance={i18n}>
    <BrowserRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <App />
    </BrowserRouter>
    {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
  </AppShell>
);

// Use hydrateRoot when SSR HTML is present (Phase 2+), createRoot otherwise
if (rootElement.childElementCount > 0) {
  hydrateRoot(rootElement, tree);
} else {
  createRoot(rootElement).render(tree);
}
