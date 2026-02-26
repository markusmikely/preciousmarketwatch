import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { fetchMetalTicker } from '../services/metalTicker';

const REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

const defaultMarketData = [
    { name: "Gold", symbol: "XAU", price: 0, change: 0, change_percent: 0, high: 0, low: 0, isUp: false },
    { name: "Silver", symbol: "XAG", price: 0, change: 0, change_percent: 0, high: 0, low: 0, isUp: false },
    { name: "Platinum", symbol: "XPT", price: 0, change: 0, change_percent: 0, high: 0, low: 0, isUp: false },
    { name: "Palladium", symbol: "XPD", price: 0, change: 0, change_percent: 0, high: 0, low: 0, isUp: false },
];

const MarketContext = createContext(null);

export const MarketProvider = ({ children }: { children: React.ReactNode }) => {
    const [marketData, setMarketData] = useState(defaultMarketData);
    const [loading, setLoading] = useState(false);

    const updateMarketData = useCallback(async () => {
        setLoading(true);
        try {
            const tickerList = await fetchMetalTicker();
            if (tickerList && Array.isArray(tickerList) && tickerList.length > 0) {
                setMarketData(tickerList.map((t) => ({
                    name: t.name,
                    symbol: t.symbol,
                    price: t.price,
                    change: t.change,
                    change_percent: t.change_percent,
                    high: t.high,
                    low: t.low,
                    isUp: t.isUp,
                })));
            } else {
                console.warn("[MarketContext] Invalid ticker data received:", tickerList);
            }
        } catch (error) {
            console.error("[MarketContext] Error fetching metal ticker:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    const value = useMemo(() => ({
        marketData,
        loading,
        updateMarketData
    }), [marketData, loading, updateMarketData]);
   
    useEffect(() => {
        const interval = setInterval(updateMarketData, REFRESH_INTERVAL_MS);
        updateMarketData();
        return () => clearInterval(interval);
    }, [updateMarketData]);

    return <MarketContext.Provider value={value}>{children}</MarketContext.Provider>;
};



// Custom hook for cleaner usage
// eslint-disable-next-line react-refresh/only-export-components
export const useMarket = () => useContext(MarketContext);