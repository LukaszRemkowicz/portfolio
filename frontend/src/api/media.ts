/**
 * Media URL normalization helpers.
 *
 * Backend serializers may return a mix of relative paths, absolute API-host
 * URLs, and secure image helper URLs. This module converts those values into
 * browser-safe URLs that stay aligned with `SITE_DOMAIN`.
 */
import { API_BASE_URL } from './routes';
import { publicEnv } from '../../server/publicEnv.js';
import type { AstroImage, MainPageLocation, UserProfile } from '../types';

const PUBLIC_SITE_BASE_URL =
  typeof window !== 'undefined'
    ? window.location.origin
    : `https://${publicEnv.SITE_DOMAIN}`;

/**
 * Normalize a backend media path into the public URL that the browser should
 * request. Public `/media/*` and signed image serve URLs are rewritten onto the
 * current site host.
 */
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

/** Normalize thumbnail fields for an astro image payload. */
export const normalizeAstroImage = <T extends AstroImage>(image: T): T => ({
  ...image,
  thumbnail_url: getMediaUrl(image.thumbnail_url) || undefined,
});

/** Normalize media fields across a list of astro image payloads. */
export const normalizeAstroImages = <T extends AstroImage>(images: T[]): T[] =>
  images.map(normalizeAstroImage);

/** Normalize profile image fields returned by the backend. */
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

/** Normalize homepage/travel highlight image references. */
export const normalizeTravelLocation = (
  location: MainPageLocation
): MainPageLocation => ({
  ...location,
  images: normalizeAstroImages(location.images),
});
