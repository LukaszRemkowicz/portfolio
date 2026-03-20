// frontend/src/hooks/useProfile.ts
import { useQuery } from '@tanstack/react-query';
import { fetchProfile } from '../api/services';
import { UserProfile } from '../types';

export const useProfile = () =>
  useQuery<UserProfile, Error>({
    queryKey: ['profile'],
    queryFn: () => fetchProfile(),
    staleTime: Infinity,
    gcTime: Infinity,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  });
