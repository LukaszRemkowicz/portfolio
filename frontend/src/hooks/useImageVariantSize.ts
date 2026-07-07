import { useEffect, useState } from 'react';
import {
  getCurrentHeroVariantWidth,
  getCurrentImageVariantWidth,
} from '../utils/imageVariants';

const useResponsiveImageSize = (getCurrentSize: () => number): number => {
  const [size, setSize] = useState<number>(() => getCurrentSize());

  useEffect(() => {
    if (typeof window === 'undefined') return undefined;

    const syncSize = () => setSize(getCurrentSize());
    window.addEventListener('resize', syncSize);
    syncSize();

    return () => window.removeEventListener('resize', syncSize);
  }, [getCurrentSize]);

  return size;
};

export const useHeroImageVariantSize = (): number =>
  useResponsiveImageSize(getCurrentHeroVariantWidth);

export const useImageVariantSize = (): number =>
  useResponsiveImageSize(getCurrentImageVariantWidth);
