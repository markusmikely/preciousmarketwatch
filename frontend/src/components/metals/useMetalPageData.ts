import { useMemo } from "react";
import { useGraphQL } from "@/hooks/useGraphQL";
import { METAL_PAGE_QUERY } from "@/queries/metalPages";

export type MetalSlug = "gold" | "silver" | "platinum" | "palladium";

const CATEGORY_MAP: Record<MetalSlug, string> = {
  gold: "gold",
  silver: "silver",
  platinum: "platinum",
  palladium: "palladium",
};

export interface ArticleForCard {
  title: string;
  excerpt: string;
  category: string;
  author: string;
  date: string;
  readTime: string;
  image: string;
  href: string;
}

export interface DealerForCard {
  name: string;
  description: string;
  rating: number;
  reviews: number;
  categories: string[];
  features: string[];
  logo: string;
  href: string;
  featured?: boolean;
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return dateStr;
  }
}

function transformArticle(node: {
  title: string;
  slug: string;
  date: string;
  excerpt: string;
  featuredImage?: { node?: { sourceUrl: string } };
  author?: { node?: { name: string } };
  categories?: { nodes: { name: string }[] };
  articleMeta?: { readTime?: string };
}): ArticleForCard {
  return {
    title: node.title || "",
    excerpt: node.excerpt || "",
    category: node.categories?.nodes?.[0]?.name || "Article",
    author: node.author?.node?.name || "Staff",
    date: formatDate(node.date || ""),
    readTime: node.articleMeta?.readTime || "5 min read",
    image: node.featuredImage?.node?.sourceUrl || "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=800&q=80",
    href: `/articles/${node.slug || ""}`,
  };
}

function transformDealer(
  node: {
    id: string;
    title: string;
    slug: string;
    dealers?: {
      shortDescription?: string;
      rating?: number;
      featured?: boolean;
      affiliateLink?: string;
      logo?: { sourceUrl?: string };
    };
    metalTypes?: { nodes: { name: string }[] };
    gemstoneTypes?: { nodes: { name: string }[] };
    dealerCategories?: { nodes: { name: string }[] };
  },
  metalFilter: string
): DealerForCard {
  const metals = node.metalTypes?.nodes?.map((n) => n.name) || [];
  const gems = node.gemstoneTypes?.nodes?.map((n) => n.name) || [];
  const cats = node.dealerCategories?.nodes?.map((n) => n.name) || [];
  const categories = [...metals, ...gems, ...cats].filter(Boolean);
  return {
    name: node.title || "",
    description: node.dealers?.shortDescription || "",
    rating: node.dealers?.rating || 0,
    reviews: Math.floor(Math.random() * 5000) + 1000,
    categories: categories.length ? categories : ["Bullion"],
    features: ["Secure payment", "Fast shipping"],
    logo: node.dealers?.logo?.sourceUrl || "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
    href: node.dealers?.affiliateLink || `/dealers/${node.slug || ""}`,
    featured: node.dealers?.featured || false,
  };
}

export function useMetalPageData(metal: MetalSlug) {
  const categorySlug = CATEGORY_MAP[metal];
  const { data, loading, error } = useGraphQL(METAL_PAGE_QUERY, {
    variables: { categorySlug, articlesFirst: 6, dealersFirst: 50 },
  });

  const articles = useMemo(() => {
    const nodes = data?.posts?.nodes || [];
    return nodes.map(transformArticle);
  }, [data]);

  const dealers = useMemo(() => {
    const nodes = data?.dealers?.nodes || [];
    const metalName = metal.charAt(0).toUpperCase() + metal.slice(1);
    return nodes
      .filter((d: { metalTypes?: { nodes: { name: string }[] } }) => {
        const metals = d.metalTypes?.nodes?.map((n) => n.name) || [];
        return metals.some((m) => m.toLowerCase().includes(metalName.toLowerCase()));
      })
      .map((d: Parameters<typeof transformDealer>[0]) => transformDealer(d, metal));
  }, [data, metal]);

  return { articles, dealers, loading, error };
}
