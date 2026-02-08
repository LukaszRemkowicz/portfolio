// frontend/src/__tests__/hooks/useBackground.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useBackground } from '../../hooks/useBackground';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fetchBackground } from '../../api/services';
import React from 'react';

jest.mock('../../api/services');
const mockFetchBackground = fetchBackground as jest.MockedFunction<
  typeof fetchBackground
>;

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
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

describe('useBackground hook', () => {
  it('fetches background successfully', async () => {
    const mockBg = '/test-bg.jpg';
    mockFetchBackground.mockResolvedValue(mockBg);

    const { result } = renderHook(() => useBackground(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe(mockBg);
  });
});
