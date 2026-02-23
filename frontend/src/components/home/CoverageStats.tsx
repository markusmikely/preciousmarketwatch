import { TrendingUp, Users, BookOpen, Award } from "lucide-react";

export function CoverageStats() {
  const stats = [
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
      description: "Verified precious metals & gemstone retailers"
    },
    {
      icon: Award,
      value: "100%",
      label: "Independent Reviews",
      description: "Transparent, AI-verified dealer ratings"
    }
  ];

  return (
    <section className="py-16 lg:py-20 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl lg:text-4xl font-bold text-foreground mb-4">
            Our Coverage
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Comprehensive market intelligence across precious metals and gemstones with independent, AI-verified dealer reviews.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <div key={index} className="bg-card rounded-lg border border-border p-6 text-center hover:shadow-md transition-shadow">
              <div className="flex justify-center mb-4">
                <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center">
                  <stat.icon className="h-7 w-7 text-primary" />
                </div>
              </div>
              <div className="font-display text-3xl font-bold text-foreground mb-2">
                {stat.value}
              </div>
              <div className="font-semibold text-foreground mb-1">
                {stat.label}
              </div>
              <p className="text-sm text-muted-foreground">
                {stat.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
