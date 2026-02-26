import { useParams, Link } from "react-router-dom";
import { useMemo } from "react";
import { Clock, User, Calendar, Share2, Bookmark, ArrowLeft, ArrowRight, Loader2, AlertCircle } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { AffiliateProductCard } from "@/components/shared/AffiliateProductCard";
import { DealerCard } from "@/components/shared/DealerCard";
import { ArticleNewsletterSignup } from "@/components/shared/ArticleNewsletterSignup";
import { DataFetchStateHandler } from "@/components/shared/DataFetchStateHandler";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useGraphQL } from "@/hooks/useGraphQL";
import { ARTICLE_BY_SLUG, RELATED_ARTICLES } from "@/queries/articles";


// Demo affiliate products - these would come from product catalog
const affiliateProducts = [
  {
    name: "1 oz American Gold Eagle",
    description: "Official US Mint gold bullion coin, .9167 fine gold",
    price: "$2,789",
    originalPrice: "$2,850",
    dealer: "APMEX",
    rating: 4.9,
    image: "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=400&q=80",
    href: "https://apmex.com/product/gold-eagle",
    badge: "Best Seller",
    features: ["IRA Eligible", "Free Shipping"],
  },
  {
    name: "1 oz Gold Bar - PAMP Suisse",
    description: "Lady Fortuna design, 999.9 fine gold with assay certificate",
    price: "$2,720",
    dealer: "JM Bullion",
    rating: 4.8,
    image: "https://images.unsplash.com/photo-1624365168968-f283d506c6b6?w=400&q=80",
    href: "https://jmbullion.com/pamp-gold-bar",
    features: ["Assay Card", "Secure Packaging"],
  },
  {
    name: "1 Carat Round Diamond - VS1/G",
    description: "GIA certified, excellent cut, eye-clean clarity",
    price: "$8,450",
    originalPrice: "$9,200",
    dealer: "Blue Nile",
    rating: 4.7,
    image: "https://images.unsplash.com/photo-1586882829491-b81178aa622e?w=400&q=80",
    href: "https://bluenile.com/diamond",
    badge: "15% Off",
    features: ["GIA Certified", "Free Returns"],
  },
];

const featuredDealer = {
  name: "APMEX",
  description: "One of the largest online precious metals dealers with extensive selection and competitive pricing.",
  rating: 4.8,
  reviews: 12450,
  categories: ["Gold", "Silver", "Platinum"],
  features: ["Free shipping $199+", "Price match guarantee", "IRA eligible"],
  logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
  href: "https://apmex.com",
  featured: true,
};

