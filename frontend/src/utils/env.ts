// frontend/src/utils/env.ts

/**
 * Safely access environment variables via Vite's import.meta.env.
 * All env vars must be prefixed with VITE_ in .env files.
 */
export const getEnv = (key: string, fallback: string = ''): string => {
  try {
    switch (key) {
      case 'API_URL':
        return import.meta.env.VITE_API_URL || fallback;
      case 'GA_TRACKING_ID':
        return import.meta.env.VITE_GA_TRACKING_ID || fallback;
      case 'ENABLE_GA':
        return import.meta.env.VITE_ENABLE_GA || fallback;
      case 'NODE_ENV':
        return import.meta.env.MODE || fallback;
      case 'SENTRY_DSN_FE':
        return import.meta.env.VITE_SENTRY_DSN_FE || fallback;
      case 'ENVIRONMENT':
        return (
          import.meta.env.VITE_ENVIRONMENT || import.meta.env.MODE || fallback
        );
      default:
        return fallback;
    }
  } catch {
    return fallback;
  }
};
