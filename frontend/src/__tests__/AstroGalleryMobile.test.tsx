import { act } from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import '@testing-library/jest-dom';
import AstroGallery from '../components/AstroGallery';
import { useAppStore } from '../store/useStore';
import {
  fetchAstroImages,
  fetchSettings,
  fetchTags,
  fetchCategories,
} from '../api/services';

// Mock the API services
jest.mock('../api/services', () => ({
  fetchAstroImages: jest.fn(),
  fetchBackground: jest.fn(),
  fetchSettings: jest.fn(),
  fetchTags: jest.fn(),
  fetchCategories: jest.fn(),
}));

describe('AstroGallery Mobile Navigation', () => {
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
    (fetchSettings as jest.Mock).mockResolvedValue({
      programming: true,
      contactForm: true,
      lastimages: true,
      meteors: null,
    });
    (fetchTags as jest.Mock).mockResolvedValue([
      { name: 'Nebula', slug: 'nebula', count: 5 },
      { name: 'Galaxy', slug: 'galaxy', count: 10 },
    ]);
    (fetchAstroImages as jest.Mock).mockResolvedValue([]);
    (fetchCategories as jest.Mock).mockResolvedValue(['Landscape', 'Deep Sky']);
    resetStore();
  });

  const renderGallery = async () => {
    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path='/' element={<AstroGallery />} />
          </Routes>
        </MemoryRouter>
      );
    });

    // Wait for loading screen to be removed
    await waitFor(() => {
      expect(screen.queryByTestId('loading-screen')).not.toBeInTheDocument();
    });
  };

  it('toggles "Explore Tags" drawer on click', async () => {
    await renderGallery();

    const tagButton = screen.getByRole('button', { name: /Explore Tags/i });
    expect(tagButton).toBeInTheDocument();

    // Initially closed
    expect(tagButton).toHaveAttribute('aria-expanded', 'false');

    // Click to open
    await act(async () => {
      fireEvent.click(tagButton);
    });
    expect(tagButton).toHaveAttribute('aria-expanded', 'true');

    // Click to close
    await act(async () => {
      fireEvent.click(tagButton);
    });
    expect(tagButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('toggles "Categories" drawer on click', async () => {
    await renderGallery();

    const categoryButtons = screen.getAllByRole('button', {
      name: /Categories/i,
    });
    const categoryButton = categoryButtons[0];
    expect(categoryButton).toBeInTheDocument();

    // Initially closed
    expect(categoryButton).toHaveAttribute('aria-expanded', 'false');

    // Click to open
    await act(async () => {
      fireEvent.click(categoryButton);
    });
    expect(categoryButton).toHaveAttribute('aria-expanded', 'true');

    // Click to close
    await act(async () => {
      fireEvent.click(categoryButton);
    });
    expect(categoryButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('closes Tags drawer when Categories drawer opens', async () => {
    await renderGallery();

    const tagButton = screen.getByRole('button', { name: /Explore Tags/i });
    const categoryButtons = screen.getAllByRole('button', {
      name: /Categories/i,
    });
    const categoryButton = categoryButtons[0];

    // Open Tags
    await act(async () => {
      fireEvent.click(tagButton);
    });
    expect(tagButton).toHaveAttribute('aria-expanded', 'true');

    // Open Categories (should auto-close Tags)
    await act(async () => {
      fireEvent.click(categoryButton);
    });
    expect(categoryButton).toHaveAttribute('aria-expanded', 'true');
    expect(tagButton).toHaveAttribute('aria-expanded', 'false');
  });
});
