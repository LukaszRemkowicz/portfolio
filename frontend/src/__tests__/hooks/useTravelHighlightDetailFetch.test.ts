import { BFF_ROUTES } from '../../api/routes';
import type { DataTransport } from '../../api/transport';
import { fetchTravelHighlightDetail } from '../../hooks/useTravelHighlightDetail';

describe('fetchTravelHighlightDetail', () => {
  it('requests travel detail without image size filtering', async () => {
    const get = jest.fn().mockResolvedValue({
      full_location: 'Norway',
      images: [
        {
          pk: 1,
          fallback_image: {
            url: '/media/travel-card.webp',
            width: 560,
            height: 373,
            mime_type: 'image/webp',
          },
        },
      ],
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
      clientOrTransport: transport,
    });

    expect(get).toHaveBeenCalledWith(
      expect.objectContaining({
        browser: `${BFF_ROUTES.travelBySlug}norway/lofoten/2026-02/`,
      })
    );
    expect(result.images[0].fallback_image?.url).toBe(
      '/media/travel-card.webp'
    );
  });
});
