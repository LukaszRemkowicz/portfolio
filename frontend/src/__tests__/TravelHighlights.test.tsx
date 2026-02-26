import { act } from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import TravelHighlights from '../components/TravelHighlights';
import { useSettings } from '../hooks/useSettings';
import { useTravelHighlights } from '../hooks/useTravelHighlights';

// Mock Hooks
jest.mock('../hooks/useSettings');
jest.mock('../hooks/useTravelHighlights');

describe('TravelHighlights Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useSettings as jest.Mock).mockReturnValue({
      data: { travelHighlights: true },
    });
    (useTravelHighlights as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
    });
  });

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
    (useTravelHighlights as jest.Mock).mockReturnValue({
      data: mockLocations,
      isLoading: false,
    });

    await act(async () => {
      render(
        <MemoryRouter>
          <TravelHighlights />
        </MemoryRouter>
      );
    });

    expect(await screen.findByText('travel.title')).toBeInTheDocument();
    expect(screen.getByText('Fjord Expedition')).toBeInTheDocument();
  });

  it('renders nothing if feature is disabled', async () => {
    (useSettings as jest.Mock).mockReturnValue({
      data: { travelHighlights: false },
    });

    await act(async () => {
      render(<TravelHighlights />);
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

    (useTravelHighlights as jest.Mock).mockReturnValue({
      data: mockLocations,
      isLoading: false,
    });

    jest.useFakeTimers();
    await act(async () => {
      render(
        <MemoryRouter>
          <TravelHighlights />
        </MemoryRouter>
      );
    });

    // Advance timers to allow initial render effect
    await act(async () => {
      jest.advanceTimersByTime(0);
    });

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
