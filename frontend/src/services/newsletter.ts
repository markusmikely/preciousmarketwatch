/**
 * Newsletter subscribe — single shared endpoint for menu, footer, and article sign-up.
 * POST https://preciousmarketwatch.com/wp/wp-json/pmw/v1/subscribe
 */
import { getWordPressRestBaseUrl } from "@/lib/wordPressRestUrl";

const API_BASE = getWordPressRestBaseUrl();

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

  if (res.ok) {
    return { success: true, message: data?.message || "Subscribed!" };
  }

  // User-friendly messages; do not expose technical detail
  let message: string;
  if (res.status === 403) {
    message = "Unable to subscribe. Please try again later.";
  } else if (res.status >= 500) {
    message = "Something went wrong. Please try again later.";
  } else if (res.status === 400 && data?.message) {
    message = data.message;
  } else {
    message = "Something went wrong. Please try again.";
  }

  return {
    success: false,
    message,
    error_code: data?.error_code,
  };
}
