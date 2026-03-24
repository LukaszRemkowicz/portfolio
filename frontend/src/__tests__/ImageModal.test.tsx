// frontend/src/__tests__/ImageModal.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ImageModal from '../components/common/ImageModal';
import { AstroImage } from '../types';
import { useAstroImageDetail } from '../hooks/useAstroImageDetail';
import { useImageUrls } from '../hooks/useImageUrls';

jest.mock('../hooks/useAstroImageDetail');
jest.mock('../hooks/useImageUrls');

const mockImage: AstroImage = {
  pk: '1',
  slug: 'test-image',
  name: 'Test Image',
  thumbnail_url: 'test.jpg',
  description: 'A test nebula',
  capture_date: '2023-01-01',
  tags: [
    { name: 'nebula', slug: 'nebula', count: 1 },
    { name: 'space', slug: 'space', count: 1 },
  ],
};

const renderModal = (
  image: AstroImage | null = mockImage,
  onClose = jest.fn()
) => {
  (useAstroImageDetail as jest.Mock).mockReturnValue({
    data: undefined,
    isLoading: false,
    error: null,
  });

  (useImageUrls as jest.Mock).mockReturnValue({
    data: {},
  });

  return render(
    <BrowserRouter>
      <ImageModal image={image} onClose={onClose} />
    </BrowserRouter>
  );
};

describe('ImageModal Lightbox', () => {
  const originalImage = global.Image;

  afterEach(() => {
    global.Image = originalImage;
  });

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

  it('switches the modal image from thumbnail to async signed URL when it arrives', () => {
    (useAstroImageDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    class SuccessfulImage {
      onload: null | (() => void) = null;
      onerror: null | (() => void) = null;

      set src(_value: string) {
        queueMicrotask(() => {
          this.onload?.();
        });
      }
    }

    global.Image = SuccessfulImage as unknown as typeof Image;

    (useImageUrls as jest.Mock)
      .mockReturnValueOnce({ data: {} })
      .mockReturnValueOnce({ data: { '1': '/signed-image.webp' } });

    const { rerender } = render(
      <BrowserRouter>
        <ImageModal image={mockImage} onClose={jest.fn()} />
      </BrowserRouter>
    );

    expect(screen.getByAltText('Test Image')).toHaveAttribute(
      'src',
      'test.jpg'
    );

    rerender(
      <BrowserRouter>
        <ImageModal image={mockImage} onClose={jest.fn()} />
      </BrowserRouter>
    );

    return screen.findByAltText('Test Image').then(img => {
      expect(img).toHaveAttribute('src', '/signed-image.webp');
    });
  });

  it('uses the resolved signed URL for the full resolution overlay after zoom is opened', () => {
    class SuccessfulImage {
      onload: null | (() => void) = null;
      onerror: null | (() => void) = null;

      set src(_value: string) {
        queueMicrotask(() => {
          this.onload?.();
        });
      }
    }

    global.Image = SuccessfulImage as unknown as typeof Image;

    (useAstroImageDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    (useImageUrls as jest.Mock).mockReturnValue({
      data: { '1': '/signed-image.webp' },
    });

    render(
      <BrowserRouter>
        <ImageModal image={mockImage} onClose={jest.fn()} />
      </BrowserRouter>
    );

    return screen.findByAltText('Test Image').then(img => {
      expect(img).toHaveAttribute('src', '/signed-image.webp');

      fireEvent.click(img);

      const images = screen.getAllByAltText('Test Image');
      expect(images[0]).toHaveAttribute('src', '/signed-image.webp');
      expect(images[1]).toHaveAttribute('src', '/signed-image.webp');
    });
  });

  it('keeps the working thumbnail when the async signed URL fails to load', () => {
    class FailingImage {
      onload: null | (() => void) = null;
      onerror: null | (() => void) = null;

      set src(_value: string) {
        queueMicrotask(() => {
          this.onerror?.();
        });
      }
    }

    global.Image = FailingImage as unknown as typeof Image;

    (useAstroImageDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    (useImageUrls as jest.Mock)
      .mockReturnValueOnce({ data: {} })
      .mockReturnValueOnce({ data: { '1': '/broken-signed-image.webp' } });

    const { rerender } = render(
      <BrowserRouter>
        <ImageModal image={mockImage} onClose={jest.fn()} />
      </BrowserRouter>
    );

    expect(screen.getByAltText('Test Image')).toHaveAttribute(
      'src',
      'test.jpg'
    );

    rerender(
      <BrowserRouter>
        <ImageModal image={mockImage} onClose={jest.fn()} />
      </BrowserRouter>
    );

    return screen.findByAltText('Test Image').then(img => {
      expect(img).toHaveAttribute('src', 'test.jpg');
    });
  });
});
