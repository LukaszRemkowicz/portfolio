describe('media URL normalization', () => {
  afterEach(() => {
    jest.resetModules();
  });

  it('keeps relative public media paths same-origin', () => {
    jest.isolateModules(() => {
      process.env.SSR_API_URL = 'http://be:8000';
      const { getMediaUrl } = require('../media');

      expect(getMediaUrl('/media/thumbnails/thumb.webp')).toBe(
        '/media/thumbnails/thumb.webp'
      );
    });
  });

  it('keeps relative secure image URLs same-origin', () => {
    jest.isolateModules(() => {
      process.env.SSR_API_URL = 'http://be:8000';
      const { getMediaUrl } = require('../media');

      expect(getMediaUrl('/v1/images/test-slug/serve/?s=abc&e=123')).toBe(
        '/app/image-files/test-slug/serve/?s=abc&e=123'
      );
    });
  });

  it('keeps generic relative paths on the API origin', () => {
    jest.isolateModules(() => {
      process.env.SSR_API_URL = 'http://be:8000';
      const { getMediaUrl } = require('../media');

      expect(getMediaUrl('foo/bar.jpg')).toBe(
        `${window.location.origin}/foo/bar.jpg`
      );
    });
  });
});
