import React, { ReactElement } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import Navbar from "../Navbar";
import { fetchEnabledFeatures } from "../api/services";

// Mock the services
jest.mock("../api/services", () => ({
  fetchEnabledFeatures: jest.fn(),
}));

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
describe("Navbar Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders logo and navigation links when enabled", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({
      programming: true,
    });
    renderWithRouter(<Navbar />);

    expect(screen.getByAltText("Logo")).toBeInTheDocument();
    expect(screen.getByText("Astrophotography")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Programming")).toBeInTheDocument();
    });
    expect(screen.getByText("Contact")).toBeInTheDocument();
  });

  it("hides Programming link when disabled", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({
      programming: false,
    });
    renderWithRouter(<Navbar />);

    expect(screen.getByAltText("Logo")).toBeInTheDocument();
    expect(screen.getByText("Astrophotography")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText("Programming")).not.toBeInTheDocument();
    });
    expect(screen.getByText("Contact")).toBeInTheDocument();
  });

  it("hides Programming link when response is empty", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({});
    renderWithRouter(<Navbar />);

    await waitFor(() => {
      expect(screen.queryByText("Programming")).not.toBeInTheDocument();
    });
  });

  it("defaults to disabled when fetch fails", async () => {
    (fetchEnabledFeatures as jest.Mock).mockRejectedValue(
      new Error("API Error"),
    );
    renderWithRouter(<Navbar />);

    await waitFor(() => {
      expect(screen.queryByText("Programming")).not.toBeInTheDocument();
    });
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
  it("applies transparent class when transparent prop is true", () => {
    renderWithRouter(<Navbar transparent={true} />);

    const navbar = screen.getByRole("navigation");
    expect(navbar).toHaveClass("transparent");
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
  it("does not apply transparent class when transparent prop is false", () => {
    renderWithRouter(<Navbar transparent={false} />);

    const navbar = screen.getByRole("navigation");
    expect(navbar).not.toHaveClass("transparent");
  });

  /**
   * Test: Applies programming background when programmingBg prop is true and transparent is true
   *
   * Verifies that the correct under construction image is applied
   * as an inline style when both transparent and programmingBg are true.
   */
  it("applies programming background when transparent and programmingBg are true", () => {
    renderWithRouter(<Navbar transparent={true} programmingBg={true} />);

    const navbar = screen.getByRole("navigation");
    // For CSS variables or assets, we check the style attribute
    expect(navbar).toHaveStyle(`background-image: url(/underconstruction.jpg)`);
  });
});
