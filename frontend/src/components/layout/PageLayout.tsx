import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { MarketTicker } from "@/components/home/MarketTicker";

interface PageLayoutProps {
  children: React.ReactNode;
  showTicker?: boolean;
}

export function PageLayout({ children, showTicker = true }: PageLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      {showTicker && <MarketTicker />}
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
