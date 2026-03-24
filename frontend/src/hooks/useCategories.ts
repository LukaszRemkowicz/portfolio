import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchCategories } from '../api/services';

export const useCategories = () => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<string[], Error>({
    queryKey: ['categories', language],
    queryFn: () => fetchCategories(),
    staleTime: 30 * 60 * 1000,
  });
};
