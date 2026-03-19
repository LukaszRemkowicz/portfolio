import { renderHook } from '@testing-library/react';
import { useQuery } from '@tanstack/react-query';
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
  });

  it('useProfile calls useQuery with correct options', () => {
    renderHook(() => useProfile());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['profile'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useBackground calls useQuery with correct options', () => {
    renderHook(() => useBackground());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['background'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useSettings calls useQuery with correct options', () => {
    renderHook(() => useSettings());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['settings'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useAstroImages calls useQuery with correct options', () => {
    renderHook(() => useAstroImages({ filter: 'filter', tag: 'tag' }));
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['astro-images', { filter: 'filter', tag: 'tag' }],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useAstroImageDetail calls useQuery with correct options', () => {
    renderHook(() => useAstroImageDetail('m31'));
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['astro-image', 'm31'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useLatestAstroImages calls useQuery with correct options', () => {
    renderHook(() => useLatestAstroImages());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['latest-astro-images'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useCategories calls useQuery with correct options', () => {
    renderHook(() => useCategories());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['categories'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useTags calls useQuery with correct options', () => {
    renderHook(() => useTags('galaxy'));
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['tags', 'galaxy'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useProjects calls useQuery with correct options', () => {
    renderHook(() => useProjects());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['projects'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useTravelHighlights calls useQuery with correct options', () => {
    renderHook(() => useTravelHighlights());
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['travel-highlights'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useTravelHighlightDetail calls useQuery with correct options', () => {
    renderHook(() => useTravelHighlightDetail('italy', 'rome', '2023-05'));
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['travel-highlight', 'italy', 'rome', '2023-05'],
        queryFn: expect.any(Function),
      })
    );
  });

  it('useImageUrls calls useQuery with correct options', () => {
    renderHook(() => useImageUrls(['1', '2']));
    expect(useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['image-urls', ['1', '2']],
        queryFn: expect.any(Function),
      })
    );
  });
});
