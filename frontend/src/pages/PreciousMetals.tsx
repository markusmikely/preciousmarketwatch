import { useMemo } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BarChart3, Coins, TrendingUp, Shield } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { PriceCard } from "@/components/shared/PriceCard";
import { DataFetchStateHandler } from "@/components/shared/DataFetchStateHandler";
import { Button } from "@/components/ui/button";
import { useGraphQL } from "@/hooks/useGraphQL";
import { ARTICLES_BY_CATEGORY } from "@/queries/articles";
import { useMarket } from "@/contexts/MarketContext";

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

interface WpArticle {
  id: string;
  title: string;
  slug: string;
  date: string;
  excerpt: string;
  featuredImage?: { node: { sourceUrl: string } };
  author?: { node: { name: string } };
  categories?: { nodes: { name: string }[] };
  articleMeta?: { readTime: string };
}

function transformArticle(article: WpArticle, index: number) {
  return {
    id: article.id || `article-${index}`,
    title: article.title,
    excerpt: article.excerpt,
    slug: article.slug,
    category: article.categories?.nodes[0]?.name || "Precious Metals",
    author: article.author?.node?.name || "Editorial Team",
    readTime: article.articleMeta?.readTime || "5 min read",
    date: new Date(article.date).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }),
    image: article.featuredImage?.node?.sourceUrl || "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80",
    href: `/articles/${article.slug}`,
  };
}

export default function PreciousMetals() {
  const { marketData } = useMarket();

  // Fetch articles about precious metals
  const { data, loading, error, refetch } = useGraphQL(ARTICLES_BY_CATEGORY, {
    variables: { categorySlug: "precious-metals", first: 4 },
  });

  const articles = useMemo(() => {
    try {
      if (data?.posts?.nodes && Array.isArray(data.posts.nodes) && data.posts.nodes.length > 0) {
        return data.posts.nodes.map((article: any, index: number) => transformArticle(article, index));
      }
    } catch (e) {
      console.warn("[PreciousMetals] Error transforming articles:", e);
    }
    return [];
  }, [data]);

  // Format market data for price cards
  const priceData = useMemo(() => {
    return marketData?.map((metal: any) => ({
      name: metal.name,
      symbol: metal.symbol,
      price: `$${metal.price?.toFixed(2) || "0.00"}`,
      change: `${(metal.change || 0).toFixed(2)}`,
      changePercent: `${(metal.change_percent || 0).toFixed(2)}%`,
      isUp: metal.isUp !== false,
      high24h: `$${(metal.high || 0).toFixed(2)}`,
      low24h: `$${(metal.low || 0).toFixed(2)}`,
      volume: "N/A",
    })) || [];
  }, [marketData]);

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
            {priceData.map((metal: any) => (
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
          <DataFetchStateHandler loading={loading} error={error} onRetry={refetch} loadingMessage="Loading articles..." hideError={true}>
            {articles.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {articles.map((article: any) => (
                  <ArticleCard key={article.id} {...article} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No articles found. Check back soon!</p>
              </div>
            )}
          </DataFetchStateHandler>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-hero">
        <div className="container mx-auto px-4 lg:px-8 text-center">
          <h2 className="font-display text-3xl font-bold text-silver-light mb-4">Start Investing in Precious Metals</h2>
          <p className="text-silver max-w-2xl mx-auto mb-8">
            Connect with trusted dealers, access expert analysis, and build your precious metals portfolio with confidence.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold" asChild>
              <Link to="/top-dealers">Find Trusted Dealers</Link>
            </Button>
            <Button size="lg" variant="outline" className="border-silver/30 text-silver-light hover:bg-silver/10" asChild>
              <Link to="/market-insights">Investment Guides</Link>
            </Button>
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
