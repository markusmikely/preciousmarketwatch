/**
 * Newsletter subscribe — single shared endpoint for menu, footer, and article sign-up.
 * POST /wp-json/pmw/v1/subscribe
 */
const API_BASE =
  (import.meta.env.VITE_WORDPRESS_API_URL || "http://localhost:8888/wp")
    .replace(/\/graphql\/?$/, "")
    .replace(/\/$/, "") + "/wp-json";

export interface SubscribeResult {
  success: boolean;
  message: string;
  error_code?: number;
}

export async function subscribeNewsletter(
  email: string,
  tags?: string[]
): Promise<SubscribeResult> {
  const url = `${API_BASE}/pmw/v1/subscribe`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email.trim(), ...(tags?.length ? { tags } : {}) }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    return {
      success: false,
      message: data?.message || "Something went wrong. Please try again.",
      error_code: data?.error_code,
    };
  }
  return { success: true, message: data?.message || "Subscribed!" };
}
