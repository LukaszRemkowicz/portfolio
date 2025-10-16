import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import About from '../About';
import { UserProfile } from '../types';

// Mock the API services
jest.mock('../api/services', () => ({
  fetchProfile: jest.fn(),
}));

import { fetchProfile } from '../api/services';

/**
 * Test suite for the About component
 *
 * The About component displays user profile information including:
 * - A section title "About me"
 * - User bio text (can contain multiple lines)
 * - An optional profile image
 *
 * The component expects a UserProfile object with:
 * - bio: string - The user's biography text
 * - about_me_image: string | null - Optional profile image URL
 *
 * The component handles:
 * - Loading states while profile data is being fetched
 * - Conditional rendering of the profile image
 * - Display of multi-line bio text with proper formatting
 *
 * Testing Strategy:
 * - Verify component renders nothing when profile is not loaded
 * - Test bio text rendering after profile loads
 * - Test conditional image rendering when image is available
 * - Ensure proper handling of null/undefined profile data
 */

const mockFetchProfile = fetchProfile as jest.MockedFunction<
  typeof fetchProfile
>;

describe('About Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * Test: Renders nothing when profile is not loaded
   *
   * Verifies that the About component doesn't render any content
   * when the profile is not loaded from API. This ensures
   * the component gracefully handles missing data.
   */
  it('renders nothing when profile is not loaded', () => {
    mockFetchProfile.mockResolvedValue(null);
    const { container } = render(<About />);
    expect(container.firstChild).toBeNull();
  });

  /**
   * Test: Renders profile bio after loading
   *
   * Verifies that the About component correctly displays the user's
   * biography text when profile data is available. Tests that:
   * - The "About me" section title is displayed
   * - The bio text content is rendered correctly
   * - Multi-line bio text is handled properly
   */
  it('renders profile bio after loading', async () => {
    const mockProfile: UserProfile = {
      first_name: 'John',
      last_name: 'Doe',
      avatar: null,
      bio: 'This is a test bio with multiple lines.\nIt should display correctly.',
      about_me_image: null,
      about_me_image2: null,
    };

    mockFetchProfile.mockResolvedValue(mockProfile);
    render(<About />);

    await waitFor(() => {
      expect(screen.getByText('About me')).toBeInTheDocument();
    });

    expect(
      screen.getByText(/This is a test bio with multiple lines/)
    ).toBeInTheDocument();
  });

  /**
   * Test: Renders about me image when available
   *
   * Verifies that the About component correctly displays the profile
   * image when available in the profile data. Tests that:
   * - The image element is rendered with correct src attribute
   * - The image has proper alt text
   * - The component handles image URLs correctly
   */
  it('renders about me image when available', async () => {
    const mockProfile: UserProfile = {
      first_name: 'John',
      last_name: 'Doe',
      avatar: null,
      bio: 'Test bio',
      about_me_image: '/test-image.jpg',
      about_me_image2: null,
    };

    mockFetchProfile.mockResolvedValue(mockProfile);
    render(<About />);

    await waitFor(() => {
      expect(screen.getByText('About me')).toBeInTheDocument();
    });

    const image = screen.getByAltText('About me');
    expect(image).toHaveAttribute('src', '/test-image.jpg');
  });
});
