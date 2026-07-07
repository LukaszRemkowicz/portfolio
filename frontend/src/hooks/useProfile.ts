// frontend/src/hooks/useProfile.ts
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchProfile } from '../api/services';
import { UserProfile } from '../types';
import { useHeroImageVariantSize } from './useImageVariantSize';

export const useProfile = () => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];
  const imageSize = useHeroImageVariantSize();

  return useQuery<UserProfile, Error>({
    queryKey: ['profile', language, imageSize],
    queryFn: () => fetchProfile(imageSize),
    staleTime: Infinity,
    gcTime: Infinity,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  });
};
