// frontend/src/utils/env.ts

/**
 * Adding a variable here automatically types it globally.
 */
export interface EnvSchema {
  API_URL: string;
  GA_TRACKING_ID: string;
  ENABLE_GA: string;
  SENTRY_DSN_FE: string;
  ENVIRONMENT: string;
  NODE_ENV: string;
}

/**
 * Derived type that maps EnvSchema keys to their Vite-prefixed equivalents.
 * This drives the global ImportMetaEnv type.
 */
export type ViteMappedEnv = {
  [K in keyof EnvSchema as K extends 'NODE_ENV' ? 'MODE' : `VITE_${K}`]: string;
};

/**
 * Static assignment required by Vite to enable build-time replacement.
 */
const SETTINGS: EnvSchema = {
  API_URL: import.meta.env.VITE_API_URL,
  GA_TRACKING_ID: import.meta.env.VITE_GA_TRACKING_ID,
  ENABLE_GA: import.meta.env.VITE_ENABLE_GA,
  SENTRY_DSN_FE: import.meta.env.VITE_SENTRY_DSN_FE,
  ENVIRONMENT: import.meta.env.VITE_ENVIRONMENT || import.meta.env.MODE,
  NODE_ENV: import.meta.env.MODE,
};

/**
 * Safely access environment variables with type support.
 */
export const getEnv = (key: keyof EnvSchema, fallback: string = ''): string => {
  try {
    if (typeof window !== 'undefined') {
      const runtimeValue = window.__PUBLIC_ENV__?.[key];
      if (runtimeValue) {
        return runtimeValue;
      }
    }
    return SETTINGS[key] || fallback;
  } catch {
    return fallback;
  }
};
