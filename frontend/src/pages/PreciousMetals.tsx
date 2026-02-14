import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BarChart3, Coins, TrendingUp, Shield } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { PriceCard } from "@/components/shared/PriceCard";
import { Button } from "@/components/ui/button";

const metalCategories = [
  {
    name: "Gold",
    href: "/precious-metals/gold",
    icon: Coins,
    description: "The ultimate safe-haven asset for wealth preservation",
    color: "bg-primary/10 text-primary",
  },
  {
    name: "Silver",
    href: "/precious-metals/silver",
    icon: Coins,
    description: "Industrial demand meets investment opportunity",
    color: "bg-silver/20 text-silver-dark",
  },
  {
    name: "Platinum",
    href: "/precious-metals/platinum",
    icon: Shield,
    description: "Rare metal with automotive and industrial applications",
    color: "bg-muted text-muted-foreground",
  },
  {
    name: "Palladium",
    href: "/precious-metals/palladium",
    icon: BarChart3,
    description: "Essential for catalytic converters and electronics",
    color: "bg-accent/10 text-accent",
  },
];

const priceData = [
  { name: "Gold", symbol: "XAU/USD", price: "$2,634.20", change: "+12.50", changePercent: "+0.48%", isUp: true, high24h: "$2,641.80", low24h: "$2,618.30", volume: "182.5K" },
  { name: "Silver", symbol: "XAG/USD", price: "$31.24", change: "+0.35", changePercent: "+1.13%", isUp: true, high24h: "$31.45", low24h: "$30.82", volume: "98.2K" },
  { name: "Platinum", symbol: "XPT/USD", price: "$978.50", change: "-2.80", changePercent: "-0.29%", isUp: false, high24h: "$985.20", low24h: "$972.10", volume: "45.8K" },
  { name: "Palladium", symbol: "XPD/USD", price: "$1,024.80", change: "+6.60", changePercent: "+0.65%", isUp: true, high24h: "$1,032.40", low24h: "$1,012.50", volume: "28.3K" },
];

const articles = [
  {
    title: "Gold Reaches New Highs as Inflation Concerns Persist",
    excerpt: "Central bank policies continue to drive investor interest in gold as a hedge against currency devaluation and economic uncertainty.",
    category: "Gold",
    author: "Michael Chen",
    date: "Dec 9, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80",
    href: "/articles/gold-new-highs-inflation",
  },
  {
    title: "Silver Industrial Demand Surges on Green Energy Push",
    excerpt: "Solar panel production and electric vehicle manufacturing drive unprecedented demand for silver in industrial applications.",
    category: "Silver",
    author: "Sarah Williams",
    date: "Dec 8, 2024",
    readTime: "4 min read",
    image: "https://images.unsplash.com/photo-1589656966895-2f33e7653819?w=800&q=80",
    href: "/articles/silver-industrial-demand",
  },
  {
    title: "Platinum Market Analysis: Supply Constraints Continue",
    excerpt: "Mining disruptions in South Africa create supply deficit, potentially supporting platinum prices through 2025.",
    category: "Platinum",
    author: "David Park",
    date: "Dec 7, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1624365168968-f283d506c6b6?w=800&q=80",
    href: "/articles/platinum-supply-constraints",
  },
  {
    title: "Beginner's Guide to Precious Metals Investment",
    excerpt: "Everything you need to know about building a diversified precious metals portfolio for long-term wealth preservation.",
    category: "Guide",
    author: "Jennifer Adams",
    date: "Dec 6, 2024",
    readTime: "8 min read",
    image: "https://images.unsplash.com/photo-1579532536935-619928decd08?w=800&q=80",
    href: "/articles/beginners-guide-precious-metals",
  },
];

export default function PreciousMetals() {
  return (
    <PageLayout>
      <PageHero
        title="Precious Metals"
        subtitle="Comprehensive market analysis, investment guides, and real-time pricing for gold, silver, platinum, and palladium."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Precious Metals" },
        ]}
        badge="Investment Hub"
      />

      {/* Live Prices Section */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="font-display text-2xl font-bold text-foreground">Live Spot Prices</h2>
              <p className="text-muted-foreground mt-1">Real-time precious metals market data</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
              Live data
            </div>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {priceData.map((metal) => (
              <PriceCard key={metal.symbol} {...metal} />
            ))}
          </div>
        </div>
      </section>

      {/* Metal Categories */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Explore by Metal</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {metalCategories.map((category) => (
              <Link
                key={category.name}
                to={category.href}
                className="group bg-card rounded-xl border border-border p-6 hover:border-primary/50 hover:shadow-lg transition-all duration-300"
              >
                <div className={`inline-flex p-3 rounded-lg ${category.color} mb-4`}>
                  <category.icon className="h-6 w-6" />
                </div>
                <h3 className="font-display text-xl font-semibold text-foreground mb-2 group-hover:text-primary transition-colors">
                  {category.name}
                </h3>
                <p className="text-sm text-muted-foreground mb-4">{category.description}</p>
                <span className="inline-flex items-center text-sm font-medium text-primary">
                  Learn more
                  <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-1" />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Latest Articles */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-2xl font-bold text-foreground">Latest Analysis</h2>
            <Button variant="outline" asChild>
              <Link to="/market-insights">
                View all articles
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {articles.map((article) => (
              <ArticleCard key={article.title} {...article} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-hero">
        <div className="container mx-auto px-4 lg:px-8 text-center">
          <h2 className="font-display text-3xl font-bold text-silver-light mb-4">
            Start Investing in Precious Metals
          </h2>
          <p className="text-silver max-w-2xl mx-auto mb-8">
            Connect with trusted dealers, access expert analysis, and build your precious metals portfolio with confidence.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold">
              Find Trusted Dealers
            </Button>
            <Button size="lg" variant="outline" className="border-silver/30 text-silver-light hover:bg-silver/10">
              Investment Guides
            </Button>
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
