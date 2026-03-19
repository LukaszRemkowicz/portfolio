import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Footer from '../components/Footer';
import { useProfile } from '../hooks/useProfile';

const PROJECT_OWNER = process.env.PROJECT_OWNER || 'Portfolio Owner';

// Mock the hook
jest.mock('../hooks/useProfile');

describe('Footer Component', () => {
  beforeEach(() => {
    (useProfile as jest.Mock).mockClear();
  });

  it('renders copyright text', () => {
    (useProfile as jest.Mock).mockReturnValue({
      data: { contact_email: 'test@example.com' },
    });
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>
    );
    expect(screen.getByText(`${PROJECT_OWNER} © 2026`)).toBeInTheDocument();
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
    (useProfile as jest.Mock).mockReturnValue({ data: mockProfile });

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
    (useProfile as jest.Mock).mockReturnValue({ data: { profiles: [] } });
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>
    );

    expect(screen.queryByText('Instagram')).not.toBeInTheDocument();
    expect(screen.queryByText('Astrobin')).not.toBeInTheDocument();
  });
});
