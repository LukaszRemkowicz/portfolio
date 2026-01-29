import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Footer from '../components/Footer';
import { useAppStore } from '../store/useStore';

// Mock the store
jest.mock('../store/useStore');

const mockUseAppStore = useAppStore as unknown as jest.Mock;

describe('Footer Component', () => {
  beforeEach(() => {
    mockUseAppStore.mockClear();
  });

  it('renders copyright text', () => {
    mockUseAppStore.mockReturnValue({
      profile: { contact_email: 'test@example.com' },
    });
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>
    );
    expect(screen.getByText('Łukasz Remkowicz © 2026')).toBeInTheDocument();
  });

  it('renders social links when profile data is present', () => {
    const mockProfile = {
      contact_email: 'test@example.com',
      profiles: [
        {
          type: 'ASTRO',
          ig_url: 'https://instagram.com/test',
          astrobin_url: 'https://astrobin.com/test',
        },
      ],
    };
    mockUseAppStore.mockReturnValue({ profile: mockProfile });

    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>
    );

    const igLink = screen.getByText('Instagram');
    const astroLink = screen.getByText('Astrobin');

    expect(igLink).toBeInTheDocument();
    expect(igLink.closest('a')).toHaveAttribute(
      'href',
      'https://instagram.com/test'
    );

    expect(astroLink).toBeInTheDocument();
    expect(astroLink.closest('a')).toHaveAttribute(
      'href',
      'https://astrobin.com/test'
    );
  });

  it('does not render social links when profile data is missing', () => {
    mockUseAppStore.mockReturnValue({ profile: { profiles: [] } });
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>
    );

    expect(screen.queryByText('Instagram')).not.toBeInTheDocument();
    expect(screen.queryByText('Astrobin')).not.toBeInTheDocument();
  });
});
