// frontend/src/hooks/useSettings.ts
import { useQuery } from '@tanstack/react-query';
import { fetchSettings } from '../api/services';

export const useSettings = () => {
  return useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
    staleTime: 1000 * 60 * 60, // 1 hour
  });
};
