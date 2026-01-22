import { AxiosResponse } from 'axios';
import { API_ROUTES, getMediaUrl } from './routes';
import { api } from './api';
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

const handleResponse = <T>(response: AxiosResponse<T>): T => {
  if (response && response.data !== undefined) {
    // The API returns an array for lists and an object for single items.
    // Both are valid and should be returned.
    return response.data;
  }
  // Handle cases where response or response.data is undefined
  console.error('Invalid response structure:', response);
  throw new Error('Invalid response from server.');
};

export const fetchProfile = async (): Promise<UserProfile> => {
  try {
    const response: AxiosResponse<UserProfile> = await api.get(
      API_ROUTES.profile
    );
    const data = handleResponse<UserProfile>(response);

    // Transform relative media paths to full URLs
    if (data) {
      return {
        ...data,
        avatar: data.avatar ? getMediaUrl(data.avatar) : null,
        about_me_image: data.about_me_image
          ? getMediaUrl(data.about_me_image)
          : null,
        about_me_image2: data.about_me_image2
          ? getMediaUrl(data.about_me_image2)
          : null,
      };
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

export const fetchBackground = async (): Promise<string | null> => {
  try {
    const response: AxiosResponse<BackgroundImage> = await api.get(
      API_ROUTES.background
    );
    const data = handleResponse<BackgroundImage>(response);
    if (data && data.url) {
      return data.url;
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

export const fetchAstroImages = async (
  params: FilterParams = {}
): Promise<AstroImage[]> => {
  const response: AxiosResponse<AstroImage[]> = await api.get(
    API_ROUTES.astroImages,
    { params }
  );
  const data = handleResponse<AstroImage[]>(response);
  if (Array.isArray(data)) {
    return data.map(image => ({
      ...image,
      url: getMediaUrl(image.url) || '',
      thumbnail_url: getMediaUrl(image.thumbnail_url) || undefined,
    }));
  }
  return data;
};

export const fetchAstroImage = async (
  id: number | string
): Promise<AstroImage> => {
  if (!id) throw new Error('id is required');

  const url = API_ROUTES.astroImage.replace(':id', String(id));
  const response: AxiosResponse<AstroImage> = await api.get(url);
  const image = handleResponse<AstroImage>(response);
  if (image) {
    return {
      ...image,
      url: getMediaUrl(image.url) || '',
      thumbnail_url: getMediaUrl(image.thumbnail_url) || undefined,
    };
  }
  return image;
};

export const fetchContact = async (
  contactData: ContactFormData
): Promise<void> => {
  if (!contactData) throw new Error('contactData is required');

  const response: AxiosResponse<void> = await api.post(
    API_ROUTES.contact,
    contactData
  );
  return handleResponse<void>(response);
};

export const fetchTags = async (category_filter?: string): Promise<Tag[]> => {
  const params: { filter?: string } = {};
  if (category_filter) {
    params.filter = category_filter;
  }
  const response: AxiosResponse<Tag[]> = await api.get(API_ROUTES.tags, {
    params,
  });
  return handleResponse<Tag[]>(response);
};

export const fetchEnabledFeatures = async (): Promise<EnabledFeatures> => {
  try {
    const response: AxiosResponse<EnabledFeatures> = await api.get(
      API_ROUTES.whatsEnabled
    );
    return handleResponse<EnabledFeatures>(response);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {
    console.error('Error fetching enabled features:', error);
    // Return empty object on error - safer than crashing
    return {};
  }
};
export const fetchProjects = async (): Promise<Project[]> => {
  const response: AxiosResponse<Project[]> = await api.get(API_ROUTES.projects);
  const data = handleResponse<Project[]>(response);
  if (Array.isArray(data)) {
    return data.map(project => ({
      ...project,
      images: project.images.map(image => ({
        ...image,
        url: getMediaUrl(image.url) || '',
        thumbnail_url: getMediaUrl(image.thumbnail_url) || undefined,
      })),
    }));
  }
  return data;
};

export const fetchTravelHighlights = async (): Promise<MainPageLocation[]> => {
  const response: AxiosResponse<MainPageLocation[]> = await api.get(
    API_ROUTES.travelHighlights
  );
  const data = handleResponse<MainPageLocation[]>(response);

  if (Array.isArray(data)) {
    return data.map(slider => ({
      ...slider,
      images: slider.images.map(image => ({
        ...image,
        url: getMediaUrl(image.url) || '',
        thumbnail_url: getMediaUrl(image.thumbnail_url) || undefined,
      })),
    }));
  }
  return [];
};
