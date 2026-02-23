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
  const [dealers, setDealers] = useState(null);
  const [articles, setArticles] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await client.request(HOMEPAGE_QUERY);
        console.log('[PMW] GraphQL response:', res);
        
        if (res?.dealers?.nodes?.length) {
          console.log(`[PMW] Setting ${res.dealers.nodes.length} dealers`);
          setDealers(res.dealers.nodes);
        }
        
        if (res?.posts?.nodes?.length) {
          console.log(`[PMW] Setting ${res.posts.nodes.length} articles`);
          setArticles(res.posts.nodes);
        }
      } catch (err) {
        console.error('[PMW] GraphQL fetch failed:', err);
        setError(err);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <MarketProvider>
        <Header />
        <MarketTicker />
        <main className="flex-1">
          <HeroSection />
          <MarketOverview />
          <FeaturedArticles articles={articles} />
          <CategoryCards />
          <TopDealers dealers={dealers} />
        </main>
      </MarketProvider>
      <Footer />
    </div>
  );
};

export default Index;
