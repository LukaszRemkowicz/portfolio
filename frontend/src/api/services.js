import { API_ROUTES, API_BASE_URL, getMediaUrl } from './routes';
import { api } from './api';

const handleResponse = (response) => {
    if (response && response.data) {
        // The API returns an array for lists and an object for single items.
        // Both are valid and should be returned.
        return response.data;
    }
    // Handle cases where response or response.data is undefined
    console.error("Invalid response structure:", response);
    throw new Error("Invalid response from server.");
};

export const fetchProfile = async () => {
    const response = await api.get(API_ROUTES.profile);
    const data = handleResponse(response);
    
    // Transform relative media paths to full URLs
    if (data) {
        return {
            ...data,
            avatar: data.avatar ? getMediaUrl(data.avatar) : null,
            about_me_image: data.about_me_image ? getMediaUrl(data.about_me_image) : null,
            about_me_image2: data.about_me_image2 ? getMediaUrl(data.about_me_image2) : null,
        };
    }
    return data;
};

export const fetchBackground = async () => {
    const response = await api.get(API_ROUTES.background);
    const data = handleResponse(response);
    if (data && data.url) {
        return data.url;
    }
    return null;
};

export const fetchAstroImages = async (params = {}) => {
    const response = await api.get(API_ROUTES.astroImages, { params });
    return handleResponse(response);
}; 