import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Navbar from '../Navbar';

/**
 * Helper function to render components with React Router context
 * 
 * The Navbar component uses React Router's Link components,
 * so it needs to be wrapped in a Router context for testing.
 */
const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
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
 * - All navigation elements render correctly
 * - Logo is displayed with proper alt text
 * - Navigation links are present and accessible
 * - Transparent styling prop works correctly
 * - Component integrates properly with React Router
 */
describe('Navbar Component', () => {
  /**
   * Test: Renders logo and navigation links
   * 
   * Verifies that:
   * - Logo image is displayed with proper alt text
   * - All navigation links are rendered (Astrophotography, Programming, Contact)
   * - Navigation elements are accessible and clickable
   * - Component renders without errors in router context
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
   * - Component accepts transparent prop
   * - When transparent=true, component gets 'transparent' CSS class
   * - Transparent styling is applied correctly
   * - Component can be used as overlay on hero sections
   */
  it('applies transparent class when transparent prop is true', () => {
    const { container } = renderWithRouter(<Navbar transparent />);
    expect(container.firstChild).toHaveClass('transparent');
  });

  /**
   * Test: Does not apply transparent class when transparent prop is false
   * 
   * Verifies that:
   * - Default behavior when transparent prop is not provided
   * - Component doesn't get 'transparent' class by default
   * - Normal navbar styling is applied
   * - Prop handling works correctly for both true/false states
   */
  it('does not apply transparent class when transparent prop is false', () => {
    const { container } = renderWithRouter(<Navbar />);
    expect(container.firstChild).not.toHaveClass('transparent');
  });
});
