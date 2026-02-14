import { TrendingUp, TrendingDown, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useMarket } from "@/contexts/MarketContext";

// const metalPrices = [
//   { 
//     name: "Gold", 
//     symbol: "XAU/USD", 
//     price: 2634.20, 
//     change: 11.85, 
//     changePercent: 0.45, 
//     high: 2650.40, 
//     low: 2618.90 
//   },
//   { 
//     name: "Silver", 
//     symbol: "XAG/USD", 
//     price: 31.24, 
//     change: 0.35, 
//     changePercent: 1.12, 
//     high: 31.52, 
//     low: 30.78 
//   },
//   { 
//     name: "Platinum", 
//     symbol: "XPT/USD", 
//     price: 978.50, 
//     change: -2.75, 
//     changePercent: -0.28, 
//     high: 985.20, 
//     low: 972.30 
//   },
//   { 
//     name: "Palladium", 
//     symbol: "XPD/USD", 
//     price: 1024.80, 
//     change: 6.60, 
//     changePercent: 0.65, 
//     high: 1035.40, 
//     low: 1012.50 
//   },
// ];


const gemstoneIndices = [
  { name: "Diamond (1ct D-FL)", value: 14250, change: -0.8 },
  { name: "Ruby (1ct Pigeon Blood)", value: 18500, change: 2.3 },
  { name: "Sapphire (1ct Kashmir)", value: 12800, change: 1.1 },
  { name: "Emerald (1ct Colombian)", value: 9200, change: -0.4 },
];

export function MarketOverview() {

  const { marketData, loading, updateMarketData } = useMarket();
  console.log("marketData", marketData);
  return (
    <section className="py-16 lg:py-24 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        {/* Section Header */}
        <div className="flex items-center justify-between mb-10">
          <div>
            <h2 className="font-display text-3xl font-bold text-foreground lg:text-4xl">
              Market Overview
            </h2>
            <p className="mt-2 text-muted-foreground">
              Real-time precious metals and gemstone market data
            </p>
          </div>
          <span className="hidden sm:flex items-center gap-2 text-xs text-muted-foreground">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-success"></span>
            </span>
            Live Data
          </span>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Metal Prices Table */}
          <div className="lg:col-span-2">
            <Card className="border-border bg-card">
              <CardHeader className="border-b border-border pb-4">
                <CardTitle className="flex items-center gap-2 text-lg">
                  Precious Metals Spot Prices
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-4 w-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Prices updated every 60 seconds during market hours</p>
                    </TooltipContent>
                  </Tooltip>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border bg-muted/30 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        <th className="px-6 py-3">Metal</th>
                        <th className="px-6 py-3 text-right">Price (USD)</th>
                        <th className="px-6 py-3 text-right">Change</th>
                        <th className="hidden px-6 py-3 text-right sm:table-cell">High</th>
                        <th className="hidden px-6 py-3 text-right sm:table-cell">Low</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {marketData.map((metal) => (
                        <tr key={metal.symbol} className="hover:bg-muted/20 transition-colors">
                          <td className="px-6 py-4">
                            <div>
                              <div className="font-semibold text-card-foreground">{metal.name}</div>
                              <div className="text-xs text-muted-foreground">{metal.symbol}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-right font-semibold text-card-foreground">
                            ${metal.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <div className={`flex items-center justify-end gap-1 font-medium ${
                              metal.change >= 0 ? 'text-success' : 'text-destructive'
                            }`}>
                              {metal.change >= 0 ? (
                                <TrendingUp className="h-4 w-4" />
                              ) : (
                                <TrendingDown className="h-4 w-4" />
                              )}
                              <span>
                                {metal.change >= 0 ? '+' : ''}{metal.change_percent.toFixed(2)}%
                              </span>
                            </div>
                          </td>
                          <td className="hidden px-6 py-4 text-right text-muted-foreground sm:table-cell">
                            ${metal.high.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="hidden px-6 py-4 text-right text-muted-foreground sm:table-cell">
                            ${metal.low.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Gemstone Index */}
          <div>
            <Card className="border-border bg-card h-full">
              <CardHeader className="border-b border-border pb-4">
                <CardTitle className="flex items-center gap-2 text-lg">
                  Gemstone Index
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-4 w-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Average prices for top-quality specimens</p>
                    </TooltipContent>
                  </Tooltip>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-border">
                  {gemstoneIndices.map((gem) => (
                    <div key={gem.name} className="flex items-center justify-between px-6 py-4 hover:bg-muted/20 transition-colors">
                      <div>
                        <div className="font-medium text-card-foreground text-sm">{gem.name}</div>
                        <div className="text-lg font-semibold text-card-foreground">
                          ${gem.value.toLocaleString()}
                        </div>
                      </div>
                      <div className={`flex items-center gap-1 font-medium ${
                        gem.change >= 0 ? 'text-success' : 'text-destructive'
                      }`}>
                        {gem.change >= 0 ? (
                          <TrendingUp className="h-4 w-4" />
                        ) : (
                          <TrendingDown className="h-4 w-4" />
                        )}
                        <span>{gem.change >= 0 ? '+' : ''}{gem.change}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Disclaimer */}
        <p className="mt-6 text-xs text-muted-foreground text-center">
          Market data is for informational purposes only. Prices may vary by dealer. 
          Not investment advice. Always verify with multiple sources before making decisions.
        </p>
      </div>
    </section>
  );
}
