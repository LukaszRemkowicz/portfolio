import React from 'react';
import { PassThrough } from 'node:stream';

const mockCreateApiClient: jest.Mock = jest.fn(() => 'mock-client');
const mockFetchSettings: jest.Mock = jest.fn(async () => ({ theme: 'dark' }));
const mockFetchProfile: jest.Mock = jest.fn(async () => ({
  first_name: 'Lukasz',
}));
const mockFetchBackground: jest.Mock = jest.fn(async () => '/background.webp');
const mockFetchTravelHighlights: jest.Mock = jest.fn(async () => []);
const mockFetchLatestAstroImages: jest.Mock = jest.fn(async () => []);
const mockFetchCategories: jest.Mock = jest.fn(async () => []);
const mockFetchTags: jest.Mock = jest.fn(async () => []);
const mockFetchAstroImages: jest.Mock = jest.fn(async () => []);
const mockFetchTravelHighlightDetail: jest.Mock = jest.fn(async () => ({
  title: 'Tatras',
}));
const mockCachedShellLoaderFactory: jest.Mock = jest.fn(
  () =>
    async (
      resourceConfig: { resource: string },
      loader: () => Promise<unknown>
    ) =>
      loader()
);

jest.mock('react-dom/server', () => ({
  renderToPipeableStream: (
    _element: React.ReactElement,
    options: {
      onAllReady?: () => void;
      onShellReady?: () => void;
      onShellError?: (error: Error) => void;
    }
  ) => ({
    abort: jest.fn(),
    pipe(destination: NodeJS.WritableStream) {
      destination.write('<div data-testid="ssr-app">SSR App</div>');
      destination.end();
    },
    ...(options.onAllReady
      ? (() => {
          queueMicrotask(() => options.onAllReady?.());
          return {};
        })()
      : {}),
    ...(options.onShellReady
      ? (() => {
          queueMicrotask(() => options.onShellReady?.());
          return {};
        })()
      : {}),
    ...(options.onShellError
      ? {
          onShellError: options.onShellError,
        }
      : {}),
  }),
}));

jest.mock('../App', () => ({
  __esModule: true,
  default: () => <div data-testid='ssr-app'>SSR App</div>,
}));

jest.mock('../AppShell', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../api/api', () => ({
  createApiClient: (
    languageGetter?: unknown,
    requestOrigin?: unknown,
    requestId?: unknown
  ) => mockCreateApiClient(languageGetter, requestOrigin, requestId),
}));

jest.mock('../api/services', () => ({
  fetchSettings: (client?: unknown) => mockFetchSettings(client),
  fetchProfile: (client?: unknown) => mockFetchProfile(client),
  fetchBackground: (client?: unknown) => mockFetchBackground(client),
  fetchTravelHighlights: (client?: unknown) =>
    mockFetchTravelHighlights(client),
  fetchLatestAstroImages: (client?: unknown) =>
    mockFetchLatestAstroImages(client),
  fetchCategories: (client?: unknown) => mockFetchCategories(client),
  fetchTags: (filter?: unknown, client?: unknown) =>
    mockFetchTags(filter, client),
  fetchAstroImages: (params?: unknown, client?: unknown) =>
    mockFetchAstroImages(params, client),
}));

jest.mock('../hooks/useTravelHighlightDetail', () => ({
  fetchTravelHighlightDetail: (params?: unknown) =>
    mockFetchTravelHighlightDetail(params),
}));

jest.mock('../i18n.server', () => ({
  createServerI18n: jest.fn(async (language: string) => ({
    language,
    resolvedLanguage: language,
  })),
}));

jest.mock('../../server/views/shell.js', () => ({
  SHELL_RESOURCES: {
    settings: { resource: 'settings', tags: ['settings'] },
    profile: { resource: 'profile', tags: ['profile'] },
    background: { resource: 'background', tags: ['background'] },
    travelHighlights: {
      resource: 'travel-highlights',
      tags: ['travel-highlights'],
    },
    latestAstroImages: {
      resource: 'latest-astro-images',
      tags: ['latest-astro-images'],
    },
  },
  getCachedShellLoader: (language?: unknown, requestOrigin?: unknown) =>
    mockCachedShellLoaderFactory(language, requestOrigin),
}));

import { render, renderStream } from '../entry-server';

async function consumeStream(stream: PassThrough): Promise<string> {
  let html = '';

  await new Promise<void>((resolve, reject) => {
    stream.on('data', chunk => {
      html += chunk.toString();
    });
    stream.on('end', resolve);
    stream.on('error', reject);
  });

  return html;
}

describe('SSR entry server', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('prefetches shared shell data for the homepage', async () => {
    const result = await render('/', 'pl', 'https://portfolio.local', 'req-1');

    expect(result.language).toBe('pl');
    expect(result.html).toContain('SSR App');
    expect(mockCreateApiClient).toHaveBeenCalledWith(
      expect.any(Function),
      'https://portfolio.local',
      'req-1'
    );
    expect(mockFetchSettings).toHaveBeenCalledWith('mock-client');
    expect(mockFetchProfile).toHaveBeenCalledWith('mock-client');
    expect(mockFetchBackground).toHaveBeenCalledWith('mock-client');
    expect(mockFetchTravelHighlights).toHaveBeenCalledWith('mock-client');
    expect(mockFetchLatestAstroImages).toHaveBeenCalledWith('mock-client');
    expect(mockFetchTravelHighlightDetail).not.toHaveBeenCalled();
    expect(mockFetchCategories).not.toHaveBeenCalled();
    expect(mockFetchTags).not.toHaveBeenCalled();
    expect(mockFetchAstroImages).not.toHaveBeenCalled();
    expect(mockCachedShellLoaderFactory).toHaveBeenCalledWith(
      'pl',
      'https://portfolio.local'
    );
  });

  it('prefetches travel detail data for travel routes', async () => {
    await render(
      '/travel/poland/tatras/dec2025',
      'en',
      'https://portfolio.local',
      'req-travel'
    );

    expect(mockFetchTravelHighlightDetail).toHaveBeenCalledWith({
      countrySlug: 'poland',
      placeSlug: 'tatras',
      dateSlug: 'dec2025',
      client: 'mock-client',
    });
  });

  it('prefetches gallery dependencies for astrophotography routes', async () => {
    await render(
      '/astrophotography?filter=landscape&tag=moon',
      'en',
      'https://portfolio.local',
      'req-gallery'
    );

    expect(mockFetchCategories).toHaveBeenCalledWith('mock-client');
    expect(mockFetchTags).toHaveBeenCalledWith('landscape', 'mock-client');
    expect(mockFetchAstroImages).toHaveBeenCalledWith(
      {
        filter: 'landscape',
        tag: 'moon',
      },
      'mock-client'
    );
  });

  it('streams rendered HTML', async () => {
    const result = await renderStream(
      '/',
      'en',
      'https://portfolio.local',
      'req-stream'
    );

    const html = await consumeStream(result.stream);

    expect(result.language).toBe('en');
    expect(typeof result.abort).toBe('function');
    expect(html).toContain('SSR App');
  });
});
