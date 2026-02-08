import { act } from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Gallery from '../components/Gallery';
import { useAppStore } from '../store/useStore';
import { fetchAstroImages } from '../api/services';

// Mock Services
jest.mock('../api/services', () => ({
  fetchAstroImages: jest.fn().mockResolvedValue([]),
  fetchBackground: jest.fn().mockResolvedValue(null),
  fetchEnabledFeatures: jest.fn().mockResolvedValue({}),
  fetchProfile: jest.fn().mockResolvedValue({}),
}));

describe('Gallery Component', () => {
  const mockFetchAstroImages = fetchAstroImages as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    useAppStore.setState({
      images: [],
      isImagesLoading: false,
      error: null,
      features: { lastimages: true },
    });
    // Default successful fetch to avoid unhandled rejections if store calls it
    mockFetchAstroImages.mockResolvedValue([]);
  });

  it('renders the gallery using store data', async () => {
    // Mock API return
    mockFetchAstroImages.mockResolvedValue([
      {
        pk: 1,
        slug: 'm31-andromeda',
        name: 'M31 Andromeda',
        url: 'test.jpg',
        thumbnail_url: 'thumb.jpg',
        tags: ['deepsky', 'galaxy'],
        celestial_object: 'Galaxy',
        created_at: '2023-01-01',
      },
    ]);

    await act(async () => {
      render(
        <MemoryRouter>
          <Gallery />
        </MemoryRouter>
      );
    });

    // Wait for load to complete
    expect(await screen.findByText('gallery.title')).toBeInTheDocument();
    expect(await screen.findByText('M31 Andromeda')).toBeInTheDocument();
  });

  it('filters images when category is selected', async () => {
    mockFetchAstroImages.mockResolvedValue([
      {
        pk: 1,
        slug: 'deep-sky-object',
        name: 'Deep Sky Object',
        url: 'dso.jpg',
        tags: ['deepsky'],
        celestial_object: 'Nebula',
        created_at: '2023-01-01',
      },
      {
        pk: 2,
        slug: 'landscape-object',
        name: 'Landscape Object',
        url: 'lands.jpg',
        tags: ['astrolandscape'],
        celestial_object: 'Landscape',
        created_at: '2023-01-02',
      },
    ]);

    await act(async () => {
      render(
        <MemoryRouter>
          <Gallery />
        </MemoryRouter>
      );
    });

    expect(await screen.findByText('Deep Sky Object')).toBeInTheDocument();
    expect(screen.getByText('Landscape Object')).toBeInTheDocument();

    const filterBtn = screen.getByRole('button', { name: 'Deep Sky' });
    fireEvent.click(filterBtn);

    // Filter logic is inside Gallery component using useMemo, not API call
    // Wait for update
    await waitFor(() => {
      expect(screen.getByText('Deep Sky Object')).toBeInTheDocument();
      expect(screen.queryByText('Landscape Object')).not.toBeInTheDocument();
    });
  });

  it('opens modal when image clicked', async () => {
    mockFetchAstroImages.mockResolvedValue([
      {
        pk: 1,
        slug: 'test-image',
        name: 'Test Image',
        url: 'test.jpg',
        tags: [],
        celestial_object: 'Star',
      },
    ]);

    await act(async () => {
      render(
        <MemoryRouter>
          <Gallery />
        </MemoryRouter>
      );
    });

    expect(
      await screen.findByLabelText('View details for Test Image')
    ).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('View details for Test Image'));

    expect(await screen.findByTestId('image-modal')).toBeInTheDocument();
  });

  it('renders nothing if feature disabled and no images', async () => {
    useAppStore.setState({
      features: { lastimages: false },
      images: [],
    });

    await act(async () => {
      render(
        <MemoryRouter>
          <Gallery />
        </MemoryRouter>
      );
    });

    expect(screen.queryByText('gallery.title')).not.toBeInTheDocument();
  });
});
