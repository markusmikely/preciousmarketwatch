/**
 * Fetch agent profiles from REST API.
 * GET /wp-json/pmw/v1/agents
 *
 * Normalized shape for both REST (snake_case) and GraphQL (camelCase) responses.
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

/** GraphQL agents from page section (camelCase) */
export interface GraphQLAgent {
  id: number;
  slug: string;
  displayName?: string;
  title?: string;
  role?: string;
  tier?: string;
  bio?: string;
  personality?: string;
  quirks?: string[] | null;
  specialisms?: string[] | null;
  status?: string;
  eta?: string | null;
  displayOrder?: number;
  avatarImageUrl?: string | null;
  avatarVideoUrl?: string | null;
}

/** Normalize GraphQL agent shape to Agent */
export function normalizeAgent(a: GraphQLAgent | Agent): Agent {
  if ("display_name" in a && a.display_name !== undefined) {
    return a as Agent;
  }
  const g = a as GraphQLAgent;
  return {
    id: g.id,
    slug: g.slug ?? "",
    display_name: g.displayName ?? "",
    title: g.title ?? "",
    role: g.role ?? "",
    tier: g.tier ?? "",
    model_family: "",
    bio: g.bio ?? "",
    personality: g.personality ?? "",
    quirks: Array.isArray(g.quirks) ? g.quirks : [],
    specialisms: Array.isArray(g.specialisms) ? g.specialisms : [],
    status: g.status ?? "active",
    eta: g.eta ?? null,
    display_order: g.displayOrder ?? 999,
    avatar_image_url: g.avatarImageUrl ?? null,
    avatar_video_url: g.avatarVideoUrl ?? null,
    avatar_image_prompt: "",
    avatar_video_prompt: "",
  };
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
