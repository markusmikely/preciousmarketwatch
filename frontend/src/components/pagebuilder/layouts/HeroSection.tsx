import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import type { PageSection } from "../PageBuilder";

interface Breadcrumb {
  label?: string | null;
  url?: string | null;
}

interface Bookmark {
  label?: string | null;
  url?: string | null;
}

interface HeroSectionData {
  heading?: string | null;
  subheading?: string | null;
  backgroundImage?: { sourceUrl?: string | null; altText?: string | null } | null;
  topicPill?: string | null;
  breadcrumbs?: Breadcrumb[] | null;
  bookmarks?: Bookmark[] | null;
}

export function HeroSection({
  section,
  page,
}: {
  section: PageSection;
  page?: { title?: string; breadcrumbLabel?: string | null } | null;
}) {
  const data = section as HeroSectionData;
  const bg = data.backgroundImage?.sourceUrl;
  const breadcrumbLinks = data.breadcrumbs ?? [];
  const bookmarks = data.bookmarks ?? [];
  const currentPageLabel = page?.breadcrumbLabel || page?.title || "";

  const hasBreadcrumbs = breadcrumbLinks.length > 0 || currentPageLabel;

  return (
    <section
      className="relative overflow-hidden py-12 lg:py-16 bg-gradient-hero"
      style={bg ? { backgroundImage: `url(${bg})`, backgroundSize: "cover", backgroundPosition: "center" } : undefined}
    >
      <div className="absolute inset-0 bg-navy/70" />
      <div className="container relative mx-auto px-4 lg:px-8">
        <div className="max-w-4xl text-left">
          {hasBreadcrumbs && (
            <nav className="mb-6">
              <ol className="flex items-center gap-2 text-sm text-silver/80">
                {breadcrumbLinks.map((crumb, index) => (
                  <li key={index} className="flex items-center gap-2">
                    {crumb.url && crumb.url.startsWith("/") ? (
                      <Link to={crumb.url} className="hover:text-primary transition-colors">
                        {crumb.label ?? ""}
                      </Link>
                    ) : crumb.url ? (
                      <a href={crumb.url} className="hover:text-primary transition-colors" target="_blank" rel="noopener noreferrer">
                        {crumb.label ?? ""}
                      </a>
                    ) : (
                      <span className="text-silver-light">{crumb.label ?? ""}</span>
                    )}
                    <ChevronRight className="h-4 w-4 text-silver/40" />
                  </li>
                ))}
                {currentPageLabel && (
                  <li>
                    <span className="text-silver-light">{currentPageLabel}</span>
                  </li>
                )}
              </ol>
            </nav>
          )}
          {data.topicPill && (
            <span className="inline-block mb-4 px-3 py-1 text-xs font-semibold uppercase tracking-wider bg-primary/20 text-primary rounded-full">
              {data.topicPill}
            </span>
          )}
          {data.heading && (
            <h1 className="font-display text-4xl font-bold tracking-tight text-silver-light sm:text-5xl lg:text-6xl">
              {data.heading}
            </h1>
          )}
          {data.subheading && (
            <p className="mt-6 text-lg leading-relaxed text-silver sm:text-xl">{data.subheading}</p>
          )}
          {bookmarks.length > 0 && (
            <nav className="mt-8 flex flex-wrap gap-4">
              {bookmarks.map((b, i) => {
                if (!b.label) return null;
                const href = b.url ?? "#";
                const isInternal = href.startsWith("/");
                return isInternal ? (
                  <Link
                    key={i}
                    to={href}
                    className="text-sm font-medium text-silver hover:text-primary transition-colors"
                  >
                    {b.label}
                  </Link>
                ) : (
                  <a
                    key={i}
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-silver hover:text-primary transition-colors"
                  >
                    {b.label}
                  </a>
                );
              })}
            </nav>
          )}
        </div>
      </div>
    </section>
  );
}
