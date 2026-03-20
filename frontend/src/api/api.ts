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
};

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

export function setLanguageGetter(getter: () => string): void {
  _getLanguage = getter;
}

function getCurrentLanguage(): string {
  return _getLanguage?.() ?? 'en';
}

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

export function createApiClient(getLanguage: () => string): AxiosInstance {
  const defaultHeaders: Record<string, string> = {};

  if (typeof window === 'undefined') {
    try {
      const publicApiUrl = new URL(publicEnv.API_URL);
      defaultHeaders.Host = publicApiUrl.host;
      defaultHeaders['X-Forwarded-Host'] = publicApiUrl.host;
      defaultHeaders['X-Forwarded-Proto'] = publicApiUrl.protocol.replace(
        ':',
        ''
      );
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

export const api: AxiosInstance = createApiClient(getCurrentLanguage);
