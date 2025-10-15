import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Footer from '../Footer';

/**
 * Test suite for the Footer component
 * 
 * The Footer component displays site footer information including:
 * - Copyright text with current year and author name
 * - Footer styling and layout
 * - Consistent branding across the site
 * 
 * This is a simple, static component that doesn't require:
 * - API calls
 * - Router context
 * - Complex state management
 * 
 * Tests verify:
 * - Copyright text is displayed correctly
 * - Footer renders without errors
 * - Text content is properly formatted
 */
describe('Footer Component', () => {
  /**
   * Test: Renders copyright text
   * 
   * Verifies that:
   * - Copyright text is displayed with proper formatting
   * - Author name (Łukasz Remkowicz) is shown correctly
   * - Year (2025) is included in the copyright
   * - Footer component renders without errors
   * - Text is accessible and readable
   */
  it('renders copyright text', () => {
    render(<Footer />);
    expect(screen.getByText('© 2025 Łukasz Remkowicz')).toBeInTheDocument();
  });
});
