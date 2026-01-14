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

describe("Gallery Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the gallery with the new portfolio title", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({
      programming: true,
    });
    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>,
    );

    expect(screen.getByText("Portfolio")).toBeInTheDocument();
    expect(screen.getByText("M31 Andromeda")).toBeInTheDocument();
    expect(screen.getByText("Milky Way Core")).toBeInTheDocument();
  });

  it("renders filter buttons", async () => {
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({
      programming: true,
    });
    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>,
    );

    expect(screen.getByText("All Works")).toBeInTheDocument();
    expect(screen.getByText("Deep Sky")).toBeInTheDocument();
    expect(screen.getByText("Landscape")).toBeInTheDocument();
    expect(screen.getByText("Timelapses")).toBeInTheDocument();
  });
});
