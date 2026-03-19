// frontend/src/utils/env.shared.ts
//
// Runtime-safe environment variable resolver.
// Works in both the Vite client build (import.meta.env) and
// the Node SSR runtime (process.env).

export const getSharedEnv = (key: string, fallback = ''): string => {
  // Node SSR runtime: process.env uses the unprefixed key (e.g. API_URL)
  if (typeof process !== 'undefined' && process.env[key]) {
    return process.env[key] as string;
  }

  // Vite client build: variables are prefixed with VITE_ and statically replaced.
  // We read via a dynamic path to avoid crashing in Node where import.meta.env
  // is undefined at runtime.
  try {
    const viteEnv = (import.meta as { env?: Record<string, string> }).env;
    const viteKey = `VITE_${key}`;
    return viteEnv?.[viteKey] ?? fallback;
  } catch {
    return fallback;
  }
};
