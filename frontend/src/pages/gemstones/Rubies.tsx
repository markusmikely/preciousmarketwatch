import { Link } from "react-router-dom";
import { ArrowRight, Gem, MapPin, Award, Sparkles } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { Button } from "@/components/ui/button";

const origins = [
  { name: "Burma (Myanmar)", quality: "Pigeon Blood - Most Prized", premium: "+50-100%" },
  { name: "Mozambique", quality: "High Quality, Good Color", premium: "Baseline" },
  { name: "Thailand", quality: "Darker Tones, Good Clarity", premium: "-10-20%" },
  { name: "Sri Lanka", quality: "Lighter Pink-Red", premium: "-20-30%" },
];

const qualityFactors = [
  { name: "Color", description: "Vivid red with slight blue undertone ('pigeon blood') is most valuable", icon: Gem },
  { name: "Clarity", description: "Inclusions ('silk') can enhance beauty if minimal", icon: Sparkles },
  { name: "Origin", description: "Burmese rubies command highest premiums", icon: MapPin },
  { name: "Treatment", description: "Unheated rubies are significantly more valuable", icon: Award },
];

const articles = [
  {
    title: "Burmese Ruby: The Gold Standard",
    excerpt: "Understanding why Myanmar rubies command the highest prices in the market.",
    category: "Origin Guide",
    author: "Emma Thompson",
    date: "Dec 9, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1551122087-f99a40461414?w=800&q=80",
    href: "/articles/burmese-ruby",
  },
  {
    title: "Ruby vs Red Spinel: Know the Difference",
    excerpt: "How to distinguish rubies from commonly mistaken red gemstones.",
    category: "Education",
    author: "David Park",
    date: "Dec 8, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1599707367072-cd6ada2bc375?w=800&q=80",
    href: "/articles/ruby-vs-spinel",
  },
  {
    title: "Ruby Heat Treatment: What Buyers Should Know",
    excerpt: "Understanding common treatments and their impact on value.",
    category: "Treatment",
    author: "Sarah Williams",
    date: "Dec 7, 2024",
    readTime: "7 min read",
    image: "https://images.unsplash.com/photo-1583937443573-a03e7d8d0f0f?w=800&q=80",
    href: "/articles/ruby-treatment",
  },
];

export default function Rubies() {
  return (
    <PageLayout>
      <PageHero
        title="Rubies"
        subtitle="The king of colored gemstones. Discover ruby quality factors, origins, and investment potential for this precious red corundum."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Gemstones", href: "/gemstones" },
          { label: "Rubies" },
        ]}
        badge="Precious Corundum"
      >
        <div className="flex items-center gap-4 mt-6">
          <div className="text-silver text-sm">
            <span className="block">Ruby Index: 198.3 (+2.34%)</span>
            <span className="block">Top quality: $15,000-$25,000+ per carat</span>
          </div>
        </div>
      </PageHero>

      {/* Quality Factors */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Ruby Quality Factors</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {qualityFactors.map((factor) => (
              <div key={factor.name} className="bg-card rounded-xl border border-border p-6 hover:border-destructive/50 hover:shadow-lg transition-all duration-300">
                <div className="inline-flex p-3 rounded-lg bg-destructive/10 text-destructive mb-4">
                  <factor.icon className="h-6 w-6" />
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-2">{factor.name}</h3>
                <p className="text-sm text-muted-foreground">{factor.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Origins */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Ruby Origins & Value</h2>
          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Origin</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Quality Characteristics</th>
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
            <h2 className="font-display text-2xl font-bold text-foreground">Ruby Guides</h2>
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
