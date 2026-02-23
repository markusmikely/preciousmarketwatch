import { TrendingUp, TrendingDown } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchMetalData } from "../../services/metalService";
import { useMarket, MarketProvider } from "../../contexts/MarketContext";

const marketDataList = [
  { name: "Gold", symbol: "XAU", price: "$2,634.20", change: "+0.45%", isUp: true },
  { name: "Silver", symbol: "XAG", price: "$31.24", change: "+1.12%", isUp: true },
  { name: "Platinum", symbol: "XPT", price: "$978.50", change: "-0.28%", isUp: false },
  { name: "Palladium", symbol: "XPD", price: "$1,024.80", change: "+0.65%", isUp: true },
  { name: "Diamond Index", symbol: "DMD", price: "142.5", change: "-0.15%", isUp: false },
  { name: "Ruby Index", symbol: "RBY", price: "198.3", change: "+2.34%", isUp: true },
];

export function MarketTicker() {

  const { marketData, loading } = useMarket();

  // Guard against undefined/null data
  const displayData = Array.isArray(marketData) && marketData.length > 0 ? marketData : marketDataList;

  return (  
      <div className="bg-navy text-silver-light overflow-hidden border-b border-navy-light">
        <div className="flex animate-ticker">
          {/* Duplicate the content for seamless loop */}
          {[...displayData, ...displayData].map((item, index) => (
            <div
              key={`${item.symbol}-${index}`}
              className="flex items-center gap-4 px-6 py-2 border-r border-navy-light whitespace-nowrap"
            >
              <span className="font-medium text-silver-light">{item.name}</span>
              <span className="text-xs text-silver/60">{item.symbol}</span>
              <span className="font-semibold text-silver-light">
                {typeof item.price === 'number' ? `$${item.price.toFixed(2)}` : item.price}
              </span>
              <span
                className={`flex items-center gap-1 text-sm font-medium ${
                  item.isUp ? "text-success" : "text-destructive"
                }`}
              >
                {item.isUp ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                {typeof item.change_percent === 'number' 
                  ? `${item.change_percent.toFixed(2)}%`
                  : item.change_percent || '0%'
                }
              </span>
            </div>
          ))}
        </div>
      </div>
  );
}
