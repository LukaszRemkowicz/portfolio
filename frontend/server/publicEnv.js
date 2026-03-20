const TEMPLATE_PLACEHOLDERS = {
  API_URL: '__API_ORIGIN__',
  GA_TRACKING_ID: '__GA_TRACKING_ID__',
  PROJECT_OWNER: '__PROJECT_OWNER__',
  SITE_DOMAIN: '__SITE_DOMAIN__',
};

function getWindowEnv() {
  if (typeof window === 'undefined') {
    return null;
  }

  return window.__PUBLIC_ENV__ || null;
}

function readProcessEnv(key) {
  if (typeof process === 'undefined') {
    return '';
  }

  return process.env?.[key] || '';
}

function readViteEnv(key) {
  try {
    const viteEnv = Function('return import.meta?.env')();
    return viteEnv?.[`VITE_${key}`] || '';
  } catch {
    return '';
  }
}

function readPublicEnv(key, fallback = '') {
  return (
    getWindowEnv()?.[key] || readProcessEnv(key) || readViteEnv(key) || fallback
  );
}

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
    PROJECT_OWNER:
      overrides.PROJECT_OWNER ||
      readPublicEnv('PROJECT_OWNER', 'Portfolio Owner'),
    SITE_DOMAIN,
  };
}

export const publicEnv = Object.freeze(createPublicEnv());

export function resolvePublicEnv(overrides = {}) {
  return Object.freeze(createPublicEnv(overrides));
}

export function replacePublicEnvPlaceholders(template, env = publicEnv) {
  return Object.entries(TEMPLATE_PLACEHOLDERS).reduce(
    (output, [key, placeholder]) => {
      return output.replaceAll(placeholder, env[key] || '');
    },
    template
  );
}
