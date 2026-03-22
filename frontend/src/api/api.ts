/**
 * Shared Axios client setup for frontend data access.
 *
 * This module owns the low-level HTTP transport concerns used by both SSR and
 * browser-side code:
 * - API base URL selection
 * - language query propagation
 * - SSR request logging
 * - backend error normalization
 * - SSR forwarding headers such as Host and X-Request-ID
 *
 * Higher-level route ownership lives in `services.ts` and `bff.ts`.
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import { API_BASE_URL } from './routes';
import { publicEnv } from '../../server/publicEnv.js';
import {
  NetworkError,
  NotFoundError,
  ServerError,
  UnauthorizedError,
  ValidationError,
  AppError,
} from './errors';

type SsrRequestMeta = {
  startedAt: number;
  requestId?: string;
};

/** Emit structured SSR -> backend transport logs for request tracing. */
function logSsrBackendRequest(info: Record<string, unknown>): void {
  console.log(
    JSON.stringify({
      ts: new Date().toISOString(),
      service: 'frontend-ssr',
      kind: 'ssr-backend',
      ...info,
    })
  );
}

// Language getter — safe to call in both the browser and the Node SSR runtime.
// On the client: lazily reads the language from the i18n singleton after it has
// been initialised. On the server: i18n is not initialised here, so it falls
// back to 'en' (server-side language is handled per-request in Phase 3+).
let _getLanguage: (() => string) | null = null;

/** Register the language getter used by request interceptors. */
export function setLanguageGetter(getter: () => string): void {
  _getLanguage = getter;
}

/** Read the current language without depending directly on i18n at import time. */
function getCurrentLanguage(): string {
  return _getLanguage?.() ?? 'en';
}

/**
 * Attach the request interceptor that adds the language parameter and records
 * SSR timing metadata used by the response logger.
 */
function attachLanguageInterceptor(
  client: AxiosInstance,
  getLanguage: () => string
) {
  client.interceptors.request.use(config => {
    if (typeof window === 'undefined') {
      (
        config as typeof config & {
          metadata?: SsrRequestMeta;
        }
      ).metadata = {
        startedAt: Date.now(),
        requestId:
          typeof config.headers?.['X-Request-ID'] === 'string'
            ? config.headers['X-Request-ID']
            : undefined,
      };
    }

    const lang = getLanguage();
    const shortLang = lang.split('-')[0];

    config.params = {
      ...config.params,
      lang: shortLang,
    };

    return config;
  });
}

/**
 * Attach the response interceptor that logs SSR backend requests and converts
 * Axios/network failures into project-specific error types.
 */
function attachErrorInterceptor(client: AxiosInstance) {
  client.interceptors.response.use(
    response => {
      if (typeof window === 'undefined') {
        const config = response.config as typeof response.config & {
          metadata?: SsrRequestMeta;
        };
        const durationMs = config.metadata
          ? Date.now() - config.metadata.startedAt
          : undefined;

        logSsrBackendRequest({
          method: (response.config.method || 'GET').toUpperCase(),
          url: response.config.url || '',
          base_url: response.config.baseURL || '',
          status: response.status,
          duration_ms: durationMs,
          request_id: config.metadata?.requestId,
        });
      }

      return response;
    },
    (error: AxiosError) => {
      if (typeof window === 'undefined') {
        const config = error.config as typeof error.config & {
          metadata?: SsrRequestMeta;
        };
        const durationMs = config?.metadata
          ? Date.now() - config.metadata.startedAt
          : undefined;

        logSsrBackendRequest({
          method: (config?.method || 'GET').toUpperCase(),
          url: config?.url || '',
          base_url: config?.baseURL || '',
          status: error.response?.status || 0,
          duration_ms: durationMs,
          request_id: config?.metadata?.requestId,
          error: error.code || error.message || 'unknown',
        });
      }

      if (!error.response) {
        // Network error (no response received)
        throw new NetworkError(undefined, error);
      }

      const { status, data } = error.response;
      const errorData = data as {
        errors?: Record<string, string[]>;
        message?: string;
        detail?: string;
      };

      switch (status) {
        case 400:
          throw new ValidationError(
            errorData?.errors || {},
            errorData?.message || errorData?.detail || 'Validation failed.',
            error
          );
        case 401:
        case 403:
          throw new UnauthorizedError(undefined, status, error);
        case 404:
          throw new NotFoundError(undefined, error);
        case 500:
        case 501:
        case 502:
        case 503:
        case 504:
          throw new ServerError(undefined, status, error);
        default:
          throw new AppError(
            errorData?.message ||
              errorData?.detail ||
              'An unexpected error occurred.',
            status,
            error
          );
      }
    }
  );
}

/**
 * Create a configured Axios client for either browser or SSR usage.
 *
 * On the server this also forwards the public site host and request ID to the
 * backend so generated URLs and request tracing stay aligned with the incoming
 * request.
 */
export function createApiClient(
  getLanguage: () => string,
  requestOrigin?: string,
  requestId?: string
): AxiosInstance {
  const defaultHeaders: Record<string, string> = {};

  if (typeof window === 'undefined') {
    try {
      const publicSiteUrl = requestOrigin
        ? new URL(requestOrigin)
        : new URL(`https://${publicEnv.SITE_DOMAIN}`);

      defaultHeaders.Host = publicSiteUrl.host;
      defaultHeaders['X-Forwarded-Host'] = publicSiteUrl.host;
      defaultHeaders['X-Forwarded-Proto'] = publicSiteUrl.protocol.replace(
        ':',
        ''
      );
      if (requestId) {
        defaultHeaders['X-Request-ID'] = requestId;
      }
    } catch {
      // Ignore malformed public API URLs and fall back to transport defaults.
    }
  }

  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: defaultHeaders,
  });

  attachLanguageInterceptor(client, getLanguage);
  attachErrorInterceptor(client);

  return client;
}

/** Default shared client used by browser code and most SSR service calls. */
export const api: AxiosInstance = createApiClient(getCurrentLanguage);
