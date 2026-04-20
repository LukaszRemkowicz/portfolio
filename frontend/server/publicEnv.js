/**
 * Public environment helpers shared by the frontend server and browser runtime.
 *
 * These helpers define the frontend's public configuration contract and handle
 * reading that data from the appropriate source:
 *
 * - `window.__PUBLIC_ENV__` in the browser
 * - `process.env` on the server
 * - `import.meta.env` during Vite build time
 *
 * The same module also owns HTML placeholder replacement so public metadata
 * such as `SITE_DOMAIN` and `PROJECT_OWNER` stay defined in one place.
 */

const TEMPLATE_PLACEHOLDERS = {
  API_URL: '__API_ORIGIN__',
  GA_TRACKING_ID: '__GA_TRACKING_ID__',
  ENABLE_GA: '__ENABLE_GA__',
  PROJECT_OWNER: '__PROJECT_OWNER__',
  SITE_DOMAIN: '__SITE_DOMAIN__',
};

/**
 * Read runtime-injected public env from the browser when available.
 */
function getWindowEnv() {
  if (typeof window === 'undefined') {
    return null;
  }

  return window.__PUBLIC_ENV__ || null;
}

/**
 * Read a public env key from Node `process.env`.
 */
function readProcessEnv(key) {
  if (typeof process === 'undefined') {
    return '';
  }

  return process.env?.[key] || '';
}

/**
 * Read a public env key from Vite build-time environment variables.
 */
function readViteEnv(key) {
  try {
    const viteEnv = Function('return import.meta?.env')();
    return viteEnv?.[`VITE_${key}`] || '';
  } catch {
    return '';
  }
}

/**
 * Resolve a public env key from browser, process, or Vite env sources.
 */
function readPublicEnv(key, fallback = '') {
  return (
    getWindowEnv()?.[key] || readProcessEnv(key) || readViteEnv(key) || fallback
  );
}

/**
 * Build the frontend public env object, optionally applying explicit overrides.
 */
function createPublicEnv(overrides = {}) {
  const SITE_DOMAIN =
    overrides.SITE_DOMAIN ||
    readPublicEnv(
      'SITE_DOMAIN',
      typeof window !== 'undefined' ? window.location.host : 'localhost'
    );

  return {
    API_URL:
      overrides.API_URL ||
      readPublicEnv('API_URL', `https://api.${SITE_DOMAIN}`),
    GA_TRACKING_ID:
      overrides.GA_TRACKING_ID || readPublicEnv('GA_TRACKING_ID', ''),
    ENABLE_GA: overrides.ENABLE_GA || readPublicEnv('ENABLE_GA', 'false'),
    SENTRY_DSN_FE:
      overrides.SENTRY_DSN_FE || readPublicEnv('SENTRY_DSN_FE', ''),
    ENVIRONMENT:
      overrides.ENVIRONMENT || readPublicEnv('ENVIRONMENT', 'development'),
    PROJECT_OWNER:
      overrides.PROJECT_OWNER ||
      readPublicEnv('PROJECT_OWNER', 'Portfolio Owner'),
    SITE_DOMAIN,
  };
}

export const publicEnv = Object.freeze(createPublicEnv());

/**
 * Create a request-aware public env snapshot without mutating the shared base env.
 */
export function resolvePublicEnv(overrides = {}) {
  return Object.freeze(createPublicEnv(overrides));
}

/**
 * Replace HTML template placeholders with public env values.
 */
export function replacePublicEnvPlaceholders(template, env = publicEnv) {
  return Object.entries(TEMPLATE_PLACEHOLDERS).reduce(
    (output, [key, placeholder]) => {
      return output.replaceAll(placeholder, env[key] || '');
    },
    template
  );
}
