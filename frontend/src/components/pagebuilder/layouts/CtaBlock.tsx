import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import type { PageSection } from "../PageBuilder";

interface CtaBlockSectionData {
  heading?: string | null;
  body?: string | null;
  buttonLabel?: string | null;
  buttonUrl?: string | null;
}

export function CtaBlock({ section }: { section: PageSection }) {
  const data = section as CtaBlockSectionData;

  return (
    <section className="py-16 bg-gradient-hero">
      <div className="container mx-auto px-4 lg:px-8 text-center">
        {data.heading && (
          <h2 className="font-display text-3xl font-bold text-silver-light mb-4">{data.heading}</h2>
        )}
        {data.body && <p className="text-silver max-w-2xl mx-auto mb-8">{data.body}</p>}
        {data.buttonLabel && data.buttonUrl && (
          data.buttonUrl.startsWith("/") ? (
            <Button asChild size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold">
              <Link to={data.buttonUrl}>{data.buttonLabel}</Link>
            </Button>
          ) : (
            <Button asChild size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold">
              <a href={data.buttonUrl} target="_blank" rel="noopener noreferrer">
                {data.buttonLabel}
              </a>
            </Button>
          )
        )}
      </div>
    </section>
  );
}
