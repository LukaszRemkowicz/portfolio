import { act } from 'react';
import {
  render,
  screen,
  waitFor,
  within,
  fireEvent,
} from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import '@testing-library/jest-dom';
import AstroGallery from '../components/AstroGallery';
import { AstroImage } from '../types';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the API services
jest.mock('../api/services', () => ({
  fetchAstroImages: jest.fn(),
  fetchBackground: jest.fn(),
  fetchSettings: jest.fn(),
  fetchProfile: jest.fn(),
  fetchTags: jest.fn(),
  fetchCategories: jest.fn(),
}));

import {
  fetchAstroImages,
  fetchSettings,
  fetchProfile,
  fetchTags,
  fetchCategories,
} from '../api/services';
import { useAppStore } from '../store/useStore';
import { Tag } from '../types';

/**
 * Test suite for the AstroGallery component
 */
describe('AstroGallery Component', () => {
  const mockFetchAstroImages = fetchAstroImages as jest.MockedFunction<
    typeof fetchAstroImages
  >;
  const mockFetchTags = fetchTags as jest.MockedFunction<typeof fetchTags>;
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const resetStore = () => {
    useAppStore.setState({
      profile: null,
      backgroundUrl: null,
      images: [],
      projects: [],
      categories: [],
      tags: [],
      features: null,
      isInitialLoading: true,
      isImagesLoading: true,
      isProjectsLoading: false,
      error: null,
      initialSessionId: '',
      imagesSessionId: '',
      projectsSessionId: '',
      tagsSessionId: '',
      meteorConfig: null,
    });
  };

  beforeEach(() => {
    jest.resetAllMocks();
    queryClient.clear();
    (fetchSettings as jest.Mock).mockResolvedValue({
      programming: true,
      contactForm: true,
      lastimages: true,
      meteors: {
        randomShootingStars: true,
        bolidChance: 0.1,
        bolidMinInterval: 60,
        starPathRange: [50, 500],
        bolidPathRange: [50, 500],
        starStreakRange: [100, 200],
        bolidStreakRange: [20, 100],
        starDurationRange: [0.4, 1.2],
        bolidDurationRange: [0.4, 0.9],
        starOpacityRange: [0.4, 0.8],
        bolidOpacityRange: [0.7, 1.0],
        smokeOpacityRange: [0.5, 0.8],
      },
    });
    mockFetchTags.mockResolvedValue([]);
    mockFetchAstroImages.mockResolvedValue([]);
    (fetchCategories as jest.Mock).mockResolvedValue([
      'Landscape',
      'Deep Sky',
      'Startrails',
      'Solar System',
      'Milky Way',
      'Northern Lights',
    ]);
    resetStore();
  });

  it('shows loading state initially', async () => {
    mockFetchAstroImages.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve([]), 100))
    );
    (fetchProfile as jest.Mock).mockImplementation(
      () =>
        new Promise(resolve =>
          setTimeout(
            () => resolve({ first_name: 'John', last_name: 'Doe' }),
            100
          )
        )
    );

    await act(async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={['/']}>
            <Routes>
              <Route path='/' element={<AstroGallery />} />
            </Routes>
          </MemoryRouter>
        </QueryClientProvider>
      );
    });

    expect(screen.getByTestId('loading-screen')).toBeInTheDocument();
    expect(screen.getByText(/Synchronizing/i)).toBeInTheDocument();
  });

  it('renders the gallery title and filter boxes after loading', async () => {
    await act(async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={['/']}>
            <Routes>
              <Route path='/' element={<AstroGallery />} />
            </Routes>
          </MemoryRouter>
        </QueryClientProvider>
      );
    });

    // Wait for loading screen to be removed
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

    expect(screen.getByText(/Gallery/i)).toBeInTheDocument();
    // Categories are rendered twice (Mobile Sidebar + Desktop List)
    expect(screen.getAllByText(/Landscape/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Deep Sky/i).length).toBeGreaterThan(0);
  });

  it('renders images from the API after loading', async () => {
    const mockImages: AstroImage[] = [
      {
        pk: 1,
        slug: 'test-image-1',
        url: '/test1.jpg',
        name: 'Test Image 1',
        description: 'Test description 1',
      },
    ];

    mockFetchAstroImages.mockResolvedValue(mockImages);

    await act(async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={['/']}>
            <Routes>
              <Route path='/' element={<AstroGallery />} />
            </Routes>
          </MemoryRouter>
        </QueryClientProvider>
      );
    });

    // Wait for initial loading screen to be removed
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

    // Wait for images loading state to resolve (important for tests triggered by effects)
    await waitFor(() => {
      expect(
        screen.queryByText(/Scanning deep space sectors/i)
      ).not.toBeInTheDocument();
    });

    // Verify images were fetched
    expect(fetchAstroImages).toHaveBeenCalled();

    // Wait for the card to be present and stable
    await waitFor(
      () => {
        expect(
          screen.getByRole('button', {
            name: /View details for Test Image 1/i,
          })
        ).toBeInTheDocument();
      },
      { timeout: 4000 }
    );
  });

  it('handles API errors gracefully', async () => {
    mockFetchAstroImages.mockRejectedValue(new Error('API Error'));

    const consoleSpy = jest
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    await act(async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={['/']}>
            <Routes>
              <Route path='/' element={<AstroGallery />} />
            </Routes>
          </MemoryRouter>
        </QueryClientProvider>
      );
    });

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

    await waitFor(
      () => {
        expect(screen.getByText(/API Error/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    consoleSpy.mockRestore();
  });

  it('filters images when filter is clicked', async () => {
    const mockImages: AstroImage[] = [
      {
        pk: 1,
        slug: 'test-image-1',
        url: '/test1.jpg',
        name: 'Test Image 1',
        description: 'Test description 1',
      },
    ];

    mockFetchAstroImages.mockResolvedValue(mockImages);

    await act(async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={['/']}>
            <Routes>
              <Route path='/' element={<AstroGallery />} />
            </Routes>
          </MemoryRouter>
        </QueryClientProvider>
      );
    });

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

    // Use findByText to ensure we wait for category buttons to appear (might be multiple)
    const landscapeFilters = await screen.findAllByText(/Landscape/i);
    const landscapeFilter = landscapeFilters[0]; // Click the first available one

    await act(async () => {
      fireEvent.click(landscapeFilter);
    });

    await waitFor(() => {
      expect(fetchAstroImages).toHaveBeenCalledWith(
        expect.objectContaining({ filter: 'Landscape' })
      );
    });
  });

  it('opens modal when image is clicked', async () => {
    const mockImages: AstroImage[] = [
      {
        pk: 1,
        slug: 'test-image-1',
        url: '/test1.jpg',
        name: 'Test Image 1',
        description: 'Test description 1',
      },
    ];

    mockFetchAstroImages.mockResolvedValue(mockImages);

    await act(async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={['/']}>
            <Routes>
              <Route path='/' element={<AstroGallery />} />
            </Routes>
          </MemoryRouter>
        </QueryClientProvider>
      );
    });

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

    // Wait for the button to be present and stable before clicking
    await waitFor(
      () => {
        expect(
          screen.getByRole('button', {
            name: /View details for Test Image 1/i,
          })
        ).toBeInTheDocument();
      },
      { timeout: 4000 }
    );

    const firstImageButton = screen.getByRole('button', {
      name: /View details for Test Image 1/i,
    });

    await act(async () => {
      fireEvent.click(firstImageButton);
    });

    await waitFor(() => {
      const modal = screen.getByTestId('image-modal');
      expect(within(modal).getByText(/Test description 1/)).toBeInTheDocument();
    });
  });

  it('renders tags in Sidebar and filters by them', async () => {
    const mockTags: Tag[] = [
      { name: 'Nebula', slug: 'nebula', count: 5 },
      { name: 'Galaxies', slug: 'galaxies', count: 3 },
    ];
    mockFetchTags.mockResolvedValue(mockTags);

    await act(async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={['/']}>
            <Routes>
              <Route path='/' element={<AstroGallery />} />
            </Routes>
          </MemoryRouter>
        </QueryClientProvider>
      );
    });

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

    // Wait for tags to be rendered and stable
    await waitFor(
      () => {
        expect(screen.getByText(/Nebula/i)).toBeInTheDocument();
        expect(screen.getByText(/Galaxies/i)).toBeInTheDocument();
      },
      { timeout: 4000 }
    );

    const nebulaTag = screen.getByText(/Nebula/i);

    await act(async () => {
      fireEvent.click(nebulaTag);
    });

    // Verify imagery is refetched with the tag filter
    await waitFor(() => {
      expect(fetchAstroImages).toHaveBeenCalledWith(
        expect.objectContaining({ tag: 'nebula' })
      );
    });
  });

  it('refetches tags when category filter changes', async () => {
    await act(async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={['/']}>
            <Routes>
              <Route path='/' element={<AstroGallery />} />
            </Routes>
          </MemoryRouter>
        </QueryClientProvider>
      );
    });

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

    const milkiWayFilters = await screen.findAllByText(/Milky Way/i);
    const milkiWayFilter = milkiWayFilters[0];

    // Clear initial load call
    mockFetchTags.mockClear();

    await act(async () => {
      fireEvent.click(milkiWayFilter);
    });

    // Verify fetchTags was called with "Milky Way"
    await waitFor(() => {
      expect(fetchTags).toHaveBeenCalledWith('Milky Way');
    });
  });
});
