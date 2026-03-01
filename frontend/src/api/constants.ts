// frontend/src/api/constants.ts
import { getEnv } from '../utils/env';

export const API_BASE_URL = getEnv('API_URL');

if (!API_BASE_URL) {
  console.warn(
    '[API] VITE_API_URL is not set. API calls will fail. ' +
      'Create frontend/.env with VITE_API_URL=https://api.your-domain.com'
  );
}

export const API_V1 = '/v1';

export const APP_ROUTES = {
  HOME: '/',
  ASTROPHOTOGRAPHY: '/astrophotography',
  PROGRAMMING: '/programming',
  CONTACT: '/contact',
  TRAVEL_HIGHLIGHTS: '/travel',
  PRIVACY: '/privacy',
};

export const DEFAULT_TRAVEL_IMAGE = '/default-travel.jpg';
