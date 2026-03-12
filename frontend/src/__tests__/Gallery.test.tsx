import { act } from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Gallery from '../components/Gallery';
import { useSettings } from '../hooks/useSettings';
import { useLatestAstroImages } from '../hooks/useLatestAstroImages';
import { useAstroImageDetail } from '../hooks/useAstroImageDetail';

jest.mock('../hooks/useSettings');
jest.mock('../hooks/useLatestAstroImages');
jest.mock('../hooks/useAstroImageDetail');

describe('Gallery Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useSettings as jest.Mock).mockReturnValue({
      data: { lastimages: true },
    });
    (useLatestAstroImages as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
    });
    (useAstroImageDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });
  });

  it('renders the gallery using store data', async () => {
    // Mock API return
    (useLatestAstroImages as jest.Mock).mockReturnValue({
      data: [
        {
          pk: '1',
          slug: 'm31-andromeda',
          name: 'M31 Andromeda',
          url: 'test.jpg',
          thumbnail_url: 'thumb.jpg',
          tags: ['deepsky', 'galaxy'],
          celestial_object: 'Galaxy',
          created_at: '2023-01-01',
          description: '',
        },
      ],
      isLoading: false,
    });

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
    (useLatestAstroImages as jest.Mock).mockReturnValue({
      data: [
        {
          pk: '1',
          slug: 'deep-sky-object',
          name: 'Deep Sky Object',
          url: 'dso.jpg',
          tags: ['deepsky'],
          celestial_object: 'Nebula',
          created_at: '2023-01-01',
          description: '',
        },
        {
          pk: '2',
          slug: 'landscape-object',
          name: 'Landscape Object',
          url: 'lands.jpg',
          tags: ['astrolandscape'],
          celestial_object: 'Landscape',
          created_at: '2023-01-02',
          description: '',
        },
      ],
      isLoading: false,
    });

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

    // Wait for update
    await waitFor(() => {
      expect(screen.getByText('Deep Sky Object')).toBeInTheDocument();
      expect(screen.queryByText('Landscape Object')).not.toBeInTheDocument();
    });
  });

  it('navigates to /astrophotography/:slug when image is clicked', async () => {
    (useLatestAstroImages as jest.Mock).mockReturnValue({
      data: [
        {
          pk: '1',
          slug: 'test-image',
          name: 'Test Image',
          url: 'test.jpg',
          tags: [],
          celestial_object: 'Star',
          description: '',
        },
      ],
      isLoading: false,
    });

    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <Gallery />
        </MemoryRouter>
      );
    });

    expect(
      await screen.findByLabelText('View details for Test Image')
    ).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('View details for Test Image'));

    // Gallery no longer shows an inline modal — clicking navigates to
    // /astrophotography/:slug. The modal must NOT be rendered here.
    expect(screen.queryByTestId('image-modal')).not.toBeInTheDocument();
  });

  it('renders nothing if feature disabled and no images', async () => {
    (useSettings as jest.Mock).mockReturnValue({
      data: { lastimages: false },
    });
    (useLatestAstroImages as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
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
