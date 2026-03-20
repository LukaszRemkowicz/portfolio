/**
 * Browser-side helpers for frontend-owned transport endpoints.
 *
 * These helpers are used when the browser should talk to the frontend server
 * instead of calling backend `/v1/*` routes directly. SSR code should continue
 * to use the backend client directly and avoid looping through the BFF layer.
 */
import type { AxiosInstance } from 'axios';
import { api } from './api';
import { AppError, NotFoundError, ValidationError } from './errors';

type BffErrorPayload = {
  detail?: string;
  errors?: Record<string, string[]>;
  message?: string;
};

/** Detect the default browser transport path: browser runtime + shared API client. */
export const isBrowserDefaultClient = (client: AxiosInstance = api): boolean =>
  typeof window !== 'undefined' && client === api;

/** Translate frontend BFF error payloads into the same app error types as Axios calls. */
const throwBffError = (
  status: number,
  payload: BffErrorPayload | null | undefined
): never => {
  switch (status) {
    case 400:
      throw new ValidationError(
        payload?.errors || {},
        payload?.message || payload?.detail || 'Validation failed.'
      );
    case 401:
    case 403:
      throw new AppError(
        payload?.message || payload?.detail || 'Unauthorized access.',
        status
      );
    case 404:
      throw new NotFoundError();
    case 500:
    case 501:
    case 502:
    case 503:
    case 504:
      throw new AppError(
        payload?.message ||
          payload?.detail ||
          'Internal server error. Please try again later.',
        status
      );
    default:
      throw new AppError(
        payload?.message || payload?.detail || 'An unexpected error occurred.',
        status
      );
  }
};

/** Perform a browser-side GET against a frontend-owned JSON endpoint. */
export const fetchBffJson = async <TResponse>(
  url: string
): Promise<TResponse> => {
  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
    },
  });

  const payload = (await response.json().catch(() => null)) as TResponse &
    BffErrorPayload;

  if (!response.ok) {
    throwBffError(response.status, payload);
  }

  return payload;
};

/** Perform a browser-side POST against a frontend-owned JSON endpoint. */
export const postBffJson = async <TResponse>(
  url: string,
  body: unknown
): Promise<TResponse> => {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  const payload = (await response.json().catch(() => null)) as TResponse &
    BffErrorPayload;

  if (!response.ok) {
    throwBffError(response.status, payload);
  }

  return payload;
};
