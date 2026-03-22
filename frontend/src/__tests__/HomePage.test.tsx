import { act } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import HomePage from '../HomePage';
import { UserProfile } from '../types';

import { useProfile } from '../hooks/useProfile';
import { useBackground } from '../hooks/useBackground';
import { useSettings } from '../hooks/useSettings';
import { useLatestAstroImages } from '../hooks/useLatestAstroImages';
import { useTravelHighlights } from '../hooks/useTravelHighlights';
import { useAstroImageDetail } from '../hooks/useAstroImageDetail';

jest.mock('../hooks/useProfile');
jest.mock('../hooks/useBackground');
jest.mock('../hooks/useSettings');
jest.mock('../hooks/useLatestAstroImages');
jest.mock('../hooks/useTravelHighlights');
jest.mock('../hooks/useAstroImageDetail');

describe('HomePage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useBackground as jest.Mock).mockReturnValue({ data: '/test-bg.jpg' });
    (useProfile as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    (useLatestAstroImages as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    (useTravelHighlights as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    (useAstroImageDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    (useSettings as jest.Mock).mockReturnValue({
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
      error: null,
    });
  });

  it('shows loading state initially', async () => {
    (useProfile as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

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

    (useProfile as jest.Mock).mockReturnValue({
      data: mockProfile,
      isLoading: false,
      error: null,
    });

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

    expect(screen.getByText('hero.titlePart1')).toBeInTheDocument();
    expect(screen.getByText('This is a test bio')).toBeInTheDocument();
  });

  it('renders the hero background as a high-priority eager image', async () => {
    (useProfile as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    await act(async () => {
      render(
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      );
    });

    const backgroundImage = screen.getByTestId('hero-background-image');
    expect(backgroundImage).toHaveAttribute('src', '/test-bg.jpg');
    expect(backgroundImage).toHaveAttribute('loading', 'eager');
    expect(backgroundImage).toHaveAttribute('fetchpriority', 'high');
  });
});
