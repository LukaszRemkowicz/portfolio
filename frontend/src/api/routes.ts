import { ApiRoutes } from '../types';

// API Base URLs - Injected via Webpack DefinePlugin
export const API_BASE_URL: string =
  typeof process !== 'undefined' && process.env && process.env.API_URL
    ? process.env.API_URL
    : 'https://admin.portfolio.local';

// Define API_V1 for use in API_ROUTES
const API_V1 = '/api/v1';

export const API_ROUTES: ApiRoutes = {
  profile: '/api/v1/profile/',
  background: '/api/v1/background/',
  astroImages: '/api/v1/image/',
  astroImage: '/api/v1/image/:id/',
  contact: '/api/v1/contact/',
  whatsEnabled: `${API_V1}/whats-enabled/`,
  projects: '/api/v1/projects/',
  travelHighlights: '/api/v1/travel-highlights/',
  travelBySlug: `${API_V1}/travel/`,
  tags: '/api/v1/tags/',
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
