import { Link } from "react-router-dom";
import { ArrowRight, TrendingDown, Car, Zap, Factory, FlaskConical } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { PriceChart } from "@/components/shared/PriceChart";

const articles = [
  {
    title: "Platinum in the Automotive Industry: Future Outlook",
    excerpt: "How hydrogen fuel cells and emissions standards are driving platinum demand.",
    category: "Industry Analysis",
    author: "David Park",
    date: "Dec 9, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1624365168968-f283d506c6b6?w=800&q=80",
    href: "/articles/platinum-automotive",
  },
  {
    title: "Platinum vs Gold: Investment Comparison",
    excerpt: "Comparing the investment characteristics of platinum against gold.",
    category: "Comparison",
    author: "Sarah Williams",
    date: "Dec 8, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80",
    href: "/articles/platinum-vs-gold",
  },
  {
    title: "South African Mining: Platinum Supply Dynamics",
    excerpt: "Understanding how South African production affects global platinum supply.",
    category: "Supply Chain",
    author: "Michael Chen",
    date: "Dec 7, 2024",
    readTime: "7 min read",
    image: "https://images.unsplash.com/photo-1579532536935-619928decd08?w=800&q=80",
    href: "/articles/south-african-platinum",
  },
];

const applications = [
  { name: "Automotive", percentage: 40, icon: Car, description: "Catalytic converters" },
  { name: "Jewelry", percentage: 30, icon: Zap, description: "Fine jewelry & watches" },
  { name: "Industrial", percentage: 20, icon: Factory, description: "Chemical & petroleum" },
  { name: "Medical", percentage: 10, icon: FlaskConical, description: "Cancer treatments" },
];

export default function Platinum() {
  return (
    <PageLayout>
      <PageHero
        title="Platinum Investment Guide"
        subtitle="Rarer than gold with unique industrial applications. Explore platinum market dynamics, investment strategies, and supply chain insights."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Precious Metals", href: "/precious-metals" },
          { label: "Platinum" },
        ]}
        badge="Rare Industrial Metal"
      >
        <div className="flex items-center gap-6 mt-6">
          <div className="flex items-center gap-2">
            <span className="text-3xl font-display font-bold text-silver-light">$978.50</span>
            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-destructive/20 text-destructive text-sm font-medium">
              <TrendingDown className="h-4 w-4" />
              -0.29%
            </span>
          </div>
          <div className="text-silver text-sm">
            <span className="block">Platinum/Gold Ratio: 0.37</span>
            <span className="block">Supply: Deficit</span>
          </div>
        </div>
      </PageHero>

      {/* Price Chart */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <PriceChart metal="platinum" />
        </div>
      </section>

      {/* Applications */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Platinum Applications</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {applications.map((app) => (
              <div key={app.name} className="bg-card rounded-xl border border-border p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="inline-flex p-3 rounded-lg bg-muted">
                    <app.icon className="h-6 w-6 text-foreground" />
                  </div>
                  <span className="text-2xl font-display font-bold text-accent">{app.percentage}%</span>
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-1">{app.name}</h3>
                <p className="text-sm text-muted-foreground">{app.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Articles */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-2xl font-bold text-foreground">Platinum Insights</h2>
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

      {/* Key Facts */}
      <section className="py-12 bg-gradient-hero">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-silver-light mb-8 text-center">Platinum Key Facts</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { label: "Symbol", value: "Pt (XPT)" },
              { label: "Standard Purity", value: "99.95% (999.5)" },
              { label: "Density", value: "21.45 g/cm³" },
              { label: "Annual Production", value: "~180 tonnes" },
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
