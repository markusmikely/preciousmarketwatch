import { Link } from "react-router-dom";
import { Shield, Award, Users, BookOpen, Target, Eye } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PageHero } from "@/components/shared/PageHero";
import { Button } from "@/components/ui/button";

const values = [
  {
    icon: Shield,
    title: "Integrity",
    description: "We maintain strict editorial independence. Our recommendations are never influenced by advertising relationships.",
  },
  {
    icon: BookOpen,
    title: "Education",
    description: "We believe informed investors make better decisions. Our content aims to educate, not just promote.",
  },
  {
    icon: Target,
    title: "Accuracy",
    description: "Every fact is verified, every price checked. We correct errors promptly and transparently.",
  },
  {
    icon: Eye,
    title: "Transparency",
    description: "We clearly disclose affiliate relationships and potential conflicts of interest.",
  },
];


const team = [
  {
    name: "Michael Chen",
    role: "Editor-in-Chief",
    bio: "15+ years covering precious metals markets. Former analyst at Goldman Sachs.",
    image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&q=80",
  },
  {
    name: "Sarah Williams",
    role: "Senior Analyst",
    bio: "Gemologist (GIA) with expertise in colored stones and diamond markets.",
    image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&q=80",
  },
  {
    name: "David Park",
    role: "Market Analyst",
    bio: "Former commodities trader specializing in platinum group metals.",
    image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&q=80",
  },
  {
    name: "Emma Thompson",
    role: "Gemstone Editor",
    bio: "Certified gemologist with 10+ years in the jewelry industry.",
    image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&q=80",
  },
];

const stats = [
  { value: "500K+", label: "Monthly Readers" },
  { value: "1,000+", label: "Articles Published" },
  { value: "50+", label: "Vetted Dealers" },
  { value: "10+", label: "Years Experience" },
];

export default function About() {
  return (
    <PageLayout showTicker={false}>
      <PageHero
        title="About Precious Market Watch"
        subtitle="Your trusted source for precious metals and gemstone market intelligence. We combine decades of industry expertise with rigorous journalism."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "About" },
        ]}
      />

      {/* Mission */}
      <section className="py-16">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="font-display text-3xl font-bold text-foreground mb-6">Our Mission</h2>
            <p className="text-lg text-muted-foreground leading-relaxed">
              Precious Market Watch exists to democratize access to precious metals and gemstone market intelligence. We believe every investor—from first-time buyers to institutional traders—deserves accurate, unbiased information to make informed decisions.
            </p>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 bg-gradient-hero">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <span className="font-display text-4xl font-bold text-primary block mb-2">{stat.value}</span>
                <span className="text-silver">{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-16">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8 text-center">Our Values</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((value) => (
              <div key={value.title} className="bg-card rounded-xl border border-border p-6 text-center">
                <div className="inline-flex p-4 rounded-full bg-primary/10 text-primary mb-4">
                  <value.icon className="h-6 w-6" />
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-2">{value.title}</h3>
                <p className="text-sm text-muted-foreground">{value.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Editorial Standards */}
      <section className="py-16 bg-muted/30">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
            <h2 className="font-display text-2xl font-bold text-foreground mb-6">Editorial Standards</h2>
            <div className="prose prose-lg text-muted-foreground">
              <p>
                Our editorial team operates independently from our business operations. Advertising and affiliate partnerships never influence our coverage or recommendations.
              </p>
              <p className="mt-4">
                <strong className="text-foreground">Fact-Checking:</strong> All market data is verified from primary sources. Price information is updated in real-time from major exchanges.
              </p>
              <p className="mt-4">
                <strong className="text-foreground">Corrections:</strong> We promptly correct any errors and maintain a transparent correction policy.
              </p>
              <p className="mt-4">
                <strong className="text-foreground">Disclosure:</strong> We clearly label sponsored content and disclose affiliate relationships in all relevant articles.
              </p>
            </div>
            <Button asChild className="mt-8">
              <Link to="/editorial-standards">Read Full Editorial Policy</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="py-16">
        <div className="container mx-auto px-4 lg:px-8">
          <h2 className="font-display text-2xl font-bold text-foreground mb-8 text-center">Our Team</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {team.map((member) => (
              <div key={member.name} className="bg-card rounded-xl border border-border overflow-hidden">
                <div className="aspect-square overflow-hidden">
                  <img
                    src={member.image}
                    alt={member.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-5">
                  <h3 className="font-display text-lg font-semibold text-foreground">{member.name}</h3>
                  <span className="text-sm text-primary block mb-2">{member.role}</span>
                  <p className="text-sm text-muted-foreground">{member.bio}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact CTA */}
      <section className="py-16 bg-gradient-hero">
        <div className="container mx-auto px-4 lg:px-8 text-center">
          <h2 className="font-display text-3xl font-bold text-silver-light mb-4">
            Get in Touch
          </h2>
          <p className="text-silver max-w-2xl mx-auto mb-8">
            Have questions, feedback, or partnership inquiries? We'd love to hear from you.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold">
              Contact Us
            </Button>
            <Button size="lg" variant="outline" className="border-silver/30 text-silver-light hover:bg-silver/10">
              Press Inquiries
            </Button>
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
