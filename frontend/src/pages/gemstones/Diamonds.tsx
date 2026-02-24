import { Link } from "react-router-dom";
import { ArrowRight, Diamond, Award, Shield, Sparkles } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { GemIndexSection } from "@/components/shared/GemIndexSection";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { Button } from "@/components/ui/button";

const fourCs = [
  { name: "Cut", description: "The most important factor determining brilliance and fire", icon: Sparkles },
  { name: "Clarity", description: "Absence of inclusions and blemishes under 10x magnification", icon: Diamond },
  { name: "Color", description: "Graded from D (colorless) to Z (light yellow/brown)", icon: Award },
  { name: "Carat", description: "Weight measurement - 1 carat equals 200 milligrams", icon: Shield },
];

const articles = [
  {
    title: "Diamond Buying Guide: How to Choose the Perfect Stone",
    excerpt: "Expert tips on selecting a diamond that maximizes beauty while staying within budget.",
    category: "Buying Guide",
    author: "Emma Thompson",
    date: "Dec 9, 2024",
    readTime: "8 min read",
    image: "https://images.unsplash.com/photo-1586882829491-b81178aa622e?w=800&q=80",
    href: "/articles/diamond-buying-guide",
  },
  {
    title: "Lab-Grown Diamonds: Are They Worth It?",
    excerpt: "Comparing lab-grown to natural diamonds in terms of value, quality, and sustainability.",
    category: "Analysis",
    author: "Michael Chen",
    date: "Dec 8, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=800&q=80",
    href: "/articles/lab-grown-diamonds",
  },
  {
    title: "Understanding GIA Diamond Certificates",
    excerpt: "How to read and interpret GIA grading reports for informed purchasing decisions.",
    category: "Education",
    author: "Sarah Williams",
    date: "Dec 7, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1599707367072-cd6ada2bc375?w=800&q=80",
    href: "/articles/gia-certificates",
  },
];

const shapes = [
  "Round Brilliant", "Princess", "Cushion", "Oval", "Emerald", "Pear", "Marquise", "Radiant"
];

export default function Diamonds() {
  return (
    <PageLayout>
      <PageHero
        title="Diamonds"
        subtitle="The ultimate guide to diamond grading, buying, and investment. Master the 4Cs and find your perfect stone."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Gemstones", href: "/gemstones" },
          { label: "Diamonds" },
        ]}
        badge="King of Gemstones"
      />

      <GemIndexSection gemIndexName="Diamond" />

      {/* The 4Cs */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-2">The 4Cs of Diamond Quality</h2>
          <p className="text-muted-foreground mb-8">Understanding these four factors is essential for evaluating any diamond</p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {fourCs.map((c, index) => (
              <div key={c.name} className="bg-card rounded-xl border border-border p-6 hover:border-primary/50 hover:shadow-lg transition-all duration-300">
                <div className="flex items-center gap-3 mb-4">
                  <div className="inline-flex p-3 rounded-lg bg-primary/10 text-primary">
                    <c.icon className="h-6 w-6" />
                  </div>
                  <span className="text-3xl font-display font-bold text-primary">{index + 1}</span>
                </div>
                <h3 className="font-display text-xl font-semibold text-foreground mb-2">{c.name}</h3>
                <p className="text-sm text-muted-foreground">{c.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Diamond Shapes */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Popular Diamond Shapes</h2>
          <div className="flex flex-wrap gap-3">
            {shapes.map((shape) => (
              <span
                key={shape}
                className="px-4 py-2 bg-card rounded-full border border-border text-sm font-medium text-foreground hover:border-primary hover:text-primary transition-colors cursor-pointer"
              >
                {shape}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Price Guide */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Diamond Price Ranges</h2>
          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Carat Weight</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Good Quality</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Very Good</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Excellent</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {[
                  { carat: "0.5 ct", good: "$1,200 - $2,500", veryGood: "$2,500 - $4,000", excellent: "$4,000 - $6,000" },
                  { carat: "1.0 ct", good: "$4,000 - $7,000", veryGood: "$7,000 - $12,000", excellent: "$12,000 - $20,000" },
                  { carat: "1.5 ct", good: "$8,000 - $15,000", veryGood: "$15,000 - $25,000", excellent: "$25,000 - $40,000" },
                  { carat: "2.0 ct", good: "$15,000 - $30,000", veryGood: "$30,000 - $50,000", excellent: "$50,000 - $80,000" },
                ].map((row) => (
                  <tr key={row.carat} className="hover:bg-muted/50">
                    <td className="px-6 py-4 text-sm font-medium text-foreground">{row.carat}</td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">{row.good}</td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">{row.veryGood}</td>
                    <td className="px-6 py-4 text-sm text-foreground font-medium">{row.excellent}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="px-6 py-3 text-xs text-muted-foreground bg-muted/50">
              *Prices are estimates for natural diamonds with GIA certification. Actual prices vary based on market conditions.
            </p>
          </div>
        </div>
      </section>

      {/* Articles */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-2xl font-bold text-foreground">Diamond Guides</h2>
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
