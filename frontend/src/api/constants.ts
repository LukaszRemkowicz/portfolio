// frontend/src/api/constants.ts
import { getSharedEnv } from '../utils/env.shared';

// getSharedEnv reads from process.env in Node (SSR) and VITE_* in the browser build.
// env.ts is NOT imported here — import.meta.env crashes in Node at module level.
export const API_BASE_URL = getSharedEnv('API_URL');

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
  // Corrected from /travel-highlights — matches App.tsx route definition
  TRAVEL_HIGHLIGHTS: '/travel',
  PRIVACY: '/privacy',
};

export const DEFAULT_TRAVEL_IMAGE = '/default-travel.jpg';
