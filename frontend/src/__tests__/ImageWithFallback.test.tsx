import { render, screen } from '@testing-library/react';
import ImageWithFallback from '../components/common/ImageWithFallback';

describe('ImageWithFallback', () => {
  it('recovers from an initial empty src when a real src arrives later', () => {
    const { rerender } = render(
      <ImageWithFallback src='' alt='Travel card' fallbackSrc='/fallback.jpg' />
    );

    expect(screen.getByAltText('Travel card')).toHaveAttribute(
      'src',
      '/fallback.jpg'
    );

    rerender(
      <ImageWithFallback
        src='/real-image.jpg'
        alt='Travel card'
        fallbackSrc='/fallback.jpg'
      />
    );

    expect(screen.getByAltText('Travel card')).toHaveAttribute(
      'src',
      '/real-image.jpg'
    );
  });
});
