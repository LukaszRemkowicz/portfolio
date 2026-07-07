// frontend/src/hooks/useBackground.ts
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchBackground } from '../api/services';
import { useHeroImageVariantSize } from './useImageVariantSize';

export const useBackground = () => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];
  const imageSize = useHeroImageVariantSize();

  return useQuery<string | null, Error>({
    queryKey: ['background', language, imageSize],
    queryFn: () => fetchBackground(imageSize),
    staleTime: Infinity,
    gcTime: Infinity,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  });
};
