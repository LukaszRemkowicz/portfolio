import { api } from '../api/api';
import { AppError, ValidationError, NetworkError } from '../api/errors';
import { AxiosError, InternalAxiosRequestConfig } from 'axios';

// Helper to create a mocked AxiosError
const createAxiosError = (status: number, data: unknown): AxiosError => {
  return {
    isAxiosError: true,
    name: 'AxiosError',
    message: 'Request failed',
    config: {} as InternalAxiosRequestConfig,
    response: {
      status,
      data,
      statusText: 'Error',
      headers: {},
      config: {} as InternalAxiosRequestConfig,
    },
    toJSON: () => ({}),
  } as AxiosError;
};

describe('API Interceptor', () => {
  let errorHandler: (error: AxiosError) => unknown;

  beforeAll(() => {
    // Extract the error handler from the interceptor
    // @ts-ignore - accessing private/internal interceptor storage for testing
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const interceptor = (api.interceptors.response as any).handlers[0];
    errorHandler = interceptor.rejected;
  });

  it("extracts 'detail' from 400 Validation Errors", async () => {
    const error = createAxiosError(400, { detail: 'Invalid input provided.' });

    try {
      errorHandler(error);
    } catch (e: unknown) {
      expect(e).toBeInstanceOf(ValidationError);
      expect((e as ValidationError).message).toBe('Invalid input provided.');
    }
  });

  it("extracts 'detail' from 429 Throttling Errors", async () => {
    const error = createAxiosError(429, {
      detail: 'Too many messages. Wait 1 hour.',
    });

    try {
      errorHandler(error);
    } catch (e: unknown) {
      expect(e).toBeInstanceOf(AppError);
      expect((e as AppError).statusCode).toBe(429);
      expect((e as AppError).message).toBe('Too many messages. Wait 1 hour.');
    }
  });

  it("prefers 'message' over 'detail' if both exist", async () => {
    const error = createAxiosError(400, {
      message: 'Explicit message',
      detail: 'Hidden detail',
    });

    try {
      errorHandler(error);
    } catch (e: unknown) {
      expect((e as Error).message).toBe('Explicit message');
    }
  });

  it('handles network errors (no response)', async () => {
    const error = {
      isAxiosError: true,
      config: {},
      response: undefined,
    } as AxiosError;

    try {
      errorHandler(error);
    } catch (e: unknown) {
      expect(e).toBeInstanceOf(NetworkError);
    }
  });

  it('handles fallback for unknown status codes', async () => {
    const error = createAxiosError(418, {}); // I'm a teapot

    try {
      errorHandler(error);
    } catch (e: unknown) {
      expect(e).toBeInstanceOf(AppError);
      expect((e as AppError).statusCode).toBe(418);
      expect((e as AppError).message).toBe('An unexpected error occurred.');
    }
  });
});
