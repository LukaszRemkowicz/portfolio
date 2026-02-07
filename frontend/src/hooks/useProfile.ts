// frontend/src/hooks/useProfile.ts
import { useQuery } from '@tanstack/react-query';
import { fetchProfile } from '../api/services';
import { useTranslation } from 'react-i18next';

export const useProfile = () => {
  const { i18n } = useTranslation();

  return useQuery({
    queryKey: ['profile', i18n.language],
    queryFn: fetchProfile,
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
};
