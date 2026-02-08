// frontend/src/hooks/useTags.ts
import { useQuery } from '@tanstack/react-query';
import { fetchTags } from '../api/services';
import { useTranslation } from 'react-i18next';

export const useTags = (category?: string) => {
  const { i18n } = useTranslation();

  return useQuery({
    queryKey: ['tags', category, i18n.language],
    queryFn: () => fetchTags(category),
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
};
