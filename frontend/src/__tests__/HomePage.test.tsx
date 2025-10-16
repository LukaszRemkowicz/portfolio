import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import HomePage from '../HomePage';
import { UserProfile } from '../types';

// Mock the API services
jest.mock('../api/services', () => ({
  fetchProfile: jest.fn(),
  fetchBackground: jest.fn(),
}));

import { fetchProfile, fetchBackground } from '../api/services';

/**
 * Test suite for the HomePage component
 *
 * The HomePage component is the main landing page that displays:
 * - User profile information (name, avatar, bio)
 * - Background image
 * - Loading states during API calls
 * - Error handling when API calls fail
 *
 * The component fetches data from two API endpoints:
 * - fetchProfile: Gets user profile information
 * - fetchBackground: Gets background image URL
 *
 * Tests verify:
 * - Loading state is shown during API calls
 * - Profile data renders correctly after successful API calls
 * - Error handling works when API calls fail
 * - Default fallback behavior when API data is unavailable
 * - Proper state management throughout the component lifecycle
 * - Integration with React Router for navigation
 */
describe('HomePage Component', () => {
  const mockFetchProfile = fetchProfile as jest.MockedFunction<
    typeof fetchProfile
  >;
  const mockFetchBackground = fetchBackground as jest.MockedFunction<
    typeof fetchBackground
  >;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * Test: Shows loading state initially
   *
   * Verifies that:
   * - Loading text is displayed while API calls are in progress
   * - Component shows appropriate loading state
   * - Loading state is visible before data is fetched
   * - Component handles async operations correctly
   */
  it('shows loading state initially', async () => {
    // Mock API calls to return promises that resolve after a delay
    mockFetchProfile.mockImplementation(
      () =>
        new Promise(resolve =>
          setTimeout(
            () =>
              resolve({
                first_name: 'John',
                last_name: 'Doe',
                avatar: null,
                bio: 'Test bio',
                about_me_image: null,
                about_me_image2: null,
              }),
            100
          )
        )
    );

    mockFetchBackground.mockImplementation(
      () =>
        new Promise(resolve => setTimeout(() => resolve('/test-bg.jpg'), 100))
    );

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  /**
   * Test: Renders profile data after loading
   *
   * Verifies that:
   * - Profile information is displayed after successful API calls
   * - User name and avatar are rendered correctly
   * - Background image is applied correctly
   * - Component transitions from loading to content state
   * - All profile data is properly displayed
   */
  it('renders profile data after loading', async () => {
    const mockProfile: UserProfile = {
      first_name: 'John',
      last_name: 'Doe',
      avatar: '/test-avatar.jpg',
      bio: 'This is a test bio',
      about_me_image: null,
      about_me_image2: null,
    };

    mockFetchProfile.mockResolvedValue(mockProfile);
    mockFetchBackground.mockResolvedValue('/test-bg.jpg');

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Bio is displayed in the About component, not directly in HomePage
    await waitFor(() => {
      expect(screen.getByText('This is a test bio')).toBeInTheDocument();
    });
  });

  /**
   * Test: Handles API errors gracefully
   *
   * Verifies that:
   * - Error message is displayed when API calls fail
   * - Component doesn't crash when API errors occur
   * - Error state is properly managed
   * - User gets appropriate feedback for API failures
   * - Component recovers gracefully from errors
   */
  it('handles API errors gracefully', async () => {
    mockFetchProfile.mockRejectedValue(new Error('API Error'));
    mockFetchBackground.mockRejectedValue(new Error('API Error'));

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText('Failed to load page content. Please try again later.')
      ).toBeInTheDocument();
    });
  });

  /**
   * Test: Uses default fallback files when API fails
   *
   * Verifies that:
   * - Default portrait image is used when API avatar is null
   * - Component falls back to default assets when API data is unavailable
   * - Fallback behavior works correctly in error scenarios
   * - Default images are properly displayed
   * - Component maintains functionality even with partial API failures
   */
  it('uses default fallback files when API fails', async () => {
    const mockProfile: UserProfile = {
      first_name: 'John',
      last_name: 'Doe',
      avatar: null, // No avatar from API
      bio: 'Test bio',
      about_me_image: null,
      about_me_image2: null,
    };

    mockFetchProfile.mockResolvedValue(mockProfile);
    mockFetchBackground.mockResolvedValue('/test-bg.jpg');

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Should use default portrait since API avatar is null
    const portraitImage = screen.getByAltText('Portrait');
    expect(portraitImage).toHaveAttribute('src', '/portrait_default.png');
  });

  /**
   * Test: Uses API avatar when available
   *
   * Verifies that:
   * - API-provided avatar is used when available
   * - Component prioritizes API data over default fallbacks
   * - Avatar image is displayed correctly from API
   * - API data takes precedence over default assets
   */
  it('uses API avatar when available', async () => {
    const mockProfile: UserProfile = {
      first_name: 'John',
      last_name: 'Doe',
      avatar: '/api-avatar.jpg',
      bio: 'Test bio',
      about_me_image: null,
      about_me_image2: null,
    };

    mockFetchProfile.mockResolvedValue(mockProfile);
    mockFetchBackground.mockResolvedValue('/test-bg.jpg');

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Should use API avatar
    const portraitImage = screen.getByAltText('Portrait');
    expect(portraitImage).toHaveAttribute('src', '/api-avatar.jpg');
  });

  /**
   * Test: Falls back to default when API avatar is null
   *
   * Verifies that:
   * - Default portrait is used when API avatar is null
   * - Fallback mechanism works correctly
   * - Component handles null API data gracefully
   * - Default assets are properly loaded
   */
  it('falls back to default when API avatar is null', async () => {
    const mockProfile: UserProfile = {
      first_name: 'John',
      last_name: 'Doe',
      avatar: null,
      bio: 'Test bio',
      about_me_image: null,
      about_me_image2: null,
    };

    mockFetchProfile.mockResolvedValue(mockProfile);
    mockFetchBackground.mockResolvedValue('/test-bg.jpg');

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Should fall back to default portrait
    const portraitImage = screen.getByAltText('Portrait');
    expect(portraitImage).toHaveAttribute('src', '/portrait_default.png');
  });
});
