// frontend/src/__tests__/hooks/useTags.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useTags } from '../../hooks/useTags';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fetchTags } from '../../api/services';
import { Tag } from '../../types';
import React from 'react';

jest.mock('../../api/services');
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' },
  }),
  initReactI18next: { type: '3rdParty', init: () => {} },
}));

const mockFetchTags = fetchTags as jest.MockedFunction<typeof fetchTags>;

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

describe('useTags hook', () => {
  it('fetches tags successfully', async () => {
    const mockTags = [{ name: 'Tag 1', slug: 'tag-1', count: 1 }];
    mockFetchTags.mockResolvedValue(mockTags as unknown as Tag[]);

    const { result } = renderHook(() => useTags('Landscape'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockTags);
    expect(mockFetchTags).toHaveBeenCalledWith('Landscape');
  });
});
