import { act } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import HomePage from '../HomePage';
import { UserProfile } from '../types';
import * as services from '../api/services';
import { useAppStore } from '../store/useStore';

// Mock the API services
jest.mock('../api/services');

describe('HomePage Component', () => {
  const mockFetchProfile = services.fetchProfile as jest.Mock;
  const mockFetchBackground = services.fetchBackground as jest.Mock;
  const mockFetchSettings = services.fetchSettings as jest.Mock;
  const mockFetchTravelHighlights = services.fetchTravelHighlights as jest.Mock;
  const mockFetchAstroImages = services.fetchAstroImages as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockFetchBackground.mockResolvedValue('/test-bg.jpg');
    mockFetchTravelHighlights.mockResolvedValue([]); // Prevent undefined crash
    mockFetchAstroImages.mockResolvedValue([]); // Prevent undefined crash
    mockFetchSettings.mockResolvedValue({
      programming: true,
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

    // Reset Zustand store to initial state
    useAppStore.setState({
      profile: null,
      backgroundUrl: null,
      images: [],
      features: null,
      meteorConfig: null,
      isInitialLoading: false,
      isImagesLoading: false,
      error: null,
    });
  });

  it('shows loading state initially', async () => {
    mockFetchProfile.mockReturnValue(new Promise(() => {})); // Never resolves

    await act(async () => {
      render(
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/Synchronizing/i)).toBeInTheDocument();
    });
  });

  it('renders profile data after loading', async () => {
    const mockProfile: UserProfile = {
      first_name: 'John',
      last_name: 'Doe',
      short_description: 'Professional Photographer',
      avatar: '/test-avatar.jpg',
      bio: 'This is a test bio',
      about_me_image: null,
      about_me_image2: null,
    };

    mockFetchProfile.mockResolvedValue(mockProfile);

    await act(async () => {
      render(
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      );
    });

    await waitFor(
      () => {
        expect(screen.queryByText(/Synchronizing/i)).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(screen.getByText(/The Beauty of/i)).toBeInTheDocument();
    expect(screen.getByText('This is a test bio')).toBeInTheDocument();
  });
});
