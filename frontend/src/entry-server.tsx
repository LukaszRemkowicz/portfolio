// frontend/src/entry-server.tsx
//
// Server-side render function.
// Called by the Hono SSR server (Phase 2) for each request.
// Uses StaticRouter (react-router-dom v6) — no browser globals.

import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import { QueryClient } from '@tanstack/react-query';
import type { HelmetServerState } from 'react-helmet-async';
import AppShell from './AppShell';
import App from './App';

export interface RenderResult {
  html: string;
  helmetContext: { helmet?: HelmetServerState };
}

export async function render(url: string): Promise<RenderResult> {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        // On the server, never refetch — data is prefetched explicitly (Phase 3)
        staleTime: Infinity,
      },
    },
  });

  // Use i18n.server.ts for per-request initialisation (Phase 4).
  // For now, import the shared singleton which is set up in i18n.server.ts.
  // We import lazily to avoid the singleton being cached across requests.
  const { createServerI18n } = await import('./i18n.server');
  const i18nInstance = await createServerI18n('en');

  const helmetContext: { helmet?: HelmetServerState } = {};

  const html = renderToString(
    <AppShell
      queryClient={queryClient}
      i18nInstance={i18nInstance}
      helmetContext={helmetContext}
    >
      <StaticRouter location={url}>
        <App />
      </StaticRouter>
    </AppShell>
  );

  return { html, helmetContext };
}
