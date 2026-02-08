// frontend/src/hooks/useBackground.ts
import { useQuery } from '@tanstack/react-query';
import { fetchBackground } from '../api/services';

export const useBackground = () => {
  return useQuery({
    queryKey: ['background'],
    queryFn: fetchBackground,
    staleTime: 1000 * 60 * 60, // 1 hour
  });
};
