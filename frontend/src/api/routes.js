// API Base URLs - Always using HTTPS since nginx is configured for it
export const API_BASE_URL = 'https://admin.portfolio.local';

export const API_ROUTES = {
  profile: `/api/v1/profile/`,
  background: `/api/v1/background/`,
  logo: `/api/v1/logo/`,
};

// Helper function to get full media URL
export const getMediaUrl = (path) => {
  if (!path) return null;
  return `${API_BASE_URL}${path}`;
}; 