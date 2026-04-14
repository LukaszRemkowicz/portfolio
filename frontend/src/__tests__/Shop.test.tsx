import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import Shop from '../components/Shop';
import { useShopProducts } from '../hooks/useShopProducts';

jest.mock('../hooks/useShopProducts', () => ({
  useShopProducts: jest.fn(),
}));

describe('Shop Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderWithRouter = () => {
    render(
      <MemoryRouter>
        <Shop />
      </MemoryRouter>
    );
  };

  it('renders loading state correctly', () => {
    (useShopProducts as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    renderWithRouter();
    expect(screen.getByText('Loading catalog...')).toBeInTheDocument();
  });

  it('renders error state correctly', () => {
    (useShopProducts as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    renderWithRouter();
    expect(
      screen.getByText('Catalog is temporarily out of orbit.')
    ).toBeInTheDocument();
  });

  it('renders empty state correctly', () => {
    (useShopProducts as jest.Mock).mockReturnValue({
      data: {
        title: '',
        description: '',
        background_url: '',
        products: [],
      },
      isLoading: false,
      isError: false,
    });

    renderWithRouter();
    expect(
      screen.getByText('No releases are available yet.')
    ).toBeInTheDocument();
  });

  it('renders shop cards correctly without outdated headers/buttons', () => {
    (useShopProducts as jest.Mock).mockReturnValue({
      data: {
        title: 'Collect the night sky in print.',
        description: 'Shop description from backend settings.',
        background_url: 'https://example.com/background.webp',
        products: [
          {
            id: 'dragons',
            title: 'Fighting Dragons with the Egg',
            description: 'Mock description for the dragons.',
            thumbnail_url: 'https://example.com/dragons.webp',
            external_url: 'https://example.com/products/dragons',
          },
        ],
      },
      isLoading: false,
      isError: false,
    });

    renderWithRouter();

    // Check main title
    expect(
      screen.getByRole('heading', { name: 'Collect the night sky in print.' })
    ).toBeInTheDocument();

    // Check product specific info
    expect(
      screen.getByRole('heading', { name: 'Fighting Dragons with the Egg' })
    ).toBeInTheDocument();
    expect(
      screen.getByText('Mock description for the dragons.')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Shop description from backend settings.')
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View product' })).toHaveAttribute(
      'href',
      'https://example.com/products/dragons'
    );
  });
});
