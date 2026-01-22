import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import TravelHighlights from '../components/TravelHighlights';
import { fetchTravelHighlights } from '../api/services';
import { useAppStore } from '../store/useStore';

// Mock Services
jest.mock('../api/services', () => ({
  fetchTravelHighlights: jest.fn().mockResolvedValue([]),
  fetchProfile: jest.fn().mockResolvedValue({}),
  fetchBackground: jest.fn().mockResolvedValue(null),
  fetchEnabledFeatures: jest.fn().mockResolvedValue({}),
}));

describe('TravelHighlights Component', () => {
  const mockedFetchTravelHighlights = fetchTravelHighlights as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    useAppStore.setState({
      features: { travelHighlights: true },
    });
  });

  it('renders content when loaded with data', async () => {
    const mockLocations = [
      {
        pk: 1,
        country_name: 'Norway',
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
    mockedFetchTravelHighlights.mockResolvedValue(mockLocations);

    await act(async () => {
      render(
        <MemoryRouter>
          <TravelHighlights />
        </MemoryRouter>
      );
    });

    expect(await screen.findByText('Travel Highlights')).toBeInTheDocument();
    expect(screen.getByText('Fjord Expedition')).toBeInTheDocument();
  });

  it('renders nothing if feature is disabled', async () => {
    useAppStore.setState({
      features: { travelHighlights: false },
    });

    await act(async () => {
      render(<TravelHighlights />);
    });
    expect(screen.queryByText('Travel Highlights')).not.toBeInTheDocument();
  });

  it('cycles images automatically', async () => {
    const mockLocations = [
      {
        pk: 1,
        country_name: 'Multi Image',
        country_slug: 'multi',
        images: [
          { url: 'img1.jpg', thumbnail_url: 'thumb1.jpg', description: '1' },
          { url: 'img2.jpg', thumbnail_url: 'thumb2.jpg', description: '2' },
        ],
      },
    ];
    mockedFetchTravelHighlights.mockResolvedValue(mockLocations);

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

    // Now we can find the text
    // Use getBy instead of findBy since we advanced timers
    // Use getAllByText because it appears in title and location
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
