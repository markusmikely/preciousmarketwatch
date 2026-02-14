import { Link } from "react-router-dom";
import { ArrowRight, Gem, TrendingUp, Shield, Award, Crown, Watch, CircleDot } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { Button } from "@/components/ui/button";

const investmentCategories = [
  {
    name: "High Jewelry",
    icon: Crown,
    description: "Exceptional pieces from renowned maisons - Cartier, Van Cleef, Bulgari",
    appreciation: "+5-15% annually",
  },
  {
    name: "Vintage & Antique",
    icon: Gem,
    description: "Art Deco, Victorian, and estate pieces with provenance",
    appreciation: "+3-10% annually",
  },
  {
    name: "Luxury Watches",
    icon: Watch,
    description: "Rolex, Patek Philippe, Audemars Piguet as wearable investments",
    appreciation: "+5-20% annually",
  },
  {
    name: "Signed Pieces",
    icon: CircleDot,
    description: "Designer jewelry with brand recognition and collectibility",
    appreciation: "+4-12% annually",
  },
];

const tips = [
  { title: "Buy Quality", description: "Focus on exceptional craftsmanship and materials over quantity" },
  { title: "Verify Authenticity", description: "Always request certificates and provenance documentation" },
  { title: "Consider Resale", description: "Choose timeless designs over trendy pieces" },
  { title: "Proper Storage", description: "Invest in proper insurance and secure storage" },
];

const articles = [
  {
    title: "Jewelry as an Alternative Investment Asset",
    excerpt: "How high jewelry compares to stocks, bonds, and real estate as an investment vehicle.",
    category: "Investment",
    author: "Victoria Sterling",
    date: "Dec 9, 2024",
    readTime: "8 min read",
    image: "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=800&q=80",
    href: "/articles/jewelry-alternative-investment",
    featured: true,
  },
  {
    title: "Top 10 Most Collectible Jewelry Brands",
    excerpt: "From Cartier to JAR, discover which brands hold their value best.",
    category: "Collectibles",
    author: "Emma Thompson",
    date: "Dec 8, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=800&q=80",
    href: "/articles/collectible-jewelry-brands",
  },
  {
    title: "Auction Records: Most Expensive Jewelry Ever Sold",
    excerpt: "Explore the record-breaking sales that shaped the luxury jewelry market.",
    category: "Market",
    author: "David Park",
    date: "Dec 7, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1602751584552-8ba73aad10e1?w=800&q=80",
    href: "/articles/auction-records",
  },
  {
    title: "Vintage Jewelry Authentication Guide",
    excerpt: "How to verify the authenticity and value of antique jewelry pieces.",
    category: "Guide",
    author: "Sarah Williams",
    date: "Dec 6, 2024",
    readTime: "7 min read",
    image: "https://images.unsplash.com/photo-1573408301185-9146fe634ad0?w=800&q=80",
    href: "/articles/vintage-authentication",
  },
];

export default function JewelryInvestment() {
  return (
    <PageLayout>
      <PageHero
        title="Jewelry Investment"
        subtitle="Navigate the world of jewelry as an investment asset. From high jewelry to vintage pieces, discover strategies for building a valuable collection."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Jewelry Investment" },
        ]}
        badge="Alternative Assets"
      />

      {/* Investment Categories */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Investment Categories</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {investmentCategories.map((category) => (
              <div key={category.name} className="bg-card rounded-xl border border-border p-6 hover:border-primary/50 hover:shadow-lg transition-all duration-300">
                <div className="inline-flex p-3 rounded-lg bg-primary/10 text-primary mb-4">
                  <category.icon className="h-6 w-6" />
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-2">{category.name}</h3>
                <p className="text-sm text-muted-foreground mb-4">{category.description}</p>
                <div className="flex items-center gap-2 text-success">
                  <TrendingUp className="h-4 w-4" />
                  <span className="text-sm font-medium">{category.appreciation}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Article */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <ArticleCard {...articles[0]} featured />
        </div>
      </section>

      {/* Investment Tips */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Investment Principles</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {tips.map((tip, index) => (
              <div key={tip.title} className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-display font-bold">
                  {index + 1}
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">{tip.title}</h3>
                  <p className="text-sm text-muted-foreground">{tip.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* More Articles */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-2xl font-bold text-foreground">Latest Insights</h2>
            <Button variant="outline" asChild>
              <Link to="/market-insights">
                All articles
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {articles.slice(1).map((article) => (
              <ArticleCard key={article.title} {...article} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-gradient-hero">
        <div className="container mx-auto px-4 lg:px-8 text-center">
          <h2 className="font-display text-3xl font-bold text-silver-light mb-4">
            Find Investment-Grade Jewelry
          </h2>
          <p className="text-silver max-w-2xl mx-auto mb-8">
            Connect with vetted dealers specializing in investment-quality pieces with proper documentation and provenance.
          </p>
          <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold">
            Browse Dealers
          </Button>
        </div>
      </section>
    </PageLayout>
  );
}
