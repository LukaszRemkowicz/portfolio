// frontend/src/utils/env.ts

/**
 * Centralized environment variable access.
 * Abstracts the difference between development (vite) and production/test (process.env).
 */

export const getEnv = (key: string, defaultVal: string = ''): string => {
  // 1. Try process.env (Works in Jest natively, and Vite replaces it in build)
  try {
    if (typeof process !== 'undefined' && process.env) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const env = process.env as any;
      if (key === 'API_URL')
        return env.VITE_API_URL || env.API_URL || defaultVal;
      if (key === 'GA_TRACKING_ID')
        return env.VITE_GA_TRACKING_ID || env.GA_TRACKING_ID || defaultVal;
      if (key === 'ENABLE_GA')
        return env.VITE_ENABLE_GA || env.ENABLE_GA || defaultVal;
      if (key === 'NODE_ENV')
        return env.NODE_ENV || env.VITE_USER_NODE_ENV || defaultVal;
      return env[`VITE_${key}`] || env[key] || defaultVal;
    }
  } catch {
    // Ignore errors accessing import.meta
  }

  // 2. Fallback to import.meta.env (Vite native) - Wrapped in new Function to avoid Jest SyntaxError
  try {
    const metaEnv = new Function(
      'try { return import.meta.env; } catch { return undefined; }'
    )();
    if (metaEnv) {
      if (key === 'NODE_ENV') {
        return metaEnv.MODE || defaultVal;
      }
      const val = metaEnv[`VITE_${key}`] || metaEnv[key];
      return val !== undefined ? String(val) : defaultVal;
    }
  } catch {
    // Ignore access errors
  }

  return defaultVal;
};
