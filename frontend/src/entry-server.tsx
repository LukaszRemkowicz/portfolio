// frontend/src/entry-server.tsx
//
// Server-side render function.
// Called by the Hono SSR server (Phase 2) for each request.
// Uses StaticRouter (react-router-dom v6) — no browser globals.

import { renderToPipeableStream } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import { DehydratedState, dehydrate, QueryClient } from '@tanstack/react-query';
import { matchPath } from 'react-router-dom';
import type { HelmetServerState } from 'react-helmet-async';
import { PassThrough, Writable } from 'node:stream';
import AppShell from './AppShell';
import App from './App';
import { createApiClient } from './api/api';
import {
  getCachedShellLoader,
  SHELL_RESOURCES,
} from '../server/views/shell.js';
import {
  fetchAstroImages,
  fetchBackground,
  fetchCategories,
  fetchProfile,
  fetchSettings,
  fetchTags,
  fetchTravelHighlights,
  fetchLatestAstroImages,
} from './api/services';
import { ASTRO_GALLERY_PAGE_SIZE } from './hooks/useAstroImages';
import { fetchTravelHighlightDetail } from './hooks/useTravelHighlightDetail';
import { APP_ROUTES } from './api/constants';

export interface RenderResult {
  html: string;
  helmetContext: { helmet?: HelmetServerState };
  dehydratedState: DehydratedState;
  language: string;
}

export interface StreamRenderResult {
  stream: PassThrough;
  helmetContext: { helmet?: HelmetServerState };
  dehydratedState: DehydratedState;
  language: string;
  abort: () => void;
}

