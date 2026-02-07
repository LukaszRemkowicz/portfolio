import { type ReactElement } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Navbar from '../components/Navbar';
import { useSettings } from '../hooks/useSettings';
import { APP_ROUTES } from '../api/constants';

// Mock useSettings hook
jest.mock('../hooks/useSettings');

const renderWithRouter = (component: ReactElement, initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>{component}</MemoryRouter>
  );
};

describe('Navbar Component', () => {
  const mockUseSettings = useSettings as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSettings.mockReturnValue({
      data: null,
      isLoading: false,
    });
  });

  it('renders brand and navigation links', async () => {
    mockUseSettings.mockReturnValue({
      data: { programming: true },
      isLoading: false,
    });
    renderWithRouter(<Navbar />);

    expect(screen.getByText('Łukasz Remkowicz')).toBeInTheDocument();
    expect(screen.getAllByText('Home')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Astrophotography')[0]).toBeInTheDocument();
    expect(screen.getByText('About')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Programming')).toBeInTheDocument();
    });
    expect(screen.getByText('Contact')).toBeInTheDocument();
  });

  it('hides Programming link when disabled', async () => {
    mockUseSettings.mockReturnValue({
      data: { programming: false },
      isLoading: false,
    });
    renderWithRouter(<Navbar />);

    expect(screen.getByText('Łukasz Remkowicz')).toBeInTheDocument();
    expect(screen.getAllByText('Astrophotography')[0]).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText('Programming')).not.toBeInTheDocument();
    });
    expect(screen.getByText('Contact')).toBeInTheDocument();
  });

  it('handles mobile menu toggle', () => {
    renderWithRouter(<Navbar />);
    const menuBtn = screen.getByRole('button', { name: /open menu/i });
    expect(menuBtn).toBeInTheDocument();
  });

  it('highlights About when hash is #about and Home is NOT highlighted', () => {
    renderWithRouter(<Navbar />, [`${APP_ROUTES.HOME}#about`]);

    const aboutLink = screen.getByRole('link', { name: 'About' });
    const homeLink = screen.getAllByRole('link', { name: 'Home' })[0];

    expect(aboutLink).toHaveClass('active');
    expect(homeLink).not.toHaveClass('active');
  });

  it('highlights Home when at root path and NO hash', () => {
    renderWithRouter(<Navbar />, [APP_ROUTES.HOME]);

    const homeLink = screen.getAllByRole('link', { name: 'Home' })[0];
    const aboutLink = screen.getByRole('link', { name: 'About' });

    expect(homeLink).toHaveClass('active');
    expect(aboutLink).not.toHaveClass('active');
  });

  it('highlights Astrophotography when on its route', () => {
    renderWithRouter(<Navbar />, [APP_ROUTES.ASTROPHOTOGRAPHY]);

    // The logo also contains 'Astrophotography' as a subtitle, but matches 'Łukasz Remkowicz Astrophotography'
    // We want the navigation link specifically.
    const astroLinks = screen.getAllByRole('link', {
      name: 'Astrophotography',
    });
    const astroLink = astroLinks[0]; // Usually the first one in the desktop nav
    const homeLink = screen.getAllByRole('link', { name: 'Home' })[0];

    expect(astroLink).toHaveClass('active');
    expect(homeLink).not.toHaveClass('active');
  });
});
