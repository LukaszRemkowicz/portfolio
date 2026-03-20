import type { AxiosInstance } from 'axios';
import { api } from './api';
import { AppError, NotFoundError, ValidationError } from './errors';

type BffErrorPayload = {
  detail?: string;
  errors?: Record<string, string[]>;
  message?: string;
};

export const isBrowserDefaultClient = (client: AxiosInstance = api): boolean =>
  typeof window !== 'undefined' && client === api;

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
