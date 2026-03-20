// frontend/src/api/imageUrlService.ts
import { API_BASE_URL, BFF_ROUTES } from './routes';
import { API_V1 } from './constants';

export async function fetchImageUrls(
  ids?: string[]
): Promise<Record<string, string>> {
  const useFrontendBff = typeof window !== 'undefined';
  let url = useFrontendBff
    ? BFF_ROUTES.images
    : `${API_BASE_URL}${API_V1}/images/`;
  if (ids && ids.length > 0) {
    url += `?ids=${ids.join(',')}`;
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch image URLs');
  }
  return response.json();
}

export async function fetchSingleImageUrl(slug: string): Promise<string> {
  const useFrontendBff = typeof window !== 'undefined';
  const url = useFrontendBff
    ? `${BFF_ROUTES.images}${slug}/`
    : `${API_BASE_URL}${API_V1}/images/${slug}/`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch URL for ${slug}`);
  }
  const data = await response.json();
  return data.url;
}
