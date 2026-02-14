import { TrendingUp, TrendingDown } from "lucide-react";

interface PriceCardProps {
  name: string;
  symbol: string;
  price: string;
  change: string;
  changePercent: string;
  isUp: boolean;
  high24h?: string;
  low24h?: string;
  volume?: string;
}

export function PriceCard({
  name,
  symbol,
  price,
  change,
  changePercent,
  isUp,
  high24h,
  low24h,
  volume,
}: PriceCardProps) {
  return (
    <div className="bg-card rounded-xl border border-border p-6 hover:border-primary/50 hover:shadow-lg transition-all duration-300">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-display text-lg font-semibold text-foreground">{name}</h3>
          <span className="text-sm text-muted-foreground">{symbol}</span>
        </div>
        <div
          className={`flex items-center gap-1 px-2 py-1 rounded-full text-sm font-medium ${
            isUp ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive"
          }`}
        >
          {isUp ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
          {changePercent}
        </div>
      </div>

      <div className="mb-4">
        <span className="font-display text-3xl font-bold text-foreground">{price}</span>
        <span className={`ml-2 text-sm ${isUp ? "text-success" : "text-destructive"}`}>
          {isUp ? "+" : ""}
          {change}
        </span>
      </div>

      {(high24h || low24h || volume) && (
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border">
          {high24h && (
            <div>
              <span className="text-xs text-muted-foreground block">24h High</span>
              <span className="text-sm font-medium text-foreground">{high24h}</span>
            </div>
          )}
          {low24h && (
            <div>
              <span className="text-xs text-muted-foreground block">24h Low</span>
              <span className="text-sm font-medium text-foreground">{low24h}</span>
            </div>
          )}
          {volume && (
            <div>
              <span className="text-xs text-muted-foreground block">Volume</span>
              <span className="text-sm font-medium text-foreground">{volume}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
