// frontend/src/api/imageUrlService.ts
import { API_BASE_URL } from './routes';
import { API_V1 } from './constants';

export async function fetchImageUrls(
  ids?: number[]
): Promise<Record<string, string>> {
  let url = `${API_BASE_URL}${API_V1}/images/`;
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
  const response = await fetch(`${API_BASE_URL}${API_V1}/images/${slug}/`);
  if (!response.ok) {
    throw new Error(`Failed to fetch URL for ${slug}`);
  }
  const data = await response.json();
  return data.url;
}
