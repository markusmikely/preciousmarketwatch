import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatMetalPrice, type Currency } from "@/hooks/useLatestMetalPrices";
import type { LatestPrice } from "@/services/latestPrices";

type MetalSlug = "gold" | "silver" | "platinum" | "palladium";

interface MetalHeroPriceProps {
  metal: MetalSlug;
  currency: Currency;
  onCurrencyChange: (c: Currency) => void;
  latest: LatestPrice | null;
  loading: boolean;
  /** Optional extra line (e.g. "24h High/Low" or ratio). Not currency-dependent by default. */
  secondaryLine?: React.ReactNode;
}

export function MetalHeroPrice({
  metal,
  currency,
  onCurrencyChange,
  latest,
  loading,
  secondaryLine,
}: MetalHeroPriceProps) {
  const priceUsd = latest?.price_usd ?? null;
  const priceGbp = latest?.price_gbp ?? null;
  const displayPrice = formatMetalPrice(priceUsd, priceGbp, currency);
  const dateLabel = latest?.date
    ? new Date(latest.date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })
    : null;

  return (
    <div className="flex flex-wrap items-center gap-4 mt-6">
      <div className="flex items-center gap-3">
        {loading ? (
          <Skeleton className="h-10 w-40" />
        ) : (
          <span className="text-3xl font-display font-bold text-silver-light">{displayPrice}</span>
        )}
        <div className="flex border border-silver/30 rounded-lg p-0.5 bg-navy-light/50">
          <Button
            variant={currency === "usd" ? "default" : "ghost"}
            size="sm"
            className="rounded-md"
            onClick={() => onCurrencyChange("usd")}
          >
            USD
          </Button>
          <Button
            variant={currency === "gbp" ? "default" : "ghost"}
            size="sm"
            className="rounded-md"
            onClick={() => onCurrencyChange("gbp")}
          >
            GBP
          </Button>
        </div>
      </div>
      <div className="text-silver text-sm">
        {dateLabel && <span className="block">As of {dateLabel}</span>}
        {secondaryLine}
      </div>
    </div>
  );
}
