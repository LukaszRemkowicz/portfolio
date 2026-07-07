import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchImageUrls } from '../api/imageUrlService';

export const useImageUrls = (
  imageId?: string | null,
  enabled: boolean = true
) => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<Record<string, string>, Error>({
    queryKey: ['image-urls', language, imageId || 'none'],
    queryFn: () => fetchImageUrls(imageId),
    enabled: enabled && Boolean(imageId),
    staleTime: 10 * 60 * 1000,
  });
};
