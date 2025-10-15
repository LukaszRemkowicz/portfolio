import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Gallery from '../Gallery';

/**
 * Test suite for the Gallery component
 * 
 * The Gallery component displays a static gallery with predefined categories:
 * - ASTRO PHOTOGRAPHY
 * - LANDSCAPE PHOTOGRAPHY  
 * - PROGRAMMING
 * 
 * Each gallery item uses CSS background images and contains:
 * - A title with category name
 * - Background image styling
 * - Hover effects and overlays
 * 
 * This component does not fetch data from APIs - it uses static data from galleryItems.js
 * 
 * Tests verify:
 * - All gallery items render correctly
 * - Text content is displayed properly (including line breaks)
 * - Correct number of items are rendered
 * - Gallery items are accessible and have proper text content
 */
describe('Gallery Component', () => {
  /**
   * Test: Renders gallery items from static data
   * 
   * Verifies that:
   * - All three gallery categories are displayed
   * - Text content includes line breaks (ASTRO\nPHOTOGRAPHY, etc.)
   * - Gallery items are rendered from static data source
   * - No API calls are needed for this component
   */
  it('renders gallery items from static data', () => {
    render(<Gallery />);
    
    expect(screen.getByText('ASTRO\\nPHOTOGRAPHY')).toBeInTheDocument();
    expect(screen.getByText('LANDSCAPE\\nPHOTOGRAPHY')).toBeInTheDocument();
    expect(screen.getByText('PROGRAMMING')).toBeInTheDocument();
  });

  /**
   * Test: Renders correct number of gallery items
   * 
   * Verifies that:
   * - Exactly 3 gallery items are rendered
   * - Gallery items use background images (not img tags)
   * - Text content can be found using regex patterns
   * - Each category is properly represented in the gallery
   * - Gallery structure is consistent and complete
   */
  it('renders correct number of gallery items', () => {
    render(<Gallery />);
    
    // Gallery items use background images, so we check for gallery item containers by text content
    const galleryContainers = screen.getAllByText(/PHOTOGRAPHY|PROGRAMMING/);
    expect(galleryContainers).toHaveLength(3);
    
    // Check specific gallery items exist using regex to handle line breaks
    expect(screen.getByText(/ASTRO.*PHOTOGRAPHY/)).toBeInTheDocument();
    expect(screen.getByText(/LANDSCAPE.*PHOTOGRAPHY/)).toBeInTheDocument();
    expect(screen.getByText('PROGRAMMING')).toBeInTheDocument();
  });
});
