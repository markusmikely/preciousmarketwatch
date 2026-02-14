import { Link } from "react-router-dom";
import { ArrowRight, TrendingUp, TrendingDown, BarChart3, Shield, Award, Coins } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { DealerCard } from "@/components/shared/DealerCard";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

const priceHistory = [
  { date: "Jan", price: 2050 },
  { date: "Feb", price: 2020 },
  { date: "Mar", price: 2180 },
  { date: "Apr", price: 2320 },
  { date: "May", price: 2380 },
  { date: "Jun", price: 2340 },
  { date: "Jul", price: 2420 },
  { date: "Aug", price: 2510 },
  { date: "Sep", price: 2580 },
  { date: "Oct", price: 2650 },
  { date: "Nov", price: 2620 },
  { date: "Dec", price: 2634 },
];

const articles = [
  {
    title: "Gold ETFs vs Physical Gold: Which is Right for You?",
    excerpt: "A comprehensive comparison of gold investment vehicles, including costs, liquidity, and storage considerations.",
    category: "Investment Guide",
    author: "Michael Chen",
    date: "Dec 9, 2024",
    readTime: "7 min read",
    image: "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80",
    href: "/articles/gold-etfs-vs-physical",
  },
  {
    title: "Understanding Gold Purity: 24K, 22K, and 18K Explained",
    excerpt: "Everything you need to know about gold karats, hallmarks, and how purity affects value and durability.",
    category: "Education",
    author: "Sarah Williams",
    date: "Dec 8, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1624365168968-f283d506c6b6?w=800&q=80",
    href: "/articles/gold-purity-explained",
  },
  {
    title: "Gold Coins vs Gold Bars: A Complete Buying Guide",
    excerpt: "Learn the pros and cons of investing in gold coins versus gold bars, including premiums and resale value.",
    category: "Buying Guide",
    author: "David Park",
    date: "Dec 7, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1579532536935-619928decd08?w=800&q=80",
    href: "/articles/gold-coins-vs-bars",
  },
];

const dealers = [
  {
    name: "APMEX",
    description: "One of the largest online precious metals dealers with extensive gold selection.",
    rating: 4.8,
    reviews: 12450,
    categories: ["Gold Bars", "Gold Coins", "Bullion"],
    features: ["Free shipping $199+", "Price match guarantee", "Secure storage"],
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: "https://apmex.com",
    featured: true,
  },
  {
    name: "JM Bullion",
    description: "Trusted dealer offering competitive prices on gold products.",
    rating: 4.7,
    reviews: 8920,
    categories: ["Gold", "Silver", "Platinum"],
    features: ["Low premiums", "Fast shipping", "IRA eligible"],
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: "https://jmbullion.com",
    featured: false,
  },
];

const investmentOptions = [
  { name: "Physical Gold", icon: Coins, description: "Bars and coins for direct ownership" },
  { name: "Gold ETFs", icon: BarChart3, description: "Exchange-traded funds tracking gold prices" },
  { name: "Gold Mining Stocks", icon: TrendingUp, description: "Equity in gold mining companies" },
  { name: "Gold IRAs", icon: Shield, description: "Retirement accounts backed by gold" },
];

export default function Gold() {
  return (
    <PageLayout>
      <PageHero
        title="Gold Investment Guide"
        subtitle="Comprehensive analysis, real-time pricing, and expert insights for gold investors. From bullion to ETFs, discover the best ways to invest in gold."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Precious Metals", href: "/precious-metals" },
          { label: "Gold" },
        ]}
        badge="Safe Haven Asset"
      >
        <div className="flex items-center gap-6 mt-6">
          <div className="flex items-center gap-2">
            <span className="text-3xl font-display font-bold text-silver-light">$2,634.20</span>
            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-success/20 text-success text-sm font-medium">
              <TrendingUp className="h-4 w-4" />
              +0.48%
            </span>
          </div>
          <div className="text-silver text-sm">
            <span className="block">24h High: $2,641.80</span>
            <span className="block">24h Low: $2,618.30</span>
          </div>
        </div>
      </PageHero>

      {/* Price Chart */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="bg-card rounded-xl border border-border p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="font-display text-xl font-bold text-foreground">Gold Price History</h2>
                <p className="text-muted-foreground text-sm">USD per troy ounce - 2024 YTD</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">1M</Button>
                <Button variant="outline" size="sm">3M</Button>
                <Button variant="outline" size="sm">6M</Button>
                <Button size="sm" className="bg-primary text-primary-foreground">1Y</Button>
              </div>
            </div>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={priceHistory}>
                  <defs>
                    <linearGradient id="goldGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(43, 74%, 49%)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(43, 74%, 49%)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 87%)" />
                  <XAxis dataKey="date" stroke="hsl(220, 10%, 46%)" fontSize={12} />
                  <YAxis stroke="hsl(220, 10%, 46%)" fontSize={12} domain={['dataMin - 100', 'dataMax + 50']} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(0, 0%, 100%)',
                      border: '1px solid hsl(220, 13%, 87%)',
                      borderRadius: '8px',
                    }}
                    formatter={(value: number) => [`$${value.toFixed(2)}`, 'Gold Price']}
                  />
                  <Area type="monotone" dataKey="price" stroke="hsl(43, 74%, 49%)" fill="url(#goldGradient)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </section>

      {/* Investment Options */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Ways to Invest in Gold</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {investmentOptions.map((option) => (
              <div key={option.name} className="bg-card rounded-xl border border-border p-6 hover:border-primary/50 hover:shadow-lg transition-all duration-300">
                <div className="inline-flex p-3 rounded-lg bg-primary/10 text-primary mb-4">
                  <option.icon className="h-6 w-6" />
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-2">{option.name}</h3>
                <p className="text-sm text-muted-foreground">{option.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Top Dealers */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="font-display text-2xl font-bold text-foreground">Top Gold Dealers</h2>
              <p className="text-muted-foreground mt-1">Vetted and trusted precious metals dealers</p>
            </div>
            <Button variant="outline" asChild>
              <Link to="/top-dealers">
                View all dealers
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {dealers.map((dealer) => (
              <DealerCard key={dealer.name} {...dealer} />
            ))}
          </div>
        </div>
      </section>

      {/* Latest Articles */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-2xl font-bold text-foreground">Gold Investment Guides</h2>
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
          <h2 className="font-display text-2xl font-bold text-silver-light mb-8 text-center">Gold Key Facts</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { label: "Symbol", value: "Au (XAU)" },
              { label: "Standard Purity", value: "99.99% (24K)" },
              { label: "Troy Ounce", value: "31.1035 grams" },
              { label: "Annual Production", value: "~3,000 tonnes" },
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
