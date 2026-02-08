// frontend/src/hooks/useAstroImageDetail.ts
import { useQuery } from '@tanstack/react-query';
import { fetchAstroImageDetail } from '../api/services';
import { useTranslation } from 'react-i18next';

export const useAstroImageDetail = (slug: string | null) => {
  const { i18n } = useTranslation();

  return useQuery({
    queryKey: ['astroImageDetail', slug, i18n.language],
    queryFn: () =>
      slug ? fetchAstroImageDetail(slug) : Promise.reject('No slug provided'),
    enabled: !!slug,
    staleTime: 1000 * 60 * 60, // 1 hour
  });
};
