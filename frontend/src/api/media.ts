/**
 * Media URL normalization helpers.
 *
 * Backend serializers may return a mix of relative paths, absolute API-host
 * URLs, and secure image helper URLs. This module converts those values into
 * browser-safe URLs that stay aligned with `SITE_DOMAIN`.
 */
import { API_BASE_URL } from './routes';
import type { AstroImage, MainPageLocation, UserProfile } from '../types';

const toSameOriginPath = (input: URL | string): string => {
  if (typeof input === 'string') {
    return input;
  }

  return `${input.pathname}${input.search}`;
};

const toFrontendImageFilePath = (path: string): string => {
  if (path.startsWith('/app/image-files/')) {
    return path;
  }

  if (path.startsWith('/image-files/')) {
    return `/app${path}`;
  }

  if (/^\/v1\/images\/[^/]+\/serve\/?(?:\?.*)?$/.test(path)) {
    return path.replace(/^\/v1\/images\//, '/app/image-files/');
  }

  return path;
};

/**
 * Normalize a backend media path into the public URL that the browser should
 * request. Public `/media/*` and signed image serve URLs are rewritten onto the
 * current site host.
 */
export const getMediaUrl = (path: string | null | undefined): string | null => {
  if (!path) return null;

  const isPublicRelativeMedia =
    path.startsWith('/media/') ||
    path.startsWith('/static/') ||
    path.startsWith('/app/image-files/') ||
    path.startsWith('/image-files/') ||
    /^\/v1\/images\/[^/]+\/serve\/?(?:\?.*)?$/.test(path);

  if (isPublicRelativeMedia) {
    return toFrontendImageFilePath(path);
  }

  if (path.startsWith('http://') || path.startsWith('https://')) {
    try {
      const url = new URL(path);
      const isPublicMedia = url.pathname.startsWith('/media/');
      const isPublicStatic = url.pathname.startsWith('/static/');
      const isInternalImageFile = url.pathname.startsWith('/image-files/');
      const isFrontendImageFile = url.pathname.startsWith('/app/image-files/');
      const isSecureImageServe = /^\/v1\/images\/[^/]+\/serve\/?$/.test(
        url.pathname
      );

      if (
        isPublicMedia ||
        isPublicStatic ||
        isInternalImageFile ||
        isFrontendImageFile
      ) {
        return toFrontendImageFilePath(toSameOriginPath(url));
      }

      if (isSecureImageServe) {
        return toFrontendImageFilePath(toSameOriginPath(url));
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
