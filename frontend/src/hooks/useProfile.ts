// frontend/src/hooks/useProfile.ts
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchProfile } from '../api/services';
import { UserProfile } from '../types';
import { languageBoundShellQueryOptions } from './languageBoundShellQueryOptions';

export const useProfile = () => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<UserProfile, Error>({
    queryKey: ['profile', language],
    queryFn: () => fetchProfile(),
    ...languageBoundShellQueryOptions,
  });
};
