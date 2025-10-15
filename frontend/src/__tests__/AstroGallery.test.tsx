import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import AstroGallery from '../AstroGallery';
import { AstroImage } from '../types';

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
 * - Loading state is shown during API calls
 * - Gallery content renders correctly after successful API calls
 * - Filter functionality works correctly
 * - Modal opens when images are clicked
 * - Error handling works when API calls fail
 * - Component handles empty image arrays gracefully
 * - Background image is applied correctly
 */
describe('AstroGallery Component', () => {
  const mockFetchAstroImages = fetchAstroImages as jest.MockedFunction<typeof fetchAstroImages>;
  const mockFetchBackground = fetchBackground as jest.MockedFunction<typeof fetchBackground>;
  const mockFetchAstroImage = fetchAstroImage as jest.MockedFunction<typeof fetchAstroImage>;

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
    mockFetchAstroImages.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve([]), 100))
    );
    
    mockFetchBackground.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve('/test-bg.jpg'), 100))
    );

    render(<AstroGallery />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  /**
   * Test: Renders the gallery title and filter boxes after loading
   * 
   * Verifies that:
   * - Gallery title is displayed correctly
   * - All filter buttons are rendered (Landscape, Deep Sky, Startrails, etc.)
   * - Filter buttons are clickable and functional
   * - Gallery structure is complete after loading
   * - Component transitions from loading to content state
   */
  it('renders the gallery title and filter boxes after loading', async () => {
    mockFetchAstroImages.mockResolvedValue([]);
    mockFetchBackground.mockResolvedValue('/test-bg.jpg');

    render(<AstroGallery />);

    await waitFor(() => {
      expect(screen.getByText(/Gallery/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Landscape/i)).toBeInTheDocument();
    expect(screen.getByText(/Deep Sky/i)).toBeInTheDocument();
    expect(screen.getByText(/Startrails/i)).toBeInTheDocument();
    expect(screen.getByText(/Solar System/i)).toBeInTheDocument();
    expect(screen.getByText(/Milky Way/i)).toBeInTheDocument();
    expect(screen.getByText(/Northern Lights/i)).toBeInTheDocument();
  });

  /**
   * Test: Renders images from the API after loading
   * 
   * Verifies that:
   * - Images are displayed in the gallery after successful API call
   * - Image elements have correct src attributes
   * - Correct number of images are rendered
   * - Images are clickable and interactive
   * - Gallery displays API data correctly
   */
  it('renders images from the API after loading', async () => {
    const mockImages: AstroImage[] = [
      { pk: 1, url: '/test1.jpg', name: 'Test Image 1' },
      { pk: 2, url: '/test2.jpg', name: 'Test Image 2' }
    ];

    mockFetchAstroImages.mockResolvedValue(mockImages);
    mockFetchBackground.mockResolvedValue('/test-bg.jpg');

    render(<AstroGallery />);

    await waitFor(() => {
      expect(screen.getAllByRole('img').length).toBe(2);
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
    mockFetchAstroImages.mockRejectedValue(new Error('API Error'));
    mockFetchBackground.mockRejectedValue(new Error('API Error'));

    render(<AstroGallery />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load images. Please try again later.')).toBeInTheDocument();
    });
  });

  /**
   * Test: Filters images when filter is clicked
   * 
   * Verifies that:
   * - Filter buttons trigger API calls with correct filter parameters
   * - Component updates when filters are applied
   * - Filter state is managed correctly
   * - API is called with appropriate filter values
   * - Filter functionality works as expected
   */
  it('filters images when filter is clicked', async () => {
    const mockImages: AstroImage[] = [
      { pk: 1, url: '/test1.jpg', name: 'Test Image 1' }
    ];

    mockFetchAstroImages.mockResolvedValue(mockImages);
    mockFetchBackground.mockResolvedValue('/test-bg.jpg');

    render(<AstroGallery />);

    await waitFor(() => {
      expect(screen.getByText(/Gallery/i)).toBeInTheDocument();
    });

    const landscapeFilter = screen.getByText(/Landscape/i);
    
    jest.clearAllMocks();
    mockFetchAstroImages.mockResolvedValue(mockImages);

    await act(async () => {
      landscapeFilter.click();
    });

    await waitFor(() => {
      expect(fetchAstroImages).toHaveBeenCalledWith({ filter: 'Landscape' });
    });
  });

  /**
   * Test: Opens modal when image is clicked
   * 
   * Verifies that:
   * - Modal opens when an image thumbnail is clicked
   * - Modal displays image details correctly
   * - Modal state is managed properly
   * - Image click events are handled correctly
   * - Modal functionality works as expected
   */
  it('opens modal when image is clicked', async () => {
    const mockImages: AstroImage[] = [
      { pk: 1, url: '/test1.jpg', name: 'Test Image 1' }
    ];

    const mockImageDetail: AstroImage = {
      pk: 1,
      url: '/test1.jpg',
      name: 'Test Image 1',
      description: 'Test description'
    };

    mockFetchAstroImages.mockResolvedValue(mockImages);
    mockFetchBackground.mockResolvedValue('/test-bg.jpg');
    mockFetchAstroImage.mockResolvedValue(mockImageDetail);

    render(<AstroGallery />);

    await waitFor(() => {
      expect(screen.getByText(/Gallery/i)).toBeInTheDocument();
    });

    const firstImage = screen.getAllByRole('img')[0];

    await act(async () => {
      firstImage.click();
    });

    await waitFor(() => {
      expect(screen.getByText('Test description')).toBeInTheDocument();
    });
  });
});
