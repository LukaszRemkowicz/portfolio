import { API_BASE_URL } from './routes';
import { publicEnv } from '../../server/publicEnv.js';
import type { AstroImage, MainPageLocation, UserProfile } from '../types';

const PUBLIC_SITE_BASE_URL =
  typeof window !== 'undefined'
    ? window.location.origin
    : `https://${publicEnv.SITE_DOMAIN}`;

export const getMediaUrl = (path: string | null | undefined): string | null => {
  if (!path) return null;

  if (path.startsWith('http://') || path.startsWith('https://')) {
    try {
      const url = new URL(path);
      const isPublicMedia = url.pathname.startsWith('/media/');
      const isSecureImageServe = /^\/v1\/images\/[^/]+\/serve\/?$/.test(
        url.pathname
      );

      if (isPublicMedia || isSecureImageServe) {
        return `${PUBLIC_SITE_BASE_URL}${url.pathname}${url.search}`;
      }
    } catch {
      return path;
    }

    return path;
  }

  const cleanPath = path.startsWith('/') ? path.substring(1) : path;
  return `${API_BASE_URL}/${cleanPath}`;
};

export const normalizeAstroImage = <T extends AstroImage>(image: T): T => ({
  ...image,
  thumbnail_url: getMediaUrl(image.thumbnail_url) || undefined,
});

export const normalizeAstroImages = <T extends AstroImage>(images: T[]): T[] =>
  images.map(normalizeAstroImage);

export const normalizeProfileMedia = (profile: UserProfile): UserProfile => ({
  ...profile,
  avatar: profile.avatar ? getMediaUrl(profile.avatar) : null,
  about_me_image: profile.about_me_image
    ? getMediaUrl(profile.about_me_image)
    : null,
  about_me_image2: profile.about_me_image2
    ? getMediaUrl(profile.about_me_image2)
    : null,
});

export const normalizeTravelLocation = (
  location: MainPageLocation
): MainPageLocation => ({
  ...location,
  images: normalizeAstroImages(location.images),
});
