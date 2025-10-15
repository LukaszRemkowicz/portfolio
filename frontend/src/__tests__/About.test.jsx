import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import About from '../About';

// Mock the API services
jest.mock('../api/services', () => ({
  fetchProfile: jest.fn()
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
 * The component fetches data from the API and conditionally renders content
 * based on whether profile data is available.
 * 
 * Tests verify:
 * - Conditional rendering when no profile data exists
 * - Proper display of bio text with line breaks
 * - Image rendering with correct attributes
 */
describe('About Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * Test: Renders nothing when profile is not loaded
   * 
   * Verifies that the component handles the case when:
   * - API returns null/undefined profile data
   * - Component should not render any content
   * - Container should be empty (null firstChild)
   */
  it('renders nothing when profile is not loaded', () => {
    fetchProfile.mockResolvedValue(null);
    const { container } = render(<About />);
    expect(container.firstChild).toBeNull();
  });

  /**
   * Test: Renders profile bio after loading
   * 
   * Verifies that when profile data is available:
   * - The "About me" title is displayed
   * - Bio text is rendered correctly
   * - Multi-line bio text is split into separate lines
   * - Each line is displayed as a separate element
   */
  it('renders profile bio after loading', async () => {
    fetchProfile.mockResolvedValue({
      bio: 'This is a test bio\nWith multiple lines',
      about_me_image: '/test-image.jpg'
    });

    render(<About />);
    
    await waitFor(() => {
      expect(screen.getByText('About me')).toBeInTheDocument();
      expect(screen.getByText('This is a test bio')).toBeInTheDocument();
      expect(screen.getByText('With multiple lines')).toBeInTheDocument();
    });
  });

  /**
   * Test: Renders about me image when available
   * 
   * Verifies that when profile includes an image:
   * - The "About me" title is displayed
   * - Image element is rendered with correct alt text
   * - Image src attribute points to the correct file path
   * - Image is accessible with proper alt text
   */
  it('renders about me image when available', async () => {
    fetchProfile.mockResolvedValue({
      bio: 'Test bio',
      about_me_image: '/test-image.jpg'
    });

    render(<About />);
    
    await waitFor(() => {
      expect(screen.getByText('About me')).toBeInTheDocument();
      const image = screen.getByAltText('About me');
      expect(image).toHaveAttribute('src', '/test-image.jpg');
    });
  });
});