// Fallback article
const fallbackArticle = {
  title: "Loading article...",
  excerpt: "",
  slug: "",
  content: "<p>Article not found. Please try again.</p>",
  category: "General",
  author: { name: "Editorial Team", role: "Editor", image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&q=80" },
  date: new Date().toLocaleDateString("en-GB", { year: "numeric", month: "long", day: "numeric" }),
  readTime: "5 min read",
  image: "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=1200&q=80",
};

const relatedArticles = [
  {
    title: "Understanding GIA Diamond Certificates",
    excerpt: "How to read and interpret GIA grading reports for informed purchasing decisions.",
    category: "Education",
    author: "Sarah Williams",
    date: "Dec 8, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1599707367072-cd6ada2bc375?w=800&q=80",
    href: "/articles/gia-certificates",
  },
  {
    title: "Diamond Buying Guide: How to Choose the Perfect Stone",
    excerpt: "Expert tips on selecting a diamond that maximizes beauty while staying within budget.",
    category: "Buying Guide",
    author: "Emma Thompson",
    date: "Dec 7, 2024",
    readTime: "8 min read",
    image: "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=800&q=80",
    href: "/articles/diamond-buying-guide",
  },
  {
    title: "Colored Gemstone Investment Trends 2024",
    excerpt: "Which colored stones are gaining investor attention this year.",
    category: "Investment",
    author: "Victoria Sterling",
    date: "Dec 6, 2024",
    readTime: "7 min read",
    image: "https://images.unsplash.com/photo-1551122087-f99a40461414?w=800&q=80",
    href: "/articles/gemstone-trends",
  },
];

export default function Article() {
  const { slug } = useParams<{ slug: string }>();

  // Fetch article by slug
  const { data: articleData, loading: articleLoading, error: articleError, refetch: refetchArticle } = useGraphQL(
    ARTICLE_BY_SLUG,
    {
      variables: { slug: slug || "" },
      skip: !slug,
    }
  );

  // Fetch related articles
  const { data: relatedData, loading: relatedLoading } = useGraphQL(
    RELATED_ARTICLES,
    {
      variables: {
        categorySlug: articleData?.postBy?.categories?.nodes[0]?.slug || "",
        slug: slug || "",
        first: 3,
      },
      skip: !articleData?.postBy?.categories?.nodes[0]?.slug,
    }
  );

  // Safely handle missing article with fallback
  const article = useMemo(() => {
    try {
      if (articleData?.postBy) return articleData.postBy;
    } catch (e) {
      console.warn("[Article] Error parsing article data:", e);
    }
    return fallbackArticle;
  }, [articleData]);

  // Safely map related articles with fallback
  const relatedArticlesList = useMemo(() => {
    try {
      if (relatedData?.posts?.nodes && Array.isArray(relatedData.posts.nodes) && relatedData.posts.nodes.length > 0) {
        return relatedData.posts.nodes.map((post: any) => ({
          id: post.id,
          title: post.title,
          excerpt: post.excerpt,
          slug: post.slug,
          category: post.categories?.nodes[0]?.name || "General",
          author: post.author?.node?.name || "Editorial Team",
          readTime: post.articleMeta?.readTime || "5 min read",
          date: new Date(post.date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }),
          image: post.featuredImage?.node?.sourceUrl || "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80",
          href: `/articles/${post.slug}`,
        }));
      }
    } catch (e) {
      console.warn("[Article] Error mapping related articles:", e);
    }
    return relatedArticles;
  }, [relatedData]);

  return (
    <PageLayout>
      <DataFetchStateHandler loading={articleLoading} error={articleError} onRetry={refetchArticle} hideError={true}>
        {/* Article Header */}
        <header className="bg-gradient-hero py-12 lg:py-16">
          <div className="container mx-auto px-4 lg:px-8">
            <div className="max-w-4xl">
              <Link to="/market-insights" className="inline-flex items-center text-silver hover:text-primary transition-colors mb-6">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Market Insights
              </Link>
              {article.categories && (
                <Badge className="mb-4 bg-primary/20 text-primary">{article.categories.nodes?.[0]?.name || "Article"}</Badge>
              )}
              <h1 className="font-display text-3xl md:text-4xl lg:text-5xl font-bold text-silver-light mb-6">{article.title}</h1>
              <p className="text-lg text-silver mb-8">{article.excerpt}</p>
              <div className="flex flex-wrap items-center gap-6">
                {article.author?.node && (
                  <div className="flex items-center gap-3">
                    <img
                      src={article.author.node.avatar?.url || "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&q=80"}
                      alt={article.author.node.name}
                      className="h-12 w-12 rounded-full object-cover"
                    />
                    <div>
                      <span className="block font-medium text-silver-light">{article.author.node.name}</span>
                      {article.author.node.description && <span className="text-sm text-silver">{article.author.node.description}</span>}
                    </div>
                  </div>
                )}
                <div className="flex items-center gap-4 text-sm text-silver">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {new Date(article.date).toLocaleDateString("en-GB", { year: "numeric", month: "long", day: "numeric" })}
                  </span>
                  {article.articleMeta?.readTime && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {article.articleMeta.readTime}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Featured Image */}
        <div className="container mx-auto px-4 lg:px-8 -mt-6 relative z-10">
          <div className="max-w-4xl">
            <img
              src={article.featuredImage?.node?.sourceUrl || "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=1200&q=80"}
              alt={article.title}
              className="w-full aspect-[16/9] object-cover rounded-xl shadow-lg"
            />
          </div>
        </div>

        {/* Article Content */}
        <article className="py-12">
          <div className="container mx-auto px-4 lg:px-8">
            <div className="grid lg:grid-cols-12 gap-12">
              {/* Main Content */}
              <div className="lg:col-span-8">
                <div
                  className="prose prose-lg max-w-none prose-headings:font-display prose-headings:text-foreground prose-p:text-muted-foreground prose-a:text-primary prose-strong:text-foreground"
                  dangerouslySetInnerHTML={{ __html: article.content }}
                />

                {/* Inline Affiliate Products */}
                <div className="my-12 p-6 bg-muted/30 rounded-xl border border-border">
                  <h3 className="font-display text-xl font-bold text-foreground mb-6">Related Products</h3>
                  <div className="grid md:grid-cols-3 gap-4">
                    {affiliateProducts.map((product) => (
                      <AffiliateProductCard key={product.name} {...product} />
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground mt-4 text-center">*Affiliate links - we may earn a commission at no cost to you</p>
                </div>

                {/* Share Buttons */}
                <div className="flex items-center gap-4 py-8 border-t border-border">
                  <span className="text-sm font-medium text-foreground">Share this article:</span>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Share2 className="h-4 w-4 mr-2" />
                      Share
                    </Button>
                    <Button variant="outline" size="sm">
                      <Bookmark className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                  </div>
                </div>

                {/* Author Bio */}
                {article.author?.node && (
                  <div className="bg-card rounded-xl border border-border p-6 mt-8">
                    <div className="flex items-start gap-4">
                      <img
                        src={article.author.node.avatar?.url || "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&q=80"}
                        alt={article.author.node.name}
                        className="h-16 w-16 rounded-full object-cover"
                      />
                      <div>
                        <h4 className="font-display font-semibold text-foreground">{article.author.node.name}</h4>
                        {article.author.node.description && <span className="text-sm text-primary block mb-2">{article.author.node.description}</span>}
                        <p className="text-sm text-muted-foreground">{article.author.node.description || "Expert contributor providing in-depth analysis."}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Sidebar */}
              <aside className="lg:col-span-4">
                <div className="sticky top-24 space-y-8">
                  {/* Featured Dealer */}
                  <div>
                    <h3 className="font-display text-lg font-bold text-foreground mb-4">Featured Dealer</h3>
                    <DealerCard {...featuredDealer} />
                  </div>

                  {/* Newsletter */}
                  <ArticleNewsletterSignup />

                  {/* Quick Links */}
                  <div className="bg-card rounded-xl border border-border p-6">
                    <h3 className="font-display text-lg font-bold text-foreground mb-4">Quick Links</h3>
                    <ul className="space-y-3">
                      <li>
                        <Link to="/gemstones/diamonds" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                          → Diamond Buying Guide
                        </Link>
                      </li>
                      <li>
                        <Link to="/top-dealers" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                          → Find Trusted Dealers
                        </Link>
                      </li>
                      <li>
                        <Link to="/precious-metals/gold" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                          → Gold Investment Guide
                        </Link>
                      </li>
                    </ul>
                  </div>
                </div>
              </aside>
            </div>
          </div>
        </article>

        {/* Related Articles */}
        <section className="py-12 bg-muted/30">
          <div className="container mx-auto px-4 lg:px-8">
            <div className="flex items-center justify-between mb-8">
              <h2 className="font-display text-2xl font-bold text-foreground">Related Articles</h2>
              <Button variant="outline" asChild>
                <Link to="/market-insights">
                  View all
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
            {relatedLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
              </div>
            ) : (
              <div className="grid md:grid-cols-3 gap-6">
                {relatedArticlesList.map((article: any) => (
                  <ArticleCard key={article.id || article.title} {...article} />
                ))}
              </div>
            )}
          </div>
        </section>
      </DataFetchStateHandler>
    </PageLayout>
  );
}
