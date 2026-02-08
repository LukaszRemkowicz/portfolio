// frontend/src/hooks/useTravelHighlights.ts
import { useQuery } from '@tanstack/react-query';
import { fetchTravelHighlights } from '../api/services';
import { useTranslation } from 'react-i18next';

export const useTravelHighlights = () => {
  const { i18n } = useTranslation();

  return useQuery({
    queryKey: ['travelHighlights', i18n.language],
    queryFn: fetchTravelHighlights,
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
};
