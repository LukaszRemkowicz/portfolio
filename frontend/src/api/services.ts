import { AxiosResponse } from 'axios';
import { API_ROUTES, getMediaUrl } from './routes';
import { api } from './api';
import {
  UserProfile,
  BackgroundImage,
  AstroImage,
  ContactFormData,
  FilterParams,
} from '../types';

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
  } catch (error: unknown) {
    console.error('Error fetching profile:', error);
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
  } catch (error: unknown) {
    console.error('Error fetching background:', error);
    throw error;
  }
};

export const fetchAstroImages = async (
  params: FilterParams = {}
): Promise<AstroImage[]> => {
  try {
    const response: AxiosResponse<AstroImage[]> = await api.get(
      API_ROUTES.astroImages,
      { params }
    );
    return handleResponse<AstroImage[]>(response);
  } catch (error: unknown) {
    console.error('Error fetching astro images:', error);
    throw error;
  }
};

export const fetchAstroImage = async (
  id: number | string
): Promise<AstroImage> => {
  if (!id) throw new Error('id is required');

  try {
    const url = API_ROUTES.astroImage.replace(':id', String(id));
    const response: AxiosResponse<AstroImage> = await api.get(url);
    return handleResponse<AstroImage>(response);
  } catch (error: unknown) {
    console.error('Error fetching astro image:', error);
    throw error;
  }
};

export const fetchContact = async (
  contactData: ContactFormData
): Promise<void> => {
  if (!contactData) throw new Error('contactData is required');

  try {
    const response: AxiosResponse<void> = await api.post(
      API_ROUTES.contact,
      contactData
    );
    return handleResponse<void>(response);
  } catch (error: unknown) {
    console.error('Error sending contact form:', error);
    throw error;
  }
};
