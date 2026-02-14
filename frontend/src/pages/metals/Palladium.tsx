import { Link } from "react-router-dom";
import { ArrowRight, TrendingUp, Car, Cpu, Factory, Zap } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { ArticleCard } from "@/components/shared/ArticleCard";
import { Button } from "@/components/ui/button";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const priceHistory = [
  { date: "Jan", price: 1050 },
  { date: "Feb", price: 980 },
  { date: "Mar", price: 1020 },
  { date: "Apr", price: 1080 },
  { date: "May", price: 1010 },
  { date: "Jun", price: 920 },
  { date: "Jul", price: 950 },
  { date: "Aug", price: 980 },
  { date: "Sep", price: 1050 },
  { date: "Oct", price: 1080 },
  { date: "Nov", price: 1010 },
  { date: "Dec", price: 1024 },
];

const articles = [
  {
    title: "Palladium Supply Crisis: Russia's Market Impact",
    excerpt: "Analyzing how geopolitical factors affect palladium supply and pricing.",
    category: "Market Analysis",
    author: "Michael Chen",
    date: "Dec 9, 2024",
    readTime: "7 min read",
    image: "https://images.unsplash.com/photo-1624365168968-f283d506c6b6?w=800&q=80",
    href: "/articles/palladium-russia-impact",
  },
  {
    title: "Palladium vs Platinum: Catalytic Converter Battle",
    excerpt: "How automakers choose between palladium and platinum for emissions control.",
    category: "Industry",
    author: "David Park",
    date: "Dec 8, 2024",
    readTime: "5 min read",
    image: "https://images.unsplash.com/photo-1579532536935-619928decd08?w=800&q=80",
    href: "/articles/palladium-vs-platinum",
  },
  {
    title: "Investing in Palladium: Complete Guide",
    excerpt: "Everything you need to know about palladium investment options.",
    category: "Investment Guide",
    author: "Sarah Williams",
    date: "Dec 7, 2024",
    readTime: "6 min read",
    image: "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80",
    href: "/articles/palladium-investment-guide",
  },
];

const useCases = [
  { name: "Catalytic Converters", percentage: 85, icon: Car, description: "Gasoline vehicle emissions" },
  { name: "Electronics", percentage: 8, icon: Cpu, description: "Capacitors, connectors" },
  { name: "Chemical", percentage: 4, icon: Factory, description: "Catalysts, refining" },
  { name: "Jewelry/Dental", percentage: 3, icon: Zap, description: "White gold alloy" },
];

export default function Palladium() {
  return (
    <PageLayout>
      <PageHero
        title="Palladium Investment Guide"
        subtitle="The automotive industry's essential metal. Discover palladium market dynamics, supply chain insights, and investment opportunities."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Precious Metals", href: "/precious-metals" },
          { label: "Palladium" },
        ]}
        badge="Automotive Essential"
      >
        <div className="flex items-center gap-6 mt-6">
          <div className="flex items-center gap-2">
            <span className="text-3xl font-display font-bold text-silver-light">$1,024.80</span>
            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-success/20 text-success text-sm font-medium">
              <TrendingUp className="h-4 w-4" />
              +0.65%
            </span>
          </div>
          <div className="text-silver text-sm">
            <span className="block">Primary source: Russia, S. Africa</span>
            <span className="block">Automotive demand: Strong</span>
          </div>
        </div>
      </PageHero>

      {/* Price Chart */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="bg-card rounded-xl border border-border p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="font-display text-xl font-bold text-foreground">Palladium Price History</h2>
                <p className="text-muted-foreground text-sm">USD per troy ounce - 2024 YTD</p>
              </div>
            </div>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={priceHistory}>
                  <defs>
                    <linearGradient id="palladiumGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(216, 77%, 45%)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(216, 77%, 45%)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 87%)" />
                  <XAxis dataKey="date" stroke="hsl(220, 10%, 46%)" fontSize={12} />
                  <YAxis stroke="hsl(220, 10%, 46%)" fontSize={12} domain={['dataMin - 50', 'dataMax + 50']} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(0, 0%, 100%)',
                      border: '1px solid hsl(220, 13%, 87%)',
                      borderRadius: '8px',
                    }}
                    formatter={(value: number) => [`$${value.toFixed(2)}`, 'Palladium Price']}
                  />
                  <Area type="monotone" dataKey="price" stroke="hsl(216, 77%, 45%)" fill="url(#palladiumGradient)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8">Palladium Demand by Sector</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {useCases.map((useCase) => (
              <div key={useCase.name} className="bg-card rounded-xl border border-border p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="inline-flex p-3 rounded-lg bg-accent/10">
                    <useCase.icon className="h-6 w-6 text-accent" />
                  </div>
                  <span className="text-2xl font-display font-bold text-accent">{useCase.percentage}%</span>
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-1">{useCase.name}</h3>
                <p className="text-sm text-muted-foreground">{useCase.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Articles */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-display text-2xl font-bold text-foreground">Palladium Insights</h2>
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
          <h2 className="font-display text-2xl font-bold text-silver-light mb-8 text-center">Palladium Key Facts</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { label: "Symbol", value: "Pd (XPD)" },
              { label: "Standard Purity", value: "99.95% (999.5)" },
              { label: "Density", value: "12.02 g/cm³" },
              { label: "Annual Production", value: "~210 tonnes" },
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
