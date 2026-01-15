import axios, { AxiosInstance, AxiosError } from "axios";
import { API_BASE_URL } from "./routes";
import {
  NetworkError,
  NotFoundError,
  ServerError,
  UnauthorizedError,
  ValidationError,
  AppError,
} from "./errors";

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (!error.response) {
      // Network error (no response received)
      throw new NetworkError(undefined, error);
    }

    const { status, data } = error.response;

    switch (status) {
      case 400:
        throw new ValidationError(
          (data as any)?.errors || {},
          (data as any)?.message || "Validation failed.",
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
          (data as any)?.message || "An unexpected error occurred.",
          status,
          error
        );
    }
  }
);
