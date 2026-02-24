import { Link } from "react-router-dom";
import { ArrowRight, TrendingUp, Car, Cpu, Factory, Zap } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { PriceChart } from "@/components/shared/PriceChart";
import { Button } from "@/components/ui/button";
import { useMetalPageData } from "@/components/metals/useMetalPageData";

const FALLBACK_ARTICLES = [
  { title: "Palladium Supply Crisis: Russia's Market Impact", excerpt: "How geopolitical factors affect palladium supply and pricing.", category: "Market Analysis", author: "Staff", date: "Dec 9, 2024", readTime: "7 min read", image: "https://images.unsplash.com/photo-1624365168968-f283d506c6b6?w=800&q=80", href: "/market-insights" },
  { title: "Palladium vs Platinum: Catalytic Converter Battle", excerpt: "How automakers choose between palladium and platinum.", category: "Industry", author: "Staff", date: "Dec 8, 2024", readTime: "5 min read", image: "https://images.unsplash.com/photo-1579532536935-619928decd08?w=800&q=80", href: "/market-insights" },
  { title: "Investing in Palladium: Complete Guide", excerpt: "Everything you need to know about palladium investment.", category: "Investment Guide", author: "Staff", date: "Dec 7, 2024", readTime: "6 min read", image: "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80", href: "/market-insights" },
];

const useCases = [
  { name: "Catalytic Converters", percentage: 85, icon: Car, description: "Gasoline vehicle emissions" },
  { name: "Electronics", percentage: 8, icon: Cpu, description: "Capacitors, connectors" },
  { name: "Chemical", percentage: 4, icon: Factory, description: "Catalysts, refining" },
  { name: "Jewelry/Dental", percentage: 3, icon: Zap, description: "White gold alloy" },
];

export default function Palladium() {
  const { articles: graphqlArticles } = useMetalPageData("palladium");
  const articles = graphqlArticles.length > 0 ? graphqlArticles : FALLBACK_ARTICLES;

  return (
    <PageLayout>
      <PageHero
        title="Palladium Investment Guide"
        subtitle="The automotive industry's essential metal. Discover palladium market dynamics, supply chain insights, and investment opportunities."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Precious Metals", href: "/precious-metals" },
          { label: "Palladium" },
        ]}
        badge="Automotive Essential"
      >
        <div className="flex items-center gap-6 mt-6">
          <div className="flex items-center gap-2">
            <span className="text-3xl font-display font-bold text-silver-light">$1,024.80</span>
            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-success/20 text-success text-sm font-medium">
              <TrendingUp className="h-4 w-4" />
              +0.65%
            </span>
          </div>
          <div className="text-silver text-sm">
            <span className="block">Primary source: Russia, S. Africa</span>
            <span className="block">Automotive demand: Strong</span>
          </div>
        </div>
      </PageHero>

      {/* Price Chart */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <PriceChart metal="palladium" />
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Palladium Demand by Sector</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {useCases.map((useCase) => (
              <div key={useCase.name} className="bg-card rounded-xl border border-border p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="inline-flex p-3 rounded-lg bg-accent/10">
                    <useCase.icon className="h-6 w-6 text-accent" />
                  </div>
                  <span className="text-2xl font-display font-bold text-accent">{useCase.percentage}%</span>
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-1">{useCase.name}</h3>
                <p className="text-sm text-muted-foreground">{useCase.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Articles */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-2xl font-bold text-foreground">Palladium Insights</h2>
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
          <h2 className="font-display text-2xl font-bold text-silver-light mb-8 text-center">Palladium Key Facts</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { label: "Symbol", value: "Pd (XPD)" },
              { label: "Standard Purity", value: "99.95% (999.5)" },
              { label: "Density", value: "12.02 g/cm³" },
              { label: "Annual Production", value: "~210 tonnes" },
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
