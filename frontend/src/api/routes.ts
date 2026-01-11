import { ApiRoutes } from "../types";

// API Base URLs - Always using HTTPS since nginx is configured for it
export const API_BASE_URL: string = "https://admin.portfolio.local";

export const API_ROUTES: ApiRoutes = {
  profile: "/api/v1/profile/",
  background: "/api/v1/background/",
  astroImages: "/api/v1/image/",
  astroImage: "/api/v1/image/:id/",
  contact: "/api/v1/contact/",
};

// Helper function to get full media URL
export const getMediaUrl = (path: string | null | undefined): string | null => {
  if (!path) return null;

  // If the path is already an absolute URL, return it as-is
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  // Ensure we don't have double slashes for relative paths
  const cleanPath = path.startsWith("/") ? path.substring(1) : path;
  return `${API_BASE_URL}/${cleanPath}`;
};
