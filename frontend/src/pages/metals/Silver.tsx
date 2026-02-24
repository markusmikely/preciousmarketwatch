import { Link } from "react-router-dom";
import { ArrowRight, Zap, Factory, Coins, Sun } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { PriceChart } from "@/components/shared/PriceChart";
import { Button } from "@/components/ui/button";
import { useMetalPageData } from "@/components/metals/useMetalPageData";
import { MetalHeroPrice } from "@/components/metals/MetalHeroPrice";
import { useLatestMetalPrices } from "@/hooks/useLatestMetalPrices";
import { useState } from "react";
import type { Currency } from "@/hooks/useLatestMetalPrices";

const FALLBACK_ARTICLES = [
  { title: "Silver's Role in the Green Energy Revolution", excerpt: "How solar panel demand and EV production reshape the silver market.", category: "Market Analysis", author: "Staff", date: "Dec 9, 2024", readTime: "6 min read", image: "https://images.unsplash.com/photo-1589656966895-2f33e7653819?w=800&q=80", href: "/market-insights" },
  { title: "Silver Coins for Investment", excerpt: "Discover the best silver coins for your portfolio.", category: "Buying Guide", author: "Staff", date: "Dec 8, 2024", readTime: "5 min read", image: "https://images.unsplash.com/photo-1607292803062-5b3f3d3e5e3a?w=800&q=80", href: "/market-insights" },
  { title: "Gold-to-Silver Ratio", excerpt: "Trading strategies using the gold-silver ratio.", category: "Strategy", author: "Staff", date: "Dec 7, 2024", readTime: "7 min read", image: "https://images.unsplash.com/photo-1624365168968-f283d506c6b6?w=800&q=80", href: "/market-insights" },
];

const demandSectors = [
  { name: "Industrial", percentage: 50, icon: Factory, description: "Electronics, solar, medical" },
  { name: "Investment", percentage: 25, icon: Coins, description: "Bars, coins, ETFs" },
  { name: "Jewelry", percentage: 18, icon: Zap, description: "Silverware, jewelry" },
  { name: "Photography", percentage: 7, icon: Sun, description: "Film and imaging" },
];

export default function Silver() {
  const [currency, setCurrency] = useState<Currency>("usd");
  const { articles: graphqlArticles } = useMetalPageData("silver");
  const { latest, loading: priceLoading } = useLatestMetalPrices();
  const articles = graphqlArticles.length > 0 ? graphqlArticles : FALLBACK_ARTICLES;

  return (
    <PageLayout>
      <PageHero
        title="Silver Investment Guide"
        subtitle="The dual-nature precious metal with both investment appeal and industrial demand. Explore silver market analysis, buying guides, and dealer reviews."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Precious Metals", href: "/precious-metals" },
          { label: "Silver" },
        ]}
        badge="Industrial & Investment"
      >
        <MetalHeroPrice
          metal="silver"
          currency={currency}
          onCurrencyChange={setCurrency}
          latest={latest?.silver ?? null}
          loading={priceLoading}
          secondaryLine={<span className="block">Per troy ounce</span>}
        />
      </PageHero>

      {/* Price Chart */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <PriceChart metal="silver" currency={currency} onCurrencyChange={setCurrency} />
        </div>
      </section>

      {/* Demand Breakdown */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Silver Demand by Sector</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {demandSectors.map((sector) => (
              <div key={sector.name} className="bg-card rounded-xl border border-border p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="inline-flex p-3 rounded-lg bg-secondary/20">
                    <sector.icon className="h-6 w-6 text-foreground" />
                  </div>
                  <span className="text-2xl font-display font-bold text-primary">{sector.percentage}%</span>
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-1">{sector.name}</h3>
                <p className="text-sm text-muted-foreground">{sector.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Articles */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-2xl font-bold text-foreground">Silver Investment Guides</h2>
            <Button variant="outline" asChild>
              <Link to="/market-insights">
                All articles
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {articles.slice(0, 6).map((article) => (
              <ArticleCard key={article.title} {...article} />
            ))}
          </div>
        </div>
      </section>

      {/* Key Facts */}
      <section className="py-12 bg-gradient-hero">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-silver-light mb-8 text-center">Silver Key Facts</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { label: "Symbol", value: "Ag (XAG)" },
              { label: "Standard Purity", value: "99.9% (.999)" },
              { label: "Troy Ounce", value: "31.1035 grams" },
              { label: "Annual Production", value: "~25,000 tonnes" },
            ].map((fact) => (
              <div key={fact.label} className="text-center">
                <span className="block text-silver text-sm mb-1">{fact.label}</span>
                <span className="font-display text-xl font-bold text-silver-light">{fact.value}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
