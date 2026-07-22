/**
 * Media URL normalization helpers.
 *
 * Backend serializers may return a mix of relative paths, absolute API-host
 * URLs, and secure image helper URLs. This module converts those values into
 * browser-safe URLs that stay aligned with `SITE_DOMAIN`.
 */
import { API_BASE_URL } from './routes';
import type {
  AstroImage,
  BackgroundImage,
  ImageVariantCandidate,
  ImageVariantsByRole,
  MainPageLocation,
  ProfileImage,
  UserProfile,
} from '../types';

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

export const normalizeImageVariants = (
  variants: ImageVariantsByRole | undefined
): ImageVariantsByRole | undefined => {
  if (!variants) return undefined;

  return Object.fromEntries(
    Object.entries(variants).map(([role, candidates]) => [
      role,
      candidates
        .map(candidate => {
          const url = getMediaUrl(candidate.url);
          return url ? { ...candidate, url } : null;
        })
        .filter(candidate => candidate !== null),
    ])
  );
};

export const normalizeImageCandidate = <T extends { url: string }>(
  candidate: T | null | undefined
): T | undefined => {
  if (!candidate) return undefined;
  const url = getMediaUrl(candidate.url);
  return url ? { ...candidate, url } : undefined;
};

export const normalizeImageVariantPayload = <
  T extends {
    fallback_image?: ImageVariantCandidate | null;
    variants?: ImageVariantsByRole;
  },
>(
  image: T | null | undefined
): T | null => {
  if (!image?.fallback_image) return null;

  return {
    ...image,
    fallback_image: normalizeImageCandidate(image.fallback_image),
    variants: normalizeImageVariants(image.variants),
  };
};

/** Normalize image fallback fields for an astro image payload. */
export const normalizeAstroImage = <T extends AstroImage>(image: T): T => ({
  ...image,
  fallback_image: normalizeImageCandidate(image.fallback_image),
  variants: normalizeImageVariants(image.variants),
});

/** Normalize media fields across a list of astro image payloads. */
export const normalizeAstroImages = <T extends AstroImage>(images: T[]): T[] =>
  images.map(normalizeAstroImage);

export const normalizeBackgroundImage = (
  image: BackgroundImage | null | undefined
): BackgroundImage | null => normalizeImageVariantPayload(image);

const normalizeProfileImage = (
  image: ProfileImage | null | undefined
): ProfileImage | null => normalizeImageVariantPayload(image);

/** Normalize profile image fields returned by the backend. */
export const normalizeProfileMedia = (profile: UserProfile): UserProfile => ({
  ...profile,
  avatar: normalizeProfileImage(profile.avatar),
  about_me_image: normalizeProfileImage(profile.about_me_image),
  about_me_image2: normalizeProfileImage(profile.about_me_image2),
});

/** Normalize homepage/travel highlight image references. */
export const normalizeTravelLocation = (
  location: MainPageLocation
): MainPageLocation => ({
  ...location,
  images: normalizeAstroImages(location.images),
});
