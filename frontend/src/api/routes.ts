import { ApiRoutes } from '../types';

// API Base URLs - Injected via Webpack
export const API_BASE_URL =
  (typeof window !== 'undefined' &&
    (window as unknown as { env?: { API_URL?: string } }).env?.API_URL) ||
  (typeof process !== 'undefined' && process.env?.API_URL) ||
  'https://api.portfolio.local';

// Define API_V1 for use in API_ROUTES
const API_V1 = '/v1';

export const API_ROUTES: ApiRoutes = {
  profile: '/v1/profile/',
  background: '/v1/background/',
  astroImages: '/v1/image/',
  astroImage: '/v1/image/:id/',
  contact: '/v1/contact/',
  whatsEnabled: `${API_V1}/whats-enabled/`,
  projects: '/v1/projects/',
  travelHighlights: '/v1/travel-highlights/',
  travelBySlug: `${API_V1}/travel/`,
  tags: '/v1/tags/',
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
