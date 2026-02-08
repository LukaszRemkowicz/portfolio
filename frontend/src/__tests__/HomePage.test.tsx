import { act } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import { HelmetProvider } from 'react-helmet-async';
import HomePage from '../HomePage';
import { UserProfile } from '../types';
import { useProfile } from '../hooks/useProfile';
import { useBackground } from '../hooks/useBackground';
import { useSettings } from '../hooks/useSettings';
import { useTravelHighlights } from '../hooks/useTravelHighlights';
import { useAstroImages } from '../hooks/useAstroImages';

// Mock the hooks
jest.mock('../hooks/useProfile');
jest.mock('../hooks/useBackground');
jest.mock('../hooks/useSettings');
jest.mock('../hooks/useTravelHighlights');
jest.mock('../hooks/useAstroImages');

describe('HomePage Component', () => {
  const mockUseProfile = useProfile as jest.Mock;
  const mockUseBackground = useBackground as jest.Mock;
  const mockUseSettings = useSettings as jest.Mock;
  const mockUseTravelHighlights = useTravelHighlights as jest.Mock;
  const mockUseAstroImages = useAstroImages as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockUseBackground.mockReturnValue({
      data: '/test-bg.jpg',
      isLoading: false,
    });
    mockUseTravelHighlights.mockReturnValue({ data: [], isLoading: false });
    mockUseAstroImages.mockReturnValue({ data: [], isLoading: false });
    mockUseSettings.mockReturnValue({
      data: {
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
      },
      isLoading: false,
    });
  });

  it('shows loading state initially', async () => {
    mockUseProfile.mockReturnValue({ data: null, isLoading: true });

    await act(async () => {
      render(
        <HelmetProvider>
          <MemoryRouter>
            <HomePage />
          </MemoryRouter>
        </HelmetProvider>
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

    mockUseProfile.mockReturnValue({ data: mockProfile, isLoading: false });

    await act(async () => {
      render(
        <HelmetProvider>
          <MemoryRouter>
            <HomePage />
          </MemoryRouter>
        </HelmetProvider>
      );
    });

    await waitFor(
      () => {
        expect(screen.queryByText(/Synchronizing/i)).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(screen.getByText('hero.titlePart1')).toBeInTheDocument();
    expect(screen.getByText('This is a test bio')).toBeInTheDocument();
  });
});
