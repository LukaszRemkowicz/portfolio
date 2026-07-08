import { buildResponsiveImageProps } from '../utils/imageVariants';

describe('image variant utilities', () => {
  it('builds srcSet, sizes, fallback src, and dimensions for a role', () => {
    const props = buildResponsiveImageProps({
      variants: {
        thumbnail: [
          {
            url: '/media/images/thumbnail.webp',
            width: 560,
            height: 373,
            mime_type: 'image/webp',
          },
        ],
      },
      role: 'thumbnail',
      fallbackSrc: '/media/images/thumb.webp',
      preferredWidth: 560,
      sizes: '(max-width: 640px) 100vw, 33vw',
    });

    expect(props).toEqual({
      src: '/media/images/thumb.webp',
      srcSet: '/media/images/thumbnail.webp 560w',
      sizes: '(max-width: 640px) 100vw, 33vw',
      width: 560,
      height: 373,
    });
  });
});
