import { useParams, Link } from "react-router-dom";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { useGraphQL } from "@/hooks/useGraphQL";
import { GET_NEWS_ARTICLE_BY_SLUG_QUERY } from "@/queries/news";
import { DataFetchStateHandler } from "@/components/shared/DataFetchStateHandler";

export default function NewsArticlePage() {
  const { slug } = useParams<{ slug: string }>();
  const { data, loading, error, refetch } = useGraphQL<{ newsArticle?: any }>(
    GET_NEWS_ARTICLE_BY_SLUG_QUERY,
    { variables: { slug: slug ?? "" }, skip: !slug }
  );

  const article = data?.newsArticle;

  return (
    <PageLayout>
      <DataFetchStateHandler loading={loading} error={error} onRetry={refetch}>
        {article && (
          <>
            <PageHero
              title={article.title ?? ""}
              subtitle={article.excerpt ?? undefined}
              breadcrumbs={[
                { label: "Home", href: "/" },
                { label: "News & Analysis", href: "/news-analysis" },
                { label: article.title ?? slug ?? "Article" },
              ]}
            />
            <section className="py-12">
              <div className="container mx-auto px-4 lg:px-8 max-w-3xl">
                {article.content && (
                  <div
                    className="prose prose-lg max-w-none"
                    dangerouslySetInnerHTML={{ __html: article.content }}
                  />
                )}
                <p className="mt-8">
                  <Link to="/news-analysis" className="text-primary hover:underline">
                    ← Back to News & Analysis
                  </Link>
                </p>
              </div>
            </section>
          </>
        )}
      </DataFetchStateHandler>
    </PageLayout>
  );
}
