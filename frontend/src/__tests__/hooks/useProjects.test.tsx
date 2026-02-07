// frontend/src/__tests__/hooks/useProjects.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useProjects } from '../../hooks/useProjects';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fetchProjects } from '../../api/services';
import { Project } from '../../types';
import React from 'react';

jest.mock('../../api/services');
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' },
  }),
  initReactI18next: { type: '3rdParty', init: () => {} },
}));

const mockFetchProjects = fetchProjects as jest.MockedFunction<
  typeof fetchProjects
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

describe('useProjects hook', () => {
  it('fetches projects successfully', async () => {
    const mockProjects = [{ pk: 1, name: 'Project 1' }];
    mockFetchProjects.mockResolvedValue(mockProjects as unknown as Project[]);

    const { result } = renderHook(() => useProjects(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockProjects);
  });
});
