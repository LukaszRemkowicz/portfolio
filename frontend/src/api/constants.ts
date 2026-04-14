/**
 * Shared frontend API constants.
 *
 * This module resolves the correct API base URL for both SSR and browser
 * environments and keeps route-independent constants in one place.
 */
import { publicEnv } from '../../server/publicEnv.js';

const SSR_API_BASE_URL =
  typeof window === 'undefined' && typeof process !== 'undefined'
    ? (process.env.SSR_API_URL ?? '')
    : '';

const BROWSER_API_BASE_URL =
  typeof window !== 'undefined'
    ? window.location.origin ||
      (publicEnv.SITE_DOMAIN ? `https://${publicEnv.SITE_DOMAIN}` : '')
    : '';

/** Public base URL used by API transport helpers in the current runtime context. */
export const API_BASE_URL =
  SSR_API_BASE_URL || BROWSER_API_BASE_URL || publicEnv.API_URL;

if (!API_BASE_URL) {
  console.warn(
    '[API] SITE_DOMAIN/API_URL/SSR_API_URL is not set. API calls will fail.'
  );
}

export const API_V1 = '/v1';

/** Public website routes used by the frontend application. */
export const APP_ROUTES = {
  HOME: '/',
  ASTROPHOTOGRAPHY: '/astrophotography',
  SHOP: '/shop',
  PROGRAMMING: '/programming',
  CONTACT: '/contact',
  // Corrected from /travel-highlights — matches App.tsx route definition
  TRAVEL_HIGHLIGHTS: '/travel',
  PRIVACY: '/privacy',
};

/** Fallback image used when travel content has no primary image available. */
export const DEFAULT_TRAVEL_IMAGE = '/landscape.webp';
