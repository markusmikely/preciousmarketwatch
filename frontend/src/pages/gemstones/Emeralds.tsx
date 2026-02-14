import { Link } from "react-router-dom";
import { ArrowRight, Gem, Droplets, MapPin, Eye } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { Button } from "@/components/ui/button";

const qualityFactors = [
  { name: "Color", description: "Vivid green with slight blue is most valuable", icon: Gem },
  { name: "Clarity", description: "Inclusions ('jardin') are expected and often tolerated", icon: Eye },
  { name: "Treatment", description: "Oil/resin treatment is standard - disclosure is key", icon: Droplets },
  { name: "Origin", description: "Colombian emeralds command highest premiums", icon: MapPin },
];

const origins = [
  { name: "Colombia", quality: "Vivid green, warm undertones - benchmark quality", premium: "+50-100%" },
  { name: "Zambia", quality: "Bluish-green, high clarity", premium: "Baseline" },
  { name: "Brazil", quality: "Darker tones, good value", premium: "-20-40%" },
  { name: "Ethiopia", quality: "High clarity, newer source", premium: "-30-50%" },
];

const treatments = [
  { type: "None", rarity: "Extremely Rare", premium: "+200-500%" },
  { type: "Minor Oil", rarity: "Rare", premium: "+50-100%" },
  { type: "Moderate Oil", rarity: "Common", premium: "Baseline" },
  { type: "Significant Treatment", rarity: "Common", premium: "-30-50%" },
];

const articles = [
  {
    title: "Colombian Emeralds: The World's Finest Green Gems",
    excerpt: "Why Muzo and Chivor mines produce the most sought-after emeralds.",
    category: "Origin",
    author: "Emma Thompson",
    date: "Dec 9, 2024",
    readTime: "7 min read",
    image: "https://images.unsplash.com/photo-1583937443573-a03e7d8d0f0f?w=800&q=80",
    href: "/articles/colombian-emeralds",
  },
  {
    title: "Understanding Emerald Treatments",
    excerpt: "Oil, resin, and clarity enhancement - what every buyer should know.",
    category: "Education",
    author: "David Park",
    date: "Dec 8, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1551122087-f99a40461414?w=800&q=80",
    href: "/articles/emerald-treatments",
  },
  {
    title: "Emerald Care: Protecting Your Investment",
    excerpt: "How to clean, store, and maintain emerald jewelry safely.",
    category: "Care Guide",
    author: "Sarah Williams",
    date: "Dec 7, 2024",
    readTime: "4 min read",
    image: "https://images.unsplash.com/photo-1599707367072-cd6ada2bc375?w=800&q=80",
    href: "/articles/emerald-care",
  },
];

export default function Emeralds() {
  return (
    <PageLayout>
      <PageHero
        title="Emeralds"
        subtitle="The green treasure of beryl. Navigate emerald quality, treatments, and origins with our comprehensive guides and market insights."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Gemstones", href: "/gemstones" },
          { label: "Emeralds" },
        ]}
        badge="Green Beryl"
      >
        <div className="flex items-center gap-4 mt-6">
          <div className="text-silver text-sm">
            <span className="block">Emerald Index: 178.2 (+0.89%)</span>
            <span className="block">Colombian premium: 50-100% over Zambian</span>
          </div>
        </div>
      </PageHero>

      {/* Quality Factors */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Emerald Quality Factors</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {qualityFactors.map((factor) => (
              <div key={factor.name} className="bg-card rounded-xl border border-border p-6 hover:border-success/50 hover:shadow-lg transition-all duration-300">
                <div className="inline-flex p-3 rounded-lg bg-success/10 text-success mb-4">
                  <factor.icon className="h-6 w-6" />
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-2">{factor.name}</h3>
                <p className="text-sm text-muted-foreground">{factor.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Treatment Guide */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Treatment Impact on Value</h2>
          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Treatment Level</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Market Availability</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Price Impact</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {treatments.map((treatment) => (
                  <tr key={treatment.type} className="hover:bg-muted/50">
                    <td className="px-6 py-4 text-sm font-medium text-foreground">{treatment.type}</td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">{treatment.rarity}</td>
                    <td className="px-6 py-4 text-sm text-foreground font-medium">{treatment.premium}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Origins */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Emerald Origins</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {origins.map((origin) => (
              <div key={origin.name} className="bg-card rounded-xl border border-border p-6">
                <h3 className="font-display text-lg font-semibold text-foreground mb-2">{origin.name}</h3>
                <p className="text-sm text-muted-foreground mb-3">{origin.quality}</p>
                <span className="text-sm font-medium text-success">{origin.premium}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Articles */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-2xl font-bold text-foreground">Emerald Guides</h2>
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
