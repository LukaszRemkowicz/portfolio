/**
 * High-level frontend data services.
 *
 * This module defines the application-facing API contract used by hooks, SSR
 * prefetch, and selected server-side views. It sits above the low-level Axios
 * client and below the React Query hooks:
 * - chooses backend routes
 * - applies payload normalization
 * - provides fallback behavior for selected content
 * - stays transport-agnostic while callers resolve browser vs. SSR transport
 */
import type { AxiosInstance } from 'axios';
import { API_ROUTES, BFF_ROUTES } from './routes';
import { api } from './api';
import {
  normalizeAstroImage,
  normalizeAstroImages,
  getMediaUrl,
  normalizeProfileMedia,
  normalizeTravelLocation,
} from './media';
import {
  UserProfile,
  BackgroundImage,
  AstroImage,
  ContactFormData,
  FilterParams,
  EnabledFeatures,
  Project,
  MainPageLocation,
  Tag,
} from '../types';
import { NotFoundError } from './errors';
import { DataTransport, resolveDataTransport } from './transport';

/** Fetch and normalize the public user profile used across the site shell. */
export const fetchProfile = async (
  clientOrTransport: AxiosInstance | DataTransport = api
): Promise<UserProfile> => {
  const transport = resolveDataTransport(clientOrTransport);

  try {
    const data = await transport.get<UserProfile>({
      browser: BFF_ROUTES.profile,
      server: API_ROUTES.profile,
    });

    if (data) {
      return normalizeProfileMedia(data);
    }
    return data;
  } catch (error) {
    if (error instanceof NotFoundError) {
      console.warn('Profile not found, using fallbacks');
      return {
        first_name: 'Portfolio',
        last_name: 'Owner',
        short_description: 'Landscape and Astrophotography',
        avatar: null,
        bio: '',
        about_me_image: null,
        about_me_image2: null,
      };
    }
    throw error;
  }
};

/** Fetch the homepage background image URL, if configured. */
export const fetchBackground = async (
  clientOrTransport: AxiosInstance | DataTransport = api
): Promise<string | null> => {
  const transport = resolveDataTransport(clientOrTransport);

  try {
    const data = await transport.get<BackgroundImage>({
      browser: BFF_ROUTES.background,
      server: API_ROUTES.background,
    });
    if (data && data.url) {
      return transport.kind === 'browser' ? getMediaUrl(data.url) : data.url;
    }
    return null;
  } catch (error) {
    if (error instanceof NotFoundError) {
      console.warn('Background image not found');
      return null;
    }
    throw error;
  }
};

/** Fetch the astrophotography gallery list with optional filtering parameters. */
export const fetchAstroImages = async (
  params: FilterParams = {},
  clientOrTransport: AxiosInstance | DataTransport = api
): Promise<AstroImage[]> => {
  const transport = resolveDataTransport(clientOrTransport);
  const data = await transport.get<AstroImage[] | { results: AstroImage[] }>(
    {
      browser: BFF_ROUTES.astroImages,
      server: API_ROUTES.astroImages,
    },
    params
  );
  const items = Array.isArray(data) ? data : data?.results || [];
  return normalizeAstroImages(items);
};

/** Fetch the latest homepage astro images used in the shared shell. */
export const fetchLatestAstroImages = async (
  clientOrTransport: AxiosInstance | DataTransport = api
): Promise<AstroImage[]> => {
  const transport = resolveDataTransport(clientOrTransport);
  const data = await transport.get<AstroImage[] | { results: AstroImage[] }>({
    browser: `${BFF_ROUTES.astroImages}latest/`,
    server: `${API_ROUTES.astroImages}latest/`,
  });
  const items = Array.isArray(data) ? data : data?.results || [];
  return normalizeAstroImages(items);
};

/** Fetch a single astro image detail payload by slug. */
export const fetchAstroImageDetail = async (
  slug: string,
  clientOrTransport: AxiosInstance | DataTransport = api
): Promise<AstroImage> => {
  const transport = resolveDataTransport(clientOrTransport);
  const data = await transport.get<AstroImage>({
    browser: `${BFF_ROUTES.astroImages}${slug}/`,
    server: `${API_ROUTES.astroImages}${slug}/`,
  });
  if (data) {
    return normalizeAstroImage(data);
  }
  return data;
};

/**
 * Submit the contact form.
 *
 * Browser callers post through the frontend-owned transport endpoint, while SSR
 * or internal callers can still use the backend client directly.
 */
export const fetchContact = async (
  contactData: ContactFormData,
  clientOrTransport: AxiosInstance | DataTransport = api
): Promise<void> => {
  if (!contactData) throw new Error('contactData is required');

  const transport = resolveDataTransport(clientOrTransport);
  await transport.post<void>(
    {
      browser: BFF_ROUTES.contact,
      server: API_ROUTES.contact,
    },
    contactData
  );
};

/** Fetch public tag options, optionally filtered by category. */
export const fetchTags = async (
  params: { filter?: string; latest?: boolean; lang?: string } = {},
  clientOrTransport: AxiosInstance | DataTransport = api
): Promise<Tag[]> => {
  const transport = resolveDataTransport(clientOrTransport);
  return transport.get<Tag[]>(
    {
      browser: BFF_ROUTES.tags,
      server: API_ROUTES.tags,
    },
    params
  );
};

/** Fetch enabled frontend feature flags and configuration switches. */
export const fetchSettings = async (
  clientOrTransport: AxiosInstance | DataTransport = api
): Promise<EnabledFeatures> => {
  const transport = resolveDataTransport(clientOrTransport);

  try {
    return transport.get<EnabledFeatures>({
      browser: BFF_ROUTES.settings,
      server: API_ROUTES.settings,
    });
  } catch (error: unknown) {
    console.error('Error fetching settings:', error);
    // Unexpected failures should propagate so SSR and client callers can decide
    // whether to surface an error state or fall back at a higher level.
    throw error;
  }
};

/** Placeholder project service kept for compatibility until project data is reintroduced. */
export const fetchProjects = async (): Promise<Project[]> => {
  // const response: AxiosResponse<Project[]> = await api.get(API_ROUTES.projects);
  // const data = handleResponse<Project[]>(response);
  // if (Array.isArray(data)) {
  //   return data.map(project => ({
  //     ...project,
  //     images: project.images.map(image => ({
  //       ...image,
  //       url: getMediaUrl(image.url) || '',
  //       thumbnail_url: getMediaUrl(image.thumbnail_url) || undefined,
  //     })),
  //   }));
  // }
  // return data;
  return [];
};

/** Fetch and normalize the travel highlights shown on the homepage. */
export const fetchTravelHighlights = async (
  clientOrTransport: AxiosInstance | DataTransport = api
): Promise<MainPageLocation[]> => {
  const transport = resolveDataTransport(clientOrTransport);
  const data = await transport.get<MainPageLocation[]>({
    browser: BFF_ROUTES.travelHighlights,
    server: API_ROUTES.travelHighlights,
  });

  if (Array.isArray(data)) {
    return data.map(normalizeTravelLocation);
  }
  return [];
};

/** Fetch the public astrophotography category list. */
export const fetchCategories = async (
  clientOrTransport: AxiosInstance | DataTransport = api
): Promise<string[]> => {
  const transport = resolveDataTransport(clientOrTransport);
  return transport.get<string[]>({
    browser: BFF_ROUTES.categories,
    server: API_ROUTES.categories,
  });
};
