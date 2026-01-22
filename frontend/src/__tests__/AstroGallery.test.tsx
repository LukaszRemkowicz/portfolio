import React from "react";
import { render, screen, waitFor, act, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import "@testing-library/jest-dom";
import AstroGallery from "../components/AstroGallery";
import { AstroImage } from "../types";

// Mock the API services
jest.mock("../api/services", () => ({
  fetchAstroImages: jest.fn(),
  fetchBackground: jest.fn(),
  fetchAstroImage: jest.fn(),
  fetchEnabledFeatures: jest.fn(),
  fetchProfile: jest.fn(),
}));

import {
  fetchAstroImages,
  fetchBackground,
  fetchAstroImage,
  fetchEnabledFeatures,
  fetchProfile,
} from "../api/services";
import { useAppStore } from "../store/useStore";

/**
 * Test suite for the AstroGallery component
 */
describe("AstroGallery Component", () => {
  const mockFetchAstroImages = fetchAstroImages as jest.MockedFunction<
    typeof fetchAstroImages
  >;
  const mockFetchAstroImage = fetchAstroImage as jest.MockedFunction<
    typeof fetchAstroImage
  >;

  const resetStore = () => {
    useAppStore.setState({
      profile: null,
      backgroundUrl: null,
      images: [],
      projects: [],
      features: null,
      isInitialLoading: false,
      isImagesLoading: false,
      isProjectsLoading: false,
      error: null,
    });
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({
      programming: true,
    });
    (fetchProfile as jest.Mock).mockResolvedValue({
      first_name: "Test",
      last_name: "User",
    });
    (fetchBackground as jest.Mock).mockResolvedValue("/test-bg.jpg");
    (fetchAstroImages as jest.Mock).mockResolvedValue([]);
    (fetchAstroImage as jest.Mock).mockResolvedValue({
      pk: 1,
      name: "Test",
      description: "Test",
    });
    resetStore();
  });

  it("shows loading state initially", async () => {
    mockFetchAstroImages.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve([]), 100)),
    );
    (fetchProfile as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () => resolve({ first_name: "John", last_name: "Doe" }),
            100,
          ),
        ),
    );

    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={<AstroGallery />} />
          </Routes>
        </MemoryRouter>,
      );
    });

    expect(screen.getByTestId("loading-screen")).toBeInTheDocument();
    expect(screen.getByText(/Synchronizing/i)).toBeInTheDocument();
  });

  it("renders the gallery title and filter boxes after loading", async () => {
    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={<AstroGallery />} />
          </Routes>
        </MemoryRouter>,
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/Gallery/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Landscape/i)).toBeInTheDocument();
    expect(screen.getByText(/Deep Sky/i)).toBeInTheDocument();
  });

  it("renders images from the API after loading", async () => {
    const mockImages: AstroImage[] = [
      {
        pk: 1,
        url: "/test1.jpg",
        name: "Test Image 1",
        description: "Test description 1",
      },
    ];

    mockFetchAstroImages.mockResolvedValue(mockImages);

    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={<AstroGallery />} />
          </Routes>
        </MemoryRouter>,
      );
    });

    const card = await screen.findByRole("button", {
      name: /View details for Test Image 1/i,
    });
    expect(card).toBeInTheDocument();
  });

  it("handles API errors gracefully", async () => {
    mockFetchAstroImages.mockRejectedValue(new Error("API Error"));

    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={<AstroGallery />} />
          </Routes>
        </MemoryRouter>,
      );
    });

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to fetch gallery images/i),
      ).toBeInTheDocument();
    });
  });

  it("filters images when filter is clicked", async () => {
    const mockImages: AstroImage[] = [
      {
        pk: 1,
        url: "/test1.jpg",
        name: "Test Image 1",
        description: "Test description 1",
      },
    ];

    mockFetchAstroImages.mockResolvedValue(mockImages);

    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={<AstroGallery />} />
          </Routes>
        </MemoryRouter>,
      );
    });

    const landscapeFilter = await screen.findByText(/Landscape/i);

    await act(async () => {
      landscapeFilter.click();
    });

    await waitFor(() => {
      expect(fetchAstroImages).toHaveBeenCalledWith(
        expect.objectContaining({ filter: "Landscape" }),
      );
    });
  });

  it("opens modal when image is clicked", async () => {
    const mockImages: AstroImage[] = [
      {
        pk: 1,
        url: "/test1.jpg",
        name: "Test Image 1",
        description: "Test description 1",
      },
    ];

    const mockImageDetail: AstroImage = {
      pk: 1,
      url: "/test2.jpg",
      name: "Test Image 1",
      description: "Test detailed description",
    };

    mockFetchAstroImages.mockResolvedValue(mockImages);
    mockFetchAstroImage.mockResolvedValue(mockImageDetail);

    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={<AstroGallery />} />
          </Routes>
        </MemoryRouter>,
      );
    });

    const firstImageButton = await screen.findByRole("button", {
      name: /View details for Test Image 1/i,
    });

    await act(async () => {
      firstImageButton.click();
    });

    const modal = await screen.findByTestId("image-modal");
    expect(
      within(modal).getByText(/Test detailed description/),
    ).toBeInTheDocument();
  });
});
