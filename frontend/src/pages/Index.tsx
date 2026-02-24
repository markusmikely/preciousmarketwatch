import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { MarketTicker } from "@/components/home/MarketTicker";
import { HeroSection } from "@/components/home/HeroSection";
import { FeaturedArticles } from "@/components/home/FeaturedArticles";
import { CategoryCards } from "@/components/home/CategoryCards";
import { MarketOverview } from "@/components/home/MarketOverview";
import { TopDealers } from "@/components/home/TopDealers";
import { CoverageStats } from "@/components/home/CoverageStats";
import { AIDealerReviews } from "@/components/home/AIDealerReviews";
import { client } from '../lib/graphql';
import { HOMEPAGE_QUERY, COVERAGE_STATS_QUERY } from '../queries/homepage';
import React, { useEffect, useState } from 'react';

const METALS_COUNT = 4;

const Index = () => {
  const [dealers, setDealers] = useState(null);
  const [articles, setArticles] = useState(null);
  const [coverageStats, setCoverageStats] = useState<{ articlesCount: number; dealersCount: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [homeRes, statsRes] = await Promise.all([
          client.request(HOMEPAGE_QUERY),
          client.request(COVERAGE_STATS_QUERY).catch(() => null),
        ]);
        const res = homeRes as { dealers?: { nodes?: unknown[] }; posts?: { nodes?: unknown[] } };

        if (res?.dealers?.nodes?.length) {
          setDealers(res.dealers.nodes);
        }
        if (res?.posts?.nodes?.length) {
          setArticles(res.posts.nodes);
        }
        if (statsRes && typeof statsRes === 'object') {
          const s = statsRes as { posts?: { nodes?: unknown[] }; dealers?: { nodes?: unknown[] } };
          setCoverageStats({
            articlesCount: s.posts?.nodes?.length ?? 0,
            dealersCount: s.dealers?.nodes?.length ?? 0,
          });
        }
        setError(null);
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
    <div className="min-h-screen flex flex-col bg-white">
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
            <CoverageStats
              metalsCount={METALS_COUNT}
              articlesCount={coverageStats?.articlesCount}
              dealersCount={coverageStats?.dealersCount}
            />
            <FeaturedArticles articles={articles} />
            <CategoryCards />
            <TopDealers dealers={dealers} />
            <AIDealerReviews dealers={dealers} />
          </>
        )}
      </main>
      <Footer />
    </div>
  );
};

export default Index;
