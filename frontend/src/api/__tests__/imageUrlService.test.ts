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
    const payload = { '1': 'http://be:8000/v1/images/test/serve/?s=abc&e=123' };
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
    expect(result).toEqual({
      '1': '/app/image-files/test/serve/?s=abc&e=123',
    });
  });

  it('uses frontend BFF route for single image in the browser', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        url: 'http://be:8000/v1/images/m31/serve/?s=abc&e=123',
      }),
    } as Response);

    const result = await fetchSingleImageUrl('m31');

    expect(fetchMock).toHaveBeenCalledWith(`${BFF_ROUTES.images}m31/`, {
      headers: {
        Accept: 'application/json',
      },
    });
    expect(result).toBe('/app/image-files/m31/serve/?s=abc&e=123');
  });
});
