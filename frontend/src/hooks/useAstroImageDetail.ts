import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchAstroImageDetail } from '../api/services';
import { AstroImage } from '../types';

export const useAstroImageDetail = (slug: string | null) => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<AstroImage, Error>({
    queryKey: ['astro-image', language, slug],
    queryFn: () => fetchAstroImageDetail(slug!),
    enabled: !!slug,
    staleTime: 5 * 60 * 1000,
  });
};