async function renderAppToString(element: React.ReactElement): Promise<string> {
  return new Promise((resolve, reject) => {
    let html = '';
    let settled = false;

    const writable = new Writable({
      write(chunk, _encoding, callback) {
        html += chunk.toString();
        callback();
      },
    });

    const timeout = setTimeout(() => {
      if (!settled) {
        settled = true;
        abort();
        reject(new Error('SSR render timed out while waiting for allReady.'));
      }
    }, 10000);

    writable.on('finish', () => {
      if (!settled) {
        settled = true;
        clearTimeout(timeout);
        resolve(html);
      }
    });

    writable.on('error', error => {
      if (!settled) {
        settled = true;
        clearTimeout(timeout);
        reject(error);
      }
    });

    const { abort, pipe } = renderToPipeableStream(element, {
      onAllReady() {
        pipe(writable);
      },
      onShellError(error) {
        if (!settled) {
          settled = true;
          clearTimeout(timeout);
          reject(error);
        }
      },
      onError(error) {
        console.error('[frontend-ssr] render error', error);
      },
    });
  });
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

async function prefetchInfiniteQuerySafely(
  queryClient: QueryClient,
  options: Parameters<QueryClient['prefetchInfiniteQuery']>[0]
) {
  try {
    await queryClient.prefetchInfiniteQuery(options);
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
  language: string,
  requestOrigin?: string,
  requestId?: string
) {
  const client = createApiClient(() => language, requestOrigin, requestId);
  const cachedShellQuery = getCachedShellLoader(language, requestOrigin);
  const requestUrl = new URL(url, 'http://frontend.local');
  const pathname = requestUrl.pathname;
  const searchParams = requestUrl.searchParams;
  const commonPrefetches = [
    prefetchQuerySafely(queryClient, {
      queryKey: ['settings'],
      queryFn: () =>
        cachedShellQuery(SHELL_RESOURCES.settings, () => fetchSettings(client)),
    }),
    prefetchQuerySafely(queryClient, {
      queryKey: ['profile', language],
      queryFn: () =>
        cachedShellQuery(SHELL_RESOURCES.profile, () => fetchProfile(client)),
    }),
    prefetchQuerySafely(queryClient, {
      queryKey: ['background', language],
      queryFn: () =>
        cachedShellQuery(SHELL_RESOURCES.background, () =>
          fetchBackground(client)
        ),
    }),
    prefetchQuerySafely(queryClient, {
      queryKey: ['travel-highlights', language],
      queryFn: () =>
        cachedShellQuery(SHELL_RESOURCES.travelHighlights, () =>
          fetchTravelHighlights(client)
        ),
    }),
    prefetchQuerySafely(queryClient, {
      queryKey: ['latest-astro-images', language],
      queryFn: () =>
        cachedShellQuery(SHELL_RESOURCES.latestAstroImages, () =>
          fetchLatestAstroImages(client)
        ),
    }),
  ];

  if (pathname === APP_ROUTES.HOME) {
    await Promise.all([...commonPrefetches]);
    return;
  }

  const travelMatch = matchPath(
    `${APP_ROUTES.TRAVEL_HIGHLIGHTS}/:countrySlug/:placeSlug/:dateSlug`,
    pathname
  );
  if (travelMatch?.params.countrySlug) {
    const { countrySlug, placeSlug, dateSlug } = travelMatch.params;
    await Promise.all([
      ...commonPrefetches,
      prefetchQuerySafely(queryClient, {
        queryKey: ['travel-highlight', countrySlug, placeSlug, dateSlug],
        queryFn: () =>
          fetchTravelHighlightDetail({
            countrySlug: countrySlug!,
            placeSlug: placeSlug!,
            dateSlug: dateSlug!,
            clientOrTransport: client,
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
      ...commonPrefetches,
      prefetchQuerySafely(queryClient, {
        queryKey: ['categories'],
        queryFn: () => fetchCategories(client),
      }),
      prefetchQuerySafely(queryClient, {
        queryKey: ['tags', language, selectedFilter],
        queryFn: () => fetchTags({ filter: selectedFilter }, client),
      }),
      prefetchInfiniteQuerySafely(queryClient, {
        queryKey: ['astro-images', language, imageParams],
        initialPageParam: 1,
        queryFn: ({ pageParam }) =>
          fetchAstroImages(
            {
              ...imageParams,
              page: Number(pageParam),
              limit: ASTRO_GALLERY_PAGE_SIZE,
            },
            client
          ),
      }),
    ]);
    return;
  }

  await Promise.all(commonPrefetches);
}

interface PreparedRenderContext {
  element: React.ReactElement;
  helmetContext: { helmet?: HelmetServerState };
  dehydratedState: DehydratedState;
  language: string;
}

async function prepareRenderContext(
  url: string,
  acceptLanguage = 'en',
  requestOrigin?: string,
  requestId?: string
): Promise<PreparedRenderContext> {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        // Server-side QueryClient instances are request-scoped and discarded
        // after render. We dehydrate their data into HTML and the browser uses
        // its own QueryClient after hydration, so Infinity is intentional here.
        staleTime: Infinity,
      },
    },
  });

  const { createServerI18n } = await import('./i18n.server');
  const i18nInstance = await createServerI18n(acceptLanguage);

  await prefetchRouteQueries(
    queryClient,
    url,
    i18nInstance.language || 'en',
    requestOrigin,
    requestId
  );

  const helmetContext: { helmet?: HelmetServerState } = {};
  const dehydratedState = dehydrate(queryClient);

  return {
    element: (
      <AppShell
        queryClient={queryClient}
        i18nInstance={i18nInstance}
        helmetContext={helmetContext}
        dehydratedState={dehydratedState}
        requestOrigin={requestOrigin}
      >
        <StaticRouter location={url}>
          <App />
        </StaticRouter>
      </AppShell>
    ),
    helmetContext,
    dehydratedState,
    language: i18nInstance.resolvedLanguage || i18nInstance.language || 'en',
  };
}

export async function renderStream(
  url: string,
  acceptLanguage = 'en',
  requestOrigin?: string,
  requestId?: string
): Promise<StreamRenderResult> {
  const prepared = await prepareRenderContext(
    url,
    acceptLanguage,
    requestOrigin,
    requestId
  );

  return new Promise((resolve, reject) => {
    let settled = false;
    const stream = new PassThrough();

    const timeout = setTimeout(() => {
      if (!settled) {
        settled = true;
        abort();
        reject(new Error('SSR stream timed out while waiting for shellReady.'));
      }
    }, 10000);

    stream.on('error', error => {
      if (!settled) {
        settled = true;
        clearTimeout(timeout);
        reject(error);
      }
    });

    const { abort, pipe } = renderToPipeableStream(prepared.element, {
      onShellReady() {
        if (settled) {
          return;
        }

        settled = true;
        clearTimeout(timeout);
        pipe(stream);
        resolve({
          ...prepared,
          stream,
          abort,
        });
      },
      onShellError(error) {
        if (!settled) {
          settled = true;
          clearTimeout(timeout);
          reject(error);
        }
      },
      onError(error) {
        console.error('[frontend-ssr] render error', error);
      },
    });
  });
}

export async function render(
  url: string,
  acceptLanguage = 'en',
  requestOrigin?: string,
  requestId?: string
): Promise<RenderResult> {
  const prepared = await prepareRenderContext(
    url,
    acceptLanguage,
    requestOrigin,
    requestId
  );
  const html = await renderAppToString(prepared.element);

  return {
    html,
    helmetContext: prepared.helmetContext,
    dehydratedState: prepared.dehydratedState,
    language: prepared.language,
  };
}
