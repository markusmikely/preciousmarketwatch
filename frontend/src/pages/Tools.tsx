import { Link } from "react-router-dom";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { useGraphQL } from "@/hooks/useGraphQL";
import { GET_ALL_TOOLS_QUERY } from "@/queries/tools";
import { DataFetchStateHandler } from "@/components/shared/DataFetchStateHandler";

const TYPE_ORDER = ["calculator", "comparison-table", "portfolio-tracker", "price-chart"];

interface ToolNode {
  id: string;
  slug: string;
  title?: string | null;
  excerpt?: string | null;
  toolStatus?: string | null;
  implementation?: string | null;
  displayOrder?: number | null;
  isFeatured?: boolean | null;
  metalRelevance?: (string | null)[] | null;
  featuredImage?: { node?: { sourceUrl?: string | null; altText?: string | null } } | null;
  toolTypes?: { nodes?: { name?: string | null; slug?: string | null }[] } | null;
}

function groupToolsByType(nodes: ToolNode[]) {
  const live = nodes.filter((t) => t.toolStatus === "live");
  live.sort((a, b) => (a.displayOrder ?? 99) - (b.displayOrder ?? 99));
  const grouped: Record<string, ToolNode[]> = {};
  live.forEach((tool) => {
    const type = tool.toolTypes?.nodes?.[0]?.slug ?? "other";
    if (!grouped[type]) grouped[type] = [];
    grouped[type].push(tool);
  });
  return grouped;
}

export default function ToolsPage() {
  const { data, loading, error, refetch } = useGraphQL<{ tools?: { nodes?: ToolNode[] } }>(
    GET_ALL_TOOLS_QUERY,
    { variables: { first: 50 } }
  );

  const nodes = data?.tools?.nodes ?? [];
  const featured = nodes.filter((t) => t.toolStatus === "live" && t.isFeatured);
  featured.sort((a, b) => (a.displayOrder ?? 99) - (b.displayOrder ?? 99));
  const grouped = groupToolsByType(nodes);
  const orderedGroupSlugs = TYPE_ORDER.filter((t) => grouped[t]?.length > 0);

  return (
    <PageLayout>
      <PageHero
        title="Precious Metals Tools"
        subtitle="Free calculators, trackers and price tools for gold, silver and platinum investors."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Tools" },
        ]}
      />

      <DataFetchStateHandler loading={loading} error={error} onRetry={refetch}>
        {featured.length > 0 && (
          <section className="py-12 bg-primary/5 border-y border-border">
            <div className="container mx-auto px-4 lg:px-8">
              <h2 className="font-display text-xl font-bold text-foreground mb-6">Featured tools</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {featured.map((tool) => (
                  <Link
                    key={tool.id}
                    to={`/tools/${tool.slug}`}
                    className="block rounded-xl border border-border bg-card p-6 hover:border-primary/50 hover:shadow-md transition-all"
                  >
                    {tool.featuredImage?.node?.sourceUrl && (
                      <img
                        src={tool.featuredImage.node.sourceUrl}
                        alt={tool.featuredImage.node.altText ?? ""}
                        className="w-full h-32 object-cover rounded-lg mb-4"
                      />
                    )}
                    <h3 className="font-display font-semibold text-foreground">{tool.title}</h3>
                    {tool.excerpt && (
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{tool.excerpt}</p>
                    )}
                    <span className="inline-block mt-3 text-sm font-medium text-primary">
                      Use tool →
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          </section>
        )}

        <section className="py-16">
          <div className="container mx-auto px-4 lg:px-8">
            {orderedGroupSlugs.map((typeSlug) => {
              const tools = grouped[typeSlug] ?? [];
              const typeName = tools[0]?.toolTypes?.nodes?.[0]?.name ?? typeSlug;
              return (
                <div key={typeSlug} id={typeSlug} className="mb-12 scroll-mt-8">
                  <h2 className="font-display text-2xl font-bold text-foreground mb-6">{typeName}</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {tools.map((tool) => {
                      const isComingSoon = tool.toolStatus === "coming-soon";
                      const metals = (tool.metalRelevance ?? []).filter(Boolean).join(" · ") || "All";
                      const card = (
                        <>
                          {tool.featuredImage?.node?.sourceUrl && (
                            <img
                              src={tool.featuredImage.node.sourceUrl}
                              alt=""
                              className="w-full h-36 object-cover rounded-t-xl"
                            />
                          )}
                          <div className="p-5">
                            {isComingSoon && (
                              <span className="inline-block rounded bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground mb-2">
                                Coming soon
                              </span>
                            )}
                            <h3 className="font-display font-semibold text-foreground">{tool.title}</h3>
                            {tool.excerpt && (
                              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{tool.excerpt}</p>
                            )}
                            <p className="text-xs text-muted-foreground mt-2">{metals}</p>
                            {!isComingSoon && (
                              <span className="inline-block mt-3 text-sm font-medium text-primary">
                                Use tool →
                              </span>
                            )}
                          </div>
                        </>
                      );
                      return isComingSoon ? (
                        <div
                          key={tool.id}
                          className="rounded-xl border border-border bg-card overflow-hidden opacity-80"
                        >
                          {card}
                        </div>
                      ) : (
                        <Link
                          key={tool.id}
                          to={`/tools/${tool.slug}`}
                          className="block rounded-xl border border-border bg-card overflow-hidden hover:border-primary/50 hover:shadow-md transition-all"
                        >
                          {card}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              );
            })}
            {orderedGroupSlugs.length === 0 && !loading && (
              <p className="text-muted-foreground text-center py-12">No tools available yet.</p>
            )}
          </div>
        </section>
      </DataFetchStateHandler>
    </PageLayout>
  );
}
