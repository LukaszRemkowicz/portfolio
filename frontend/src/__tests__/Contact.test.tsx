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

describe("Contact Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the form when contactForm is enabled", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({
      contactForm: true,
    });
    render(<Contact />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /Direct Inquiry/i }),
      ).toBeInTheDocument();
      expect(screen.getByText("Identity")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Submit Inquiry/i }),
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
  });
});
