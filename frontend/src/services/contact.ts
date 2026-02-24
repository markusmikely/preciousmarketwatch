/**
 * Contact form submit — POST /wp-json/pmw/v1/contact/submit
 */
const API_BASE =
  (import.meta.env.VITE_WORDPRESS_API_URL || "http://localhost:8888/wp")
    .replace(/\/graphql\/?$/, "")
    .replace(/\/$/, "") + "/wp-json";

export interface ContactSubmitPayload {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export interface ContactSubmitResult {
  success: boolean;
  message: string;
  errors?: Record<string, string>;
}

export async function submitContactForm(
  payload: ContactSubmitPayload
): Promise<ContactSubmitResult> {
  const res = await fetch(`${API_BASE}/pmw/v1/contact/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: payload.name.trim(),
      email: payload.email.trim(),
      subject: payload.subject.trim(),
      message: payload.message.trim(),
    }),
  });
  const data = await res.json().catch(() => ({}));

  if (res.ok) {
    return { success: true, message: data?.message || "Your message has been sent." };
  }

  return {
    success: false,
    message: data?.message || "Something went wrong. Please try again.",
    errors: data?.errors || undefined,
  };
}
