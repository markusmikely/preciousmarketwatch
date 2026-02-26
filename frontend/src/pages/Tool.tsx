import { useParams } from "react-router-dom";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { useGraphQL } from "@/hooks/useGraphQL";
import { GET_TOOL_BY_SLUG_QUERY } from "@/queries/tools";
import { EmbedRenderer } from "@/components/tools/EmbedRenderer";
import { ReactToolPlaceholder } from "@/components/tools/ReactToolPlaceholder";
import { DataFetchStateHandler } from "@/components/shared/DataFetchStateHandler";

interface ToolData {
  id: string;
  slug: string;
  title?: string | null;
  content?: string | null;
  excerpt?: string | null;
  toolStatus?: string | null;
  implementation?: string | null;
  embedCode?: string | null;
  reactComponent?: string | null;
  showDisclaimer?: boolean | null;
  disclaimerText?: string | null;
  featuredImage?: { node?: { sourceUrl?: string | null; altText?: string | null } } | null;
}

export default function ToolPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data, loading, error, refetch } = useGraphQL<{ tool?: ToolData | null }>(
    GET_TOOL_BY_SLUG_QUERY,
    { variables: { slug: slug ?? "" }, skip: !slug }
  );

  const tool = data?.tool;

  return (
    <PageLayout>
      <DataFetchStateHandler loading={loading} error={error} onRetry={refetch}>
        {tool && (
          <>
            <PageHero
              title={tool.title ?? "Tool"}
              subtitle={tool.excerpt ?? undefined}
              breadcrumbs={[
                { label: "Home", href: "/" },
                { label: "Tools", href: "/tools" },
                { label: tool.title ?? slug ?? "Tool" },
              ]}
            />

            <section className="py-12">
              <div className="container mx-auto px-4 lg:px-8 max-w-4xl">
                {tool.implementation === "embed" && tool.embedCode && (
                  <EmbedRenderer html={tool.embedCode} />
                )}
                {tool.implementation === "custom-react" && (
                  <ReactToolPlaceholder tool={{ title: tool.title, excerpt: tool.excerpt }} />
                )}
                {tool.implementation === "shortcode" && (
                  <ReactToolPlaceholder tool={{ title: tool.title, excerpt: tool.excerpt }} />
                )}
                {!tool.implementation && (
                  <ReactToolPlaceholder tool={{ title: tool.title, excerpt: tool.excerpt }} />
                )}

                {tool.showDisclaimer && (
                  <div className="mt-8 rounded-lg border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
                    {tool.disclaimerText ? (
                      <div dangerouslySetInnerHTML={{ __html: tool.disclaimerText }} />
                    ) : (
                      <p>
                        This tool is for informational purposes only and does not constitute investment advice.
                        Past performance is not indicative of future results.
                      </p>
                    )}
                  </div>
                )}
              </div>
            </section>
          </>
        )}
      </DataFetchStateHandler>
    </PageLayout>
  );
}
