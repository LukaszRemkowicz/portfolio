// frontend/src/hooks/useTravelHighlights.ts
import { useQuery } from '@tanstack/react-query';
import { fetchTravelHighlights } from '../api/services';
import { MainPageLocation } from '../types';

export const useTravelHighlights = (enabled = true) =>
  useQuery<MainPageLocation[], Error>({
    queryKey: ['travel-highlights'],
    queryFn: () => fetchTravelHighlights(),
    enabled,
    staleTime: Infinity,
    gcTime: Infinity,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  });
