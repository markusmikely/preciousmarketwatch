import { Star, ExternalLink, Shield, Award } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { addUtmParams, trackAffiliateClick } from "@/lib/affiliate";

interface DealerCardProps {
  name: string;
  description: string;
  rating: number;
  reviews: number;
  categories: string[];
  features: string[];
  logo: string;
  href: string;
  featured?: boolean;
}

export function DealerCard({
  name,
  description,
  rating,
  reviews,
  categories,
  features,
  logo,
  href,
  featured = false,
}: DealerCardProps) {
  const handleClick = () => {
    trackAffiliateClick(name, categories.join(", "));
  };

  return (
    <div
      className={`bg-card rounded-xl border p-6 transition-all duration-300 hover:shadow-lg ${
        featured ? "border-primary shadow-gold" : "border-border hover:border-primary/50"
      }`}
    >
      {featured && (
        <div className="flex items-center gap-2 mb-4">
          <Award className="h-5 w-5 text-primary" />
          <span className="text-sm font-semibold text-primary">Editor's Choice</span>
        </div>
      )}

      <div className="flex items-start gap-4 mb-4">
        <div className="h-16 w-16 rounded-lg bg-muted flex items-center justify-center overflow-hidden">
          <img src={logo} alt={name} className="h-full w-full object-contain p-2" />
        </div>
        <div className="flex-1">
          <h3 className="font-display text-lg font-semibold text-foreground">{name}</h3>
          <div className="flex items-center gap-2 mt-1">
            <div className="flex items-center gap-1">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={`h-4 w-4 ${
                    i < Math.floor(rating) ? "fill-primary text-primary" : "text-muted"
                  }`}
                />
              ))}
            </div>
            <span className="text-sm font-medium text-foreground">{rating}</span>
            <span className="text-sm text-muted-foreground">({reviews} reviews)</span>
          </div>
        </div>
      </div>

      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">{description}</p>

      <div className="flex flex-wrap gap-2 mb-4">
        {categories.map((category) => (
          <Badge key={category} variant="secondary">
            {category}
          </Badge>
        ))}
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        {features.map((feature) => (
          <div key={feature} className="flex items-center gap-1 text-xs text-muted-foreground">
            <Shield className="h-3 w-3 text-success" />
            {feature}
          </div>
        ))}
      </div>

      <Button 
        asChild 
        className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
        onClick={handleClick}
      >
        <a href={addUtmParams(href, "pmw", "dealer", "dealer_card")} target="_blank" rel="noopener noreferrer">
          Visit Dealer
          <ExternalLink className="ml-2 h-4 w-4" />
        </a>
      </Button>
    </div>
  );
}
