import { useQuery } from '@tanstack/react-query';
import { fetchAstroImages } from '../api/services';
import { FilterType } from '../types';
import { useTranslation } from 'react-i18next';

interface UseAstroImagesParams {
  filter?: FilterType | null;
  tag?: string | null;
}

export const useAstroImages = ({ filter, tag }: UseAstroImagesParams) => {
  const { i18n } = useTranslation();

  return useQuery({
    queryKey: ['astroImages', filter, tag, i18n.language],
    queryFn: () =>
      fetchAstroImages({
        filter: filter || undefined,
        tag: tag || undefined,
      }),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};
