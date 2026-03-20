import { fetchImageUrls, fetchSingleImageUrl } from '../imageUrlService';
import { BFF_ROUTES } from '../routes';

describe('imageUrlService', () => {
  let fetchMock: jest.Mock;

  beforeEach(() => {
    fetchMock = jest.fn();
    Object.defineProperty(global, 'fetch', {
      configurable: true,
      value: fetchMock,
      writable: true,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    delete (global as { fetch?: typeof fetch }).fetch;
  });

  it('uses frontend BFF route for image list in the browser', async () => {
    const payload = { '1': 'https://example.com/signed.webp' };
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => payload,
    } as Response);

    const result = await fetchImageUrls(['1']);

    expect(fetchMock).toHaveBeenCalledWith(`${BFF_ROUTES.images}?ids=1`, {
      headers: {
        Accept: 'application/json',
      },
    });
    expect(result).toEqual(payload);
  });

  it('uses frontend BFF route for single image in the browser', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ url: 'https://example.com/signed.webp' }),
    } as Response);

    const result = await fetchSingleImageUrl('m31');

    expect(fetchMock).toHaveBeenCalledWith(`${BFF_ROUTES.images}m31/`, {
      headers: {
        Accept: 'application/json',
      },
    });
    expect(result).toBe('https://example.com/signed.webp');
  });
});
