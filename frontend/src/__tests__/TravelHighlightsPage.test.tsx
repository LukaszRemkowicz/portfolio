import { act } from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import TravelHighlightsPage from '../components/TravelHighlightsPage';
import { useTravelHighlightDetail } from '../hooks/useTravelHighlightDetail';
import { useBackground } from '../hooks/useBackground';
import { useAstroImageDetail } from '../hooks/useAstroImageDetail';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HelmetProvider } from 'react-helmet-async';

// Mock Hooks
jest.mock('../hooks/useTravelHighlightDetail');
jest.mock('../hooks/useBackground');
jest.mock('../hooks/useAstroImageDetail');

describe('TravelHighlightsPage', () => {
  const mockUseTravelHighlightDetail = useTravelHighlightDetail as jest.Mock;
  const mockUseBackground = useBackground as jest.Mock;
  const mockUseAstroImageDetail = useAstroImageDetail as jest.Mock;
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  beforeEach(() => {
    jest.resetAllMocks();
    queryClient.clear();
    mockUseBackground.mockReturnValue({
      data: '/test-bg.jpg',
      isLoading: false,
    });
    mockUseAstroImageDetail.mockReturnValue({ data: null, isLoading: false });
  });

  const renderComponent = async (path = '/travel/iceland') => {
    await act(async () => {
      render(
        <HelmetProvider>
          <QueryClientProvider client={queryClient}>
            <MemoryRouter initialEntries={[path]}>
              <Routes>
                <Route
                  path='/travel/:countrySlug'
                  element={<TravelHighlightsPage />}
                />
                <Route
                  path='/travel/:countrySlug/:placeSlug'
                  element={<TravelHighlightsPage />}
                />
              </Routes>
            </MemoryRouter>
          </QueryClientProvider>
        </HelmetProvider>
      );
    });
  };

  test('renders loading state initially', async () => {
    mockUseTravelHighlightDetail.mockReturnValue({
      data: null,
      isLoading: true,
    });

    await renderComponent();

    expect(screen.getByTestId('loading-screen')).toBeInTheDocument();
  });

  test('renders content after successful fetch', async () => {
    const mockData = {
      place: {
        name: 'Reykjavik',
        country: 'Iceland',
      },
      story: '<p>Beautiful aurora</p>',
      adventure_date: 'Jan 2026',
      highlight_name: 'Northern Expedition',
      background_image: 'iceland.jpg',
      images: [
        {
          pk: 1,
          name: 'Aurora Borealis',
          url: '/aurora.jpg',
          thumbnail_url: '/aurora_thumb.jpg',
          description: 'Green lights',
        },
      ],
    };

    mockUseTravelHighlightDetail.mockReturnValue({
      data: mockData,
      isLoading: false,
    });

    await renderComponent();

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(
      () => {
        expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Use findBy which is implicitly waitFor + getBy
    expect(await screen.findByText('Reykjavik, Iceland')).toBeInTheDocument();

    expect(
      screen.getByText('Exploring the cosmic wonders of Reykjavik, Iceland')
    ).toBeInTheDocument();
    expect(screen.getByText('Northern Expedition')).toBeInTheDocument();
    expect(screen.getByText('ADVENTURE DATE | JAN 2026')).toBeInTheDocument();
    expect(screen.getByText('Aurora Borealis')).toBeInTheDocument();
  });

  test('handles API error gracefully', async () => {
    mockUseTravelHighlightDetail.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Network error'),
    });
    // Spy to suppress console error
    const consoleSpy = jest
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    await renderComponent();

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(
      () => {
        expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(
      await screen.findByText(
        'Failed to load travel highlights. Please check the URL and try again.'
      )
    ).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  test('opens modal on image click', async () => {
    const mockData = {
      country: 'Iceland',
      images: [
        {
          pk: 1,
          name: 'Click Me',
          url: '/click.jpg',
        },
      ],
    };
    mockUseTravelHighlightDetail.mockReturnValue({
      data: mockData,
      isLoading: false,
    });

    await renderComponent();

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(
      () => {
        expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    await waitFor(
      () => {
        expect(screen.getByAltText('Click Me')).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    const image = screen.getByAltText('Click Me');

    await act(async () => {
      fireEvent.click(image);
    });

    // Look for modal using the testid we added
    const modal = await screen.findByTestId(
      'image-modal',
      {},
      { timeout: 3000 }
    );
    expect(modal).toBeInTheDocument();
  });
});
