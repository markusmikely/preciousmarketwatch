import type { GemsApiResponse } from '@/types/gems';

/**
 * Derives the WordPress REST API base URL from the GraphQL URL.
 * e.g. https://www.preciousmarketwatch.com/wp/graphql -> https://www.preciousmarketwatch.com/wp/wp-json
 */
function getRestBaseUrl(): string {
  const restUrl = import.meta.env.VITE_WORDPRESS_REST_URL;
  if (restUrl) return restUrl.replace(/\/$/, '');

  const graphqlUrl = import.meta.env.VITE_WORDPRESS_API_URL || 'http://localhost:8888/wp/graphql';
  try {
    const url = new URL(graphqlUrl);
    const path = url.pathname.replace(/\/graphql\/?$/, '') || '/wp';
    return `${url.origin}${path}/wp-json`;
  } catch {
    return 'http://localhost:8888/wp-json';
  }
}

const GEMS_API_PATH = '/pmw/v1/gems';

export async function fetchGems(): Promise<GemsApiResponse> {
  const base = getRestBaseUrl();
  const res = await fetch(`${base}${GEMS_API_PATH}`);

  if (!res.ok) {
    throw new Error(`Gems API error: ${res.status} ${res.statusText}`);
  }

  const data = (await res.json()) as GemsApiResponse;
  return data;
}
