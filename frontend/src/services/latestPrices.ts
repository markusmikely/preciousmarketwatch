/**
 * Fetch latest price per metal from WordPress backend (metal_prices table).
 * GET /wp-json/pmw/v1/prices/latest
 */
const API_BASE =
  (import.meta.env.VITE_WORDPRESS_API_URL || "http://localhost:8888/wp")
    .replace(/\/graphql\/?$/, "")
    .replace(/\/$/, "") + "/wp-json";

export interface LatestPrice {
  date: string;
  price_usd: number | null;
  price_gbp: number | null;
}

export type LatestPricesByMetal = {
  gold: LatestPrice | null;
  silver: LatestPrice | null;
  platinum: LatestPrice | null;
  palladium: LatestPrice | null;
};

export async function fetchLatestPrices(): Promise<LatestPricesByMetal> {
  const res = await fetch(`${API_BASE}/pmw/v1/prices/latest`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return {
    gold: data.gold ?? null,
    silver: data.silver ?? null,
    platinum: data.platinum ?? null,
    palladium: data.palladium ?? null,
  };
}
