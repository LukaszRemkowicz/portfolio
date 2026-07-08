// frontend/src/hooks/useBackground.ts
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchBackgroundImage } from '../api/services';
import { BackgroundImage } from '../types';

export const useBackground = () => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<BackgroundImage | null, Error>({
    queryKey: ['background', language],
    queryFn: () => fetchBackgroundImage(),
    staleTime: Infinity,
    gcTime: Infinity,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  });
};
