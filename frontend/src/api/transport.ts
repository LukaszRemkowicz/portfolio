import type { AxiosInstance, AxiosResponse } from 'axios';
import { api } from './api';
import { fetchBffJson, isBrowserDefaultClient, postBffJson } from './bff';

type RouteTargets = {
  browser: string;
  server: string;
};

export type QueryValue = boolean | number | string | undefined;
export type QueryParams = Record<string, QueryValue>;

export type DataTransport = {
  __dataTransport: true;
  kind: 'browser' | 'server';
  get<T>(routes: RouteTargets, params?: QueryParams): Promise<T>;
  post<T>(routes: RouteTargets, body: unknown): Promise<T>;
};

/** Validate Axios responses and return the payload shape expected by callers. */
export const handleAxiosResponse = <T>(response: AxiosResponse<T>): T => {
  if (response && response.data !== undefined) {
    return response.data;
  }

  console.error('Invalid response structure:', response);
  throw new Error('Invalid response from server.');
};

const appendParams = (url: string, params?: QueryParams): string => {
  if (!params) {
    return url;
  }

  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) continue;
    search.set(key, String(value));
  }

  return search.size ? `${url}?${search.toString()}` : url;
};

export const browserTransport: DataTransport = {
  __dataTransport: true,
  kind: 'browser',
  async get<T>(routes: RouteTargets, params?: QueryParams) {
    return fetchBffJson<T>(appendParams(routes.browser, params));
  },
  async post<T>(routes: RouteTargets, body: unknown) {
    return postBffJson<T>(routes.browser, body);
  },
};

export const createAxiosTransport = (
  client: AxiosInstance = api
): DataTransport => ({
  __dataTransport: true,
  kind: 'server',
  async get<T>(routes: RouteTargets, params?: QueryParams) {
    const response =
      params && Object.keys(params).length > 0
        ? await client.get<T>(routes.server, { params })
        : await client.get<T>(routes.server);
    return handleAxiosResponse(response);
  },
  async post<T>(routes: RouteTargets, body: unknown) {
    const response = await client.post<T>(routes.server, body);
    return handleAxiosResponse(response);
  },
});

export const resolveDataTransport = (
  clientOrTransport: AxiosInstance | DataTransport = api
): DataTransport => {
  if (
    typeof clientOrTransport === 'object' &&
    clientOrTransport !== null &&
    '__dataTransport' in clientOrTransport
  ) {
    return clientOrTransport as DataTransport;
  }

  return isBrowserDefaultClient(clientOrTransport as AxiosInstance)
    ? browserTransport
    : createAxiosTransport(clientOrTransport as AxiosInstance);
};
