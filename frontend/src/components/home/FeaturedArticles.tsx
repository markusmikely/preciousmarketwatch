import { Link } from "react-router-dom";
import { ArrowRight, Clock, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

// Static fallback — shown while WP data loads or if no posts exist yet
const FALLBACK_ARTICLES = [
  {
    id: "1",
    title: "Gold Reaches New Highs Amid Global Uncertainty",
    excerpt: "Investors flock to safe-haven assets as geopolitical tensions drive gold prices to record levels.",
    category: "Precious Metals",
    author: "Editorial Team",
    readTime: "5 min read",
    date: "Coming soon",
    image: "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80",
    slug: "gold-new-highs",
    featured: true,
  },
  {
    id: "2",
    title: "Lab-Grown Diamonds: Market Disruption or Investment Opportunity?",
    excerpt: "The lab-grown diamond market continues to reshape traditional gemstone valuations.",
    category: "Gemstones",
    author: "Editorial Team",
    readTime: "7 min read",
    date: "Coming soon",
    image: "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=800&q=80",
    slug: "lab-grown-diamonds",
    featured: false,
  },
  {
    id: "3",
    title: "Silver Industrial Demand Surges with Green Energy Transition",
    excerpt: "Solar panel manufacturing drives unprecedented demand for silver in renewable energy.",
    category: "Market Insights",
    author: "Editorial Team",
    readTime: "4 min read",
    date: "Coming soon",
    image: "https://images.unsplash.com/photo-1624365168968-f283d506c6b6?w=800&q=80",
    slug: "silver-green-energy",
    featured: false,
  },
  {
    id: "4",
    title: "Buying Guide: How to Evaluate Ruby Quality",
    excerpt: "Expert tips on assessing colour, clarity and origin when investing in rubies.",
    category: "Gemstones",
    author: "Editorial Team",
    readTime: "8 min read",
    date: "Coming soon",
    image: "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=800&q=80",
    slug: "ruby-buying-guide",
    featured: false,
  },
];

interface WpPost {
  id: string;
  title: string;
  slug: string;
  date: string;
  excerpt: string;
  featuredImage?: { node: { sourceUrl: string; altText: string } };
  author?: { node: { name: string } };
  categories?: { nodes: { name: string }[] };
  articleMeta?: { readTime: string };
}

interface FeaturedArticlesProps {
  articles?: WpPost[];
}

function formatDate( dateStr: string ): string {
  try {
    return new Date( dateStr ).toLocaleDateString( 'en-GB', {
      day: 'numeric', month: 'short', year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

function stripHtml( html: string ): string {
  return html.replace( /<[^>]*>/g, '' ).trim();
}

export function FeaturedArticles({ articles: wpArticles }: FeaturedArticlesProps) {

  const articles = wpArticles && wpArticles.length > 0
    ? wpArticles.map( ( p, i ) => ({
        id: p.id,
        title: p.title,
        excerpt: stripHtml( p.excerpt || '' ),
        category: p.categories?.nodes[0]?.name || 'General',
        author: p.author?.node?.name || 'Editorial Team',
        readTime: p.articleMeta?.readTime || '5 min read',
        date: formatDate( p.date ),
        image: p.featuredImage?.node?.sourceUrl || FALLBACK_ARTICLES[i % FALLBACK_ARTICLES.length].image,
        slug: p.slug,
        featured: i === 0,
      }))
    : FALLBACK_ARTICLES;

  const mainArticle = articles[0];
  const secondaryArticles = articles.slice( 1 );

  return (
    <section className="py-16 lg:py-24 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        {/* Section Header */}
        <div className="flex items-center justify-between mb-10">
          <div>
            <h2 className="font-display text-3xl font-bold text-foreground lg:text-4xl">
              Latest Insights
            </h2>
            <p className="mt-2 text-muted-foreground">
              Expert analysis and market updates from our editorial team
            </p>
          </div>
          <Link
            to="/market-insights"
            className="hidden sm:flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
          >
            View all articles
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Articles Grid */}
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Main Featured Article */}
          <Card className="group overflow-hidden border-border bg-card hover:shadow-lg transition-shadow">
            <Link to={`/articles/${mainArticle.slug}`}>
              <div className="aspect-[16/10] overflow-hidden">
                <img
                  src={mainArticle.image}
                  alt={mainArticle.title}
                  className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
              </div>
              <CardContent className="p-6">
                <Badge variant="secondary" className="mb-3 bg-primary/10 text-primary hover:bg-primary/20">
                  {mainArticle.category}
                </Badge>
                <h3 className="font-display text-2xl font-bold text-card-foreground group-hover:text-primary transition-colors">
                  {mainArticle.title}
                </h3>
                <p className="mt-3 text-muted-foreground line-clamp-2">
                  {mainArticle.excerpt}
                </p>
                <div className="mt-4 flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <User className="h-4 w-4" />
                    {mainArticle.author}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {mainArticle.readTime}
                  </span>
                </div>
              </CardContent>
            </Link>
          </Card>

          {/* Secondary Articles */}
          <div className="flex flex-col gap-6">
            {secondaryArticles.map( ( article ) => (
              <Card
                key={article.id}
                className="group flex overflow-hidden border-border bg-card hover:shadow-lg transition-shadow"
              >
                <Link to={`/articles/${article.slug}`} className="flex w-full">
                  <div className="aspect-square w-32 flex-shrink-0 overflow-hidden sm:w-40">
                    <img
                      src={article.image}
                      alt={article.title}
                      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                  </div>
                  <CardContent className="flex flex-1 flex-col justify-center p-4">
                    <Badge variant="secondary" className="mb-2 w-fit bg-primary/10 text-primary hover:bg-primary/20 text-xs">
                      {article.category}
                    </Badge>
                    <h3 className="font-semibold text-card-foreground group-hover:text-primary transition-colors line-clamp-2">
                      {article.title}
                    </h3>
                    <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{article.author}</span>
                      <span>·</span>
                      <span>{article.readTime}</span>
                    </div>
                  </CardContent>
                </Link>
              </Card>
            ))}
          </div>
        </div>

        {/* Mobile View All */}
        <Link
          to="/market-insights"
          className="mt-8 flex sm:hidden items-center justify-center gap-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
        >
          View all articles
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </section>
  );
}
