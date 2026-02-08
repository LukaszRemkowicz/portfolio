// frontend/src/__tests__/ImageModal.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ImageModal from '../components/common/ImageModal';
import { AstroImage } from '../types';

const mockImage: AstroImage = {
  pk: 1,
  slug: 'test-image',
  name: 'Test Image',
  url: 'test.jpg',
  description: 'A test nebula',
  capture_date: '2023-01-01',
  tags: ['nebula', 'space'],
};

const renderModal = (
  image: AstroImage | null = mockImage,
  onClose = jest.fn()
) => {
  return render(
    <BrowserRouter>
      <ImageModal image={image} onClose={onClose} />
    </BrowserRouter>
  );
};

describe('ImageModal Lightbox', () => {
  it('renders the modal when image is provided', () => {
    renderModal();
    expect(screen.getByText('Test Image')).toBeInTheDocument();
    expect(screen.getByAltText('Test Image')).toBeInTheDocument();
  });

  it('opens full resolution view when image is clicked', () => {
    renderModal();
    const modalImage = screen.getByAltText('Test Image');
    fireEvent.click(modalImage);

    // After click, we should have two images (one in modal, one in full-res portal)
    const images = screen.getAllByAltText('Test Image');
    expect(images).toHaveLength(2);
  });

  it('closes full resolution view when close button in lightbox is clicked', () => {
    renderModal();
    fireEvent.click(screen.getByAltText('Test Image'));

    const closeButtons = screen.getAllByRole('button');
    // The lightbox close button is the one with the X icon (last one added)
    fireEvent.click(closeButtons[closeButtons.length - 1]);

    expect(screen.getAllByAltText('Test Image')).toHaveLength(1);
  });

  it('handles Escape key to close full resolution view first', () => {
    const onClose = jest.fn();
    renderModal(mockImage, onClose);

    fireEvent.click(screen.getByAltText('Test Image'));
    expect(screen.getAllByAltText('Test Image')).toHaveLength(2);

    fireEvent.keyDown(window, { key: 'Escape' });

    // Should still have 1 image (modal stays open)
    expect(screen.getAllByAltText('Test Image')).toHaveLength(1);
    expect(onClose).not.toHaveBeenCalled();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });

  it('toggles zoom on image click in full resolution view', () => {
    renderModal();
    const modalImage = screen.getByAltText('Test Image');
    fireEvent.click(modalImage);

    // Get the lightbox image (it's the second one rendered)
    const images = screen.getAllByAltText('Test Image');
    const lightboxImage = images[1];

    // Initial state should not have zoomed class
    expect(lightboxImage).not.toHaveClass('isZoomed');

    // Click to zoom (need mouseDown to set timing)
    fireEvent.mouseDown(lightboxImage);
    fireEvent.click(lightboxImage);
    expect(lightboxImage).toHaveClass('isZoomed');

    // Click to unzoom
    fireEvent.mouseDown(lightboxImage);
    fireEvent.click(lightboxImage);
    expect(lightboxImage).not.toHaveClass('isZoomed');
  });

  it('disables zoom when image.process is false', () => {
    const disabledImage = { ...mockImage, process: false };
    renderModal(disabledImage);

    const modalImage = screen.getByAltText('Test Image');
    fireEvent.click(modalImage);

    // Lightbox should NOT open because we disabled it in the onClick handler
    expect(screen.getAllByAltText('Test Image')).toHaveLength(1);

    // Tooltip should be undefined/null
    expect(modalImage).not.toHaveAttribute('title');
    expect(modalImage).toHaveStyle('cursor: default');
  });
});
