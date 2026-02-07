import { act } from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import '@testing-library/jest-dom';
import TravelHighlights from '../components/TravelHighlights';
import { useTravelHighlights } from '../hooks/useTravelHighlights';
import { useSettings } from '../hooks/useSettings';

// Mock Hooks
jest.mock('../hooks/useTravelHighlights');
jest.mock('../hooks/useSettings');
jest.mock('../api/services', () => ({
  fetchTravelHighlightDetailBySlug: jest.fn(),
}));

describe('TravelHighlights Component', () => {
  const mockUseTravelHighlights = useTravelHighlights as jest.Mock;
  const mockUseSettings = useSettings as jest.Mock;
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient.clear();
    mockUseSettings.mockReturnValue({
      data: { travelHighlights: true },
      isLoading: false,
    });
  });

  const renderWithClient = (ui: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>{ui}</MemoryRouter>
      </QueryClientProvider>
    );
  };

  it('renders content when loaded with data', async () => {
    const mockLocations = [
      {
        pk: 1,
        place: {
          name: '',
          country: 'Norway',
        },
        country_slug: 'norway',
        highlight_name: 'Fjord Expedition',
        images: [
          {
            pk: 101,
            url: 'norway.jpg',
            thumbnail_url: 'norway_thumb.jpg',
            description: 'A beautiful fjord',
          },
        ],
      },
    ];
    mockUseTravelHighlights.mockReturnValue({
      data: mockLocations,
      isLoading: false,
    });

    await act(async () => {
      renderWithClient(<TravelHighlights />);
    });

    expect(await screen.findByText('travel.title')).toBeInTheDocument();
    expect(screen.getByText('Fjord Expedition')).toBeInTheDocument();
  });

  it('renders nothing if feature is disabled', async () => {
    mockUseSettings.mockReturnValue({
      data: { travelHighlights: false },
      isLoading: false,
    });

    await act(async () => {
      renderWithClient(<TravelHighlights />);
    });
    expect(screen.queryByText('travel.title')).not.toBeInTheDocument();
  });

  it('cycles images automatically', async () => {
    const mockLocations = [
      {
        pk: 1,
        place: {
          name: '',
          country: 'Multi Image',
        },
        country_slug: 'multi',
        images: [
          { url: 'img1.jpg', thumbnail_url: 'thumb1.jpg', description: '1' },
          { url: 'img2.jpg', thumbnail_url: 'thumb2.jpg', description: '2' },
        ],
      },
    ];
    mockUseTravelHighlights.mockReturnValue({
      data: mockLocations,
      isLoading: false,
    });

    jest.useFakeTimers();
    await act(async () => {
      renderWithClient(<TravelHighlights />);
    });

    // Advance timers to allow initial render effect
    await act(async () => {
      jest.advanceTimersByTime(0);
    });

    // Now we can find the text
    expect(screen.getAllByText('Multi Image').length).toBeGreaterThan(0);

    const images = screen.getAllByRole('img');
    expect(images).toHaveLength(2);

    // First active
    expect(images[0]).toHaveClass('active');
    expect(images[1]).not.toHaveClass('active');

    act(() => {
      jest.advanceTimersByTime(7000);
    });

    // Second active
    expect(images[0]).not.toHaveClass('active');
    expect(images[1]).toHaveClass('active');

    jest.useRealTimers();
  });
});
