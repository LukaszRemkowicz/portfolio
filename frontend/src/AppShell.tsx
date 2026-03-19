// frontend/src/AppShell.tsx
//
// Shared provider shell — used by both entry-client.tsx and entry-server.tsx.
// Contains only providers that are safe on both server and client:
//   - QueryClientProvider  (TanStack Query)
//   - HelmetProvider       (react-helmet-async — SSR-safe with request-scoped context)
//   - I18nextProvider      (react-i18next)
//
// Does NOT include router — router is injected per entrypoint.
// Does NOT include analytics, consent state, or document-level event listeners.
// Those remain in App.tsx (client only) and are isolated in Phase 5.

import React from 'react';
import {
  DehydratedState,
  HydrationBoundary,
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import type { HelmetServerState } from 'react-helmet-async';
import { I18nextProvider } from 'react-i18next';
import type { i18n as I18nInstance } from 'i18next';
import { RequestOriginContext } from './context/RequestOriginContext';

interface AppShellProps {
  queryClient: QueryClient;
  i18nInstance: I18nInstance;
  helmetContext?: { helmet?: HelmetServerState };
  dehydratedState?: DehydratedState;
  requestOrigin?: string;
  children: React.ReactNode;
}

const AppShell: React.FC<AppShellProps> = ({
  queryClient,
  i18nInstance,
  helmetContext = {},
  dehydratedState,
  requestOrigin,
  children,
}) => {
  return (
    <QueryClientProvider client={queryClient}>
      <HelmetProvider context={helmetContext}>
        <I18nextProvider i18n={i18nInstance}>
          <RequestOriginContext.Provider value={requestOrigin ?? null}>
            <Helmet>
              <html
                lang={
                  i18nInstance.resolvedLanguage || i18nInstance.language || 'en'
                }
              />
            </Helmet>
            <HydrationBoundary state={dehydratedState}>
              {children}
            </HydrationBoundary>
          </RequestOriginContext.Provider>
        </I18nextProvider>
      </HelmetProvider>
    </QueryClientProvider>
  );
};

export default AppShell;
