/**
 * Fetch agent profiles from REST API.
 * GET /wp-json/pmw/v1/agents
 */
import { getWordPressRestBaseUrl } from "@/lib/wordPressRestUrl";

export interface Agent {
  id: number;
  slug: string;
  display_name: string;
  title: string;
  role: string;
  tier: string;
  model_family: string;
  bio: string;
  personality: string;
  quirks: string[];
  specialisms: string[];
  status: string;
  eta: string | null;
  display_order: number;
  avatar_image_url: string | null;
  avatar_video_url: string | null;
  avatar_image_prompt: string;
  avatar_video_prompt: string;
}

export async function fetchAgents(status = "active"): Promise<Agent[]> {
  const base = getWordPressRestBaseUrl();
  const url = status === "all"
    ? `${base}/pmw/v1/agents?status=all`
    : `${base}/pmw/v1/agents?status=${status}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}
