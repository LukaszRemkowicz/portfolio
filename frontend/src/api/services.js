import { API_ROUTES, API_BASE_URL, getMediaUrl } from './routes';

export const fetchProfile = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}${API_ROUTES.profile}`);
    if (!response.ok) {
      throw new Error('Failed to fetch profile');
    }
    const data = await response.json();
    
    // Transform the data to include full URLs for media
    return {
      ...data,
      avatar: data.avatar ? getMediaUrl(data.avatar) : null,
      about_me_image: data.about_me_image ? getMediaUrl(data.about_me_image) : null,
      about_me_image2: data.about_me_image2 ? getMediaUrl(data.about_me_image2) : null,
    };
  } catch (error) {
    console.error('Error fetching profile:', error);
    throw error;
  }
};

export const fetchBackground = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}${API_ROUTES.background}`);
    if (!response.ok) {
      throw new Error('Failed to fetch background');
    }
    const data = await response.json();
    // If the API returns a list, get the first item
    if (Array.isArray(data) && data.length > 0) {
      return data[0].url;
    }
    // If the API returns an object with a url field
    if (data.url) {
      return data.url;
    }
    return null;
  } catch (error) {
    console.error('Error fetching background:', error);
    return null;
  }
}; 