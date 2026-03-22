// frontend/src/hooks/useLatestAstroImages.ts
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchLatestAstroImages } from '../api/services';
import { AstroImage } from '../types';

export const useLatestAstroImages = (enabled: boolean = true) => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<AstroImage[], Error>({
    queryKey: ['latest-astro-images', language],
    queryFn: () => fetchLatestAstroImages(),
    enabled,
    staleTime: Infinity,
    gcTime: Infinity,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  });
};
