import { ExternalLink, Star, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { addUtmParams, trackAffiliateClick } from "@/lib/affiliate";

interface AffiliateProductCardProps {
  name: string;
  description: string;
  price: string;
  originalPrice?: string;
  dealer: string;
  rating: number;
  image: string;
  href: string;
  badge?: string;
  features?: string[];
}

export function AffiliateProductCard({
  name,
  description,
  price,
  originalPrice,
  dealer,
  rating,
  image,
  href,
  badge,
  features = [],
}: AffiliateProductCardProps) {
  const handleClick = () => {
    trackAffiliateClick(dealer, name);
  };

  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden hover:border-primary/50 hover:shadow-lg transition-all duration-300">
      <div className="relative aspect-square overflow-hidden bg-muted">
        <img src={image} alt={name} className="w-full h-full object-cover" />
        {badge && (
          <Badge className="absolute top-3 left-3 bg-primary text-primary-foreground">
            {badge}
          </Badge>
        )}
      </div>
      <div className="p-4">
        <div className="flex items-center gap-1 mb-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star
              key={i}
              className={`h-3 w-3 ${
                i < Math.floor(rating) ? "fill-primary text-primary" : "text-muted"
              }`}
            />
          ))}
          <span className="text-xs text-muted-foreground ml-1">({rating})</span>
        </div>
        <h3 className="font-semibold text-foreground mb-1 line-clamp-2">{name}</h3>
        <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{description}</p>
        
        {features.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {features.slice(0, 2).map((feature) => (
              <span key={feature} className="flex items-center gap-1 text-xs text-muted-foreground">
                <Shield className="h-3 w-3 text-success" />
                {feature}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-baseline gap-2 mb-3">
          <span className="font-display text-xl font-bold text-foreground">{price}</span>
          {originalPrice && (
            <span className="text-sm text-muted-foreground line-through">{originalPrice}</span>
          )}
        </div>
        
        <p className="text-xs text-muted-foreground mb-3">via {dealer}</p>
        
        <Button
          asChild
          className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
          size="sm"
          onClick={handleClick}
        >
          <a href={addUtmParams(href, "pmw", "product", "article_embed")} target="_blank" rel="noopener noreferrer">
            View Deal
            <ExternalLink className="ml-2 h-3 w-3" />
          </a>
        </Button>
      </div>
    </div>
  );
}
