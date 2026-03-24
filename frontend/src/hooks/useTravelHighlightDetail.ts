import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { api } from '../api/api';
import type { AxiosInstance } from 'axios';
import { API_ROUTES, BFF_ROUTES } from '../api/routes';
import { fetchBffJson, isBrowserDefaultClient } from '../api/bff';
import { normalizeAstroImages } from '../api/media';
import { AstroImage } from '../types';

export interface ExtendedAstroImage extends AstroImage {
  url?: string;
}

export interface TravelHighlightDetail {
  full_location?: string;
  story?: string;
  adventure_date?: string;
  highlight_name?: string;
  highlight_title?: string;
  background_image?: string;
  images: ExtendedAstroImage[];
}

export const fetchTravelHighlightDetail = async ({
  countrySlug,
  placeSlug,
  dateSlug,
  client = api,
}: {
  countrySlug: string;
  placeSlug: string;
  dateSlug: string;
  client?: AxiosInstance;
}): Promise<TravelHighlightDetail> => {
  const useFrontendBff = isBrowserDefaultClient(client);
  const response = useFrontendBff
    ? {
        data: await fetchBffJson<TravelHighlightDetail>(
          `${BFF_ROUTES.travelBySlug}${countrySlug}/${placeSlug}/${dateSlug}/`
        ),
      }
    : await client.get(
        `${API_ROUTES.travelBySlug}${countrySlug}/${placeSlug}/${dateSlug}/`
      );

  const data = response.data;
  if (!data || typeof data !== 'object') {
    throw new Error('Invalid API response structure');
  }

  const imagesArray = Array.isArray(data.images) ? data.images : [];
  const processedImages: ExtendedAstroImage[] = normalizeAstroImages(
    imagesArray as AstroImage[]
  ).map(image => ({
    ...image,
    url: undefined,
  }));

  return {
    full_location: data.full_location,
    story: data.story,
    adventure_date: data.adventure_date,
    highlight_name: data.highlight_name,
    highlight_title: data.highlight_title,
    background_image: data.background_image,
    images: processedImages,
  };
};

export const useTravelHighlightDetail = (
  countrySlug?: string,
  placeSlug?: string,
  dateSlug?: string
) => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<TravelHighlightDetail, Error>({
    queryKey: ['travel-highlight', language, countrySlug, placeSlug, dateSlug],
    queryFn: () =>
      fetchTravelHighlightDetail({
        countrySlug: countrySlug!,
        placeSlug: placeSlug!,
        dateSlug: dateSlug!,
      }),
    enabled: !!countrySlug && !!placeSlug && !!dateSlug,
    staleTime: 5 * 60 * 1000,
  });
};
