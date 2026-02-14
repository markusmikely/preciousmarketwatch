import { Link } from "react-router-dom";
import { ArrowRight, Star, Shield, CheckCircle2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const dealers = [
  {
    id: 1,
    name: "APMEX",
    description: "America's largest online precious metals dealer with extensive inventory.",
    rating: 4.8,
    reviews: 12450,
    specialties: ["Gold", "Silver", "Platinum"],
    verified: true,
    featured: true,
  },
  {
    id: 2,
    name: "JM Bullion",
    description: "Competitive pricing on bullion with free shipping over $199.",
    rating: 4.7,
    reviews: 8920,
    specialties: ["Gold Coins", "Silver Bars"],
    verified: true,
    featured: false,
  },
  {
    id: 3,
    name: "SD Bullion",
    description: "Low premiums and fast shipping for precious metals investors.",
    rating: 4.6,
    reviews: 6340,
    specialties: ["Bullion", "IRA Eligible"],
    verified: true,
    featured: false,
  },
  {
    id: 4,
    name: "James Allen",
    description: "Leading online diamond retailer with 360° diamond viewing technology.",
    rating: 4.9,
    reviews: 15280,
    specialties: ["Diamonds", "Engagement Rings"],
    verified: true,
    featured: true,
  },
];

export function TopDealers() {
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
          {dealers.map((dealer) => (
            <Card key={dealer.id} className="group border-border bg-card hover:shadow-lg hover:border-primary/30 transition-all duration-300">
              <CardContent className="p-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted font-display text-lg font-bold text-primary">
                    {dealer.name.charAt(0)}
                  </div>
                  {dealer.featured && (
                    <Badge className="bg-primary/10 text-primary hover:bg-primary/20">
                      Featured
                    </Badge>
                  )}
                </div>

                {/* Name & Verified */}
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-semibold text-card-foreground group-hover:text-primary transition-colors">
                    {dealer.name}
                  </h3>
                  {dealer.verified && (
                    <CheckCircle2 className="h-4 w-4 text-success" />
                  )}
                </div>

                {/* Description */}
                <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                  {dealer.description}
                </p>

                {/* Rating */}
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex items-center gap-1">
                    <Star className="h-4 w-4 fill-primary text-primary" />
                    <span className="font-semibold text-card-foreground">{dealer.rating}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    ({dealer.reviews.toLocaleString()} reviews)
                  </span>
                </div>

                {/* Specialties */}
                <div className="flex flex-wrap gap-1.5">
                  {dealer.specialties.map((specialty) => (
                    <Badge key={specialty} variant="secondary" className="text-xs bg-muted text-muted-foreground">
                      {specialty}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* CTA */}
        <div className="mt-12 text-center">
          <div className="inline-flex items-center gap-2 rounded-lg bg-card border border-border px-6 py-4">
            <Shield className="h-5 w-5 text-primary" />
            <span className="text-sm text-muted-foreground">
              All dealers are independently verified for authenticity and customer service
            </span>
          </div>
        </div>

        {/* Mobile View All Link */}
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
