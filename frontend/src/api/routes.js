// API Base URLs - Always using HTTPS since nginx is configured for it
export const API_BASE_URL = 'https://admin.portfolio.local';

export const API_ROUTES = {
  profile: '/api/v1/profile/',
  background: '/api/v1/background/',
  astroImages: '/api/v1/image/',
  astroImage: '/api/v1/image/:id/',
};

// Helper function to get full media URL
export const getMediaUrl = (path) => {
  if (!path) return null;
  // Ensure we don't have double slashes
  if (path.startsWith('/')) {
    path = path.substring(1);
  }
  return `${API_BASE_URL}/${path}`;
}; 