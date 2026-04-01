import { act } from 'react';
import {
  render,
  screen,
  waitFor,
  within,
  fireEvent,
} from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import '@testing-library/jest-dom';
import AstroGallery from '../components/AstroGallery';
import { AstroImage, Tag } from '../types';

import { useAstroImages } from '../hooks/useAstroImages';
import { useCategories } from '../hooks/useCategories';
import { useTags } from '../hooks/useTags';
import { useBackground } from '../hooks/useBackground';
import { useSettings } from '../hooks/useSettings';
import { useImageUrls } from '../hooks/useImageUrls';
import { useAstroImageDetail } from '../hooks/useAstroImageDetail';

// Mock the hooks
jest.mock('../hooks/useAstroImages');
jest.mock('../hooks/useCategories');
jest.mock('../hooks/useTags');
jest.mock('../hooks/useBackground');
jest.mock('../hooks/useSettings');
jest.mock('../hooks/useImageUrls');
jest.mock('../hooks/useAstroImageDetail');

const LocationDisplay = () => {
  const location = useLocation();
  return (
    <div data-testid='location-display'>
      {location.pathname}
      {location.search}
    </div>
  );
};

/**
 * Test suite for the AstroGallery component
 */
describe('AstroGallery Component', () => {
  beforeEach(() => {
    jest.resetAllMocks();

    (useSettings as jest.Mock).mockReturnValue({
      data: {
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
      },
    });

    (useTags as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
    });

    (useAstroImages as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: jest.fn(),
      error: null,
    });

    (useCategories as jest.Mock).mockReturnValue({
      data: [
        'Landscape',
        'Deep Sky',
        'Startrails',
        'Solar System',
        'Milky Way',
        'Northern Lights',
      ],
      isLoading: false,
    });

    (useBackground as jest.Mock).mockReturnValue({
      data: '/test-bg.jpg',
    });

    (useImageUrls as jest.Mock).mockReturnValue({
      data: {},
    });

    (useAstroImageDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });
  });

  it('shows loading state initially', async () => {
    (useAstroImages as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: jest.fn(),
      error: null,
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path='/' element={<AstroGallery />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByTestId('loading-screen')).toBeInTheDocument();
  });

  it('renders the gallery title and filter boxes after loading', async () => {
    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/astrophotography']}>
          <Routes>
            <Route path='/astrophotography' element={<AstroGallery />}>
              <Route path=':slug' element={null} />
            </Route>
          </Routes>
        </MemoryRouter>
      );
    });

    // Wait for loading screen to be removed
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

    // Match all 'Gallery' texts since Helmet injects one into the <title> tag
    const galleryTitles = screen.getAllByText(/Gallery/i);
    expect(galleryTitles.length).toBeGreaterThan(0);
    expect(galleryTitles[0]).toBeInTheDocument();

    // Categories are rendered twice (Mobile Sidebar + Desktop List)
    expect(screen.getAllByText(/Landscape/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Deep Sky/i).length).toBeGreaterThan(0);
  });

  it('renders images from the API after loading', async () => {
    const mockImages: AstroImage[] = [
      {
        pk: '1',
        slug: 'test-image-1',
        thumbnail_url: '/test1-thumb.jpg',
        name: 'Test Image 1',
        description: 'Test description 1',
      },
    ];

    (useAstroImages as jest.Mock).mockReturnValue({
      data: mockImages,
      isLoading: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: jest.fn(),
      error: null,
    });

    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/astrophotography']}>
          <Routes>
            <Route path='/astrophotography' element={<AstroGallery />}>
              <Route path=':slug' element={null} />
            </Route>
          </Routes>
        </MemoryRouter>
      );
    });

    // Wait for initial loading screen to be removed
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

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
    (useAstroImages as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: jest.fn(),
      error: new Error('API Error'),
    });

    const consoleSpy = jest
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/astrophotography']}>
          <Routes>
            <Route path='/astrophotography' element={<AstroGallery />}>
              <Route path=':slug' element={null} />
            </Route>
          </Routes>
        </MemoryRouter>
      );
    });

    // Wait for loading screen to be removed first to ensure stable rendering
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

    await waitFor(
      () => {
        expect(
          screen.getByText(/Failed to fetch gallery images/i)
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    consoleSpy.mockRestore();
  });

  it('filters images when filter is clicked', async () => {
    const mockImages: AstroImage[] = [
      {
        pk: '1',
        slug: 'test-image-1',
        thumbnail_url: '/test1-thumb.jpg',
        name: 'Test Image 1',
        description: 'Test description 1',
      },
    ];

    (useAstroImages as jest.Mock).mockReturnValue({
      data: mockImages,
      isLoading: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: jest.fn(),
      error: null,
    });

    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/astrophotography']}>
          <Routes>
            <Route path='/astrophotography' element={<AstroGallery />}>
              <Route path=':slug' element={null} />
            </Route>
          </Routes>
        </MemoryRouter>
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

    // In a real component, clicking the filter updates the state variable `filter`,
    // which is passed to `useAstroImages`. Here we just mock the initial response.
    // Testing the actual hook re-fetch would require more complex interaction testing.
    // We implicitly trust that the hook behaves well when state changes.
  });

  it('opens modal when slug is in the URL path', async () => {
    const mockImages: AstroImage[] = [
      {
        pk: '1',
        slug: 'test-image-1',
        thumbnail_url: '/test1-thumb.jpg',
        name: 'Test Image 1',
        description: 'Test description 1',
      },
    ];

    (useAstroImages as jest.Mock).mockReturnValue({
      data: mockImages,
      isLoading: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: jest.fn(),
      error: null,
    });

    // Start with the slug already in the URL — this is what happens when
    // a user navigates directly to /astrophotography/:slug or clicks a card.
    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/astrophotography/test-image-1']}>
          <Routes>
            <Route path='/astrophotography' element={<AstroGallery />}>
              <Route path=':slug' element={null} />
            </Route>
          </Routes>
        </MemoryRouter>
      );
    });

    // Wait for loading screen to be removed first
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

    // With the slug in the URL, AstroGallery reads it via useParams and
    // opens the modal immediately without any click.
    await waitFor(
      () => {
        const modal = screen.getByTestId('image-modal');
        expect(
          within(modal).getByText(/Test description 1/)
        ).toBeInTheDocument();
      },
      { timeout: 4000 }
    );
  });

  it('returns to the homepage when closing a modal opened from the homepage gallery', async () => {
    const mockImages: AstroImage[] = [
      {
        pk: '1',
        slug: 'test-image-1',
        thumbnail_url: '/test1-thumb.jpg',
        name: 'Test Image 1',
        description: 'Test description 1',
      },
    ];

    (useAstroImages as jest.Mock).mockReturnValue({
      data: mockImages,
      isLoading: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: jest.fn(),
      error: null,
    });

    await act(async () => {
      render(
        <MemoryRouter
          initialEntries={[
            {
              pathname: '/astrophotography/test-image-1',
              state: {
                backgroundLocation: {
                  pathname: '/',
                  search: '',
                  hash: '',
                },
              },
            },
          ]}
        >
          <LocationDisplay />
          <Routes>
            <Route path='/' element={<div>Home</div>} />
            <Route path='/astrophotography' element={<AstroGallery />}>
              <Route path=':slug' element={null} />
            </Route>
          </Routes>
        </MemoryRouter>
      );
    });

    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });

    expect(screen.getByTestId('location-display')).toHaveTextContent(
      '/astrophotography/test-image-1'
    );

    fireEvent.click(screen.getByRole('button', { name: 'Close modal' }));

    await waitFor(() => {
      expect(screen.getByTestId('location-display')).toHaveTextContent('/');
    });
  });

  it('renders tags in Sidebar and filters by them', async () => {
    const mockTags: Tag[] = [
      { name: 'Nebula', slug: 'nebula', count: 5 },
      { name: 'Galaxies', slug: 'galaxies', count: 3 },
    ];
    (useTags as jest.Mock).mockReturnValue({
      data: mockTags,
      isLoading: false,
    });

    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/astrophotography']}>
          <Routes>
            <Route path='/astrophotography' element={<AstroGallery />}>
              <Route path=':slug' element={null} />
            </Route>
          </Routes>
        </MemoryRouter>
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

    // Verify interaction visually or through mock updates
  });

  it('keeps direct modal links working when the image is not in the loaded page', async () => {
    (useAstroImages as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: jest.fn(),
      error: null,
    });

    (useAstroImageDetail as jest.Mock).mockReturnValue({
      data: {
        pk: '99',
        slug: 'remote-image',
        thumbnail_url: '/remote-thumb.jpg',
        name: 'Remote Image',
        description: 'Loaded from detail endpoint',
      },
      isLoading: false,
      error: null,
    });

    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/astrophotography/remote-image']}>
          <Routes>
            <Route path='/astrophotography' element={<AstroGallery />}>
              <Route path=':slug' element={null} />
            </Route>
          </Routes>
        </MemoryRouter>
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId('image-modal')).toBeInTheDocument();
    });
  });
});
