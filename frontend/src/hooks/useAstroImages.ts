import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchAstroImages } from '../api/services';
import { AstroImage, FilterParams } from '../types';

export const useAstroImages = (params: FilterParams = {}) => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<AstroImage[], Error>({
    queryKey: ['astro-images', language, params],
    queryFn: () => fetchAstroImages(params),
  });
};
