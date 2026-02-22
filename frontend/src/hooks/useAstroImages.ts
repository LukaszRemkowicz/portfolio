// frontend/src/hooks/useAstroImages.ts
import { useQuery } from '@tanstack/react-query';
import { fetchAstroImages } from '../api/services';
import { AstroImage, FilterParams } from '../types';

export const useAstroImages = (params: FilterParams = {}) =>
  useQuery<AstroImage[], Error>({
    queryKey: ['astro-images', params],
    queryFn: () => fetchAstroImages(params),
  });
