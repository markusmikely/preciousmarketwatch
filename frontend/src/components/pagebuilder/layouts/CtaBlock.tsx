import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import type { PageSection } from "../PageBuilder";

interface CtaBlockSectionData {
  variant?: "light" | "dark" | string | null;
  heading?: string | null;
  body?: string | null;
  buttonLabel?: string | null;
  buttonUrl?: string | null;
}

export function CtaBlock({ section }: { section: PageSection }) {
  const data = section as CtaBlockSectionData;
  const isLight = data.variant === "light";

  return (
    <section
      className={`py-16 ${isLight ? "bg-background text-foreground" : "bg-gradient-hero"}`}
    >
      <div className="container mx-auto px-4 lg:px-8 text-center">
        {data.heading && (
          <h2 className={`font-display text-3xl font-bold mb-4 ${isLight ? "text-foreground" : "text-silver-light"}`}>
            {data.heading}
          </h2>
        )}
        {data.body && (
          <div
            className={`max-w-2xl mx-auto mb-8 prose max-w-none ${isLight ? "prose-foreground prose-p:text-muted-foreground" : "prose-invert prose-p:text-silver"}`}
            dangerouslySetInnerHTML={{ __html: data.body }}
          />
        )}
        {data.buttonLabel && data.buttonUrl && (
          data.buttonUrl.startsWith("/") ? (
            <Button asChild size="lg" className={isLight ? "bg-primary text-primary-foreground hover:bg-primary/90" : "bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold"}>
              <Link to={data.buttonUrl}>{data.buttonLabel}</Link>
            </Button>
          ) : (
            <Button asChild size="lg" className={isLight ? "bg-primary text-primary-foreground hover:bg-primary/90" : "bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold"}>
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
