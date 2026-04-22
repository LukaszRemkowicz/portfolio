import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchAstroImageDetail } from '../api/services';
import { AstroImage } from '../types';

export const getAstroImageQueryKey = (language: string, slug: string | null) =>
  ['astro-image', language, slug] as const;

export const getAstroImageNotFoundQueryKey = (
  language: string,
  slug: string | null
) => ['astro-image-not-found', language, slug] as const;

export const useAstroImageDetail = (slug: string | null) => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<AstroImage, Error>({
    queryKey: getAstroImageQueryKey(language, slug),
    queryFn: () => fetchAstroImageDetail(slug!),
    enabled: !!slug,
    staleTime: 5 * 60 * 1000,
  });
};
