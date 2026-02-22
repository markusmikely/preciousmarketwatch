import { useParams, Link } from "react-router-dom";
import { Clock, User, Calendar, Share2, Bookmark, ArrowLeft, ArrowRight } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { AffiliateProductCard } from "@/components/shared/AffiliateProductCard";
import { DealerCard } from "@/components/shared/DealerCard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";


// Demo article data - would come from WordPress API
const articleData: Record<string, any> = {
  "lab-vs-natural": {
    title: "Lab-Grown vs Natural Diamonds: Complete Investment Guide",
    excerpt: "Understanding the differences, value propositions, and market dynamics of natural and lab-grown diamonds.",
    category: "Diamonds",
    author: { name: "Emma Thompson", role: "Gemstone Editor", image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&q=80" },
    date: "December 9, 2024",
    readTime: "8 min read",
    image: "https://images.unsplash.com/photo-1586882829491-b81178aa622e?w=1200&q=80",
    content: `
      <p class="lead">The diamond market has undergone a significant transformation with the rise of lab-grown diamonds. Understanding the key differences between natural and lab-grown stones is essential for making informed investment decisions.</p>
      
      <h2>What Are Lab-Grown Diamonds?</h2>
      <p>Lab-grown diamonds are chemically, physically, and optically identical to natural diamonds. They're created using two primary methods: High Pressure High Temperature (HPHT) and Chemical Vapor Deposition (CVD).</p>
      <p>Both processes replicate the conditions under which natural diamonds form, but accomplish in weeks what nature takes billions of years to achieve.</p>
      
      <h2>Price Comparison</h2>
      <p>The most significant difference between lab-grown and natural diamonds is price. Lab-grown diamonds typically cost 70-80% less than their natural counterparts of equivalent quality.</p>
      <p>However, it's important to note that lab-grown diamond prices have been declining rapidly as production technology improves, while natural diamond prices have remained relatively stable.</p>
      
      <h2>Investment Considerations</h2>
      <p>For investment purposes, natural diamonds have historically held value better than lab-grown alternatives. The resale market for lab-grown diamonds is still developing, and their rapid price decline has made them less suitable as investment vehicles.</p>
      <p>Natural diamonds, particularly rare colors and exceptional quality stones, continue to appreciate over time and maintain strong auction results.</p>
      
      <h2>Environmental Impact</h2>
      <p>Lab-grown diamonds are often marketed as more environmentally friendly, though the reality is nuanced. While they don't require mining, the energy-intensive production process has its own environmental footprint.</p>
      
      <h2>Certification and Grading</h2>
      <p>Both natural and lab-grown diamonds are graded using the same 4Cs criteria by major gemological laboratories like GIA. Lab-grown diamonds are clearly identified as such on their certificates.</p>
      
      <h2>The Bottom Line</h2>
      <p>For those prioritizing value and size, lab-grown diamonds offer compelling advantages. For investment purposes and long-term value retention, natural diamonds remain the preferred choice.</p>
    `,
  },
  "gold-new-highs": {
    title: "Gold Reaches New Highs as Inflation Concerns Persist",
    excerpt: "Central bank policies continue to drive investor interest in gold as a hedge against currency devaluation.",
    category: "Gold",
    author: { name: "Michael Chen", role: "Editor-in-Chief", image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&q=80" },
    date: "December 9, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=1200&q=80",
    content: `
      <p class="lead">Gold prices have surged to record levels as persistent inflation and geopolitical uncertainty drive investors toward safe-haven assets.</p>
      
      <h2>Current Market Conditions</h2>
      <p>The precious metal has climbed above $2,600 per ounce, marking a significant milestone for gold investors. This rally has been fueled by a combination of factors including inflation concerns, central bank buying, and geopolitical tensions.</p>
      
      <h2>Central Bank Demand</h2>
      <p>Central banks around the world have been accumulating gold at record rates. China, Russia, and several emerging market central banks have been particularly active buyers, seeking to diversify their reserves away from the US dollar.</p>
      
      <h2>Inflation Hedge</h2>
      <p>With inflation remaining elevated in many developed economies, investors are turning to gold as a traditional store of value. Gold's historical performance during inflationary periods supports its role as an effective hedge.</p>
      
      <h2>Investment Outlook</h2>
      <p>Analysts remain bullish on gold's prospects, with many forecasting prices could reach $3,000 per ounce in the coming years. However, potential headwinds include rising interest rates and a stronger dollar.</p>
    `,
  },
};

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
  const { slug } = useParams();
  const article = articleData[slug || ""] || articleData["lab-vs-natural"];

  return (
    <PageLayout>
      {/* Article Header */}
      <header className="bg-gradient-hero py-12 lg:py-16">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="max-w-4xl">
            <Link to="/market-insights" className="inline-flex items-center text-silver hover:text-primary transition-colors mb-6">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Market Insights
            </Link>
            <Badge className="mb-4 bg-primary/20 text-primary">{article.category}</Badge>
            <h1 className="font-display text-3xl md:text-4xl lg:text-5xl font-bold text-silver-light mb-6">
              {article.title}
            </h1>
            <p className="text-lg text-silver mb-8">{article.excerpt}</p>
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-3">
                <img src={article.author.image} alt={article.author.name} className="h-12 w-12 rounded-full object-cover" />
                <div>
                  <span className="block font-medium text-silver-light">{article.author.name}</span>
                  <span className="text-sm text-silver">{article.author.role}</span>
                </div>
              </div>
              <div className="flex items-center gap-4 text-sm text-silver">
                <span className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {article.date}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {article.readTime}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Featured Image */}
      <div className="container mx-auto px-4 lg:px-8 -mt-6 relative z-10">
        <div className="max-w-4xl">
          <img
            src={article.image}
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
                <p className="text-xs text-muted-foreground mt-4 text-center">
                  *Affiliate links - we may earn a commission at no cost to you
                </p>
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
              <div className="bg-card rounded-xl border border-border p-6 mt-8">
                <div className="flex items-start gap-4">
                  <img src={article.author.image} alt={article.author.name} className="h-16 w-16 rounded-full object-cover" />
                  <div>
                    <h4 className="font-display font-semibold text-foreground">{article.author.name}</h4>
                    <span className="text-sm text-primary block mb-2">{article.author.role}</span>
                    <p className="text-sm text-muted-foreground">
                      Expert in precious metals and gemstone markets with over 10 years of industry experience. 
                      Provides in-depth analysis and buying guides for investors.
                    </p>
                  </div>
                </div>
              </div>
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
                <div className="bg-gradient-hero rounded-xl p-6">
                  <h3 className="font-display text-lg font-bold text-silver-light mb-2">Stay Updated</h3>
                  <p className="text-sm text-silver mb-4">Get weekly market insights delivered to your inbox.</p>
                  <div className="space-y-3">
                    <input
                      type="email"
                      placeholder="Enter your email"
                      className="w-full px-4 py-2 rounded-lg bg-navy border border-silver/30 text-silver-light placeholder:text-silver/60 focus:outline-none focus:border-primary"
                    />
                    <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
                      Subscribe
                    </Button>
                  </div>
                </div>

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
          <div className="grid md:grid-cols-3 gap-6">
            {relatedArticles.map((article) => (
              <ArticleCard key={article.title} {...article} />
            ))}
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
