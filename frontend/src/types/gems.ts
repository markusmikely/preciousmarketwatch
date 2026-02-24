export interface GemPrice {
  id: string;
  name: string;
  category: 'Precious' | 'Semi-Precious' | 'Organic';
  priceLowUsd: number;
  priceHighUsd: number;
  priceLowGbp: number;
  priceHighGbp: number;
  qualityGrade: string;
  caratRange: string;
  trend: 'Rising' | 'Stable' | 'Declining';
  trendPercentage: number;
  lastReviewed: string;
  dataSource: string;
}

export interface GemsApiResponse {
  gems: GemPrice[];
  stale?: boolean;
}
