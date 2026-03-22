// frontend/src/hooks/useCategories.ts
import { useQuery } from '@tanstack/react-query';
import { fetchCategories } from '../api/services';

export const useCategories = () =>
  useQuery<string[], Error>({
    queryKey: ['categories'],
    queryFn: () => fetchCategories(),
    staleTime: 30 * 60 * 1000,
  });
