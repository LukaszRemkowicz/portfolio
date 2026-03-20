import { ApiRoutes } from '../types';
import { API_BASE_URL, API_V1 } from './constants';

export { API_BASE_URL };

export const API_ROUTES: ApiRoutes = {
  profile: `${API_V1}/profile/`,
  background: `${API_V1}/background/`,
  astroImages: `${API_V1}/astroimages/`,
  contact: `${API_V1}/contact/`,
  settings: `${API_V1}/settings/`,
  projects: `${API_V1}/projects/`,
  travelHighlights: `${API_V1}/travel-highlights/`,
  travelBySlug: `${API_V1}/travel/`,
  tags: `${API_V1}/tags/`,
  categories: `${API_V1}/categories/`,
};

export const BFF_ROUTES = {
  contact: '/app/contact',
  images: '/app/images/',
  travelBySlug: '/app/travel/',
};

// Centralized asset fallbacks
export const ASSETS = {
  logo: '/logo.png',
  underConstruction: '/underconstruction.jpg',
  galleryFallback: '/startrails.jpeg',
};
