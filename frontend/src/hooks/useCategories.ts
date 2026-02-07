// frontend/src/hooks/useCategories.ts
import { useQuery } from '@tanstack/react-query';
import { fetchCategories } from '../api/services';
import { useTranslation } from 'react-i18next';

export const useCategories = () => {
  const { i18n } = useTranslation();

  return useQuery({
    queryKey: ['categories', i18n.language],
    queryFn: fetchCategories,
    staleTime: 1000 * 60 * 60, // 1 hour
  });
};
