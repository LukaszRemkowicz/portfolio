import { API_BASE_URL } from './routes';
import type { AstroImage, MainPageLocation, UserProfile } from '../types';

export const getMediaUrl = (path: string | null | undefined): string | null => {
  if (!path) return null;

  if (path.startsWith('http://') || path.startsWith('https://')) {
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
