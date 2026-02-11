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

// Centralized asset fallbacks
export const ASSETS = {
  logo: '/logo.png',
  defaultPortrait: '/portrait_default.png',
  underConstruction: '/underconstruction.jpg',
  galleryFallback: '/startrails.jpeg',
};

// Helper function to get full media URL
export const getMediaUrl = (path: string | null | undefined): string | null => {
  if (!path) return null;

  // If the path is already an absolute URL, return it as-is
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  // Ensure we don't have double slashes for relative paths
  const cleanPath = path.startsWith('/') ? path.substring(1) : path;
  return `${API_BASE_URL}/${cleanPath}`;
};
