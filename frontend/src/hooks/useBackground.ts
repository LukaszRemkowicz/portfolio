// frontend/src/hooks/useBackground.ts
import { useQuery } from '@tanstack/react-query';
import { fetchBackground } from '../api/services';

export const useBackground = () =>
  useQuery<string | null, Error>({
    queryKey: ['background'],
    queryFn: () => fetchBackground(),
    staleTime: Infinity,
    gcTime: Infinity,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  });
