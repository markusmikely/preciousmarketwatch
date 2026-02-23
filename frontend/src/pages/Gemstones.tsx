import { useMemo } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Diamond, Gem, Sparkles, Star } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { DataFetchStateHandler } from "@/components/shared/DataFetchStateHandler";
import { Button } from "@/components/ui/button";
import { useGraphQL } from "@/hooks/useGraphQL";
import { ARTICLES_BY_CATEGORY } from "@/queries/articles";

const gemCategories = [
  {
    name: "Diamonds",
    href: "/gemstones/diamonds",
    icon: Diamond,
    description: "The king of gemstones - grading, buying guides, and market analysis",
    color: "bg-primary/10 text-primary",
    image: "https://images.unsplash.com/photo-1586882829491-b81178aa622e?w=600&q=80",
  },
  {
    name: "Rubies",
    href: "/gemstones/rubies",
    icon: Gem,
    description: "Precious red corundum - valuation, origins, and investment potential",
    color: "bg-destructive/10 text-destructive",
    image: "https://images.unsplash.com/photo-1551122087-f99a40461414?w=600&q=80",
  },
  {
    name: "Sapphires",
    href: "/gemstones/sapphires",
    icon: Sparkles,
    description: "Blue beauties and fancy colors - Kashmir to Ceylon origins",
    color: "bg-accent/10 text-accent",
    image: "https://images.unsplash.com/photo-1599707367072-cd6ada2bc375?w=600&q=80",
  },
  {
    name: "Emeralds",
    href: "/gemstones/emeralds",
    icon: Star,
    description: "The green treasure - Colombian quality and treatment insights",
    color: "bg-success/10 text-success",
    image: "https://images.unsplash.com/photo-1583937443573-a03e7d8d0f0f?w=600&q=80",
  },
];

const indexData = [
  { name: "Diamond Index", value: "142.5", change: "-0.15%", isUp: false },
  { name: "Ruby Index", value: "198.3", change: "+2.34%", isUp: true },
  { name: "Sapphire Index", value: "165.8", change: "+1.12%", isUp: true },
  { name: "Emerald Index", value: "178.2", change: "+0.89%", isUp: true },
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
    category: article.categories?.nodes[0]?.name || "Gemstones",
    author: article.author?.node?.name || "Editorial Team",
    readTime: article.articleMeta?.readTime || "5 min read",
    date: new Date(article.date).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }),
    image: article.featuredImage?.node?.sourceUrl || "https://images.unsplash.com/photo-1586882829491-b81178aa622e?w=800&q=80",
    href: `/articles/${article.slug}`,
  };
}

export default function Gemstones() {
  // Fetch articles about gemstones
  const { data, loading, error, refetch } = useGraphQL(ARTICLES_BY_CATEGORY, {
    variables: { categorySlug: "gemstones", first: 4 },
  });

  const articles = useMemo(() => {
    try {
      if (data?.posts?.nodes && Array.isArray(data.posts.nodes) && data.posts.nodes.length > 0) {
        return data.posts.nodes.map((article: any, index: number) => transformArticle(article, index));
      }
    } catch (e) {
      console.warn("[Gemstones] Error transforming articles:", e);
    }
    return [];
  }, [data]);

  return (
    <PageLayout>
      <PageHero
        title="Gemstones"
        subtitle="Expert guides on diamonds, rubies, sapphires, and emeralds. Learn about grading, valuation, and investment potential of precious gemstones."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Gemstones" },
        ]}
        badge="Gemstone Hub"
      />

      {/* Gemstone Indices */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="font-display text-2xl font-bold text-foreground">Gemstone Indices</h2>
              <p className="text-muted-foreground mt-1">Price trends for major precious gemstones</p>
            </div>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {indexData.map((index) => (
              <div
                key={index.name}
                className="bg-card rounded-lg border border-border p-6 hover:shadow-md transition-shadow"
              >
                <p className="text-sm text-muted-foreground mb-2">{index.name}</p>
                <div className="flex items-baseline justify-between">
                  <p className="font-display text-2xl font-bold text-foreground">{index.value}</p>
                  <span
                    className={`text-sm font-medium ${
                      index.isUp ? "text-success" : "text-destructive"
                    }`}
                  >
                    {index.change}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Gemstone Categories */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Explore by Gemstone</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {gemCategories.map((gem) => (
              <Link
                key={gem.name}
                to={gem.href}
                className="group bg-card rounded-xl border border-border overflow-hidden hover:border-primary/50 hover:shadow-lg transition-all duration-300"
              >
                <div className="aspect-[16/10] overflow-hidden">
                  <img
                    src={gem.image}
                    alt={gem.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                </div>
                <div className="p-6">
                  <div className={`inline-flex p-2 rounded-lg ${gem.color} mb-3`}>
                    <gem.icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-display text-xl font-semibold text-foreground mb-2 group-hover:text-primary transition-colors">
                    {gem.name}
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">{gem.description}</p>
                  <span className="inline-flex items-center text-sm font-medium text-primary">
                    Learn more
                    <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </span>
                </div>
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
          <h2 className="font-display text-3xl font-bold text-silver-light mb-4">Find Your Perfect Gemstone</h2>
          <p className="text-silver max-w-2xl mx-auto mb-8">
            Discover certified gemstones from trusted dealers. Access expert evaluation tools, market data, and investment guidance.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold" asChild>
              <Link to="/top-dealers">Find Dealers</Link>
            </Button>
            <Button size="lg" variant="outline" className="border-silver/30 text-silver-light hover:bg-silver/10" asChild>
              <Link to="/market-insights">Buying Guides</Link>
            </Button>
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
