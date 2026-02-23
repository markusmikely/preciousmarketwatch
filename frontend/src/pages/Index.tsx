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
        } else {
          console.warn('[PMW] No dealers in response');
        }
        
        if (res?.posts?.nodes?.length) {
          console.log(`[PMW] Setting ${res.posts.nodes.length} articles`);
          setArticles(res.posts.nodes);
        } else {
          console.warn('[PMW] No articles in response');
        }
        
        setError(null);
      } catch (err) {
        console.error('[PMW] GraphQL fetch failed:', err);
        setError(err);
        // Don't leave loading state hanging on error
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <MarketProvider>
        <Header />
        <MarketTicker />
        <main className="flex-1">
          {loading && (
            <div className="flex items-center justify-center min-h-[200px]">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading...</p>
              </div>
            </div>
          )}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 m-4 text-red-800">
              <p className="font-semibold">Error loading content</p>
              <p className="text-sm mt-2">{error instanceof Error ? error.message : 'Please refresh the page'}</p>
            </div>
          )}
          {!loading && (
            <>
              <HeroSection />
              <MarketOverview />
              <FeaturedArticles articles={articles} />
              <CategoryCards />
              <TopDealers dealers={dealers} />
            </>
          )}
        </main>
      </MarketProvider>
      <Footer />
    </div>
  );
};

export default Index;
