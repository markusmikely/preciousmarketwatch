import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Diamond, Gem, Sparkles, Star } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { Button } from "@/components/ui/button";

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

const articles = [
  {
    title: "Lab-Grown vs Natural Diamonds: Complete Guide",
    excerpt: "Understanding the differences, value propositions, and market dynamics of natural and lab-grown diamonds.",
    category: "Diamonds",
    author: "Emma Thompson",
    date: "Dec 9, 2024",
    readTime: "7 min read",
    image: "https://images.unsplash.com/photo-1586882829491-b81178aa622e?w=800&q=80",
    href: "/articles/lab-vs-natural-diamonds",
  },
  {
    title: "The 4Cs of Diamond Grading Explained",
    excerpt: "Master the fundamentals of diamond quality assessment: Cut, Clarity, Color, and Carat weight.",
    category: "Education",
    author: "Michael Chen",
    date: "Dec 8, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=800&q=80",
    href: "/articles/diamond-4cs-guide",
  },
  {
    title: "Colored Gemstone Investment: What You Need to Know",
    excerpt: "Beyond diamonds - exploring the investment potential of rubies, sapphires, and emeralds.",
    category: "Investment",
    author: "Sarah Williams",
    date: "Dec 7, 2024",
    readTime: "8 min read",
    image: "https://images.unsplash.com/photo-1599707367072-cd6ada2bc375?w=800&q=80",
    href: "/articles/colored-gemstone-investment",
  },
  {
    title: "Gemstone Certification: GIA, AGS, and More",
    excerpt: "Understanding gemological certifications and why they matter for your purchase.",
    category: "Guide",
    author: "David Park",
    date: "Dec 6, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1551122087-f99a40461414?w=800&q=80",
    href: "/articles/gemstone-certification",
  },
];

export default function Gemstones() {
  return (
    <PageLayout>
      <PageHero
        title="Gemstones"
        subtitle="Expert guides on diamonds, rubies, sapphires, and emeralds. From grading to investment, discover everything about precious gemstones."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Gemstones" },
        ]}
        badge="Precious Stones"
      />

      {/* Market Indices */}
      <section className="py-8 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {indexData.map((index) => (
              <div key={index.name} className="bg-card rounded-lg border border-border p-4 text-center">
                <span className="text-sm text-muted-foreground block mb-1">{index.name}</span>
                <span className="font-display text-xl font-bold text-foreground">{index.value}</span>
                <span className={`text-sm ml-2 ${index.isUp ? "text-success" : "text-destructive"}`}>
                  {index.change}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Gemstone Categories */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Explore Gemstones</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {gemCategories.map((category) => (
              <Link
                key={category.name}
                to={category.href}
                className="group relative h-[280px] rounded-xl overflow-hidden"
              >
                <img
                  src={category.image}
                  alt={category.name}
                  className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-navy via-navy/60 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-6">
                  <div className={`inline-flex p-2 rounded-lg ${category.color} mb-3`}>
                    <category.icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-display text-2xl font-bold text-silver-light mb-2 group-hover:text-primary transition-colors">
                    {category.name}
                  </h3>
                  <p className="text-silver text-sm mb-3">{category.description}</p>
                  <span className="inline-flex items-center text-sm font-medium text-primary">
                    Explore {category.name}
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
            <h2 className="font-display text-2xl font-bold text-foreground">Gemstone Guides & Analysis</h2>
            <Button variant="outline" asChild>
              <Link to="/market-insights">
                View all articles
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {articles.map((article) => (
              <ArticleCard key={article.title} {...article} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-gradient-hero">
        <div className="container mx-auto px-4 lg:px-8 text-center">
          <h2 className="font-display text-3xl font-bold text-silver-light mb-4">
            Find Certified Gemstone Dealers
          </h2>
          <p className="text-silver max-w-2xl mx-auto mb-8">
            Connect with trusted, certified dealers for diamonds, rubies, sapphires, and emeralds.
          </p>
          <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold">
            Browse Dealers
          </Button>
        </div>
      </section>
    </PageLayout>
  );
}
