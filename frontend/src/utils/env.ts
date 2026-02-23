// frontend/src/utils/env.ts

/**
 * Safely access environment variables via Vite's import.meta.env.
 * All env vars must be prefixed with VITE_ in .env files.
 */
const SETTINGS = {
  API_URL: import.meta.env.VITE_API_URL,
  GA_TRACKING_ID: import.meta.env.VITE_GA_TRACKING_ID,
  ENABLE_GA: import.meta.env.VITE_ENABLE_GA,
  SENTRY_DSN_FE: import.meta.env.VITE_SENTRY_DSN_FE,
  ENVIRONMENT: import.meta.env.VITE_ENVIRONMENT || import.meta.env.MODE,
  NODE_ENV: import.meta.env.MODE,
} as const;

export const getEnv = (
  key: keyof typeof SETTINGS,
  fallback: string = ''
): string => {
  try {
    return SETTINGS[key] || fallback;
  } catch {
    return fallback;
  }
};
