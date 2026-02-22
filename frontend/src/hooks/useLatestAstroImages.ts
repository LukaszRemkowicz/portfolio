// frontend/src/hooks/useLatestAstroImages.ts
import { useQuery } from '@tanstack/react-query';
import { fetchLatestAstroImages } from '../api/services';
import { AstroImage } from '../types';

export const useLatestAstroImages = (enabled: boolean = true) =>
  useQuery<AstroImage[], Error>({
    queryKey: ['latest-astro-images'],
    queryFn: fetchLatestAstroImages,
    enabled,
    staleTime: 5 * 60 * 1000,
  });
