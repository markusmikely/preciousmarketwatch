import { useGraphQL } from "@/hooks/useGraphQL";
import { GET_PAGE_QUERY } from "@/queries/pages";
import { PageBuilder } from "@/components/pagebuilder/PageBuilder";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { DataFetchStateHandler } from "@/components/shared/DataFetchStateHandler";

interface CmsPageProps {
  slug: string;
  fallback?: React.ReactNode;
  breadcrumbs?: { label: string; href?: string }[];
}

export function CmsPage({ slug, fallback, breadcrumbs = [] }: CmsPageProps) {
  const { data, loading, error } = useGraphQL(GET_PAGE_QUERY, {
    variables: { slug: slug.startsWith("/") ? slug : `/${slug}` },
  });

  if (loading) {
    return (
      <PageLayout>
        <div className="container mx-auto px-4 py-16">
          <DataFetchStateHandler loading={true} />
        </div>
      </PageLayout>
    );
  }

  if (error || !data?.page) {
    if (fallback) return <>{fallback}</>;
    return (
      <PageLayout>
        <div className="container mx-auto px-4 py-16">
          <DataFetchStateHandler error={error ?? new Error("Page not found")} />
        </div>
      </PageLayout>
    );
  }

  const page = data.page as {
    title?: string;
    slug?: string;
    breadcrumbLabel?: string | null;
    pageSections?: { sections?: unknown[] } | null;
  };
  const sections = page.pageSections?.sections ?? [];
  const hasSections = Array.isArray(sections) && sections.length > 0;

  if (!hasSections && fallback) {
    return <>{fallback}</>;
  }

  return (
    <PageLayout showTicker={slug === "home" || slug === "/"}>
      {hasSections ? (
        <PageBuilder sections={sections} page={page} />
      ) : (
        fallback ?? (
          <PageHero title={page.title ?? ""} breadcrumbs={breadcrumbs} />
        )
      )}
    </PageLayout>
  );
}
