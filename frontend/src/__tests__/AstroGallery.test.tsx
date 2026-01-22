import React from "react";
import {
  render,
  screen,
  waitFor,
  act,
  within,
  fireEvent,
} from "@testing-library/react";
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
  fetchTags: jest.fn(),
}));

import {
  fetchAstroImages,
  fetchBackground,
  fetchAstroImage,
  fetchEnabledFeatures,
  fetchProfile,
  fetchTags,
} from "../api/services";
import { useAppStore } from "../store/useStore";
import { Tag } from "../types";

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
  const mockFetchTags = fetchTags as jest.MockedFunction<typeof fetchTags>;

  const resetStore = () => {
    useAppStore.setState({
      profile: null,
      backgroundUrl: null,
      images: [],
      projects: [],
      tags: [],
      features: null,
      isInitialLoading: true,
      isImagesLoading: true,
      isProjectsLoading: false,
      error: null,
      initialSessionId: 0,
      imagesSessionId: 0,
      projectsSessionId: 0,
    });
  };

  beforeEach(() => {
    jest.resetAllMocks();
    (fetchEnabledFeatures as jest.Mock).mockResolvedValue({
      programming: true,
      contactForm: true,
      lastimages: true,
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
    mockFetchTags.mockResolvedValue([]);
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

    // Wait for loading screen to be removed
    await waitFor(() => {
      expect(screen.queryByTestId("loading-screen")).not.toBeInTheDocument();
    });

    expect(screen.getByText(/Gallery/i)).toBeInTheDocument();
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

    // Wait for initial loading screen to be removed
    await waitFor(() => {
      expect(screen.queryByTestId("loading-screen")).not.toBeInTheDocument();
    });

    // Wait for images loading state to resolve (important for tests triggered by effects)
    await waitFor(() => {
      expect(
        screen.queryByText(/Scanning deep space sectors/i),
      ).not.toBeInTheDocument();
    });

    // Verify images were fetched
    expect(fetchAstroImages).toHaveBeenCalled();

    // Wait for the card to be present and stable
    await waitFor(
      () => {
        expect(
          screen.getByRole("button", {
            name: /View details for Test Image 1/i,
          }),
        ).toBeInTheDocument();
      },
      { timeout: 4000 },
    );
  });

  it("handles API errors gracefully", async () => {
    mockFetchAstroImages.mockRejectedValue(new Error("API Error"));

    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={<AstroGallery />} />
          </Routes>
        </MemoryRouter>,
      );
    });

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(() => {
      expect(screen.queryByTestId("loading-screen")).not.toBeInTheDocument();
    });

    await waitFor(
      () => {
        expect(
          screen.getByText(/Failed to fetch gallery images/i),
        ).toBeInTheDocument();
      },
      { timeout: 3000 },
    );

    consoleSpy.mockRestore();
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

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(() => {
      expect(screen.queryByTestId("loading-screen")).not.toBeInTheDocument();
    });

    // Use findByText to ensure we wait for category buttons to appear
    const landscapeFilter = await screen.findByText(/Landscape/i);

    await act(async () => {
      fireEvent.click(landscapeFilter);
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

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(() => {
      expect(screen.queryByTestId("loading-screen")).not.toBeInTheDocument();
    });

    // Wait for the button to be present and stable before clicking
    await waitFor(
      () => {
        expect(
          screen.getByRole("button", {
            name: /View details for Test Image 1/i,
          }),
        ).toBeInTheDocument();
      },
      { timeout: 4000 },
    );

    const firstImageButton = screen.getByRole("button", {
      name: /View details for Test Image 1/i,
    });

    await act(async () => {
      fireEvent.click(firstImageButton);
    });

    await waitFor(() => {
      const modal = screen.getByTestId("image-modal");
      expect(
        within(modal).getByText(/Test detailed description/),
      ).toBeInTheDocument();
    });
  });

  it("renders tags in Sidebar and filters by them", async () => {
    const mockTags: Tag[] = [
      { name: "Nebula", slug: "nebula", count: 5 },
      { name: "Galaxies", slug: "galaxies", count: 3 },
    ];
    mockFetchTags.mockResolvedValue(mockTags);

    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={<AstroGallery />} />
          </Routes>
        </MemoryRouter>,
      );
    });

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(() => {
      expect(screen.queryByTestId("loading-screen")).not.toBeInTheDocument();
    });

    // Wait for tags to be rendered and stable
    await waitFor(
      () => {
        expect(screen.getByText(/Nebula/i)).toBeInTheDocument();
        expect(screen.getByText(/Galaxies/i)).toBeInTheDocument();
      },
      { timeout: 4000 },
    );

    const nebulaTag = screen.getByText(/Nebula/i);

    await act(async () => {
      fireEvent.click(nebulaTag);
    });

    // Verify imagery is refetched with the tag filter
    await waitFor(() => {
      expect(fetchAstroImages).toHaveBeenCalledWith(
        expect.objectContaining({ tag: "nebula" }),
      );
    });
  });

  it("refetches tags when category filter changes", async () => {
    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={<AstroGallery />} />
          </Routes>
        </MemoryRouter>,
      );
    });

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(() => {
      expect(screen.queryByTestId("loading-screen")).not.toBeInTheDocument();
    });

    const milkiWayFilter = await screen.findByText(/Milky Way/i);

    // Clear initial load call
    mockFetchTags.mockClear();

    await act(async () => {
      fireEvent.click(milkiWayFilter);
    });

    // Verify fetchTags was called with "Milky Way"
    await waitFor(() => {
      expect(fetchTags).toHaveBeenCalledWith("Milky Way");
    });
  });
});
