// frontend/src/__tests__/hooks/useTravelHighlights.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useTravelHighlights } from '../../hooks/useTravelHighlights';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fetchTravelHighlights } from '../../api/services';
import { MainPageLocation } from '../../types';
import React from 'react';

jest.mock('../../api/services');
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' },
  }),
  initReactI18next: { type: '3rdParty', init: () => {} },
}));

const mockFetchTravelHighlights = fetchTravelHighlights as jest.MockedFunction<
  typeof fetchTravelHighlights
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

describe('useTravelHighlights hook', () => {
  it('fetches highlights successfully', async () => {
    const mockHighlights = [{ pk: 1, name: 'Location 1', images: [] }];
    mockFetchTravelHighlights.mockResolvedValue(
      mockHighlights as unknown as MainPageLocation[]
    );

    const { result } = renderHook(() => useTravelHighlights(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockHighlights);
  });
});
