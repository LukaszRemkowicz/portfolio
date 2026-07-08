import type { ImageVariantsByRole } from '../types';

const MOBILE_MAX_WIDTH = 640;
const TABLET_MAX_WIDTH = 1024;
const DESKTOP_MAX_WIDTH = 1600;

export const getHeroVariantWidthForViewport = (width: number): number => {
  if (width <= TABLET_MAX_WIDTH) return 1280;
  if (width <= DESKTOP_MAX_WIDTH) return 1920;
  return 2560;
};

export const getImageVariantWidthForViewport = (width: number): number => {
  if (width <= MOBILE_MAX_WIDTH) return 320;
  if (width <= TABLET_MAX_WIDTH) return 560;
  if (width <= DESKTOP_MAX_WIDTH) return 840;
  return 1120;
};

const getCurrentViewportWidth = (): number | null => {
  if (typeof window === 'undefined') return null;
  return window.innerWidth;
};

export const getCurrentHeroVariantWidth = (): number => {
  const viewportWidth = getCurrentViewportWidth();
  if (viewportWidth === null) return 1920;
  return getHeroVariantWidthForViewport(viewportWidth);
};

export const getCurrentImageVariantWidth = (): number => {
  const viewportWidth = getCurrentViewportWidth();
  if (viewportWidth === null) return 840;
  return getImageVariantWidthForViewport(viewportWidth);
};

interface BuildResponsiveImagePropsArgs {
  variants?: ImageVariantsByRole;
  role: string;
  fallbackSrc?: string;
  preferredWidth?: number;
  sizes: string;
}

export interface ResponsiveImageProps {
  src: string;
  srcSet?: string;
  sizes?: string;
  width?: number;
  height?: number;
}

export const buildResponsiveImageProps = ({
  variants,
  role,
  fallbackSrc = '',
  preferredWidth,
  sizes,
}: BuildResponsiveImagePropsArgs): ResponsiveImageProps => {
  const candidates = [...(variants?.[role] ?? [])]
    .filter(
      candidate => candidate.url && candidate.width > 0 && candidate.height > 0
    )
    .sort((first, second) => first.width - second.width);

  if (candidates.length === 0) {
    return { src: fallbackSrc };
  }

  const preferredCandidate =
    candidates.find(candidate => candidate.width === preferredWidth) ??
    candidates.find(
      candidate => preferredWidth && candidate.width >= preferredWidth
    ) ??
    candidates[candidates.length - 1];

  return {
    src: fallbackSrc || preferredCandidate.url,
    srcSet: candidates
      .map(candidate => `${candidate.url} ${candidate.width}w`)
      .join(', '),
    sizes,
    width: preferredCandidate.width,
    height: preferredCandidate.height,
  };
};
