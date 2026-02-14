import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";

interface Breadcrumb {
  label: string;
  href?: string;
}

interface PageHeroProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: Breadcrumb[];
  badge?: string;
  children?: React.ReactNode;
}

export function PageHero({ title, subtitle, breadcrumbs, badge, children }: PageHeroProps) {
  return (
    <section className="bg-gradient-hero text-silver-light py-12 lg:py-16">
      <div className="container mx-auto px-4 lg:px-8">
        {/* Breadcrumbs */}
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="mb-6">
            <ol className="flex items-center gap-2 text-sm text-silver/80">
              {breadcrumbs.map((crumb, index) => (
                <li key={index} className="flex items-center gap-2">
                  {crumb.href ? (
                    <Link to={crumb.href} className="hover:text-primary transition-colors">
                      {crumb.label}
                    </Link>
                  ) : (
                    <span className="text-silver-light">{crumb.label}</span>
                  )}
                  {index < breadcrumbs.length - 1 && (
                    <ChevronRight className="h-4 w-4 text-silver/40" />
                  )}
                </li>
              ))}
            </ol>
          </nav>
        )}

        {/* Badge */}
        {badge && (
          <span className="inline-block mb-4 px-3 py-1 text-xs font-semibold uppercase tracking-wider bg-primary/20 text-primary rounded-full">
            {badge}
          </span>
        )}

        {/* Title */}
        <h1 className="font-display text-3xl md:text-4xl lg:text-5xl font-bold mb-4">
          {title}
        </h1>

        {/* Subtitle */}
        {subtitle && (
          <p className="text-lg text-silver max-w-3xl">
            {subtitle}
          </p>
        )}

        {/* Optional children for extra content */}
        {children && <div className="mt-6">{children}</div>}
      </div>
    </section>
  );
}
