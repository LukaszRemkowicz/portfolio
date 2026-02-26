// frontend/src/hooks/useAstroImageDetail.ts
import { useQuery } from '@tanstack/react-query';
import { fetchAstroImageDetail } from '../api/services';
import { AstroImage } from '../types';

export const useAstroImageDetail = (slug: string | null) =>
  useQuery<AstroImage, Error>({
    queryKey: ['astro-image', slug],
    queryFn: () => fetchAstroImageDetail(slug!),
    enabled: !!slug,
    staleTime: 5 * 60 * 1000,
  });
