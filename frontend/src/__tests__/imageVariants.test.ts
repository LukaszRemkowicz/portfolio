import {
  buildResponsiveImageProps,
  getHeroVariantWidthForViewport,
  getImageVariantWidthForViewport,
} from '../utils/imageVariants';

describe('image variant utilities', () => {
  it.each([
    [320, 320],
    [640, 320],
    [641, 560],
    [1024, 560],
    [1025, 840],
    [1600, 840],
    [1601, 1120],
  ] as const)('maps %dpx viewport width to %dpx variant', (width, size) => {
    expect(getImageVariantWidthForViewport(width)).toBe(size);
  });

  it.each([
    [320, 1280],
    [1024, 1280],
    [1025, 1920],
    [1600, 1920],
    [1601, 2560],
  ] as const)(
    'maps %dpx viewport width to %dpx hero variant',
    (width, size) => {
      expect(getHeroVariantWidthForViewport(width)).toBe(size);
    }
  );

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
