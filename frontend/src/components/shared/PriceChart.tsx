import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getWordPressRestBaseUrl } from "@/lib/wordPressRestUrl";

const API_BASE = getWordPressRestBaseUrl();

type Metal = "gold" | "silver" | "platinum" | "palladium";
type Range = "1M" | "3M" | "6M" | "1Y" | "5Y" | "all";
type Currency = "usd" | "gbp";

interface DataPoint {
  date: string;
  price: number;
}

interface PriceChartProps {
  metal: Metal;
  color?: string;
  gradientId?: string;
  title?: string;
  /** When set, chart currency is controlled by parent (e.g. metal page currency toggle). */
  currency?: Currency;
  onCurrencyChange?: (c: Currency) => void;
}

const RANGES: Range[] = ["1M", "3M", "6M", "1Y", "5Y", "all"];
const METAL_COLORS: Record<Metal, string> = {
  gold: "hsl(43, 74%, 49%)",
  silver: "hsl(220, 10%, 60%)",
  platinum: "hsl(173, 58%, 39%)",
  palladium: "hsl(25, 95%, 53%)",
};

function formatDateLabel(dateStr: string, range: Range): string {
  const d = new Date(dateStr);
  if (range === "1M" || range === "3M") return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  if (range === "6M" || range === "1Y") return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
  return d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

export function PriceChart({
  metal,
  color = METAL_COLORS[metal],
  gradientId = `priceChartGradient-${metal}`,
  title,
  currency: controlledCurrency,
  onCurrencyChange,
}: PriceChartProps) {
  const [internalCurrency, setInternalCurrency] = useState<Currency>("usd");
  const currency = controlledCurrency ?? internalCurrency;
  const setCurrency = onCurrencyChange ?? setInternalCurrency;

  const [range, setRange] = useState<Range>("1Y");
  const [data, setData] = useState<DataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const url = `${API_BASE}/pmw/v1/prices/history?metal=${metal}&range=${range}&currency=${currency}`;
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((res) => {
        const arr = Array.isArray(res.data) ? res.data : [];
        setData(arr.map((p: { date: string; price: number }) => ({ date: p.date, price: p.price })));
      })
      .catch((err) => setError(err?.message || "Failed to load data"))
      .finally(() => setLoading(false));
  }, [metal, range, currency]);

  const symbol = currency === "gbp" ? "£" : "$";
  const currencyLabel = currency === "gbp" ? "GBP" : "USD";

  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h2 className="font-display text-xl font-bold text-foreground">
            {title ?? `${metal.charAt(0).toUpperCase() + metal.slice(1)} Price History`}
          </h2>
          <p className="text-muted-foreground text-sm">
            {currencyLabel} per troy ounce
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {RANGES.map((r) => (
            <Button
              key={r}
              variant={range === r ? "default" : "outline"}
              size="sm"
              onClick={() => setRange(r)}
              className="min-w-[3rem]"
            >
              {r}
            </Button>
          ))}
          <div className="flex border-l pl-2 ml-1">
            <Button
              variant={currency === "usd" ? "default" : "outline"}
              size="sm"
              onClick={() => setCurrency("usd")}
            >
              USD
            </Button>
            <Button
              variant={currency === "gbp" ? "default" : "outline"}
              size="sm"
              onClick={() => setCurrency("gbp")}
            >
              GBP
            </Button>
          </div>
        </div>
      </div>

      <div className="h-[400px] w-full">
        {loading ? (
          <Skeleton className="h-full w-full rounded" />
        ) : error ? (
          <div className="flex h-full items-center justify-center text-destructive">
            <p>{error}</p>
          </div>
        ) : data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            <p>No data available</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
              <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 87%)" />
              <XAxis
                dataKey="date"
                stroke="hsl(220, 10%, 46%)"
                fontSize={12}
                tickFormatter={(v) => formatDateLabel(v, range)}
              />
              <YAxis
                stroke="hsl(220, 10%, 46%)"
                fontSize={12}
                domain={["dataMin - 50", "dataMax + 50"]}
                tickFormatter={(v) => `${symbol}${Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(0, 0%, 100%)",
                  border: "1px solid hsl(220, 13%, 87%)",
                  borderRadius: "8px",
                }}
                formatter={(value: number) => [`${symbol}${Number(value).toFixed(2)}`, "Price"]}
                labelFormatter={(label) => formatDateLabel(String(label), range)}
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke={color}
                fill={`url(#${gradientId})`}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      <p className="mt-4 text-xs text-muted-foreground">
        Gold historical data: FreeGoldAPI.com (CC) | Silver, Platinum, Palladium & live prices: Metals.dev
      </p>
    </div>
  );
}
