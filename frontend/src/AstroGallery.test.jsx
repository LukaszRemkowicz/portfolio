import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import AstroGallery from './AstroGallery';

// Mock the API services
jest.mock('./api/services', () => ({
  fetchAstroImages: jest.fn(() => Promise.resolve([
    { pk: 1, url: '/test1.jpg' },
    { pk: 2, url: '/test2.jpg' }
  ])),
  fetchBackground: jest.fn(() => Promise.resolve('/test-bg.jpg'))
}));

describe('AstroGallery', () => {
  it('renders the gallery title and filter boxes', async () => {
    render(<AstroGallery />);
    expect(screen.getByText(/Gallery/i)).toBeInTheDocument();
    expect(screen.getByText(/Landscape/i)).toBeInTheDocument();
    expect(screen.getByText(/Deep Sky/i)).toBeInTheDocument();
    expect(screen.getByText(/Startrails/i)).toBeInTheDocument();
    expect(screen.getByText(/Solar System/i)).toBeInTheDocument();
    expect(screen.getByText(/Milky Way/i)).toBeInTheDocument();
    expect(screen.getByText(/Northern Lights/i)).toBeInTheDocument();
  });

  it('renders images from the API', async () => {
    render(<AstroGallery />);
    await waitFor(() => {
      expect(screen.getAllByRole('img').length).toBe(2);
    });
  });
}); 