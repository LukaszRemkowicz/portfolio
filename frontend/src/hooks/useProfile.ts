// frontend/src/hooks/useProfile.ts
import { useQuery } from '@tanstack/react-query';
import { fetchProfile } from '../api/services';
import { UserProfile } from '../types';

export const useProfile = () =>
  useQuery<UserProfile, Error>({
    queryKey: ['profile'],
    queryFn: fetchProfile,
    staleTime: 5 * 60 * 1000,
  });
