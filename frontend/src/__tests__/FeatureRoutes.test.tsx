import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ShopRoute from '../components/ShopRoute';
import ProgrammingRoute from '../components/ProgrammingRoute';
import { useFeatureFlag } from '../hooks/useFeatureFlag';

jest.mock('../hooks/useFeatureFlag');
jest.mock('../components/MainLayout', () => ({
  __esModule: true,
  default: ({ children }: { children: unknown }) => (
    <div data-testid='main-layout'>{children}</div>
  ),
}));
jest.mock('../components/Shop', () => ({
  __esModule: true,
  default: () => <div>Shop page</div>,
}));
jest.mock('../components/Programming', () => ({
  __esModule: true,
  default: () => <div>Programming page</div>,
}));

describe('Feature routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the shop page when the feature is enabled', () => {
    (useFeatureFlag as jest.Mock).mockImplementation(feature => ({
      isEnabled: feature === 'shop',
      isLoading: false,
    }));

    render(
      <MemoryRouter initialEntries={['/shop']}>
        <Routes>
          <Route path='/' element={<div>Home page</div>} />
          <Route path='/shop' element={<ShopRoute />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('main-layout')).toBeInTheDocument();
    expect(screen.getByText('Shop page')).toBeInTheDocument();
  });

  it('redirects the shop route to home when disabled', () => {
    (useFeatureFlag as jest.Mock).mockImplementation(() => ({
      isEnabled: false,
      isLoading: false,
    }));

    render(
      <MemoryRouter initialEntries={['/shop']}>
        <Routes>
          <Route path='/' element={<div>Home page</div>} />
          <Route path='/shop' element={<ShopRoute />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Home page')).toBeInTheDocument();
    expect(screen.queryByText('Shop page')).not.toBeInTheDocument();
  });

  it('redirects the programming route to home when disabled', () => {
    (useFeatureFlag as jest.Mock).mockImplementation(() => ({
      isEnabled: false,
      isLoading: false,
    }));

    render(
      <MemoryRouter initialEntries={['/programming']}>
        <Routes>
          <Route path='/' element={<div>Home page</div>} />
          <Route path='/programming' element={<ProgrammingRoute />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Home page')).toBeInTheDocument();
    expect(screen.queryByText('Programming page')).not.toBeInTheDocument();
  });

  it('renders the programming page when the feature is enabled', () => {
    (useFeatureFlag as jest.Mock).mockImplementation(feature => ({
      isEnabled: feature === 'programming',
      isLoading: false,
    }));

    render(
      <MemoryRouter initialEntries={['/programming']}>
        <Routes>
          <Route path='/' element={<div>Home page</div>} />
          <Route path='/programming' element={<ProgrammingRoute />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('main-layout')).toBeInTheDocument();
    expect(screen.getByText('Programming page')).toBeInTheDocument();
  });

  it('renders nothing while feature settings are loading', () => {
    (useFeatureFlag as jest.Mock).mockImplementation(() => ({
      isEnabled: false,
      isLoading: true,
    }));

    const { container } = render(
      <MemoryRouter initialEntries={['/shop']}>
        <Routes>
          <Route path='/' element={<div>Home page</div>} />
          <Route path='/shop' element={<ShopRoute />} />
        </Routes>
      </MemoryRouter>
    );

    expect(container).toBeEmptyDOMElement();
  });
});
