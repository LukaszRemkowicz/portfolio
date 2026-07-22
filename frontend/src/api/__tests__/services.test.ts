import {
  fetchProfile,
  fetchBackground,
  fetchAstroImages,
  fetchLatestAstroImages,
  fetchTravelHighlights,
  fetchShopProducts,
  fetchContact,
  fetchSettings,
} from '../services';
import { API_ROUTES, BFF_ROUTES } from '../routes';
import { ValidationError } from '../errors';

// Mock the axios instance from api.ts
jest.mock('../api', () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

describe('API Services', () => {
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

  describe('fetchProfile', () => {
    it('should fetch and transform profile data through the BFF in the browser', async () => {
      const mockProfile = {
        first_name: 'John',
        last_name: 'Doe',
        avatar: {
          fallback_image: {
            url: '/media/avatars/avatar.jpg',
            width: 800,
            height: 800,
            mime_type: 'image/webp',
          },
          variants: {
            original_format: [
              {
                url: '/media/avatars/avatar.jpg',
                width: 800,
                height: 800,
                mime_type: 'image/webp',
              },
            ],
          },
        },
        about_me_image: null,
        about_me_image2: null,
      };

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile,
      } as Response);

      const result = await fetchProfile();

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.profile}?lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
      expect(result.first_name).toBe('John');
      expect(result.avatar?.fallback_image?.url).toBe(
        '/media/avatars/avatar.jpg'
      );
    });

    it('should return fallback data on 404 for profile', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      } as Response);

      const result = await fetchProfile();
      expect(result.first_name).toBe('Portfolio');
      expect(result.last_name).toBe('Owner');
    });

    it('should throw error on 500 for profile', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'server failed' }),
      } as Response);

      await expect(fetchProfile()).rejects.toThrow('server failed');
    });

    it('should still use the backend client outside the browser-default transport', async () => {
      const mockProfile = {
        first_name: 'Jane',
        last_name: 'Doe',
        avatar: {
          fallback_image: {
            url: '/media/avatars/avatar.jpg',
            width: 800,
            height: 800,
            mime_type: 'image/webp',
          },
          variants: {
            original_format: [
              {
                url: '/media/avatars/avatar.jpg',
                width: 800,
                height: 800,
                mime_type: 'image/webp',
              },
            ],
          },
        },
        about_me_image: null,
        about_me_image2: null,
      };
      const customClient = {
        get: jest.fn().mockResolvedValue({ data: mockProfile }),
      };

      const result = await fetchProfile(customClient as never);

      expect(customClient.get).toHaveBeenCalledWith(API_ROUTES.profile);
      expect(result.first_name).toBe('Jane');
    });
  });

  describe('fetchBackground', () => {
    it('should return null on 404 for background', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      } as Response);

      const result = await fetchBackground();
      expect(result).toBeNull();
    });
    it('should fetch background URL successfully', async () => {
      const mockBackground = {
        fallback_image: {
          url: '/media/backgrounds/example.webp',
          width: 2560,
          height: 1440,
          mime_type: 'image/webp',
        },
      };
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBackground,
      } as Response);

      const result = await fetchBackground();

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.background}?lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
      expect(result).toBe('/media/backgrounds/example.webp');
    });

    it('should return null if API returns no fallback image', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ fallback_image: null, variants: { hero: [] } }),
      } as Response);

      const result = await fetchBackground();
      expect(result).toBeNull();
    });
  });

  describe('fetchAstroImages', () => {
    it('should fetch astro images with params', async () => {
      const mockImages = {
        count: 1,
        next: null,
        previous: null,
        results: [{ pk: 1, name: 'Galaxy', description: 'Cool' }],
      };
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockImages,
      } as Response);

      const params = {
        filter: 'Landscape',
      } as const;
      const result = await fetchAstroImages(params);

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.astroImages}?filter=Landscape&lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
      expect(result.count).toBe(1);
      expect(result.results).toHaveLength(1);
      expect(result.results[0].name).toBe('Galaxy');
    });
  });

  describe('fetchLatestAstroImages', () => {
    it('should fetch latest astro images without image size filtering', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => [
          {
            pk: 1,
            name: 'Galaxy',
            fallback_image: {
              url: '/media/card.webp',
              width: 560,
              height: 373,
              mime_type: 'image/webp',
            },
          },
        ],
      } as Response);

      const result = await fetchLatestAstroImages();

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.astroImages}latest/?lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
      expect(result).toHaveLength(1);
      expect(result[0].fallback_image?.url).toBe('/media/card.webp');
    });
  });

  describe('fetchTravelHighlights', () => {
    it('should fetch travel highlights without image size filtering', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => [
          {
            full_location: 'Norway',
            slug: 'norway',
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
          },
        ],
      } as Response);

      const result = await fetchTravelHighlights();

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.travelHighlights}?lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
      expect(result).toHaveLength(1);
      expect(result[0].images[0].fallback_image?.url).toBe(
        '/media/travel-card.webp'
      );
    });
  });

  describe('fetchShopProducts', () => {
    it('should fetch shop products with requested image size', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          title: 'Shop',
          description: 'Catalog',
          fallback_image: {
            url: '/media/shop/background.webp',
            width: 1920,
            height: 1080,
            mime_type: 'image/webp',
          },
          variants: {
            background: [
              {
                url: '/media/shop/background-1280.webp',
                width: 1280,
                height: 720,
                mime_type: 'image/webp',
              },
            ],
          },
          products: [
            {
              id: '1',
              title: 'Print',
              description: 'Fine art print',
              fallback_image: {
                url: '/media/shop/print.webp',
                width: 560,
                height: 373,
                mime_type: 'image/webp',
              },
              variants: {
                thumbnail: [
                  {
                    url: '/media/shop/print-560.webp',
                    width: 560,
                    height: 373,
                    mime_type: 'image/webp',
                  },
                ],
              },
            },
          ],
        }),
      } as Response);

      const result = await fetchShopProducts();

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.shop}?lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
      expect(result.products).toHaveLength(1);
      expect(result.fallback_image?.url).toBe('/media/shop/background.webp');
      expect(result.variants?.background[0].url).toBe(
        '/media/shop/background-1280.webp'
      );
      expect(result.products[0].fallback_image?.url).toBe(
        '/media/shop/print.webp'
      );
      expect(result.products[0].variants?.thumbnail[0].url).toBe(
        '/media/shop/print-560.webp'
      );
    });
  });

  describe('fetchContact', () => {
    it('should send contact form successfully', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'ok' }),
      } as Response);

      const contactData = {
        name: 'John',
        email: 'john@example.com',
        subject: 'Inquiry',
        message: 'Hello',
      };

      await fetchContact(contactData);

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.contact}?lang=en`,
        expect.objectContaining({
          method: 'POST',
          headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(contactData),
        })
      );
    });

    it('should throw error on validation failure', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          errors: { email: ['Invalid email'] },
          message: 'Validation failed.',
        }),
      } as Response);

      const contactData = {
        name: 'John',
        email: 'bad-email',
        subject: 'Inquiry',
        message: 'Hello',
      };

      await expect(fetchContact(contactData)).rejects.toBeInstanceOf(
        ValidationError
      );
    });
  });

  describe('fetchSettings', () => {
    it('should fetch settings successfully', async () => {
      const mockSettings = {
        contactForm: true,
        programming: false,
        total_time_spent: 12,
        meteors: { randomShootingStars: true },
      };
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      } as Response);

      const result = await fetchSettings();

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.settings}?lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
      expect(result.contactForm).toBe(true);
      expect(result.total_time_spent).toBe(12);
      expect(result.meteors?.randomShootingStars).toBe(true);
    });

    it('should throw on error', async () => {
      const consoleSpy = jest
        .spyOn(console, 'error')
        .mockImplementation(() => {});
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'server failed' }),
      } as Response);

      await expect(fetchSettings()).rejects.toThrow('server failed');
      consoleSpy.mockRestore();
    });
  });
});
