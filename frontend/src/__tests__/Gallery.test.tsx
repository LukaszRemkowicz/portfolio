import { act } from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Gallery from '../components/Gallery';
import { useAstroImages } from '../hooks/useAstroImages';
import { useSettings } from '../hooks/useSettings';
import { useAstroImageDetail } from '../hooks/useAstroImageDetail';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock Hooks
jest.mock('../hooks/useAstroImages');
jest.mock('../hooks/useSettings');
jest.mock('../hooks/useAstroImageDetail');

describe('Gallery Component', () => {
  const mockUseAstroImages = useAstroImages as jest.Mock;
  const mockUseSettings = useSettings as jest.Mock;
  const mockUseAstroImageDetail = useAstroImageDetail as jest.Mock;
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient.clear();
    mockUseSettings.mockReturnValue({
      data: { lastimages: true },
      isLoading: false,
    });
    mockUseAstroImages.mockReturnValue({ data: [], isLoading: false });
    mockUseAstroImageDetail.mockReturnValue({ data: null, isLoading: false });
  });

  const renderWithQueryClient = (ui: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>{ui}</MemoryRouter>
      </QueryClientProvider>
    );
  };

  it('renders the gallery using store data', async () => {
    // Mock API return
    mockUseAstroImages.mockReturnValue({
      data: [
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
      ],
      isLoading: false,
    });

    await act(async () => {
      renderWithQueryClient(<Gallery />);
    });

    // Wait for load to complete
    expect(await screen.findByText('gallery.title')).toBeInTheDocument();
    expect(await screen.findByText('M31 Andromeda')).toBeInTheDocument();
  });

  it('filters images when category is selected', async () => {
    mockUseAstroImages.mockReturnValue({
      data: [
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
      ],
      isLoading: false,
    });

    await act(async () => {
      renderWithQueryClient(<Gallery />);
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
    mockUseAstroImages.mockReturnValue({
      data: [
        {
          pk: 1,
          slug: 'test-image',
          name: 'Test Image',
          url: 'test.jpg',
          tags: [],
          celestial_object: 'Star',
        },
      ],
      isLoading: false,
    });

    await act(async () => {
      renderWithQueryClient(<Gallery />);
    });

    expect(
      await screen.findByLabelText('View details for Test Image')
    ).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('View details for Test Image'));

    expect(await screen.findByTestId('image-modal')).toBeInTheDocument();
  });

  it('renders nothing if feature disabled and no images', async () => {
    mockUseSettings.mockReturnValue({
      data: { lastimages: false },
      isLoading: false,
    });
    mockUseAstroImages.mockReturnValue({
      data: [],
      isLoading: false,
    });

    await act(async () => {
      renderWithQueryClient(<Gallery />);
    });

    expect(screen.queryByText('gallery.title')).not.toBeInTheDocument();
  });
});
