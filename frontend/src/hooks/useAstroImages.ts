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
  const initialPage = params.page ?? 1;
  const isPagedRequest = params.page !== undefined;

  const infiniteQuery = useInfiniteQuery<PaginatedResponse<AstroImage>, Error>({
    queryKey: ['astro-images', language, params],
    initialPageParam: initialPage,
    queryFn: ({ pageParam }) =>
      fetchAstroImages({
        ...params,
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
