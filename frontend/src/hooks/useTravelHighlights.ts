// frontend/src/hooks/useTravelHighlights.ts
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchTravelHighlights } from '../api/services';
import { MainPageLocation } from '../types';
import { useImageVariantSize } from './useImageVariantSize';

export const useTravelHighlights = (enabled = true) => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];
  const imageSize = useImageVariantSize();

  return useQuery<MainPageLocation[], Error>({
    queryKey: ['travel-highlights', language, imageSize],
    queryFn: () => fetchTravelHighlights(imageSize),
    enabled,
    staleTime: Infinity,
    gcTime: Infinity,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  });
};
