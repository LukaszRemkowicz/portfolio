import { BFF_ROUTES } from '../../api/routes';
import type { DataTransport } from '../../api/transport';
import { fetchTravelHighlightDetail } from '../../hooks/useTravelHighlightDetail';

describe('fetchTravelHighlightDetail', () => {
  it('requests the preferred image size', async () => {
    const get = jest.fn().mockResolvedValue({
      full_location: 'Norway',
      images: [{ pk: 1, thumbnail_url: '/media/travel.webp' }],
    });
    const transport: DataTransport = {
      __dataTransport: true,
      kind: 'browser',
      get,
      post: jest.fn(),
    };

    const result = await fetchTravelHighlightDetail({
      countrySlug: 'norway',
      placeSlug: 'lofoten',
      dateSlug: '2026-02',
      imageSize: 840,
      clientOrTransport: transport,
    });

    expect(get).toHaveBeenCalledWith(
      expect.objectContaining({
        browser: `${BFF_ROUTES.travelBySlug}norway/lofoten/2026-02/`,
      }),
      { size: 840 }
    );
    expect(result.images[0].thumbnail_url).toBe('/media/travel.webp');
  });
});
