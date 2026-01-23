import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
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
  const mockFetchEnabledFeatures = services.fetchEnabledFeatures as jest.Mock;
  const mockFetchAstroImages = services.fetchAstroImages as jest.Mock;
  const mockFetchTravelHighlights = services.fetchTravelHighlights as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockFetchBackground.mockResolvedValue('/test-bg.jpg');
    mockFetchEnabledFeatures.mockResolvedValue({ programming: true });
    mockFetchAstroImages.mockResolvedValue([]);
    mockFetchTravelHighlights.mockResolvedValue([]);

    // Reset Zustand store to initial state
    useAppStore.setState({
      profile: null,
      backgroundUrl: null,
      images: [],
      features: null,
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
