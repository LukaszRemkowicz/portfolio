import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchTags } from '../api/services';
import { Tag } from '../types';

export const useTags = (category?: string) => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<Tag[], Error>({
    queryKey: ['tags', language, category],
    queryFn: () => fetchTags(category),
  });
};
