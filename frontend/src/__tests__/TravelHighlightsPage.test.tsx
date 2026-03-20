import { act } from 'react';
import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import TravelHighlightsPage from '../components/TravelHighlightsPage';
import { useBackground } from '../hooks/useBackground';
import { useImageUrls } from '../hooks/useImageUrls';
import { useTravelHighlightDetail } from '../hooks/useTravelHighlightDetail';
import { useSettings } from '../hooks/useSettings';
import { useAstroImageDetail } from '../hooks/useAstroImageDetail';

// Mock Services
jest.mock('../hooks/useBackground');
jest.mock('../hooks/useImageUrls');
jest.mock('../hooks/useTravelHighlightDetail');
jest.mock('../hooks/useSettings');
jest.mock('../hooks/useAstroImageDetail');

jest.mock('../api/routes', () => ({
  API_ROUTES: {
    travelBySlug: '/api/v1/travel/',
  },
  ASSETS: {
    galleryFallback: '/test-fallback.jpg',
  },
}));

jest.mock('../api/media', () => ({
  getMediaUrl: (path: string) => path,
}));

describe('TravelHighlightsPage', () => {
  beforeEach(() => {
    jest.resetAllMocks();

    (useSettings as jest.Mock).mockReturnValue({
      data: {
        programming: true,
        meteors: null,
      },
      isLoading: false,
    });

    (useBackground as jest.Mock).mockReturnValue({
      data: null,
    });

    (useImageUrls as jest.Mock).mockReturnValue({
      data: {},
    });

    (useAstroImageDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
    });

    (useTravelHighlightDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });
  });

  const renderComponent = async (
    path = '/travel/iceland/reykjavik/jan2024'
  ) => {
    await act(async () => {
      render(
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route
              path='/travel/:countrySlug/:placeSlug/:dateSlug'
              element={<TravelHighlightsPage />}
            />
          </Routes>
        </MemoryRouter>
      );
    });
  };

  test('renders loading state initially', async () => {
    await renderComponent();
    expect(screen.getByTestId('loading-screen')).toBeInTheDocument();
  });

  test('renders content after successful fetch', async () => {
    const mockData = {
      full_location: 'Reykjavik, Iceland',
      story: '<p>Beautiful aurora</p>',
      adventure_date: 'Jan 2026',
      highlight_name: 'Northern Expedition',
      highlight_title: 'Exploring the cosmic wonders of Reykjavik, Iceland',
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

    (useTravelHighlightDetail as jest.Mock).mockReturnValue({
      data: mockData,
      isLoading: false,
      error: null,
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
    (useTravelHighlightDetail as jest.Mock).mockReturnValue({
      data: undefined,
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

  test('opens modal on image click via URL parameter', async () => {
    const mockData = {
      images: [
        {
          pk: 1,
          slug: 'click-me',
          name: 'Click Me',
          url: '/click.jpg',
        },
      ],
    };
    (useTravelHighlightDetail as jest.Mock).mockReturnValue({
      data: mockData,
      isLoading: false,
      error: null,
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

    // Modal should open (URL routing is handled by React Router in MemoryRouter)
    const modal = await screen.findByTestId(
      'image-modal',
      {},
      { timeout: 3000 }
    );
    expect(modal).toBeInTheDocument();
  });

  test('fetches and uses full-resolution image URLs', async () => {
    const mockData = {
      images: [
        {
          pk: 1,
          slug: 'aurora-borealis',
          name: 'Aurora',
          thumbnail_url: '/thumbs/aurora.jpg',
        },
      ],
    };

    const mockImageUrls = {
      '1': 'https://cdn.example.com/full/aurora.jpg?s=signature',
    };

    (useTravelHighlightDetail as jest.Mock).mockReturnValue({
      data: mockData,
      isLoading: false,
      error: null,
    });
    (useImageUrls as jest.Mock).mockReturnValue({
      data: mockImageUrls,
    });

    await renderComponent();

    // 1. Verify thumbnail is rendered initially
    const image = await screen.findByAltText('Aurora');
    expect(image).toHaveAttribute(
      'src',
      expect.stringContaining('/thumbs/aurora.jpg')
    );

    // 3. Open modal and check for FULL RES url
    await act(async () => {
      fireEvent.click(image);
    });

    // Wait for the full resolution URL to appear
    await waitFor(async () => {
      // Scope to modal to avoid confusion with thumbnail
      const modal = screen.getByTestId('image-modal');
      expect(modal).toBeInTheDocument();

      const modalImages = within(modal).getAllByRole('img');
      const modalImage = modalImages[0];

      expect(modalImage).toHaveAttribute(
        'src',
        'https://cdn.example.com/full/aurora.jpg?s=signature'
      );
    });
  });
});
