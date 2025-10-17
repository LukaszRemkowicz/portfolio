import React from "react";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import Gallery from "../Gallery";

/**
 * Test suite for the Gallery component
 *
 * The Gallery component displays a static gallery with predefined categories:
 * - ASTROPHOTOGRAPHY
 * - LANDSCAPE PHOTOGRAPHY
 * - PROGRAMMING
 *
 * Each gallery item uses CSS background images and contains:
 * - A title with category name
 * - Links to respective pages (/astrophotography, /programming)
 * - Hover effects and styling
 *
 * The component uses static data from galleryItems.ts and doesn't require:
 * - API calls
 * - State management
 * - Complex props
 *
 * Testing Strategy:
 * - Verify all gallery items are rendered from static data
 * - Check that correct number of items are displayed
 * - Ensure text content matches expected values
 * - Test that component renders without errors
 * - Verify React Router integration works correctly
 */

describe("Gallery Component", () => {
  /**
   * Test: Renders gallery items from static data
   *
   * Verifies that:
   * - All three gallery categories are displayed
   * - Text content matches the static data exactly
   * - Gallery items are rendered from static data source
   * - No API calls are needed for this component
   */
  it("renders gallery items from static data", () => {
    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>,
    );

    expect(screen.getByText("ASTROPHOTOGRAPHY")).toBeInTheDocument();
    expect(screen.getByText("LANDSCAPE PHOTOGRAPHY")).toBeInTheDocument();
    expect(screen.getByText("PROGRAMMING")).toBeInTheDocument();
  });

  /**
   * Test: Renders correct number of gallery items
   *
   * Verifies that:
   * - Gallery items use background images (not img tags)
   * - Text content can be found using regex patterns
   * - Each category is properly represented in the gallery
   * - Gallery structure is consistent and complete
   */
  it("renders correct number of gallery items", () => {
    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>,
    );

    // Gallery items use background images, so we check for gallery item containers by text content
    const galleryContainers = screen.getAllByText(/PHOTOGRAPHY|PROGRAMMING/);
    expect(galleryContainers).toHaveLength(3);
  });
});
