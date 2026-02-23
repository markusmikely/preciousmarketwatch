import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { CategoryFilter } from "@/components/shared/CategoryFilter";
import { DataFetchStateHandler } from "@/components/shared/DataFetchStateHandler";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useGraphQL } from "@/hooks/useGraphQL";
import { ARTICLES_QUERY } from "@/queries/articles";

const categories = ["All", "Gold", "Silver", "Platinum", "Diamonds", "Gemstones", "Market Analysis", "Investment"];

// Fallback articles if GraphQL fails
const fallbackArticles = [
  {
    id: "1",
    title: "Gold Reaches New Highs as Inflation Concerns Persist",
    excerpt: "Central bank policies continue to drive investor interest in gold as a hedge against currency devaluation.",
    slug: "gold-new-highs",
    categories: { nodes: [{ name: "Gold" }] },
    author: { node: { name: "Michael Chen" } },
    date: "2024-12-09",
    articleMeta: { readTime: "5 min read" },
    featuredImage: { node: { sourceUrl: "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80" } },
    featured: true,
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
    category: article.categories?.nodes[0]?.name || "General",
    author: article.author?.node?.name || "Editorial Team",
    readTime: article.articleMeta?.readTime || "5 min read",
    date: new Date(article.date).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }),
    image: article.featuredImage?.node?.sourceUrl || "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80",
    href: `/articles/${article.slug}`,
    featured: index === 0,
  };
}

export default function MarketInsights() {
  const [activeCategory, setActiveCategory] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch articles from GraphQL
  const { data, loading, error, refetch } = useGraphQL(ARTICLES_QUERY, {
    variables: { first: 50 },
  });

  // Transform and filter articles
  const allArticles = useMemo(() => {
    if (!data?.posts?.nodes) return fallbackArticles;
    return data.posts.nodes.map((article: any, index: number) => transformArticle(article, index));
  }, [data]);

  const filteredArticles = useMemo(() => {
    return allArticles.filter((article: any) => {
      const matchesCategory = activeCategory === "All" || article.category === activeCategory;
      const matchesSearch =
        article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        article.excerpt.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesCategory && matchesSearch;
    });
  }, [allArticles, activeCategory, searchQuery]);

  const featuredArticle = filteredArticles.find((a: any) => a.featured);
  const regularArticles = filteredArticles.filter((a: any) => !a.featured);

  return (
    <PageLayout>
      <PageHero
        title="Market Insights"
        subtitle="Expert analysis, market trends, and investment strategies for precious metals and gemstones. Stay informed with our comprehensive coverage."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Market Insights" },
        ]}
        badge="Analysis & News"
      />

      {/* Search & Filter */}
      <section className="py-8 bg-muted/30 border-b border-border">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
            <div className="relative w-full lg:w-96">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <CategoryFilter
              categories={categories}
              activeCategory={activeCategory}
              onCategoryChange={setActiveCategory}
            />
          </div>
        </div>
      </section>

      {/* Featured Article */}
      {featuredArticle && (
        <section className="py-12">
          <div className="container mx-auto px-4 lg:px-8">
            <h2 className="font-display text-xl font-bold text-foreground mb-6">Featured</h2>
            <DataFetchStateHandler loading={loading} error={error} onRetry={refetch}>
              <ArticleCard {...featuredArticle} featured />
            </DataFetchStateHandler>
          </div>
        </section>
      )}

      {/* Articles Grid */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-xl font-bold text-foreground">
              {activeCategory === "All" ? "All Articles" : activeCategory}
              <span className="text-muted-foreground font-normal ml-2">({regularArticles.length})</span>
            </h2>
          </div>
          <DataFetchStateHandler loading={loading} error={error} onRetry={refetch} loadingMessage="Loading articles...">
            {regularArticles.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {regularArticles.map((article: any) => (
                  <ArticleCard key={article.id} {...article} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No articles found matching your criteria.</p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => {
                    setActiveCategory("All");
                    setSearchQuery("");
                  }}
                >
                  Clear filters
                </Button>
              </div>
            )}
          </DataFetchStateHandler>
        </div>
      </section>

      {/* Newsletter CTA */}
      <section className="py-16 bg-gradient-hero">
        <div className="container mx-auto px-4 lg:px-8 text-center">
          <h2 className="font-display text-3xl font-bold text-silver-light mb-4">Never Miss an Update</h2>
          <p className="text-silver max-w-2xl mx-auto mb-8">
            Subscribe to our newsletter for weekly market analysis and expert insights delivered to your inbox.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-md mx-auto">
            <Input
              placeholder="Enter your email"
              className="bg-navy border-silver/30 text-silver-light placeholder:text-silver/60"
            />
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold whitespace-nowrap">
              Subscribe
            </Button>
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
