import { gql } from "graphql-request";

/** Metal prices ticker: latest + previous for daily change. Data from metal_prices seed. */
export const METAL_PRICES_TICKER_QUERY = gql`
  query MetalPricesTicker {
    metalPricesTicker {
      metal
      name
      symbol
      price
      change
      changePercent
      isUp
      high
      low
      date
    }
  }
`;

export type MetalTicker = {
  metal: string;
  name: string;
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  isUp: boolean;
  high: number;
  low: number;
  date: string | null;
};
