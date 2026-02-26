// frontend/src/hooks/useImageUrls.ts
import { useQuery } from '@tanstack/react-query';
import { fetchImageUrls } from '../api/imageUrlService';

export const useImageUrls = (ids?: string[], enabled: boolean = true) =>
  useQuery<Record<string, string>, Error>({
    queryKey: ['image-urls', ids || 'all'],
    queryFn: () => fetchImageUrls(ids),
    enabled,
    staleTime: 10 * 60 * 1000,
  });
