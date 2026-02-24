import { Link } from "react-router-dom";
import { ArrowRight, Sparkles, Star, Shield } from "lucide-react";

/** HOME-03: AI dealer reviews — highlights independent, AI-informed dealer verification */
interface WpDealer {
  id: string;
  title: string;
  dealers?: {
    rating?: number;
    shortDescription?: string;
  };
}

interface AIDealerReviewsProps {
  dealers?: WpDealer[] | null;
}

export function AIDealerReviews({ dealers: wpDealers }: AIDealerReviewsProps) {
  const list = wpDealers && wpDealers.length > 0
    ? wpDealers.slice(0, 3).map((d) => ({
        id: d.id,
        name: d.title,
        rating: d.dealers?.rating ?? 0,
        description: d.dealers?.shortDescription ?? "",
      }))
    : [
        { id: "1", name: "Augusta Precious Metals", rating: 4.8, description: "Gold & silver IRA specialist, vetted for transparency." },
        { id: "2", name: "Blue Nile", rating: 4.5, description: "Diamond retailer with independent quality verification." },
        { id: "3", name: "James Allen", rating: 4.6, description: "360° viewing and verified customer reviews." },
      ];

  return (
    <section className="py-16 lg:py-20 bg-background border-t border-border">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="flex flex-col items-center text-center mb-12">
          <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary mb-4">
            <Sparkles className="h-4 w-4" />
            AI-verified reviews
          </div>
          <h2 className="font-display text-3xl font-bold text-foreground lg:text-4xl">
            Independent dealer reviews
          </h2>
          <p className="mt-3 max-w-2xl text-muted-foreground">
            Our dealer ratings are informed by independent research, verification of credentials, and transparent criteria—not paid placement.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-3 max-w-4xl mx-auto mb-10">
          {list.map((dealer) => (
            <div
              key={dealer.id}
              className="rounded-lg border border-border bg-card p-5 text-center hover:border-primary/30 transition-colors"
            >
              <div className="flex items-center justify-center gap-1 mb-2">
                {dealer.rating > 0 && (
                  <>
                    <Star className="h-4 w-4 fill-primary text-primary" />
                    <span className="font-semibold text-foreground">{dealer.rating.toFixed(1)}</span>
                  </>
                )}
              </div>
              <h3 className="font-semibold text-foreground">{dealer.name}</h3>
              {dealer.description && (
                <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{dealer.description}</p>
              )}
            </div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/top-dealers"
            className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            View all dealer reviews
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            to="/editorial-standards"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <Shield className="h-4 w-4" />
            How we review
          </Link>
        </div>
      </div>
    </section>
  );
}
