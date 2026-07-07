import { useInfiniteQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchAstroImages } from '../api/services';
import { AstroImage, FilterParams, PaginatedResponse } from '../types';
import { useImageVariantSize } from './useImageVariantSize';

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
  const imageSize = useImageVariantSize();
  const pageSize = params.limit ?? ASTRO_GALLERY_PAGE_SIZE;
  const initialPage = params.page ?? 1;
  const isPagedRequest = params.page !== undefined;
  const imageParams = {
    ...params,
    size: params.size ?? imageSize,
  } satisfies FilterParams;

  const infiniteQuery = useInfiniteQuery<PaginatedResponse<AstroImage>, Error>({
    queryKey: ['astro-images', language, imageParams],
    initialPageParam: initialPage,
    queryFn: ({ pageParam }) =>
      fetchAstroImages({
        ...imageParams,
        page: Number(pageParam),
        limit: pageSize,
      }),
    getNextPageParam: lastPage =>
      isPagedRequest ? undefined : getNextPageNumber(lastPage.next),
  });

  if (isPagedRequest) {
    const currentPageResults = infiniteQuery.data?.pages[0]?.results ?? [];

    return {
      ...infiniteQuery,
      data: currentPageResults,
      isFetchingNextPage: false,
      fetchNextPage: async () => undefined,
      hasNextPage: false,
    };
  }

  return {
    ...infiniteQuery,
    data: infiniteQuery.data?.pages.flatMap(page => page.results) ?? [],
  };
};
