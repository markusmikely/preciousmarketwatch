import { useState } from "react";
import { Link } from "react-router-dom";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { DataFetchStateHandler } from "@/components/shared/DataFetchStateHandler";
import { useGraphQL } from "@/hooks/useGraphQL";
import { GET_NEWS_ARTICLES_SIMPLE_QUERY } from "@/queries/news";

interface NewsNode {
  id: string;
  slug: string;
  title?: string | null;
  excerpt?: string | null;
  date?: string | null;
  featuredImage?: { node?: { sourceUrl?: string | null; altText?: string | null } } | null;
  author?: { node?: { name?: string | null } } | null;
  newsCategories?: { nodes?: { name?: string | null; slug?: string | null }[] } | null;
}

function toArticleCard(node: NewsNode, index: number) {
  return {
    id: node.id,
    title: node.title ?? "",
    excerpt: node.excerpt ?? "",
    slug: node.slug,
    category: node.newsCategories?.nodes?.[0]?.name ?? "News",
    author: node.author?.node?.name ?? "Editorial Team",
    readTime: "5 min read",
    date: node.date ? new Date(node.date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "",
    image: node.featuredImage?.node?.sourceUrl ?? "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80",
    href: `/news-analysis/${node.slug}`,
    featured: index === 0,
  };
}

export default function NewsAnalysis() {
  const { data, loading, error, refetch } = useGraphQL<{ newsArticles?: { nodes?: NewsNode[] } }>(
    GET_NEWS_ARTICLES_SIMPLE_QUERY,
    { variables: { first: 50 } }
  );

  const nodes = data?.newsArticles?.nodes ?? [];
  const articles = nodes.map(toArticleCard);
  const featured = articles[0];
  const rest = articles.slice(1);

  return (
    <PageLayout>
      <PageHero
        title="News & Analysis"
        subtitle="Expert analysis, market trends, and investment strategies for precious metals and gemstones."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "News & Analysis" },
        ]}
        badge="Analysis & News"
      />

      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <DataFetchStateHandler loading={loading} error={error} onRetry={refetch}>
            {featured && (
              <div className="mb-10">
                <h2 className="font-display text-xl font-bold text-foreground mb-6">Featured</h2>
                <ArticleCard {...featured} featured />
              </div>
            )}
            <h2 className="font-display text-xl font-bold text-foreground mb-6">
              All Articles <span className="text-muted-foreground font-normal">({rest.length})</span>
            </h2>
            {rest.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {rest.map((article) => (
                  <ArticleCard key={article.id} {...article} />
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">No articles yet.</p>
            )}
          </DataFetchStateHandler>
        </div>
      </section>
    </PageLayout>
  );
}
