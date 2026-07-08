import type { ImageVariantsByRole } from '../types';

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
