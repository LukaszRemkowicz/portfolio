import { api } from '../api';
import {
  fetchProfile,
  fetchBackground,
  fetchAstroImages,
  fetchContact,
  fetchSettings,
} from '../services';
import { API_ROUTES, BFF_ROUTES } from '../routes';
import { API_BASE_URL } from '../constants';
import { NotFoundError, ValidationError } from '../errors';

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
    it('should fetch and transform profile data successfully', async () => {
      const mockProfile = {
        first_name: 'John',
        last_name: 'Doe',
        avatar: '/media/avatars/avatar.jpg',
        about_me_image: null,
        about_me_image2: null,
      };

      (api.get as jest.Mock).mockResolvedValueOnce({ data: mockProfile });

      const result = await fetchProfile();

      expect(api.get).toHaveBeenCalledWith(API_ROUTES.profile);
      expect(result.first_name).toBe('John');
      expect(result.avatar).toContain(
        `${API_BASE_URL}/media/avatars/avatar.jpg`
      );
    });

    it('should return fallback data on 404 for profile', async () => {
      (api.get as jest.Mock).mockRejectedValueOnce(new NotFoundError());

      const result = await fetchProfile();
      expect(result.first_name).toBe('Portfolio');
      expect(result.last_name).toBe('Owner');
    });

    it('should throw error on 500 for profile', async () => {
      (api.get as jest.Mock).mockRejectedValueOnce(new Error('server failed'));

      await expect(fetchProfile()).rejects.toThrow('server failed');
    });
  });

  describe('fetchBackground', () => {
    it('should return null on 404 for background', async () => {
      (api.get as jest.Mock).mockRejectedValueOnce(new NotFoundError());

      const result = await fetchBackground();
      expect(result).toBeNull();
    });
    it('should fetch background URL successfully', async () => {
      const mockBackground = { url: 'https://example.com/bg.jpg' };
      (api.get as jest.Mock).mockResolvedValueOnce({ data: mockBackground });

      const result = await fetchBackground();

      expect(api.get).toHaveBeenCalledWith(API_ROUTES.background);
      expect(result).toBe('https://example.com/bg.jpg');
    });

    it('should return null if API returns no URL', async () => {
      (api.get as jest.Mock).mockResolvedValueOnce({ data: { url: null } });

      const result = await fetchBackground();
      expect(result).toBeNull();
    });
  });

  describe('fetchAstroImages', () => {
    it('should fetch astro images with params', async () => {
      const mockImages = [{ pk: 1, name: 'Galaxy', description: 'Cool' }];
      (api.get as jest.Mock).mockResolvedValueOnce({ data: mockImages });

      const params = { filter: 'Landscape' };
      const result = await fetchAstroImages(params);

      expect(api.get).toHaveBeenCalledWith(API_ROUTES.astroImages, { params });
      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('Galaxy');
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

      expect(fetchMock).toHaveBeenCalledWith(BFF_ROUTES.contact, {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(contactData),
      });
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
        meteors: { randomShootingStars: true },
      };
      (api.get as jest.Mock).mockResolvedValueOnce({ data: mockSettings });

      const result = await fetchSettings();

      expect(api.get).toHaveBeenCalledWith(API_ROUTES.settings);
      expect(result.contactForm).toBe(true);
      expect(result.meteors?.randomShootingStars).toBe(true);
    });

    it('should throw on error', async () => {
      const consoleSpy = jest
        .spyOn(console, 'error')
        .mockImplementation(() => {});
      (api.get as jest.Mock).mockRejectedValueOnce(new Error('server failed'));

      await expect(fetchSettings()).rejects.toThrow('server failed');
      consoleSpy.mockRestore();
    });
  });
});
