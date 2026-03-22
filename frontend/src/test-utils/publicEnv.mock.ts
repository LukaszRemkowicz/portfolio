const SITE_DOMAIN = 'localhost';

export const publicEnv = Object.freeze({
  API_URL: 'http://localhost:8000',
  GA_TRACKING_ID: '',
  PROJECT_OWNER: 'Portfolio Owner',
  SITE_DOMAIN,
});

export function resolvePublicEnv(
  overrides: Partial<typeof publicEnv> = {}
): typeof publicEnv {
  return Object.freeze({
    ...publicEnv,
    ...overrides,
  });
}

export function replacePublicEnvPlaceholders(
  template: string,
  env: typeof publicEnv = publicEnv
): string {
  return template
    .replaceAll('__API_ORIGIN__', env.API_URL || '')
    .replaceAll('__GA_TRACKING_ID__', env.GA_TRACKING_ID || '')
    .replaceAll('__PROJECT_OWNER__', env.PROJECT_OWNER || '')
    .replaceAll('__SITE_DOMAIN__', env.SITE_DOMAIN || '');
}
