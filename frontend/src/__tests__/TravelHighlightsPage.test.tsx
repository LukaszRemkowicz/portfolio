import { act } from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import TravelHighlightsPage from '../components/TravelHighlightsPage';
import { api } from '../api/api';
import { useAppStore } from '../store/useStore';
import { fetchProfile, fetchBackground, fetchSettings } from '../api/services';

// Mock API (direct axios calls)
jest.mock('../api/api');
const mockedApi = api as jest.Mocked<typeof api>;

// Mock Services (store calls)
jest.mock('../api/services', () => ({
  fetchProfile: jest.fn(),
  fetchBackground: jest.fn(),
  fetchSettings: jest.fn(),
}));

describe('TravelHighlightsPage', () => {
  beforeEach(() => {
    jest.resetAllMocks();

    // Re-set mock implementations because resetAllMocks clears them
    (fetchProfile as jest.Mock).mockResolvedValue({});
    (fetchBackground as jest.Mock).mockResolvedValue(null);
    (fetchSettings as jest.Mock).mockResolvedValue({
      programming: true,
      contactForm: true,
      lastimages: true,
      meteors: {
        randomShootingStars: true,
        bolidChance: 0.1,
        bolidMinInterval: 60,
        starPathRange: [50, 500],
        bolidPathRange: [50, 500],
        starStreakRange: [100, 200],
        bolidStreakRange: [20, 100],
        starDurationRange: [0.4, 1.2],
        bolidDurationRange: [0.4, 0.9],
        starOpacityRange: [0.4, 0.8],
        bolidOpacityRange: [0.7, 1.0],
        smokeOpacityRange: [0.5, 0.8],
      },
    });

    useAppStore.setState({
      backgroundUrl: null,
      meteorConfig: null,
      isInitialLoading: false,
      error: null,
    });
  });

  const renderComponent = async (path = '/travel/iceland') => {
    await act(async () => {
      render(
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
      );
    });
  };

  test('renders loading state initially', async () => {
    // Keep promise pending
    mockedApi.get.mockReturnValue(new Promise(() => {}));

    await renderComponent();

    // Check for the loading screen using the testid we added
    expect(screen.getByTestId('loading-screen')).toBeInTheDocument();
  });

  test('renders content after successful fetch', async () => {
    const mockData = {
      country: 'Iceland',
      place: 'Reykjavik',
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

    mockedApi.get.mockResolvedValue({ data: mockData });

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
    mockedApi.get.mockRejectedValue(new Error('Network error'));
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
    mockedApi.get.mockResolvedValue({ data: mockData });

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
