import { Link } from "react-router-dom";
import { ArrowRight, TrendingUp, Zap, Factory, Coins, Sun } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { Button } from "@/components/ui/button";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const priceHistory = [
  { date: "Jan", price: 24.2 },
  { date: "Feb", price: 23.8 },
  { date: "Mar", price: 25.1 },
  { date: "Apr", price: 27.5 },
  { date: "May", price: 29.8 },
  { date: "Jun", price: 29.2 },
  { date: "Jul", price: 28.5 },
  { date: "Aug", price: 29.8 },
  { date: "Sep", price: 30.5 },
  { date: "Oct", price: 32.8 },
  { date: "Nov", price: 31.0 },
  { date: "Dec", price: 31.24 },
];

const articles = [
  {
    title: "Silver's Role in the Green Energy Revolution",
    excerpt: "How solar panel demand and electric vehicle production are reshaping the silver market.",
    category: "Market Analysis",
    author: "Jennifer Adams",
    date: "Dec 9, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1589656966895-2f33e7653819?w=800&q=80",
    href: "/articles/silver-green-energy",
  },
  {
    title: "Silver Coins for Investment: Complete Guide",
    excerpt: "From American Eagles to Canadian Maples, discover the best silver coins for your portfolio.",
    category: "Buying Guide",
    author: "Michael Chen",
    date: "Dec 8, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1607292803062-5b3f3d3e5e3a?w=800&q=80",
    href: "/articles/silver-coins-guide",
  },
  {
    title: "Gold-to-Silver Ratio: Trading Strategies",
    excerpt: "Understanding the gold-silver ratio and how to use it for strategic precious metals investing.",
    category: "Strategy",
    author: "David Park",
    date: "Dec 7, 2024",
    readTime: "7 min read",
    image: "https://images.unsplash.com/photo-1624365168968-f283d506c6b6?w=800&q=80",
    href: "/articles/gold-silver-ratio",
  },
];

const demandSectors = [
  { name: "Industrial", percentage: 50, icon: Factory, description: "Electronics, solar, medical" },
  { name: "Investment", percentage: 25, icon: Coins, description: "Bars, coins, ETFs" },
  { name: "Jewelry", percentage: 18, icon: Zap, description: "Silverware, jewelry" },
  { name: "Photography", percentage: 7, icon: Sun, description: "Film and imaging" },
];

export default function Silver() {
  return (
    <PageLayout>
      <PageHero
        title="Silver Investment Guide"
        subtitle="The dual-nature precious metal with both investment appeal and industrial demand. Explore silver market analysis, buying guides, and dealer reviews."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Precious Metals", href: "/precious-metals" },
          { label: "Silver" },
        ]}
        badge="Industrial & Investment"
      >
        <div className="flex items-center gap-6 mt-6">
          <div className="flex items-center gap-2">
            <span className="text-3xl font-display font-bold text-silver-light">$31.24</span>
            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-success/20 text-success text-sm font-medium">
              <TrendingUp className="h-4 w-4" />
              +1.13%
            </span>
          </div>
          <div className="text-silver text-sm">
            <span className="block">Gold/Silver Ratio: 84.3</span>
            <span className="block">Industrial demand: Rising</span>
          </div>
        </div>
      </PageHero>

      {/* Price Chart */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="bg-card rounded-xl border border-border p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="font-display text-xl font-bold text-foreground">Silver Price History</h2>
                <p className="text-muted-foreground text-sm">USD per troy ounce - 2024 YTD</p>
              </div>
            </div>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={priceHistory}>
                  <defs>
                    <linearGradient id="silverGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(210, 11%, 71%)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(210, 11%, 71%)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 87%)" />
                  <XAxis dataKey="date" stroke="hsl(220, 10%, 46%)" fontSize={12} />
                  <YAxis stroke="hsl(220, 10%, 46%)" fontSize={12} domain={['dataMin - 2', 'dataMax + 2']} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(0, 0%, 100%)',
                      border: '1px solid hsl(220, 13%, 87%)',
                      borderRadius: '8px',
                    }}
                    formatter={(value: number) => [`$${value.toFixed(2)}`, 'Silver Price']}
                  />
                  <Area type="monotone" dataKey="price" stroke="hsl(210, 11%, 50%)" fill="url(#silverGradient)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </section>

      {/* Demand Breakdown */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Silver Demand by Sector</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {demandSectors.map((sector) => (
              <div key={sector.name} className="bg-card rounded-xl border border-border p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="inline-flex p-3 rounded-lg bg-secondary/20">
                    <sector.icon className="h-6 w-6 text-foreground" />
                  </div>
                  <span className="text-2xl font-display font-bold text-primary">{sector.percentage}%</span>
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-1">{sector.name}</h3>
                <p className="text-sm text-muted-foreground">{sector.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Articles */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-2xl font-bold text-foreground">Silver Investment Guides</h2>
            <Button variant="outline" asChild>
              <Link to="/market-insights">
                All articles
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {articles.map((article) => (
              <ArticleCard key={article.title} {...article} />
            ))}
          </div>
        </div>
      </section>

      {/* Key Facts */}
      <section className="py-12 bg-gradient-hero">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-silver-light mb-8 text-center">Silver Key Facts</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { label: "Symbol", value: "Ag (XAG)" },
              { label: "Standard Purity", value: "99.9% (.999)" },
              { label: "Troy Ounce", value: "31.1035 grams" },
              { label: "Annual Production", value: "~25,000 tonnes" },
            ].map((fact) => (
              <div key={fact.label} className="text-center">
                <span className="block text-silver text-sm mb-1">{fact.label}</span>
                <span className="font-display text-xl font-bold text-silver-light">{fact.value}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
