// frontend/src/__tests__/hooks/useProfile.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useProfile } from '../../hooks/useProfile';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fetchProfile } from '../../api/services';
import { UserProfile } from '../../types';
import React from 'react';

jest.mock('../../api/services');
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' },
  }),
  initReactI18next: {
    type: '3rdParty',
    init: () => {},
  },
}));

const mockFetchProfile = fetchProfile as jest.MockedFunction<
  typeof fetchProfile
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

describe('useProfile hook', () => {
  it('fetches profile successfully', async () => {
    const mockProfile = { first_name: 'Test', last_name: 'User' };
    mockFetchProfile.mockResolvedValue(mockProfile as unknown as UserProfile);

    const { result } = renderHook(() => useProfile(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockProfile);
  });
});
