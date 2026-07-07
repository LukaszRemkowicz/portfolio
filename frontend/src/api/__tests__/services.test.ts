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
        avatar: '/media/avatars/avatar.jpg',
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
      expect(result.avatar).toBe('/media/avatars/avatar.jpg');
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
        avatar: '/media/avatars/avatar.jpg',
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

    it('should fetch profile with requested image size', async () => {
      const mockProfile = {
        first_name: 'John',
        last_name: 'Doe',
        avatar: '/media/avatars/avatar.jpg',
        about_me_image: null,
        about_me_image2: null,
      };
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile,
      } as Response);

      await fetchProfile(1920);

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.profile}?size=1920&lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
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
      const mockBackground = { url: '/media/backgrounds/example.webp' };
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

    it('should fetch background with requested image size', async () => {
      const mockBackground = { url: '/media/backgrounds/example.webp' };
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBackground,
      } as Response);

      await fetchBackground(1920);

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.background}?size=1920&lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
    });

    it('should return null if API returns no URL', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ url: null }),
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
        size: 840,
      } as const;
      const result = await fetchAstroImages(params);

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.astroImages}?filter=Landscape&size=840&lang=en`,
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
    it('should fetch latest astro images with requested image size', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => [
          { pk: 1, name: 'Galaxy', thumbnail_url: '/media/thumb.webp' },
        ],
      } as Response);

      const result = await fetchLatestAstroImages(840);

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.astroImages}latest/?size=840&lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
      expect(result).toHaveLength(1);
      expect(result[0].thumbnail_url).toBe('/media/thumb.webp');
    });
  });

  describe('fetchTravelHighlights', () => {
    it('should fetch travel highlights with requested image size', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => [
          {
            full_location: 'Norway',
            slug: 'norway',
            images: [{ pk: 1, thumbnail_url: '/media/travel.webp' }],
          },
        ],
      } as Response);

      const result = await fetchTravelHighlights(840);

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.travelHighlights}?size=840&lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
      expect(result).toHaveLength(1);
      expect(result[0].images[0].thumbnail_url).toBe('/media/travel.webp');
    });
  });

  describe('fetchShopProducts', () => {
    it('should fetch shop products with requested image size', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          title: 'Shop',
          description: 'Catalog',
          background_url: '/media/shop/background.webp',
          products: [
            {
              id: '1',
              title: 'Print',
              description: 'Fine art print',
              thumbnail_url: '/media/shop/print.webp',
            },
          ],
        }),
      } as Response);

      const result = await fetchShopProducts(840);

      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost${BFF_ROUTES.shop}?size=840&lang=en`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      );
      expect(result.products).toHaveLength(1);
      expect(result.products[0].thumbnail_url).toBe('/media/shop/print.webp');
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
