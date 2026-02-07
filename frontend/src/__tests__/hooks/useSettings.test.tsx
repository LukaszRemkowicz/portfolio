// frontend/src/__tests__/hooks/useSettings.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useSettings } from '../../hooks/useSettings';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fetchSettings } from '../../api/services';
import { EnabledFeatures } from '../../types';
import React from 'react';

jest.mock('../../api/services');
const mockFetchSettings = fetchSettings as jest.MockedFunction<
  typeof fetchSettings
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

describe('useSettings hook', () => {
  it('fetches settings successfully', async () => {
    const mockSettings = { programming: true, contactForm: true };
    mockFetchSettings.mockResolvedValue(
      mockSettings as unknown as EnabledFeatures
    );

    const { result } = renderHook(() => useSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockSettings);
  });
});
