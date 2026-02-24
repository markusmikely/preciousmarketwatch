import { Link } from "react-router-dom";
import { TrendingUp, Mail, Youtube, Instagram, Twitter, FacebookIcon } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import mailchimp from '@mailchimp/mailchimp_marketing';

const TikTokIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
  </svg>
);

const footerNavigation = {
  categories: [
    { name: "Precious Metals", href: "/precious-metals" },
    { name: "Gemstones", href: "/gemstones" },
    { name: "Jewelry Investment", href: "/jewelry-investment" },
    { name: "Market Insights", href: "/market-insights" },
  ],
  company: [
    { name: "About Us", href: "/about" },
    { name: "Editorial Standards", href: "/editorial-standards" },
    { name: "Top Dealers", href: "/top-dealers" },
    { name: "Contact", href: "/contact" },
  ],
  legal: [
    { name: "Privacy Policy", href: "/privacy" },
    { name: "Terms of Service", href: "/terms" },
    { name: "Affiliate Disclosure", href: "/affiliate-disclosure" },
    { name: "Cookie Policy", href: "/cookies" },
  ],
  social: [
    { name: "YouTube", href: "https://www.youtube.com/@preciousmarketwatch", icon: Youtube },
    { name: "Instagram", href: "https://www.instagram.com/preciousmarketwatch", icon: Instagram },
    { name: "Twitter", href: "https://x.com/preciousmarketwatch", icon: Twitter },
    { name: "TikTok", href: "https://www.tiktok.com/@preciousmarketwatch", icon: TikTokIcon },
    { name: "Facebook", href: "https://www.facebook.com/preciousmarketwatch", icon: FacebookIcon },
  ],
};

export function Footer() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email) {
      setStatus('error');
      setMessage('Please enter an email address');
      return;
    }

    setStatus('loading');
    
    try {
      // Send to backend API endpoint which handles Mailchimp
      const response = await fetch('/wp/wp-json/pmw/v1/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage('✓ Subscribed! Check your email to confirm.');
        setEmail('');
        // Auto-clear message after 3 seconds
        setTimeout(() => setStatus('idle'), 3000);
      } else {
        setStatus('error');
        setMessage(data.message || 'Something went wrong. Please try again.');
      }
    } catch (error) {
      setStatus('error');
      setMessage('Network error. Please try again later.');
      console.error('[Newsletter] Subscription error:', error);
    }
  };

  return (
    <footer className="bg-navy text-silver-light">
      <div className="container mx-auto px-4 py-12 lg:px-8">
        {/* Newsletter Section */}
        <div className="mb-12 rounded-xl bg-navy-light/50 p-8 lg:p-12">
          <div className="mx-auto max-w-2xl text-center">
            <h3 className="font-display text-2xl font-bold text-silver-light lg:text-3xl">
              Stay Informed on Market Trends
            </h3>
            <p className="mt-3 text-silver">
              Get weekly insights on precious metals, gemstones, and investment opportunities delivered to your inbox.
            </p>
            <form className="mt-6 flex flex-col gap-3 sm:flex-row sm:gap-4" onSubmit={handleSubmit}>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="flex-1 bg-navy border-silver/30 text-silver-light placeholder:text-silver/60 focus:border-primary focus:ring-primary"
              />
              {status === 'success' && <p>✓ Subscribed!</p>}
              {status === 'error' && <p>✗ Something went wrong</p>}
              <Button className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold" type="submit" onClick={handleSubmit}>
                <Mail className="mr-2 h-4 w-4" />
                Subscribe
              </Button>
            </form>
            <p className="mt-3 text-xs text-silver/60">
              No spam. Unsubscribe anytime. Read our{" "}
              <Link to="/privacy" className="underline hover:text-primary">
                Privacy Policy
              </Link>
            </p>
          </div>
        </div>

        {/* Main Footer Content */}
        <div className="grid grid-cols-2 gap-8 lg:grid-cols-5">
          {/* Brand Column */}
          <div className="col-span-2 lg:col-span-1">
            <Link to="/" className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-gold">
                <TrendingUp className="h-5 w-5 text-navy" />
              </div>
              <div className="flex flex-col">
                <span className="font-display text-lg font-bold leading-tight text-silver-light">
                  Precious Market
                </span>
                <span className="text-xs font-medium uppercase tracking-wider text-primary">
                  Watch
                </span>
              </div>
            </Link>
            <p className="mt-4 text-sm text-silver">
              Trusted insights for precious metals & gemstones. Your authoritative source for market analysis and investment guidance.
            </p>
            {/* Social Links */}
            <div className="mt-6 flex gap-4">
              {footerNavigation.social.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  className="text-silver hover:text-primary transition-colors"
                >
                  <span className="sr-only">{item.name}</span>
                  <item.icon className="h-5 w-5" />
                </a>
              ))}
            </div>
          </div>

          {/* Categories */}
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wider text-silver-light">
              Categories
            </h4>
            <ul className="mt-4 space-y-3">
              {footerNavigation.categories.map((item) => (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className="text-sm text-silver hover:text-primary transition-colors"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wider text-silver-light">
              Company
            </h4>
            <ul className="mt-4 space-y-3">
              {footerNavigation.company.map((item) => (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className="text-sm text-silver hover:text-primary transition-colors"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wider text-silver-light">
              Legal
            </h4>
            <ul className="mt-4 space-y-3">
              {footerNavigation.legal.map((item) => (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className="text-sm text-silver hover:text-primary transition-colors"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 border-t border-silver/20 pt-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-sm text-silver/60">
              © {new Date().getFullYear()} Precious Market Watch. All rights reserved.
            </p>
            <p className="text-xs text-silver/40">
              Market data is provided for informational purposes only and should not be considered investment advice.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
