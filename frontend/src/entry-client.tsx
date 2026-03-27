// frontend/src/entry-client.tsx
//
// Client-side entrypoint.
// Hydrates (or mounts) the React tree after SSR HTML is delivered.
// This is the ONLY file allowed to import browser-only code at the top level.

import { startTransition } from 'react';
import { createRoot, hydrateRoot } from 'react-dom/client';
import { DehydratedState, QueryClient } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrowserRouter } from 'react-router-dom';
import './i18n.client';
import i18n from './i18n.client';
import { setLanguageGetter } from './api/api';
import { initClientServices } from './utils/initClientServices';
import { getEnv } from './utils/env';
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

type QueryStateWindow = Window &
  typeof globalThis & {
    __REACT_QUERY_STATE__?: DehydratedState;
  };

const dehydratedState = (window as QueryStateWindow).__REACT_QUERY_STATE__;

// Wire language getter so axios interceptor reads live i18n language
setLanguageGetter(() => i18n.language || 'en');

// Invalidate all queries on language change so server-translated data is re-fetched
i18n.on('languageChanged', () => {
  startTransition(() => {
    void queryClient.invalidateQueries();
  });
});

function bootstrapApp() {
  // Initialise browser-only services (Sentry lazy-load)
  initClientServices();

  const rootElement = document.getElementById('root');
  if (!rootElement) throw new Error('Root element not found');

  const environment = getEnv('ENVIRONMENT', getEnv('NODE_ENV', 'development'));
  // Local development prefers a clean client mount over hydration recovery noise.
  // Production-like environments should hydrate so SSR/client mismatches stay visible.
  const useClientRenderOnly = ['development', 'dev'].includes(environment);

  const tree = (
    <AppShell
      queryClient={queryClient}
      i18nInstance={i18n}
      dehydratedState={dehydratedState}
    >
      <BrowserRouter
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <App />
      </BrowserRouter>
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </AppShell>
  );

  if (rootElement.childElementCount > 0 && !useClientRenderOnly) {
    hydrateRoot(rootElement, tree);
  } else {
    createRoot(rootElement).render(tree);
  }
}

bootstrapApp();
