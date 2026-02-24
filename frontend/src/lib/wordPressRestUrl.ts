/**
 * WordPress REST API base URL for pmw/v1 endpoints.
 * Must resolve to https://preciousmarketwatch.com/wp/wp-json in production
 * (WordPress is under /wp/ subdirectory).
 *
 * Prefer VITE_WORDPRESS_REST_URL when set; otherwise derive from GraphQL URL.
 */
export function getWordPressRestBaseUrl(): string {
  const restUrl = import.meta.env.VITE_WORDPRESS_REST_URL;
  if (restUrl && typeof restUrl === "string") {
    return restUrl.replace(/\/$/, "");
  }
  const graphqlUrl =
    import.meta.env.VITE_WORDPRESS_API_URL || "http://localhost:8888/wp/graphql";
  try {
    const url = new URL(graphqlUrl);
    const path = url.pathname.replace(/\/graphql\/?$/, "") || "/wp";
    return `${url.origin}${path}/wp-json`;
  } catch {
    return "http://localhost:8888/wp/wp-json";
  }
}
