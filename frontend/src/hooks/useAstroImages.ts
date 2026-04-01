import { useInfiniteQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchAstroImages } from '../api/services';
import { AstroImage, FilterParams, PaginatedResponse } from '../types';

export const ASTRO_GALLERY_PAGE_SIZE = 24;

const getNextPageNumber = (
  nextUrl: string | null | undefined
): number | undefined => {
  if (!nextUrl) {
    return undefined;
  }

  try {
    const url = new URL(nextUrl, 'http://frontend.local');
    const page = url.searchParams.get('page');
    if (!page) {
      return undefined;
    }

    const nextPage = Number(page);
    return Number.isFinite(nextPage) ? nextPage : undefined;
  } catch {
    return undefined;
  }
};

export const useAstroImages = (params: FilterParams = {}) => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];
  const pageSize = params.limit ?? ASTRO_GALLERY_PAGE_SIZE;

  const query = useInfiniteQuery<PaginatedResponse<AstroImage>, Error>({
    queryKey: ['astro-images', language, params],
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      fetchAstroImages({
        ...params,
        page: Number(pageParam),
        limit: pageSize,
      }),
    getNextPageParam: lastPage => getNextPageNumber(lastPage.next),
  });

  return {
    ...query,
    data: query.data?.pages.flatMap(page => page.results) ?? [],
  };
};
