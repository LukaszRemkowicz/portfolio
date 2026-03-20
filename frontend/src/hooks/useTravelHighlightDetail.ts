// frontend/src/hooks/useTravelHighlightDetail.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/api';
import type { AxiosInstance } from 'axios';
import { API_ROUTES, BFF_ROUTES, getMediaUrl } from '../api/routes';
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
  const useFrontendBff = typeof window !== 'undefined' && client === api;
  const response = useFrontendBff
    ? {
        data: await fetch(
          `${BFF_ROUTES.travelBySlug}${countrySlug}/${placeSlug}/${dateSlug}/`,
          {
            headers: {
              Accept: 'application/json',
            },
          }
        ).then(async res => {
          if (!res.ok) {
            throw new Error(
              `BFF travel detail request failed with status ${res.status}`
            );
          }
          return res.json();
        }),
      }
    : await client.get(
        `${API_ROUTES.travelBySlug}${countrySlug}/${placeSlug}/${dateSlug}/`
      );

  const data = response.data;
  if (!data || typeof data !== 'object') {
    throw new Error('Invalid API response structure');
  }

  const imagesArray = Array.isArray(data.images) ? data.images : [];
  const processedImages: ExtendedAstroImage[] = imagesArray.map(
    (image: AstroImage) => ({
      ...image,
      thumbnail_url: getMediaUrl(image.thumbnail_url) || undefined,
      url: undefined,
    })
  );

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
  return useQuery<TravelHighlightDetail, Error>({
    queryKey: ['travel-highlight', countrySlug, placeSlug, dateSlug],
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
