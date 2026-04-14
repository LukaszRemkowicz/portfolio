/**
 * Central route definitions for frontend data access.
 *
 * `API_ROUTES` points at backend `/v1/*` resources.
 * `BFF_ROUTES` points at frontend-owned transport endpoints used by browser
 * code when requests should stay same-origin on `SITE_DOMAIN`.
 */
import { ApiRoutes } from '../types';
import { API_BASE_URL, API_V1 } from './constants';

export { API_BASE_URL };

/** Canonical backend API route table used by service-layer fetch helpers. */
export const API_ROUTES: ApiRoutes = {
  profile: `${API_V1}/profile/`,
  background: `${API_V1}/background/`,
  astroImages: `${API_V1}/astroimages/`,
  contact: `${API_V1}/contact/`,
  settings: `${API_V1}/settings/`,
  projects: `${API_V1}/projects/`,
  shop: `${API_V1}/shop/products/`,
  travelHighlights: `${API_V1}/travel-highlights/`,
  travelBySlug: `${API_V1}/travel/`,
  tags: `${API_V1}/tags/`,
  categories: `${API_V1}/categories/`,
};

/** Frontend-owned browser transport endpoints exposed by the SSR/BFF server. */
export const BFF_ROUTES = {
  contact: '/app/contact',
  images: '/app/images/',
  imageFiles: '/app/image-files/',
  profile: '/app/profile/',
  background: '/app/background/',
  astroImages: '/app/astroimages/',
  shop: '/app/shop/',
  settings: '/app/settings/',
  travelHighlights: '/app/travel-highlights/',
  tags: '/app/tags/',
  categories: '/app/categories/',
  travelBySlug: '/app/travel/',
};

/** Static asset fallbacks used when API-provided media is missing. */
export const ASSETS = {
  logo: '/logo.png',
  underConstruction: '/underconstruction.jpg',
  galleryFallback: '/startrails.jpeg',
};
