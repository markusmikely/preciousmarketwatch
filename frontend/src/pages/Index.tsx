import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { MarketTicker } from "@/components/home/MarketTicker";
import { HeroSection } from "@/components/home/HeroSection";
import { FeaturedArticles } from "@/components/home/FeaturedArticles";
import { CategoryCards } from "@/components/home/CategoryCards";
import { MarketOverview } from "@/components/home/MarketOverview";
import { TopDealers } from "@/components/home/TopDealers";
import { client } from '../lib/graphql';
import { HOMEPAGE_QUERY } from '../queries/homepage';
import React, { useEffect, useState } from 'react';
import { MarketProvider } from "@/contexts/MarketContext";

const Index = () => {

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await client.request(HOMEPAGE_QUERY);
        setData(res.homepage.homepage);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // if (loading) return <p>Loading...</p>;
  // if (!data) return <p>No data found</p>;

  return (
    <div className="min-h-screen flex flex-col">
      <MarketProvider>
        <Header />
        <MarketTicker />
          <main className="flex-1">
            <HeroSection />
            <MarketOverview />
            <FeaturedArticles />
            <CategoryCards />
            <TopDealers />
          </main>
      </MarketProvider>
      <Footer />
    </div>
  );
};

export default Index;
