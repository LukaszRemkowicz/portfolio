// frontend/src/hooks/useLatestTags.ts
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchTags } from '../api/services';
import { Tag } from '../types';
import { languageBoundShellQueryOptions } from './languageBoundShellQueryOptions';

export const useLatestTags = (enabled: boolean = true) => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<Tag[], Error>({
    queryKey: ['latest-tags', language],
    queryFn: () => fetchTags({ latest: true, lang: language }),
    enabled,
    ...languageBoundShellQueryOptions,
  });
};
