// frontend/src/api/imageUrlService.ts
import { API_BASE_URL, BFF_ROUTES } from './routes';
import { API_V1 } from './constants';
import { fetchBffJson } from './bff';

export async function fetchImageUrls(
  ids?: string[]
): Promise<Record<string, string>> {
  const useFrontendBff = typeof window !== 'undefined';
  const query = ids && ids.length > 0 ? `?ids=${ids.join(',')}` : '';

  if (useFrontendBff) {
    return fetchBffJson<Record<string, string>>(`${BFF_ROUTES.images}${query}`);
  }

  const response = await fetch(`${API_BASE_URL}${API_V1}/images/${query}`);
  if (!response.ok) {
    throw new Error('Failed to fetch image URLs');
  }
  return response.json();
}

export async function fetchSingleImageUrl(slug: string): Promise<string> {
  const useFrontendBff = typeof window !== 'undefined';
  if (useFrontendBff) {
    const data = await fetchBffJson<{ url: string }>(
      `${BFF_ROUTES.images}${slug}/`
    );
    return data.url;
  }

  const response = await fetch(`${API_BASE_URL}${API_V1}/images/${slug}/`);
  if (!response.ok) {
    throw new Error(`Failed to fetch URL for ${slug}`);
  }
  const data = await response.json();
  return data.url;
}
