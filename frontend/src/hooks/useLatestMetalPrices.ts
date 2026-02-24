import { useState, useEffect } from "react";
import { fetchLatestPrices, type LatestPricesByMetal } from "@/services/latestPrices";

export type Currency = "usd" | "gbp";

export function useLatestMetalPrices() {
  const [latest, setLatest] = useState<LatestPricesByMetal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchLatestPrices()
      .then((data) => {
        if (!cancelled) setLatest(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err?.message ?? "Failed to load prices");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  return { latest, loading, error };
}

export function formatMetalPrice(
  priceUsd: number | null,
  priceGbp: number | null,
  currency: Currency
): string {
  const value = currency === "gbp" ? priceGbp : priceUsd;
  if (value == null || value <= 0) return "—";
  const symbol = currency === "gbp" ? "£" : "$";
  return `${symbol}${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
