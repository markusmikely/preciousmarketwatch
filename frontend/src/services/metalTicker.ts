/**
 * Fetch metal prices ticker from backend (metal_prices seed).
 * Uses GraphQL metalPricesTicker; falls back to REST /prices/ticker.
 * Same data source as hero prices and charts.
 */
import { client } from "@/lib/graphql";
import { METAL_PRICES_TICKER_QUERY } from "@/queries/metalTicker";
import { getWordPressRestBaseUrl } from "@/lib/wordPressRestUrl";

export type MetalTickerItem = {
  metal: string;
  name: string;
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  isUp: boolean;
  high: number;
  low: number;
  date?: string | null;
};

function mapFromRest(row: {
  metal?: string;
  name?: string;
  symbol?: string;
  price?: number;
  change?: number;
  change_percent?: number;
  isUp?: boolean;
  high?: number;
  low?: number;
  date?: string | null;
}): MetalTickerItem {
  return {
    metal: row.metal ?? "",
    name: row.name ?? "",
    symbol: row.symbol ?? "",
    price: Number(row.price ?? 0),
    change: Number(row.change ?? 0),
    change_percent: Number(row.change_percent ?? 0),
    isUp: Boolean(row.isUp),
    high: Number(row.high ?? 0),
    low: Number(row.low ?? 0),
    date: row.date ?? null,
  };
}

export async function fetchMetalTicker(): Promise<MetalTickerItem[]> {
  try {
    const data = await client.request<{ metalPricesTicker: Array<{
      metal: string;
      name: string;
      symbol: string;
      price: number;
      change: number;
      changePercent: number;
      isUp: boolean;
      high: number;
      low: number;
      date: string | null;
    }> }>(METAL_PRICES_TICKER_QUERY);
    const ticker = data?.metalPricesTicker ?? [];
    return ticker.map((row) => mapFromRest({
      ...row,
      change_percent: row.changePercent,
    }));
  } catch (err) {
    // Fallback to REST
    const restBase = getWordPressRestBaseUrl();
    const res = await fetch(`${restBase}/pmw/v1/prices/ticker`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const rows = await res.json();
    if (!Array.isArray(rows)) return [];
    return rows.map(mapFromRest);
  }
}
