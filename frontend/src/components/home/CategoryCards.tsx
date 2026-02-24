import { Link } from "react-router-dom";
import { ArrowRight, CircleDot, Gem, Watch, BarChart2, TrendingUp, BookOpen, Users, Award } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const categories = [
  {
    title: "Precious Metals",
    description: "Gold, silver, platinum, and palladium investment guides, market analysis, and price trends.",
    icon: CircleDot,
    href: "/precious-metals",
    stats: "Live prices • 4 metals covered",
    gradient: "from-amber-500/20 to-yellow-500/10",
  },
  {
    title: "Gemstones",
    description: "Diamond, ruby, sapphire, and emerald buying guides, grading standards, and valuation.",
    icon: Gem,
    href: "/gemstones",
    stats: "Expert reviews • 4 gemstones",
    gradient: "from-blue-500/20 to-purple-500/10",
  },
  {
    title: "Jewelry Investment",
    description: "Fine jewelry collecting, antique pieces, auction insights, and investment strategies.",
    icon: Watch,
    href: "/jewelry-investment",
    stats: "Market reports • Investment tips",
    gradient: "from-rose-500/20 to-pink-500/10",
  },
  {
    title: "Market Insights",
    description: "Supply chain analysis, mining updates, industry news, and economic indicators.",
    icon: BarChart2,
    href: "/market-insights",
    stats: "6+ articles • Daily updates",
    gradient: "from-emerald-500/20 to-teal-500/10",
  },
];

const coverageStats = [
  {
    icon: TrendingUp,
    value: "4",
    label: "Precious Metals",
    description: "Gold, Silver, Platinum, Palladium"
  },
  {
    icon: BookOpen,
    value: "6+",
    label: "Articles & Guides",
    description: "Expert investment analysis"
  },
  {
    icon: Users,
    value: "15+",
    label: "Trusted Dealers",
    description: "Verified retailers"
  },
  {
    icon: Award,
    value: "100%",
    label: "AI Reviews",
    description: "Independent verification"
  }
];

export function CategoryCards() {
  return (
    <section className="py-16 lg:py-24 bg-muted/50">
      <div className="container mx-auto px-4 lg:px-8">
        {/* Coverage Stats Header */}
        <div className="mb-16">
          <div className="text-center mb-12">
            <h2 className="font-display text-3xl font-bold text-foreground lg:text-4xl">
              Our Coverage
            </h2>
            <p className="mt-3 text-muted-foreground max-w-2xl mx-auto">
              Comprehensive market intelligence with independent, AI-verified reviews
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {coverageStats.map((stat, index) => (
              <div key={index} className="bg-card rounded-lg border border-border p-6 text-center hover:shadow-md transition-shadow">
                <div className="flex justify-center mb-4">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                    <stat.icon className="h-6 w-6 text-primary" />
                  </div>
                </div>
                <div className="font-display text-3xl font-bold text-foreground mb-2">
                  {stat.value}
                </div>
                <div className="font-semibold text-foreground mb-1 text-sm">
                  {stat.label}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stat.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl font-bold text-foreground lg:text-4xl">
            Explore Our Coverage
          </h2>
          <p className="mt-3 text-muted-foreground max-w-2xl mx-auto">
            Comprehensive resources across precious metals, gemstones, and jewelry markets
          </p>
        </div>

        {/* Category Grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {categories.map((category) => (
            <Link key={category.title} to={category.href}>
              <Card className="group h-full border-border bg-card hover:shadow-lg hover:border-primary/30 transition-all duration-300">
                <CardContent className="p-6">
                  <div className={`inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${category.gradient}`}>
                    <category.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="mt-4 font-display text-xl font-semibold text-card-foreground group-hover:text-primary transition-colors">
                    {category.title}
                  </h3>
                  <p className="mt-2 text-sm text-muted-foreground line-clamp-3">
                    {category.description}
                  </p>
                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      {category.stats}
                    </span>
                    <ArrowRight className="h-4 w-4 text-primary opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
