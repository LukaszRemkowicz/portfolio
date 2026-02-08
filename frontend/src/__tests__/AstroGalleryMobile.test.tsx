import { act } from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import '@testing-library/jest-dom';
import AstroGallery from '../components/AstroGallery';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HelmetProvider } from 'react-helmet-async';
import { useAstroImages } from '../hooks/useAstroImages';
import { useBackground } from '../hooks/useBackground';
import { useSettings } from '../hooks/useSettings';
import { useCategories } from '../hooks/useCategories';
import { useTags } from '../hooks/useTags';
import { useProfile } from '../hooks/useProfile';

// Mock the hooks
jest.mock('../hooks/useAstroImages');
jest.mock('../hooks/useBackground');
jest.mock('../hooks/useSettings');
jest.mock('../hooks/useCategories');
jest.mock('../hooks/useTags');
jest.mock('../hooks/useProfile');

// No longer mocking services directly

describe('AstroGallery Mobile Navigation', () => {
  const mockUseAstroImages = useAstroImages as jest.Mock;
  const mockUseCategories = useCategories as jest.Mock;
  const mockUseTags = useTags as jest.Mock;
  const mockUseSettings = useSettings as jest.Mock;
  const mockUseProfile = useProfile as jest.Mock;
  const mockUseBackground = useBackground as jest.Mock;

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  const resetStore = () => {};

  beforeEach(() => {
    jest.resetAllMocks();

    mockUseSettings.mockReturnValue({
      data: {
        programming: true,
        contactForm: true,
        lastimages: true,
        meteors: null,
      },
      isLoading: false,
    });

    mockUseTags.mockReturnValue({
      data: [
        { name: 'Nebula', slug: 'nebula', count: 5 },
        { name: 'Galaxy', slug: 'galaxy', count: 10 },
      ],
      isLoading: false,
    });

    mockUseAstroImages.mockReturnValue({ data: [], isLoading: false });

    mockUseCategories.mockReturnValue({
      data: ['Landscape', 'Deep Sky'],
      isLoading: false,
    });

    mockUseProfile.mockReturnValue({
      data: { first_name: 'John', last_name: 'Doe' },
      isLoading: false,
    });

    mockUseBackground.mockReturnValue({
      data: '/test-bg.jpg',
      isLoading: false,
    });

    resetStore();
  });

  const renderGallery = async () => {
    await act(async () => {
      render(
        <HelmetProvider>
          <QueryClientProvider client={queryClient}>
            <MemoryRouter initialEntries={['/']}>
              <Routes>
                <Route path='/' element={<AstroGallery />} />
              </Routes>
            </MemoryRouter>
          </QueryClientProvider>
        </HelmetProvider>
      );
    });

    // Wait for loading screen to be removed
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });
  };

  it('toggles "Explore Tags" drawer on click', async () => {
    await renderGallery();

    const tagButton = screen.getByRole('button', { name: /Explore Tags/i });
    expect(tagButton).toBeInTheDocument();

    // Initially closed
    expect(tagButton).toHaveAttribute('aria-expanded', 'false');

    // Click to open
    await act(async () => {
      fireEvent.click(tagButton);
    });
    expect(tagButton).toHaveAttribute('aria-expanded', 'true');

    // Click to close
    await act(async () => {
      fireEvent.click(tagButton);
    });
    expect(tagButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('toggles "Categories" drawer on click', async () => {
    await renderGallery();

    const categoryButtons = screen.getAllByRole('button', {
      name: /Categories/i,
    });
    const categoryButton = categoryButtons[0];
    expect(categoryButton).toBeInTheDocument();

    // Initially closed
    expect(categoryButton).toHaveAttribute('aria-expanded', 'false');

    // Click to open
    await act(async () => {
      fireEvent.click(categoryButton);
    });
    expect(categoryButton).toHaveAttribute('aria-expanded', 'true');

    // Click to close
    await act(async () => {
      fireEvent.click(categoryButton);
    });
    expect(categoryButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('closes Tags drawer when Categories drawer opens', async () => {
    await renderGallery();

    const tagButton = screen.getByRole('button', { name: /Explore Tags/i });
    const categoryButtons = screen.getAllByRole('button', {
      name: /Categories/i,
    });
    const categoryButton = categoryButtons[0];

    // Open Tags
    await act(async () => {
      fireEvent.click(tagButton);
    });
    expect(tagButton).toHaveAttribute('aria-expanded', 'true');

    // Open Categories (should auto-close Tags)
    await act(async () => {
      fireEvent.click(categoryButton);
    });
    expect(categoryButton).toHaveAttribute('aria-expanded', 'true');
    expect(tagButton).toHaveAttribute('aria-expanded', 'false');
  });
});
