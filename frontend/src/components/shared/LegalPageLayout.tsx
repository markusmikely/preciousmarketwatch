import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";

interface LegalPageLayoutProps {
  title: string;
  subtitle?: string;
  lastUpdated?: string;
  children: React.ReactNode;
}

export function LegalPageLayout({
  title,
  subtitle,
  lastUpdated,
  children,
}: LegalPageLayoutProps) {
  return (
    <PageLayout showTicker={false}>
      <PageHero
        title={title}
        subtitle={subtitle}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: title },
        ]}
      />

      <section className="py-12 lg:py-16">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="mx-auto max-w-3xl">
            {lastUpdated && (
              <p className="mb-8 text-sm text-muted-foreground">
                Last updated: {lastUpdated}
              </p>
            )}
            <div className="space-y-6 text-muted-foreground">
              {children}
            </div>
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
