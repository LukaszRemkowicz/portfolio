import {
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
});
