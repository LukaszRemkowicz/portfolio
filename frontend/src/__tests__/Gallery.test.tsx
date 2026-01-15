import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import Gallery from "../components/Gallery";
import { fetchEnabledFeatures } from "../api/services";
import { useAppStore } from "../store/useStore";

// Mock the services
jest.mock("../api/services", () => ({
  fetchEnabledFeatures: jest.fn(),
  fetchAstroImages: jest.fn().mockResolvedValue([
    {
      pk: 1,
      name: "M31 Andromeda",
      celestial_object: "Galaxy",
      url: "test.jpg",
    },
    {
      pk: 2,
      name: "Milky Way Core",
      celestial_object: "Nebula",
      url: "test2.jpg",
    },
  ]),
  fetchAstroImage: jest.fn(),
}));

describe("Gallery Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useAppStore.setState({
      profile: null,
      backgroundUrl: null,
      images: [],
      features: null,
      isInitialLoading: false,
      isImagesLoading: false,
      error: null,
    });
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

    expect(screen.getByText("Latest images")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("M31 Andromeda")).toBeInTheDocument();
      expect(screen.getByText("Milky Way Core")).toBeInTheDocument();
    });
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
    expect(screen.getByText("Astrolandscape")).toBeInTheDocument();
    expect(screen.getByText("Timelapses")).toBeInTheDocument();
  });
});
