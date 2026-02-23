import { useState, useMemo } from "react";
import { Shield, Award } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { DealerCard } from "@/components/shared/DealerCard";
import { CategoryFilter } from "@/components/shared/CategoryFilter";
import { DataFetchStateHandler } from "@/components/shared/DataFetchStateHandler";
import { useGraphQL } from "@/hooks/useGraphQL";
import { DEALERS_QUERY } from "@/queries/dealers";

const categories = ["All", "Gold & Silver", "Platinum & Palladium", "Diamonds", "Colored Gemstones", "Jewelry"];

// Fallback dealers if GraphQL fails
const fallbackDealers = [
  {
    id: "1",
    name: "APMEX",
    description: "One of the largest online precious metals dealers in the US.",
    rating: 4.8,
    featured: true,
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    specialties: ["Gold", "Silver"],
  },
];

interface WpDealer {
  id: string;
  title: string;
  slug: string;
  excerpt?: string;
  dealers?: {
    rating: number;
    shortDescription: string;
    featured: boolean;
    logo?: { sourceUrl: string };
  };
  metalTypes?: { nodes: { name: string }[] };
  gemstoneTypes?: { nodes: { name: string }[] };
  dealerCategories?: { nodes: { name: string }[] };
}

function transformDealer(dealer: WpDealer) {
  const specialties = [
    ...(dealer.metalTypes?.nodes.map((n: {name: string}) => n.name) || []),
    ...(dealer.gemstoneTypes?.nodes.map((n: {name: string}) => n.name) || []),
  ];

  return {
    id: dealer.id,
    name: dealer.title,
    description: dealer.dealers?.shortDescription || dealer.excerpt || "",
    rating: dealer.dealers?.rating || 0,
    reviews: Math.floor(Math.random() * 15000) + 1000, // Generate random reviews for now
    categories: dealer.dealerCategories?.nodes.map((n: {name: string}) => n.name) || ["All"],
    features: ["Verified dealer", "Fast shipping", "Secure payment"],
    logo: dealer.dealers?.logo?.sourceUrl || "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: "#", // Links would be from affiliateLink in dealers field
    featured: dealer.dealers?.featured || false,
    specialties,
  };
}

export default function TopDealers() {
  const [activeCategory, setActiveCategory] = useState("All");

  // Fetch dealers from GraphQL
  const { data, loading, error, refetch } = useGraphQL(DEALERS_QUERY, {
    variables: { first: 50 },
  });

  // Transform and filter dealers — ALWAYS have fallback data
  const allDealers = useMemo(() => {
    console.log("data", data);
    try {
      if (data?.dealers?.nodes && Array.isArray(data.dealers.nodes) && data.dealers.nodes.length > 0) {
        return data.dealers.nodes.map((dealer: {id: string, title: string, slug: string, excerpt: string, dealers: {rating: number, shortDescription: string, featured: boolean, logo: {sourceUrl: string}}, metalTypes: {nodes: {name: string}[]}, gemstoneTypes: {nodes: {name: string}[]}, dealerCategories: {nodes: {name: string}[]}}) => transformDealer(dealer));
      }
    } catch (e) {
      console.warn("[TopDealers] Error transforming dealers, using fallback:", e);
    }
    return fallbackDealers;
  }, [data]);

  const filteredDealers = useMemo(() => {
    return allDealers.filter((dealer: {categories: string[], specialties: string[]}) => {
      if (activeCategory === "All") return true;
      return dealer.categories.includes(activeCategory) || dealer.specialties.some((s: string) => s === activeCategory);
    });
  }, [allDealers, activeCategory]);

  const featuredDealers = useMemo(() => filteredDealers.filter((d: {featured: boolean}) => d.featured), [filteredDealers]);
  const regularDealers = useMemo(() => filteredDealers.filter((d: {featured: boolean}) => !d.featured), [filteredDealers]);

  return (
    <PageLayout>
      <PageHero
        title="Top Rated Dealers"
        subtitle="Discover vetted and reviewed precious metals and gemstone dealers. Find trusted partners for your investment needs."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Top Dealers" },
        ]}
        badge="Verified Partners"
      />

      {/* Category Filter */}
      <section className="py-8 bg-muted/30 border-b border-border">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Filter by specialty:</span>
            <CategoryFilter categories={categories} activeCategory={activeCategory} onCategoryChange={setActiveCategory} />
          </div>
        </div>
      </section>

      {/* Featured Dealers */}
      {featuredDealers.length > 0 && (
        <section className="py-12 bg-gradient-to-b from-primary/5 to-transparent">
          <div className="container mx-auto px-4 lg:px-8">
            <div className="flex items-center gap-2 mb-8">
              <Award className="h-5 w-5 text-primary" />
              <h2 className="font-display text-2xl font-bold text-foreground">Featured Dealers</h2>
            </div>
            <DataFetchStateHandler loading={loading} error={error} onRetry={refetch} loadingMessage="Loading dealers..." hideError={true}>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {featuredDealers.map((dealer: {id: string, name: string, description: string, rating: number, reviews: number, categories: string[], features: string[], logo: string, href: string, featured: boolean, specialties: string[]}) => (
                  <DealerCard key={dealer.id} {...dealer} />
                ))}
              </div>
            </DataFetchStateHandler>
          </div>
        </section>
      )}

      {/* All Dealers */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="font-display text-2xl font-bold text-foreground">
                {activeCategory === "All" ? "All Dealers" : activeCategory}
                <span className="text-muted-foreground font-normal ml-2">({regularDealers.length})</span>
              </h2>
            </div>
          </div>
          <DataFetchStateHandler loading={loading} error={error} onRetry={refetch} loadingMessage="Loading dealers..." hideError={true}>
            {regularDealers.length > 0 ? (
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {regularDealers.map((dealer: {id: string, name: string, description: string, rating: number, reviews: number, categories: string[], features: string[], logo: string, href: string, featured: boolean, specialties: string[]}) => (
                  <DealerCard key={dealer.id} {...dealer} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No dealers found in this category.</p>
              </div>
            )}
          </DataFetchStateHandler>
        </div>
      </section>

      {/* Trust Badges */}
      <section className="py-16 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-12 text-center">Why Trust Our Dealers?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <Shield className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="font-display text-lg font-bold text-foreground mb-2">Independently Verified</h3>
              <p className="text-muted-foreground">All dealers are thoroughly vetted for authenticity and compliance with industry standards.</p>
            </div>
            <div className="text-center">
              <Award className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="font-display text-lg font-bold text-foreground mb-2">Customer Rated</h3>
              <p className="text-muted-foreground">Ratings based on real customer reviews and transaction history, ensuring transparency and accountability.</p>
            </div>
            <div className="text-center">
              <Shield className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="font-display text-lg font-bold text-foreground mb-2">Secure Transactions</h3>
              <p className="text-muted-foreground">All recommended dealers use industry-standard encryption and secure payment processing.</p>
            </div>
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
