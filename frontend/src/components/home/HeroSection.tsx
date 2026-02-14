import { Link } from "react-router-dom";
import { ArrowRight, BarChart3, Shield, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-hero py-20 lg:py-32">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23d4af37' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }} />
      </div>

      <div className="container relative mx-auto px-4 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
            </span>
            Live Market Updates
          </div>

          {/* Headline */}
          <h1 className="font-display text-4xl font-bold tracking-tight text-silver-light sm:text-5xl lg:text-6xl">
            Trusted Insights for{" "}
            <span className="text-gradient-gold">Precious Metals</span> &{" "}
            <span className="text-gradient-gold">Gemstones</span>
          </h1>

          {/* Subheadline */}
          <p className="mt-6 text-lg leading-relaxed text-silver sm:text-xl">
            Your authoritative source for gold, silver, platinum, diamonds, and fine gemstones. 
            Expert analysis, market data, and investment guidance from industry specialists.
          </p>

          {/* CTA Buttons */}
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link to="/market-insights">
              <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold group">
                Explore Market Data
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <Link to="/precious-metals">
              <Button size="lg" variant="outline" className="border-silver/30 text-silver-light hover:bg-silver/10 hover:text-silver-light">
                Browse Categories
              </Button>
            </Link>
          </div>

          {/* Trust Indicators */}
          <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-3">
            <div className="flex flex-col items-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <BarChart3 className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mt-4 font-semibold text-silver-light">Real-Time Data</h3>
              <p className="mt-1 text-sm text-silver">Live market prices & trends</p>
            </div>
            <div className="flex flex-col items-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mt-4 font-semibold text-silver-light">Expert Analysis</h3>
              <p className="mt-1 text-sm text-silver">Industry-certified insights</p>
            </div>
            <div className="flex flex-col items-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Globe className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mt-4 font-semibold text-silver-light">Global Coverage</h3>
              <p className="mt-1 text-sm text-silver">Worldwide market intelligence</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
