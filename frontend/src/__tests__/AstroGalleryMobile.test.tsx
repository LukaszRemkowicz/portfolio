import { act } from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import '@testing-library/jest-dom';
import AstroGallery from '../components/AstroGallery';
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

describe('AstroGallery Mobile Navigation', () => {
  beforeEach(() => {
    jest.resetAllMocks();
    (useBackground as jest.Mock).mockReturnValue({ data: null });
    (useSettings as jest.Mock).mockReturnValue({
      data: {
        programming: true,
        contactForm: true,
        lastimages: true,
        meteors: null,
      },
    });
    (useTags as jest.Mock).mockReturnValue({
      data: [
        { name: 'Nebula', slug: 'nebula', count: 5 },
        { name: 'Galaxy', slug: 'galaxy', count: 10 },
      ],
      isLoading: false,
    });
    (useCategories as jest.Mock).mockReturnValue({
      data: ['Landscape', 'Deep Sky'],
      isLoading: false,
    });
    (useAstroImages as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
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
