import { renderHook } from '@testing-library/react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { useProfile } from '../../hooks/useProfile';
import { useBackground } from '../../hooks/useBackground';
import { useSettings } from '../../hooks/useSettings';
import { useAstroImages } from '../../hooks/useAstroImages';
import { useAstroImageDetail } from '../../hooks/useAstroImageDetail';
import { useLatestAstroImages } from '../../hooks/useLatestAstroImages';
import { useCategories } from '../../hooks/useCategories';
import { useTags } from '../../hooks/useTags';
import { useProjects } from '../../hooks/useProjects';
import { useTravelHighlights } from '../../hooks/useTravelHighlights';
import { useTravelHighlightDetail } from '../../hooks/useTravelHighlightDetail';
import { useImageUrls } from '../../hooks/useImageUrls';

describe('TanStack Query Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (globalThis as { __TEST_I18N_LANGUAGE__?: string }).__TEST_I18N_LANGUAGE__ =
      'en';
  });

  afterEach(() => {
    delete (globalThis as { __TEST_I18N_LANGUAGE__?: string })
      .__TEST_I18N_LANGUAGE__;
  });

  it('useProfile calls useQuery with correct options', () => {
    renderHook(() => useProfile());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['profile', 'en'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useBackground calls useQuery with correct options', () => {
    renderHook(() => useBackground());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['background', 'en'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useSettings calls useQuery with correct options', () => {
    renderHook(() => useSettings());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['settings', 'en'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useAstroImages calls useInfiniteQuery with correct options', () => {
    renderHook(() => useAstroImages({ filter: 'filter', tag: 'tag' }));
    expect(useInfiniteQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['astro-images', 'en', { filter: 'filter', tag: 'tag' }],
        queryFn: expect.any(Function),
        initialPageParam: 1,
        getNextPageParam: expect.any(Function),
      })
    );
  });

  it('useAstroImages starts from the requested page when page is provided', () => {
    renderHook(() => useAstroImages({ page: 2 }));
    expect(useInfiniteQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['astro-images', 'en', { page: 2 }],
        queryFn: expect.any(Function),
        initialPageParam: 2,
        getNextPageParam: expect.any(Function),
      })
    );
  });

  it('useAstroImageDetail calls useQuery with correct options', () => {
    renderHook(() => useAstroImageDetail('m31'));
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['astro-image', 'en', 'm31'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useLatestAstroImages calls useQuery with correct options', () => {
    renderHook(() => useLatestAstroImages());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['latest-astro-images', 'en'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useCategories calls useQuery with correct options', () => {
    renderHook(() => useCategories());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['categories', 'en'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useTags calls useQuery with correct options', () => {
    renderHook(() => useTags('galaxy'));
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['tags', 'en', 'galaxy'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useProjects calls useQuery with correct options', () => {
    renderHook(() => useProjects());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['projects', 'en'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useTravelHighlights calls useQuery with correct options', () => {
    renderHook(() => useTravelHighlights());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['travel-highlights', 'en'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useTravelHighlightDetail calls useQuery with correct options', () => {
    renderHook(() => useTravelHighlightDetail('italy', 'rome', '2023-05'));
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['travel-highlight', 'en', 'italy', 'rome', '2023-05'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useImageUrls calls useQuery with correct options', () => {
    renderHook(() => useImageUrls(['1', '2']));
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['image-urls', 'en', ['1', '2']],
        queryFn: expect.any(Function),
      })
    );
  });

  it('uses Polish language in query keys after language switch', () => {
    (globalThis as { __TEST_I18N_LANGUAGE__?: string }).__TEST_I18N_LANGUAGE__ =
      'pl';

    renderHook(() => useProfile());
    renderHook(() => useBackground());
    renderHook(() => useLatestAstroImages());
    renderHook(() => useTravelHighlights());

    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['profile', 'pl'],
      })
    );
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['background', 'pl'],
      })
    );
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['latest-astro-images', 'pl'],
      })
    );
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['travel-highlights', 'pl'],
      })
    );
  });
});
