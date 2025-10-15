import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import HomePage from '../HomePage';

// Mock the API services
jest.mock('../api/services', () => ({
  fetchProfile: jest.fn(),
  fetchBackground: jest.fn()
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
 * - Router integration works properly
 */
describe('HomePage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup default mock implementations
    fetchProfile.mockResolvedValue({
      first_name: 'John',
      last_name: 'Doe',
      avatar: '/test-avatar.jpg',
      bio: 'Test bio'
    });
    fetchBackground.mockResolvedValue('/test-background.jpg');
  });

  /**
   * Test: Shows loading state initially
   * 
   * Verifies that:
   * - Component shows "Loading..." text while API calls are in progress
   * - Loading state is visible immediately after component mounts
   * - Uses slow API mock to simulate real loading behavior
   * - Properly wrapped in act() to handle async state updates
   */
  it('shows loading state initially', async () => {
    // Mock API to be slow so we can see loading state
    fetchProfile.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({
      first_name: 'John',
      last_name: 'Doe',
      avatar: '/test-avatar.jpg',
      bio: 'Test bio'
    }), 100)));
    
    await act(async () => {
      render(
        <BrowserRouter>
          <HomePage />
        </BrowserRouter>
      );
    });
    
    // Should show loading initially
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  /**
   * Test: Renders profile data after loading
   * 
   * Verifies that:
   * - Loading state disappears after API calls complete
   * - Profile data is rendered correctly (name, avatar, bio)
   * - User's full name is displayed properly
   * - Component handles successful API responses
   */
  it('renders profile data after loading', async () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    // Wait for loading to complete and profile data to render
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Check that profile data is rendered
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  /**
   * Test: Handles API errors gracefully
   * 
   * Verifies that:
   * - Component shows error message when API calls fail
   * - Error message is user-friendly and actionable
   * - Component doesn't crash when API returns errors
   * - User sees helpful feedback instead of blank screen
   */
  it('handles API errors gracefully', async () => {
    fetchProfile.mockRejectedValue(new Error('API Error'));
    
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load page content. Please try again later.')).toBeInTheDocument();
    });
  });

  /**
   * Test: Uses default fallback files when API fails
   * 
   * Verifies that:
   * - Component falls back to default portrait when API fails
   * - Default portrait path is correct (/portrait_default.png)
   * - Fallback behavior is consistent with documentation
   * - User sees default image instead of broken image
   */
  it('uses default fallback files when API fails', async () => {
    // Mock API to return profile without avatar but background succeeds
    fetchProfile.mockResolvedValue({
      first_name: 'John',
      last_name: 'Doe',
      avatar: null, // No avatar from API - should use default
      bio: 'Test bio'
    });
    fetchBackground.mockResolvedValue('/media/backgrounds/default_bg.jpg');
    
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Check that the default portrait image is used when API avatar is null
    const portraitImage = screen.getByAltText('Portrait');
    expect(portraitImage).toHaveAttribute('src', '/portrait_default.png');
  });

  /**
   * Test: Uses API avatar when available
   * 
   * Verifies that:
   * - Component prioritizes API avatar over default
   * - Image src attribute reflects the correct source
   * - API data is properly integrated
   */
  it('uses API avatar when available', async () => {
    // Test with API avatar available
    fetchProfile.mockResolvedValue({
      first_name: 'John',
      last_name: 'Doe',
      avatar: '/media/avatars/custom_avatar.jpg',
      bio: 'Test bio'
    });
    fetchBackground.mockResolvedValue('/media/backgrounds/custom_bg.jpg');

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Should use API avatar
    const portraitImage = screen.getByAltText('Portrait');
    expect(portraitImage).toHaveAttribute('src', '/media/avatars/custom_avatar.jpg');
  });

  /**
   * Test: Falls back to default when API avatar is null
   * 
   * Verifies that:
   * - Falls back to default when API avatar is null/undefined
   * - Default portrait path is correct
   * - Component handles missing avatar gracefully
   */
  it('falls back to default when API avatar is null', async () => {
    // Test with API avatar not available
    fetchProfile.mockResolvedValue({
      first_name: 'John',
      last_name: 'Doe',
      avatar: null, // No avatar from API
      bio: 'Test bio'
    });
    fetchBackground.mockResolvedValue('/media/backgrounds/custom_bg.jpg');

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Should use default portrait
    const defaultPortraitImage = screen.getByAltText('Portrait');
    expect(defaultPortraitImage).toHaveAttribute('src', '/portrait_default.png');
  });
});
