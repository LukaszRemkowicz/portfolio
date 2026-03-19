// frontend/src/entry-server.tsx
//
// Server-side render function.
// Called by the Hono SSR server (Phase 2) for each request.
// Uses StaticRouter (react-router-dom v6) — no browser globals.

import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import { DehydratedState, dehydrate, QueryClient } from '@tanstack/react-query';
import { matchPath } from 'react-router-dom';
import type { HelmetServerState } from 'react-helmet-async';
import AppShell from './AppShell';
import App from './App';
import { createApiClient } from './api/api';
import {
  fetchAstroImages,
  fetchBackground,
  fetchCategories,
  fetchProfile,
  fetchTags,
} from './api/services';
import { fetchTravelHighlightDetail } from './hooks/useTravelHighlightDetail';
import { APP_ROUTES } from './api/constants';

export interface RenderResult {
  html: string;
  helmetContext: { helmet?: HelmetServerState };
  dehydratedState: DehydratedState;
}

async function prefetchQuerySafely(
  queryClient: QueryClient,
  options: Parameters<QueryClient['prefetchQuery']>[0]
) {
  try {
    await queryClient.prefetchQuery(options);
  } catch (error) {
    console.warn('[frontend-ssr] prefetch failed', {
      queryKey: options.queryKey,
      error: error instanceof Error ? error.message : String(error),
    });
  }
}

async function prefetchRouteQueries(
  queryClient: QueryClient,
  url: string,
  language: string
) {
  const client = createApiClient(() => language);
  const requestUrl = new URL(url, 'http://frontend.local');
  const pathname = requestUrl.pathname;
  const searchParams = requestUrl.searchParams;

  if (pathname === APP_ROUTES.HOME) {
    await Promise.all([
      prefetchQuerySafely(queryClient, {
        queryKey: ['profile'],
        queryFn: () => fetchProfile(client),
      }),
      prefetchQuerySafely(queryClient, {
        queryKey: ['background'],
        queryFn: () => fetchBackground(client),
      }),
    ]);
    return;
  }

  const travelMatch = matchPath(
    `${APP_ROUTES.TRAVEL_HIGHLIGHTS}/:countrySlug/:placeSlug/:dateSlug`,
    pathname
  );
  if (travelMatch?.params.countrySlug) {
    const { countrySlug, placeSlug, dateSlug } = travelMatch.params;
    await Promise.all([
      prefetchQuerySafely(queryClient, {
        queryKey: ['background'],
        queryFn: () => fetchBackground(client),
      }),
      prefetchQuerySafely(queryClient, {
        queryKey: ['travel-highlight', countrySlug, placeSlug, dateSlug],
        queryFn: () =>
          fetchTravelHighlightDetail({
            countrySlug: countrySlug!,
            placeSlug: placeSlug!,
            dateSlug: dateSlug!,
            client,
          }),
      }),
    ]);
    return;
  }

  const astroMatch =
    pathname === APP_ROUTES.ASTROPHOTOGRAPHY ||
    matchPath(`${APP_ROUTES.ASTROPHOTOGRAPHY}/:slug`, pathname);
  if (astroMatch) {
    const selectedFilter = searchParams.get('filter') || undefined;
    const selectedTag = searchParams.get('tag') || undefined;
    const imageParams = {
      ...(selectedFilter ? { filter: selectedFilter } : {}),
      ...(selectedTag ? { tag: selectedTag } : {}),
    };

    await Promise.all([
      prefetchQuerySafely(queryClient, {
        queryKey: ['background'],
        queryFn: () => fetchBackground(client),
      }),
      prefetchQuerySafely(queryClient, {
        queryKey: ['categories'],
        queryFn: () => fetchCategories(client),
      }),
      prefetchQuerySafely(queryClient, {
        queryKey: ['tags', selectedFilter],
        queryFn: () => fetchTags(selectedFilter, client),
      }),
      prefetchQuerySafely(queryClient, {
        queryKey: ['astro-images', imageParams],
        queryFn: () => fetchAstroImages(imageParams, client),
      }),
    ]);
  }
}

export async function render(
  url: string,
  acceptLanguage = 'en'
): Promise<RenderResult> {
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
  const i18nInstance = await createServerI18n(acceptLanguage);

  await prefetchRouteQueries(queryClient, url, i18nInstance.language || 'en');

  const helmetContext: { helmet?: HelmetServerState } = {};
  const dehydratedState = dehydrate(queryClient);

  const html = renderToString(
    <AppShell
      queryClient={queryClient}
      i18nInstance={i18nInstance}
      helmetContext={helmetContext}
      dehydratedState={dehydratedState}
    >
      <StaticRouter location={url}>
        <App />
      </StaticRouter>
    </AppShell>
  );

  return { html, helmetContext, dehydratedState };
}
