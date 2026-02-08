// frontend/src/__tests__/hooks/useAstroImageDetail.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useAstroImageDetail } from '../../hooks/useAstroImageDetail';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fetchAstroImageDetail } from '../../api/services';
import { AstroImage } from '../../types';
import React from 'react';

jest.mock('../../api/services');
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' },
  }),
  initReactI18next: { type: '3rdParty', init: () => {} },
}));

const mockFetchAstroImageDetail = fetchAstroImageDetail as jest.MockedFunction<
  typeof fetchAstroImageDetail
>;

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function QueryClientWrapper({
    children,
  }: {
    children: React.ReactNode;
  }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
};

describe('useAstroImageDetail hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches image detail successfully', async () => {
    const mockImage = { pk: 1, slug: 'test-slug', name: 'Test' };
    mockFetchAstroImageDetail.mockResolvedValue(
      mockImage as unknown as AstroImage
    );

    const { result } = renderHook(() => useAstroImageDetail('test-slug'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockImage);
    expect(mockFetchAstroImageDetail).toHaveBeenCalledWith('test-slug');
  });

  it('does not fetch if slug is null', () => {
    const { result } = renderHook(() => useAstroImageDetail(null), {
      wrapper: createWrapper(),
    });
    expect(result.current.isLoading).toBe(false);
    expect(mockFetchAstroImageDetail).not.toHaveBeenCalled();
  });
});
