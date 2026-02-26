import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X, ChevronDown, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from "@/components/ui/navigation-menu";
import { cn } from "@/lib/utils";
import { SubscribeModal } from "@/components/shared/SubscribeModal";

const navigation = [
  {
    name: "Precious Metals",
    href: "/precious-metals",
    children: [
      { name: "Gold", href: "/precious-metals/gold", description: "Gold bars, coins, and investment guides" },
      { name: "Silver", href: "/precious-metals/silver", description: "Silver bullion and market analysis" },
      { name: "Platinum", href: "/precious-metals/platinum", description: "Platinum investment opportunities" },
      { name: "Palladium", href: "/precious-metals/palladium", description: "Industrial and investment demand" },
    ],
  },
  {
    name: "Gemstones",
    href: "/gemstones",
    children: [
      { name: "Diamonds", href: "/gemstones/diamonds", description: "Diamond grading and buying guides" },
      { name: "Rubies", href: "/gemstones/rubies", description: "Ruby quality and valuation" },
      { name: "Sapphires", href: "/gemstones/sapphires", description: "Sapphire colors and origins" },
      { name: "Emeralds", href: "/gemstones/emeralds", description: "Emerald treatments and pricing" },
    ],
  },
  { name: "Top Dealers", href: "/top-dealers" },
  { name: "Tools", href: "/tools" },
  { name: "News & Analysis", href: "/news-and-analysis" }
];

const ListItem = ({
  className,
  title,
  children,
  href,
  ...props
}: {
  className?: string;
  title: string;
  children: React.ReactNode;
  href: string;
}) => {
  return (
    <li>
      <NavigationMenuLink asChild>
        <Link
          to={href}
          className={cn(
            "block select-none space-y-1 rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-muted focus:bg-muted",
            className
          )}
          {...props}
        >
          <div className="text-sm font-medium leading-none text-foreground">{title}</div>
          <p className="line-clamp-2 text-sm leading-snug text-muted-foreground">
            {children}
          </p>
        </Link>
      </NavigationMenuLink>
    </li>
  );
};

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [subscribeOpen, setSubscribeOpen] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
        <nav className="container mx-auto flex items-center justify-between px-4 py-3 lg:px-8">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-gold">
              <TrendingUp className="h-5 w-5 text-navy" />
            </div>
            <div className="flex flex-col">
              <span className="font-display text-lg font-bold leading-tight text-foreground">
                Precious Market
              </span>
              <span className="text-xs font-medium uppercase tracking-wider text-primary">
                Watch
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex lg:items-center lg:gap-1">
            <NavigationMenu>
              <NavigationMenuList>
                {navigation.map((item) =>
                  item.children ? (
                    <NavigationMenuItem key={item.name}>
                      <NavigationMenuTrigger className="bg-transparent text-sm font-medium text-foreground hover:text-primary">
                        {item.name}
                      </NavigationMenuTrigger>
                      <NavigationMenuContent>
                        <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2">
                          {item.children.map((child) => (
                            <ListItem key={child.name} title={child.name} href={child.href}>
                              {child.description}
                            </ListItem>
                          ))}
                        </ul>
                      </NavigationMenuContent>
                    </NavigationMenuItem>
                  ) : (
                    <NavigationMenuItem key={item.name}>
                      <Link
                        to={item.href}
                        className="inline-flex h-10 w-max items-center justify-center rounded-md px-4 py-2 text-sm font-medium text-foreground transition-colors hover:text-primary focus:outline-none"
                      >
                        {item.name}
                      </Link>
                    </NavigationMenuItem>
                  )
                )}
              </NavigationMenuList>
            </NavigationMenu>
          </div>

          {/* CTA Button */}
          <div className="hidden lg:flex lg:items-center lg:gap-4">
            <Link to="/about">
              <Button variant="ghost" size="sm" className="text-foreground hover:text-primary">
                About
              </Button>
            </Link>
            <Button 
              size="sm" 
              className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-gold"
              onClick={() => setSubscribeOpen(true)}
            >
              Subscribe
            </Button>
          </div>

          {/* Mobile menu button */}
          <button
            type="button"
            className="lg:hidden inline-flex items-center justify-center rounded-md p-2.5 text-foreground"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <span className="sr-only">Open main menu</span>
            {mobileMenuOpen ? (
              <X className="h-6 w-6" aria-hidden="true" />
            ) : (
              <Menu className="h-6 w-6" aria-hidden="true" />
            )}
          </button>
        </nav>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-border bg-card">
            <div className="space-y-1 px-4 py-4">
              {navigation.map((item) => (
                <div key={item.name}>
                  <Link
                    to={item.href}
                    className="block rounded-md px-3 py-2 text-base font-medium text-foreground hover:bg-muted hover:text-primary"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {item.name}
                  </Link>
                  {item.children && (
                    <div className="ml-4 space-y-1">
                      {item.children.map((child) => (
                        <Link
                          key={child.name}
                          to={child.href}
                          className="block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-primary"
                          onClick={() => setMobileMenuOpen(false)}
                        >
                          {child.name}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              <div className="pt-4 border-t border-border">
                <Button 
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    setSubscribeOpen(true);
                  }}
                >
                  Subscribe
                </Button>
              </div>
            </div>
          </div>
        )}
      </header>

      <SubscribeModal open={subscribeOpen} onOpenChange={setSubscribeOpen} />
    </>
  );
}
