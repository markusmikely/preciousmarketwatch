import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp, TrendingDown, Minus, Calendar, Gem } from "lucide-react";
import { fetchGems } from "@/queries/gems";

const DISCLAIMER =
  "The PMW Gem Index is an independent editorial benchmark based on market research. Prices are indicative only and updated quarterly.";

function formatPrice(value: number): string {
  if (value == null || value <= 0 || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPriceGbp(value: number): string {
  if (value == null || value <= 0 || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(value: string): string {
  if (!value) return "—";
  try {
    const d = new Date(value);
    return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return value;
  }
}

function TrendBadge({ trend, percentage }: { trend: string; percentage: number }) {
  if (trend === "Rising") {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
        <TrendingUp className="h-3.5 w-3.5" />
        Rising {percentage > 0 ? `+${percentage}%` : ""}
      </span>
    );
  }
  if (trend === "Declining") {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
        <TrendingDown className="h-3.5 w-3.5" />
        Declining {percentage !== 0 ? `${percentage}%` : ""}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
      <Minus className="h-3.5 w-3.5" />
      Stable
    </span>
  );
}

interface GemIndexSectionProps {
  /** Gem name as stored in WordPress (e.g. "Ruby", "Diamond", "Blue Sapphire", "Emerald") */
  gemIndexName: string;
}

export function GemIndexSection({ gemIndexName }: GemIndexSectionProps) {
  const [currency, setCurrency] = useState<"USD" | "GBP">("USD");

  const { data, isLoading, error } = useQuery({
    queryKey: ["gems"],
    queryFn: fetchGems,
    staleTime: 1000 * 60 * 60 * 24, // 24 hours
  });

  if (isLoading || error || !data?.gems?.length) {
    return null;
  }

  const gem = data.gems.find(
    (g) => g.name.toLowerCase() === gemIndexName.toLowerCase()
  );

  if (!gem || gem.priceLowUsd <= 0) {
    return null;
  }

  const priceLow = currency === "USD" ? gem.priceLowUsd : gem.priceLowGbp;
  const priceHigh = currency === "USD" ? gem.priceHighUsd : gem.priceHighGbp;
  const formatFn = currency === "USD" ? formatPrice : formatPriceGbp;

  return (
    <section className="py-8 bg-muted/20">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="bg-white dark:bg-card rounded-xl border border-border shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-border bg-muted/30">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <Gem className="h-5 w-5 text-amber-600" />
                <h2 className="font-display text-lg font-semibold text-foreground">
                  PMW Gem Index — {gem.name}
                </h2>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Currency:</span>
                <div className="inline-flex rounded-lg border border-border bg-background p-0.5">
                  <button
                    type="button"
                    onClick={() => setCurrency("USD")}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                      currency === "USD"
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    USD
                  </button>
                  <button
                    type="button"
                    onClick={() => setCurrency("GBP")}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                      currency === "GBP"
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    GBP
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="p-6">
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                  Price range (per carat)
                </p>
                <p className="text-lg font-semibold text-foreground">
                  {formatFn(priceLow)} – {formatFn(priceHigh)}
                </p>
              </div>
              {gem.qualityGrade && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Quality grade
                  </p>
                  <p className="text-lg font-semibold text-foreground">{gem.qualityGrade}</p>
                </div>
              )}
              {gem.caratRange && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Carat range
                  </p>
                  <p className="text-lg font-semibold text-foreground">{gem.caratRange}</p>
                </div>
              )}
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">
                  Market trend
                </p>
                <TrendBadge trend={gem.trend} percentage={gem.trendPercentage} />
              </div>
            </div>

            {gem.lastReviewed && (
              <div className="flex items-center gap-2 mt-6 pt-6 border-t border-border">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  Last reviewed: {formatDate(gem.lastReviewed)}
                </span>
              </div>
            )}
          </div>

          <div className="px-6 py-4 bg-muted/30 border-t border-border">
            <p className="text-xs text-muted-foreground italic">{DISCLAIMER}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
