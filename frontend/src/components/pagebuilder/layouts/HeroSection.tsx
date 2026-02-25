import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import type { PageSection } from "../PageBuilder";

interface HeroSectionData {
  heading?: string | null;
  subheading?: string | null;
  backgroundImage?: { sourceUrl?: string | null; altText?: string | null } | null;
  ctaLabel?: string | null;
  ctaUrl?: string | null;
}

export function HeroSection({ section }: { section: PageSection }) {
  const data = section as HeroSectionData;
  const bg = data.backgroundImage?.sourceUrl;

  return (
    <section
      className="relative overflow-hidden py-20 lg:py-32 bg-gradient-hero"
      style={bg ? { backgroundImage: `url(${bg})`, backgroundSize: "cover", backgroundPosition: "center" } : undefined}
    >
      <div className="absolute inset-0 bg-navy/70" />
      <div className="container relative mx-auto px-4 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          {data.heading && (
            <h1 className="font-display text-4xl font-bold tracking-tight text-silver-light sm:text-5xl lg:text-6xl">
              {data.heading}
            </h1>
          )}
          {data.subheading && (
            <p className="mt-6 text-lg leading-relaxed text-silver sm:text-xl">{data.subheading}</p>
          )}
          {data.ctaLabel && data.ctaUrl && (
            <div className="mt-10">
              {data.ctaUrl.startsWith("/") ? (
                <Button asChild size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold">
                  <Link to={data.ctaUrl}>{data.ctaLabel}</Link>
                </Button>
              ) : (
                <Button asChild size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold">
                  <a href={data.ctaUrl} target="_blank" rel="noopener noreferrer">
                    {data.ctaLabel}
                  </a>
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
