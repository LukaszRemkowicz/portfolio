import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import Gallery from "../Gallery";
import { fetchEnabledFeatures } from "../api/services";

// Mock the services
jest.mock("../api/services", () => ({
  fetchEnabledFeatures: jest.fn(),
}));

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
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders all gallery items when programming is enabled", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({
      programming: true,
    });
    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>,
    );

    expect(screen.getByText("ASTROPHOTOGRAPHY")).toBeInTheDocument();
    expect(screen.getByText("LANDSCAPE PHOTOGRAPHY")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("PROGRAMMING")).toBeInTheDocument();
    });

    const galleryContainers = screen.getAllByText(/PHOTOGRAPHY|PROGRAMMING/);
    expect(galleryContainers).toHaveLength(3);
  });

  it("filters out programming item when disabled", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({
      programming: false,
    });
    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>,
    );

    expect(screen.getByText("ASTROPHOTOGRAPHY")).toBeInTheDocument();
    expect(screen.getByText("LANDSCAPE PHOTOGRAPHY")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText("PROGRAMMING")).not.toBeInTheDocument();
    });

    const galleryContainers = screen.getAllByText(/PHOTOGRAPHY|PROGRAMMING/);
    expect(galleryContainers).toHaveLength(2);
  });

  it("filters out programming item when response is empty", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({});
    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.queryByText("PROGRAMMING")).not.toBeInTheDocument();
    });
  });

  it("defaults to hidden when fetch fails", async () => {
    (fetchEnabledFeatures as jest.Mock).mockRejectedValue(
      new Error("API Error"),
    );
    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.queryByText("PROGRAMMING")).not.toBeInTheDocument();
    });
  });
});
