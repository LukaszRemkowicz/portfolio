// frontend/src/hooks/useTravelHighlightDetail.ts
import { useQuery } from '@tanstack/react-query';
import { fetchTravelHighlightDetailBySlug } from '../api/services';
import { useTranslation } from 'react-i18next';

export const useTravelHighlightDetail = (
  countrySlug?: string,
  placeSlug?: string
) => {
  const { i18n } = useTranslation();

  return useQuery({
    queryKey: ['travelHighlightDetail', countrySlug, placeSlug, i18n.language],
    queryFn: () => fetchTravelHighlightDetailBySlug(countrySlug, placeSlug),
    enabled: !!countrySlug,
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
};
