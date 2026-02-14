import { useState } from "react";
import { Shield, Award, Star } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { DealerCard } from "@/components/shared/DealerCard";
import { CategoryFilter } from "@/components/shared/CategoryFilter";

const categories = ["All", "Gold & Silver", "Platinum & Palladium", "Diamonds", "Colored Gemstones", "Jewelry"];

const dealers = [
  {
    name: "APMEX",
    description: "One of the largest online precious metals dealers in the US, offering an extensive selection of gold, silver, platinum, and palladium products.",
    rating: 4.8,
    reviews: 12450,
    categories: ["Gold & Silver", "Platinum & Palladium"],
    features: ["Free shipping $199+", "Price match guarantee", "Secure storage", "IRA eligible"],
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: "https://apmex.com",
    featured: true,
  },
  {
    name: "JM Bullion",
    description: "Trusted dealer offering competitive prices on precious metals with fast, secure shipping and excellent customer service.",
    rating: 4.7,
    reviews: 8920,
    categories: ["Gold & Silver", "Platinum & Palladium"],
    features: ["Low premiums", "Fast shipping", "Price alerts", "Buyback program"],
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: "https://jmbullion.com",
    featured: true,
  },
  {
    name: "SD Bullion",
    description: "Known for industry-low premiums and transparent pricing on gold and silver bullion products.",
    rating: 4.6,
    reviews: 6540,
    categories: ["Gold & Silver"],
    features: ["Lowest premiums", "Free shipping $199+", "IRA eligible"],
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: "https://sdbullion.com",
    featured: false,
  },
  {
    name: "Blue Nile",
    description: "Leading online diamond and fine jewelry retailer with exceptional selection and competitive pricing.",
    rating: 4.5,
    reviews: 15230,
    categories: ["Diamonds", "Jewelry"],
    features: ["GIA certified", "360° imaging", "Free returns", "Lifetime warranty"],
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: "https://bluenile.com",
    featured: true,
  },
  {
    name: "James Allen",
    description: "Innovative online jeweler offering HD 360° diamond viewing technology and custom jewelry design.",
    rating: 4.6,
    reviews: 11890,
    categories: ["Diamonds", "Jewelry"],
    features: ["360° HD video", "Real-time inspection", "Free engraving", "Lifetime warranty"],
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: "https://jamesallen.com",
    featured: false,
  },
  {
    name: "Leibish & Co.",
    description: "Specialists in natural fancy colored diamonds and colored gemstones with decades of expertise.",
    rating: 4.9,
    reviews: 3420,
    categories: ["Diamonds", "Colored Gemstones"],
    features: ["Colored diamond experts", "GIA certified", "Custom designs", "Investment grade"],
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: "https://leibish.com",
    featured: true,
  },
  {
    name: "Brilliant Earth",
    description: "Ethical jewelry company specializing in conflict-free diamonds and recycled precious metals.",
    rating: 4.4,
    reviews: 9870,
    categories: ["Diamonds", "Jewelry", "Colored Gemstones"],
    features: ["Ethically sourced", "Recycled metals", "Custom designs", "Free shipping"],
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: "https://brilliantearth.com",
    featured: false,
  },
  {
    name: "Kitco",
    description: "Industry leader in precious metals trading, news, and market information since 1977.",
    rating: 4.5,
    reviews: 7650,
    categories: ["Gold & Silver", "Platinum & Palladium"],
    features: ["Live pricing", "Pool accounts", "Allocated storage", "Trading platform"],
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: "https://kitco.com",
    featured: false,
  },
];

const trustIndicators = [
  { icon: Shield, title: "Vetted Dealers", description: "All dealers verified for legitimacy and customer satisfaction" },
  { icon: Award, title: "Quality Guarantee", description: "Products backed by authenticity certificates" },
  { icon: Star, title: "Real Reviews", description: "Ratings based on verified customer experiences" },
];

export default function TopDealers() {
  const [activeCategory, setActiveCategory] = useState("All");

  const filteredDealers = dealers.filter((dealer) => {
    if (activeCategory === "All") return true;
    return dealer.categories.includes(activeCategory);
  });

  const featuredDealers = filteredDealers.filter((d) => d.featured);
  const otherDealers = filteredDealers.filter((d) => !d.featured);

  return (
    <PageLayout>
      <PageHero
        title="Top Dealers"
        subtitle="Vetted and trusted precious metals and gemstone dealers. Find the right partner for your investment needs."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Top Dealers" },
        ]}
        badge="Affiliate Partners"
      />

      {/* Trust Indicators */}
      <section className="py-8 bg-muted/30 border-b border-border">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="grid md:grid-cols-3 gap-6">
            {trustIndicators.map((indicator) => (
              <div key={indicator.title} className="flex items-center gap-4">
                <div className="flex-shrink-0 p-3 rounded-lg bg-primary/10 text-primary">
                  <indicator.icon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{indicator.title}</h3>
                  <p className="text-sm text-muted-foreground">{indicator.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Category Filter */}
      <section className="py-6 border-b border-border">
        <div className="container mx-auto px-4 lg:px-8">
          <CategoryFilter
            categories={categories}
            activeCategory={activeCategory}
            onCategoryChange={setActiveCategory}
          />
        </div>
      </section>

      {/* Featured Dealers */}
      {featuredDealers.length > 0 && (
        <section className="py-12">
          <div className="container mx-auto px-4 lg:px-8">
            <h2 className="font-display text-2xl font-bold text-foreground mb-8">Editor's Choice</h2>
            <div className="grid md:grid-cols-2 gap-6">
              {featuredDealers.map((dealer) => (
                <DealerCard key={dealer.name} {...dealer} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* All Dealers */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">
            {activeCategory === "All" ? "All Dealers" : activeCategory}
            <span className="text-muted-foreground font-normal ml-2">({otherDealers.length})</span>
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {otherDealers.map((dealer) => (
              <DealerCard key={dealer.name} {...dealer} />
            ))}
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="py-8 bg-card border-t border-border">
        <div className="container mx-auto px-4 lg:px-8">
          <p className="text-sm text-muted-foreground text-center">
            <strong>Affiliate Disclosure:</strong> We may earn a commission when you use our links to make a purchase. This does not affect our editorial integrity or the dealers we recommend. See our{" "}
            <a href="/affiliate-disclosure" className="text-primary hover:underline">
              full disclosure
            </a>
            .
          </p>
        </div>
      </section>
    </PageLayout>
  );
}
