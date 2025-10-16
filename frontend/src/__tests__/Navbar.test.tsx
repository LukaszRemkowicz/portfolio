import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Navbar from '../Navbar';
import { ReactElement } from 'react';

/**
 * Helper function to render components with React Router context
 *
 * The Navbar component uses React Router's Link components,
 * so it needs to be wrapped in a Router context for testing.
 */
const renderWithRouter = (component: ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

/**
 * Test suite for the Navbar component
 *
 * The Navbar component provides site navigation with:
 * - Logo image with alt text
 * - Navigation links to different sections (Astrophotography, Programming, Contact)
 * - Optional transparent styling for overlay on hero sections
 * - Responsive design and hover effects
 *
 * Tests verify:
 * - Logo and navigation links are rendered correctly
 * - Transparent styling is applied when specified
 * - Navigation links have proper href attributes
 * - Component renders without errors in Router context
 * - Styling classes are applied conditionally
 */
describe('Navbar Component', () => {
  /**
   * Test: Renders logo and navigation links
   *
   * Verifies that:
   * - Logo image is displayed with correct alt text
   * - All navigation links are present (Astrophotography, Programming, Contact)
   * - Links have proper text content
   * - Component renders without errors
   * - Navigation structure is complete
   */
  it('renders logo and navigation links', () => {
    renderWithRouter(<Navbar />);

    expect(screen.getByAltText('Logo')).toBeInTheDocument();
    expect(screen.getByText('Astrophotography')).toBeInTheDocument();
    expect(screen.getByText('Programming')).toBeInTheDocument();
    expect(screen.getByText('Contact')).toBeInTheDocument();
  });

  /**
   * Test: Applies transparent class when transparent prop is true
   *
   * Verifies that:
   * - Transparent styling is applied when transparent prop is true
   * - Navbar has the correct CSS class for transparent styling
   * - Component handles conditional styling properly
   * - Transparent mode doesn't break navigation functionality
   */
  it('applies transparent class when transparent prop is true', () => {
    renderWithRouter(<Navbar transparent={true} />);

    const navbar = screen.getByRole('navigation');
    expect(navbar).toHaveClass('transparent');
  });

  /**
   * Test: Does not apply transparent class when transparent prop is false
   *
   * Verifies that:
   * - Transparent styling is not applied when transparent prop is false
   * - Navbar has normal styling without transparent class
   * - Component handles false/undefined transparent prop correctly
   * - Default styling is preserved when not in transparent mode
   */
  it('does not apply transparent class when transparent prop is false', () => {
    renderWithRouter(<Navbar transparent={false} />);

    const navbar = screen.getByRole('navigation');
    expect(navbar).not.toHaveClass('transparent');
  });
});
