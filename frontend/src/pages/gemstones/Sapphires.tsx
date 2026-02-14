import { Link } from "react-router-dom";
import { ArrowRight, Gem, Palette, MapPin, Award } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { Button } from "@/components/ui/button";

const colors = [
  { name: "Blue", description: "Classic sapphire - Kashmir is most prized", value: "Most Popular" },
  { name: "Padparadscha", description: "Pink-orange - extremely rare", value: "Most Valuable" },
  { name: "Pink", description: "Light to vivid pink hues", value: "Growing Demand" },
  { name: "Yellow", description: "From pale to vivid canary yellow", value: "Affordable Entry" },
  { name: "Green", description: "Teal to forest green", value: "Niche Market" },
  { name: "White", description: "Colorless corundum", value: "Diamond Alternative" },
];

const origins = [
  { name: "Kashmir", quality: "Velvety blue with silk - legendary", premium: "+200-500%" },
  { name: "Burma (Myanmar)", quality: "Royal blue, excellent saturation", premium: "+100-200%" },
  { name: "Sri Lanka (Ceylon)", quality: "Light to medium blue, high clarity", premium: "Baseline" },
  { name: "Madagascar", quality: "Wide range, good value", premium: "-10-30%" },
];

const articles = [
  {
    title: "Kashmir Sapphires: The Holy Grail of Blue Gems",
    excerpt: "Why these rare stones command the highest prices in the sapphire world.",
    category: "Origin",
    author: "Emma Thompson",
    date: "Dec 9, 2024",
    readTime: "7 min read",
    image: "https://images.unsplash.com/photo-1599707367072-cd6ada2bc375?w=800&q=80",
    href: "/articles/kashmir-sapphires",
  },
  {
    title: "Padparadscha: The Rarest Sapphire",
    excerpt: "Understanding the unique pink-orange sapphire that collectors crave.",
    category: "Education",
    author: "David Park",
    date: "Dec 8, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1551122087-f99a40461414?w=800&q=80",
    href: "/articles/padparadscha-sapphire",
  },
  {
    title: "Sapphire Engagement Rings: A Complete Guide",
    excerpt: "Everything you need to know about choosing a sapphire for your ring.",
    category: "Buying Guide",
    author: "Sarah Williams",
    date: "Dec 7, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1586882829491-b81178aa622e?w=800&q=80",
    href: "/articles/sapphire-engagement-rings",
  },
];

export default function Sapphires() {
  return (
    <PageLayout>
      <PageHero
        title="Sapphires"
        subtitle="Beyond blue - explore the world of sapphire colors, origins, and quality factors. From Kashmir to Ceylon, discover what makes sapphires special."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Gemstones", href: "/gemstones" },
          { label: "Sapphires" },
        ]}
        badge="Corundum Variety"
      >
        <div className="flex items-center gap-4 mt-6">
          <div className="text-silver text-sm">
            <span className="block">Sapphire Index: 165.8 (+1.12%)</span>
            <span className="block">Kashmir premium: 3-5x over Ceylon</span>
          </div>
        </div>
      </PageHero>

      {/* Color Varieties */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Sapphire Colors</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {colors.map((color) => (
              <div key={color.name} className="bg-card rounded-xl border border-border p-6 hover:border-accent/50 hover:shadow-lg transition-all duration-300">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-display text-lg font-semibold text-foreground">{color.name}</h3>
                  <span className="text-xs px-2 py-1 bg-accent/10 text-accent rounded-full">{color.value}</span>
                </div>
                <p className="text-sm text-muted-foreground">{color.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Origins */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Origins & Value</h2>
          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Origin</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Characteristics</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Price Premium</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {origins.map((origin) => (
                  <tr key={origin.name} className="hover:bg-muted/50">
                    <td className="px-6 py-4 text-sm font-medium text-foreground">{origin.name}</td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">{origin.quality}</td>
                    <td className="px-6 py-4 text-sm text-foreground font-medium">{origin.premium}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Articles */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-2xl font-bold text-foreground">Sapphire Guides</h2>
            <Button variant="outline" asChild>
              <Link to="/market-insights">
                All articles
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {articles.map((article) => (
              <ArticleCard key={article.title} {...article} />
            ))}
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
