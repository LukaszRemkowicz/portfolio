export const API_BASE_URL =
  (typeof window !== 'undefined' &&
    (window as unknown as { env?: { API_URL?: string } }).env?.API_URL) ||
  (typeof window !== 'undefined' &&
    (window as unknown as { env?: { API_URL?: string } }).env?.API_URL) ||
  (() => {
    try {
      return process.env.API_URL;
    } catch {
      return undefined;
    }
  })();

if (!API_BASE_URL) {
  throw new Error('API_URL is not defined');
}

export const API_V1 = '/v1';

export const APP_ROUTES = {
  HOME: '/',
  ASTROPHOTOGRAPHY: '/astrophotography',
  PROGRAMMING: '/programming',
  CONTACT: '/contact',
  TRAVEL_HIGHLIGHTS: '/travel-highlights',
};

export const DEFAULT_TRAVEL_IMAGE =
  'https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3?q=80&w=1000&auto=format&fit=crop';
