import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import Contact from "../Contact";
import { fetchEnabledFeatures } from "../api/services";

// Mock the services
jest.mock("../api/services", () => ({
  fetchEnabledFeatures: jest.fn(),
  fetchContact: jest.fn(),
}));

describe("Contact Component - Feature Enablement", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("shows nothing initially while loading", () => {
    (fetchEnabledFeatures as jest.Mock).mockReturnValue(new Promise(() => {})); // Never resolves
    const { container } = render(<Contact />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders the form when contactForm is enabled", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({
      contactForm: true,
    });
    render(<Contact />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /Get in Touch/i }),
      ).toBeInTheDocument();
      expect(screen.getByLabelText(/Name/i)).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Send Message/i }),
      ).toBeInTheDocument();
    });
  });

  it("renders nothing when contactForm is disabled", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({
      contactForm: false,
    });
    const { container } = render(<Contact />);

    await waitFor(() => {
      expect(container).toBeEmptyDOMElement();
    });

    expect(screen.queryByText(/Get in Touch/i)).not.toBeInTheDocument();
  });

  it("renders nothing when response is empty", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({});
    const { container } = render(<Contact />);

    await waitFor(() => {
      expect(container).toBeEmptyDOMElement();
    });
  });

  it("defaults to disabled when fetch fails", async () => {
    (fetchEnabledFeatures as jest.Mock).mockRejectedValue(
      new Error("API Error"),
    );
    const { container } = render(<Contact />);

    await waitFor(() => {
      expect(container).toBeEmptyDOMElement();
    });
  });
});
