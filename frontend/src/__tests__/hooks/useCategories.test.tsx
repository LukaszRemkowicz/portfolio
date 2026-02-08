// frontend/src/__tests__/hooks/useCategories.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useCategories } from '../../hooks/useCategories';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fetchCategories } from '../../api/services';
import React from 'react';

jest.mock('../../api/services');
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' },
  }),
  initReactI18next: { type: '3rdParty', init: () => {} },
}));

const mockFetchCategories = fetchCategories as jest.MockedFunction<
  typeof fetchCategories
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

describe('useCategories hook', () => {
  it('fetches categories successfully', async () => {
    const mockCategories = ['Cat 1', 'Cat 2'];
    mockFetchCategories.mockResolvedValue(mockCategories);

    const { result } = renderHook(() => useCategories(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockCategories);
  });
});
