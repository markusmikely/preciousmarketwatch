import { useState } from "react";
import { Link } from "react-router-dom";
import { Search, Filter } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { CategoryFilter } from "@/components/shared/CategoryFilter";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const categories = ["All", "Gold", "Silver", "Platinum", "Diamonds", "Gemstones", "Market Analysis", "Investment"];

const articles = [
  {
    title: "Gold Reaches New Highs as Inflation Concerns Persist",
    excerpt: "Central bank policies continue to drive investor interest in gold as a hedge against currency devaluation.",
    category: "Gold",
    author: "Michael Chen",
    date: "Dec 9, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80",
    href: "/articles/gold-new-highs",
    featured: true,
  },
  {
    title: "Silver Industrial Demand Surges on Green Energy Push",
    excerpt: "Solar panel and EV production drive unprecedented demand for silver.",
    category: "Silver",
    author: "Sarah Williams",
    date: "Dec 8, 2024",
    readTime: "4 min read",
    image: "https://images.unsplash.com/photo-1589656966895-2f33e7653819?w=800&q=80",
    href: "/articles/silver-demand",
  },
  {
    title: "Lab-Grown vs Natural Diamonds: Market Impact",
    excerpt: "How lab-grown diamonds are reshaping the natural diamond market dynamics.",
    category: "Diamonds",
    author: "Emma Thompson",
    date: "Dec 7, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1586882829491-b81178aa622e?w=800&q=80",
    href: "/articles/lab-vs-natural",
  },
  {
    title: "Platinum Supply Deficit: Investment Opportunity?",
    excerpt: "Mining disruptions create potential supply squeeze in platinum market.",
    category: "Platinum",
    author: "David Park",
    date: "Dec 6, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1624365168968-f283d506c6b6?w=800&q=80",
    href: "/articles/platinum-deficit",
  },
  {
    title: "Colored Gemstone Investment Trends 2024",
    excerpt: "Which colored stones are gaining investor attention this year.",
    category: "Gemstones",
    author: "Victoria Sterling",
    date: "Dec 5, 2024",
    readTime: "7 min read",
    image: "https://images.unsplash.com/photo-1599707367072-cd6ada2bc375?w=800&q=80",
    href: "/articles/gemstone-trends",
  },
  {
    title: "Central Bank Gold Buying: 2024 Analysis",
    excerpt: "Record central bank purchases and what they mean for gold prices.",
    category: "Market Analysis",
    author: "Michael Chen",
    date: "Dec 4, 2024",
    readTime: "8 min read",
    image: "https://images.unsplash.com/photo-1579532536935-619928decd08?w=800&q=80",
    href: "/articles/central-bank-gold",
  },
  {
    title: "Building a Precious Metals Portfolio",
    excerpt: "Strategic allocation guide for diversified precious metals investing.",
    category: "Investment",
    author: "Sarah Williams",
    date: "Dec 3, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80",
    href: "/articles/portfolio-guide",
  },
  {
    title: "Kashmir Sapphires: Record Auction Results",
    excerpt: "Recent auction sales highlight continued demand for rare Kashmir origin stones.",
    category: "Gemstones",
    author: "Emma Thompson",
    date: "Dec 2, 2024",
    readTime: "4 min read",
    image: "https://images.unsplash.com/photo-1551122087-f99a40461414?w=800&q=80",
    href: "/articles/kashmir-auction",
  },
];

export default function MarketInsights() {
  const [activeCategory, setActiveCategory] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredArticles = articles.filter((article) => {
    const matchesCategory = activeCategory === "All" || article.category === activeCategory;
    const matchesSearch = article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.excerpt.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const featuredArticle = filteredArticles.find((a) => a.featured);
  const regularArticles = filteredArticles.filter((a) => !a.featured);

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
            <ArticleCard {...featuredArticle} featured />
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
          {regularArticles.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {regularArticles.map((article) => (
                <ArticleCard key={article.title} {...article} />
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
        </div>
      </section>

      {/* Newsletter CTA */}
      <section className="py-16 bg-gradient-hero">
        <div className="container mx-auto px-4 lg:px-8 text-center">
          <h2 className="font-display text-3xl font-bold text-silver-light mb-4">
            Never Miss an Update
          </h2>
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
