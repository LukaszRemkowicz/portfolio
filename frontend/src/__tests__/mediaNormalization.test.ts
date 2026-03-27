import {
  normalizeBffPayload,
  normalizePublicMediaUrl,
} from '../../server/mediaNormalization.js';

describe('media normalization', () => {
  it('keeps already-public media paths unchanged', () => {
    expect(normalizePublicMediaUrl('/media/test.webp')).toBe(
      '/media/test.webp'
    );
    expect(normalizePublicMediaUrl('/static/test.webp')).toBe(
      '/static/test.webp'
    );
    expect(normalizePublicMediaUrl('/app/image-files/slug/serve/')).toBe(
      '/app/image-files/slug/serve/'
    );
  });

  it('rewrites internal image-file paths to the public app path', () => {
    expect(normalizePublicMediaUrl('/image-files/slug/serve/')).toBe(
      '/app/image-files/slug/serve/'
    );
    expect(normalizePublicMediaUrl('/v1/images/slug/serve/?s=abc&e=1')).toBe(
      '/app/image-files/slug/serve/?s=abc&e=1'
    );
  });

  it('rewrites absolute backend media URLs to public frontend paths', () => {
    expect(
      normalizePublicMediaUrl('https://api.example.com/media/test.webp')
    ).toBe('/media/test.webp');
    expect(
      normalizePublicMediaUrl('https://api.example.com/image-files/slug/serve/')
    ).toBe('/app/image-files/slug/serve/');
    expect(
      normalizePublicMediaUrl(
        'https://api.example.com/v1/images/slug/serve/?s=abc&e=1'
      )
    ).toBe('/app/image-files/slug/serve/?s=abc&e=1');
  });

  it('leaves unrelated values unchanged', () => {
    expect(normalizePublicMediaUrl('not-a-url')).toBe('not-a-url');
    expect(normalizePublicMediaUrl('https://example.com/elsewhere')).toBe(
      'https://example.com/elsewhere'
    );
    expect(normalizePublicMediaUrl(null)).toBeNull();
  });

  it('normalizes astroimage paginated results payloads', () => {
    expect(
      normalizeBffPayload(
        {
          results: [{ url: 'https://api.example.com/media/test.webp' }],
        },
        'astroimages'
      )
    ).toEqual([{ url: '/media/test.webp' }]);
  });

  it('normalizes object payload fields for image responses', () => {
    expect(
      normalizeBffPayload(
        {
          url: 'https://api.example.com/image-files/slug/serve/',
          thumbnail_url: '/media/thumb.webp',
          title: 'M31',
        },
        'images'
      )
    ).toEqual({
      url: '/app/image-files/slug/serve/',
      thumbnail_url: '/media/thumb.webp',
      title: 'M31',
    });
  });
});
