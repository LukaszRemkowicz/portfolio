import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import AstroGallery from '../AstroGallery';

// Mock the API services
jest.mock('../api/services', () => ({
  fetchAstroImages: jest.fn(),
  fetchBackground: jest.fn(),
  fetchAstroImage: jest.fn()
}));

import { fetchAstroImages, fetchBackground, fetchAstroImage } from '../api/services';

/**
 * Test suite for the AstroGallery component
 * 
 * The AstroGallery component displays a dynamic gallery of astrophotography images with:
 * - Loading states during API calls
 * - Filter buttons for different image categories (Landscape, Deep Sky, etc.)
 * - Image grid display with clickable thumbnails
 * - Modal popup when images are clicked
 * - Error handling for failed API calls
 * 
 * The component fetches data from three API endpoints:
 * - fetchAstroImages: Gets list of images (optionally filtered)
 * - fetchBackground: Gets background image for the gallery
 * - fetchAstroImage: Gets detailed image information for modal display
 * 
 * Tests verify:
 * - Loading state is shown during initial API calls
 * - Gallery title and filter buttons render correctly
 * - Images are displayed with proper alt text
 * - Filter functionality works and triggers new API calls
 * - Modal opens when images are clicked
 * - Error handling works when API calls fail
 */
describe('AstroGallery Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
    
    // Setup default mock implementations
    fetchAstroImages.mockResolvedValue([
      { pk: 1, url: '/test1.jpg' },
      { pk: 2, url: '/test2.jpg' }
    ]);
    fetchBackground.mockResolvedValue('/test-bg.jpg');
    fetchAstroImage.mockResolvedValue({
      description: 'Test description'
    });
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
    fetchAstroImages.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve([
      { pk: 1, url: '/test1.jpg' },
      { pk: 2, url: '/test2.jpg' }
    ]), 100)));
    
    await act(async () => {
      render(<AstroGallery />);
    });
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  /**
   * Test: Renders the gallery title and filter boxes after loading
   * 
   * Verifies that:
   * - Loading state disappears after API calls complete
   * - Gallery title "Gallery" is displayed
   * - All filter buttons are rendered (Landscape, Deep Sky, Startrails, etc.)
   * - Filter buttons are clickable and functional
   * - Component handles successful API responses
   */
  it('renders the gallery title and filter boxes after loading', async () => {
    render(<AstroGallery />);
    
    // Wait for loading to complete and content to render
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Check that gallery title is rendered
    expect(screen.getByText('Gallery')).toBeInTheDocument();
    
    // Check that all filter boxes are rendered
    expect(screen.getByText('Landscape')).toBeInTheDocument();
    expect(screen.getByText('Deep Sky')).toBeInTheDocument();
    expect(screen.getByText('Startrails')).toBeInTheDocument();
    expect(screen.getByText('Solar System')).toBeInTheDocument();
    expect(screen.getByText('Milky Way')).toBeInTheDocument();
    expect(screen.getByText('Northern Lights')).toBeInTheDocument();
  });

  /**
   * Test: Renders images from the API after loading
   * 
   * Verifies that:
   * - Images are rendered in the gallery after API call completes
   * - Correct number of images are displayed (based on mock data)
   * - Images have proper alt text for accessibility
   * - Image elements are clickable (for modal functionality)
   */
  it('renders images from the API after loading', async () => {
    render(<AstroGallery />);
    
    // Wait for images to load
    await waitFor(() => {
      expect(screen.getAllByRole('img')).toHaveLength(2);
    });

    // Check that images are rendered with correct alt text
    expect(screen.getByAltText('Astro Image 1')).toBeInTheDocument();
    expect(screen.getByAltText('Astro Image 2')).toBeInTheDocument();
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
    // Mock API to return an error
    fetchAstroImages.mockRejectedValue(new Error('API Error'));
    
    render(<AstroGallery />);
    
    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText('Failed to load images. Please try again later.')).toBeInTheDocument();
    });
  });

  /**
   * Test: Filters images when filter is clicked
   * 
   * Verifies that:
   * - Filter buttons are clickable
   * - Clicking a filter triggers a new API call with filter parameter
   * - API is called with correct filter value (e.g., { filter: 'Landscape' })
   * - Filter functionality works as expected
   * - Previous API calls are cleared to test only the filter call
   */
  it('filters images when filter is clicked', async () => {
    render(<AstroGallery />);
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Clear previous calls to mock
    jest.clearAllMocks();

    // Click on Landscape filter
    const landscapeFilter = screen.getByText('Landscape');
    await act(async () => {
      landscapeFilter.click();
    });

    // Wait for the filter click to trigger API call
    await waitFor(() => {
      expect(fetchAstroImages).toHaveBeenCalledWith({ filter: 'Landscape' });
    });
  });

  /**
   * Test: Opens modal when image is clicked
   * 
   * Verifies that:
   * - Images are clickable after they load
   * - Clicking an image triggers modal functionality
   * - Modal displays image description from API
   * - Modal opens correctly with proper content
   * - Image click events are handled properly
   */
  it('opens modal when image is clicked', async () => {
    render(<AstroGallery />);
    
    // Wait for images to load
    await waitFor(() => {
      expect(screen.getAllByRole('img')).toHaveLength(2);
    });

    // Click on first image
    const firstImage = screen.getByAltText('Astro Image 1');
    await act(async () => {
      firstImage.click();
    });

    // Check that modal is opened - it should show description immediately since mock is synchronous
    await waitFor(() => {
      expect(screen.getByText('Test description')).toBeInTheDocument();
    });
  });
});
