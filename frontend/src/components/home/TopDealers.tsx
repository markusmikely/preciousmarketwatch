import { Link } from "react-router-dom";
import { ArrowRight, Star, Shield, CheckCircle2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Static fallback — shown while WP data loads or if no dealers exist yet
const FALLBACK_DEALERS = [
  {
    id: "1",
    name: "Augusta Precious Metals",
    description: "Specialist in gold and silver IRAs with one of the most lucrative affiliate structures in the space.",
    rating: 4.0,
    featured: true,
    specialties: ["Gold", "Silver"],
  },
  {
    id: "2",
    name: "GoldenCrest Metals",
    description: "Premium precious metals dealer offering some of the highest commissions in the industry.",
    rating: 5.0,
    featured: true,
    specialties: ["Gold", "Silver", "Platinum", "Palladium"],
  },
  {
    id: "3",
    name: "Blue Nile",
    description: "The world's largest online diamond retailer with exceptional brand recognition and high AOV.",
    rating: 4.0,
    featured: true,
    specialties: ["Diamonds", "Gemstones"],
  },
  {
    id: "4",
    name: "James Allen",
    description: "Premium diamond retailer famous for 360° viewing technology and high average order values.",
    rating: 4.0,
    featured: true,
    specialties: ["Diamonds", "Gemstones"],
  },
];

interface WpDealer {
  id: string;
  title: string;
  dealers: {
    rating: number;
    shortDescription: string;
    featured: boolean;
    affiliateLink: string;
    logo?: { sourceUrl: string; altText: string };
  };
  metalTypes?: { nodes: { name: string }[] };
  gemstoneTypes?: { nodes: { name: string }[] };
  dealerCategories?: { nodes: { name: string }[] };
}

interface TopDealersProps {
  dealers?: WpDealer[];
}

export function TopDealers({ dealers: wpDealers }: TopDealersProps) {

  // Map WP data to display shape, fall back to static if empty
  const dealers = wpDealers && wpDealers.length > 0
    ? wpDealers.map( d => ({
        id: d.id,
        name: d.title,
        description: d.dealers?.shortDescription || '',
        rating: d.dealers?.rating || 0,
        featured: d.dealers?.featured || false,
        affiliateLink: d.dealers?.affiliateLink || '#',
        logo: d.dealers?.logo?.sourceUrl || null,
        specialties: [
          ...( d.metalTypes?.nodes.map( n => n.name ) || [] ),
          ...( d.gemstoneTypes?.nodes.map( n => n.name ) || [] ),
        ],
      }))
    : FALLBACK_DEALERS;

  return (
    <section className="py-16 lg:py-24 bg-muted/50">
      <div className="container mx-auto px-4 lg:px-8">
        {/* Section Header */}
        <div className="flex items-center justify-between mb-10">
          <div>
            <h2 className="font-display text-3xl font-bold text-foreground lg:text-4xl">
              Top Rated Dealers
            </h2>
            <p className="mt-2 text-muted-foreground">
              Vetted and reviewed precious metals and gemstone dealers
            </p>
          </div>
          <Link
            to="/top-dealers"
            className="hidden sm:flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
          >
            View all dealers
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Dealers Grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {dealers.map( ( dealer ) => (
            <Card key={dealer.id} className="group border-border bg-card hover:shadow-lg hover:border-primary/30 transition-all duration-300">
              <CardContent className="p-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted font-display text-lg font-bold text-primary overflow-hidden">
                    {( dealer as any ).logo
                      ? <img src={( dealer as any ).logo} alt={dealer.name} className="h-full w-full object-contain" />
                      : dealer.name.charAt( 0 )
                    }
                  </div>
                  {dealer.featured && (
                    <Badge className="bg-primary/10 text-primary hover:bg-primary/20">
                      Featured
                    </Badge>
                  )}
                </div>

                {/* Name */}
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-semibold text-card-foreground group-hover:text-primary transition-colors">
                    {dealer.name}
                  </h3>
                  <CheckCircle2 className="h-4 w-4 text-success flex-shrink-0" />
                </div>

                {/* Description */}
                <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                  {dealer.description}
                </p>

                {/* Rating */}
                {dealer.rating > 0 && (
                  <div className="flex items-center gap-2 mb-4">
                    <Star className="h-4 w-4 fill-primary text-primary" />
                    <span className="font-semibold text-card-foreground">{dealer.rating.toFixed(1)}</span>
                  </div>
                )}

                {/* Specialties */}
                <div className="flex flex-wrap gap-1.5">
                  {dealer.specialties.slice( 0, 3 ).map( ( specialty ) => (
                    <Badge key={specialty} variant="secondary" className="text-xs bg-muted text-muted-foreground">
                      {specialty}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Trust badge */}
        <div className="mt-12 text-center">
          <div className="inline-flex items-center gap-2 rounded-lg bg-card border border-border px-6 py-4">
            <Shield className="h-5 w-5 text-primary" />
            <span className="text-sm text-muted-foreground">
              All dealers are independently verified for authenticity and customer service
            </span>
          </div>
        </div>

        <Link
          to="/top-dealers"
          className="mt-8 flex sm:hidden items-center justify-center gap-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
        >
          View all dealers
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </section>
  );
}
