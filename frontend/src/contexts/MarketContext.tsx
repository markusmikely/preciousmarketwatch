import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { fetchMetalData } from '../services/metalService';

const MarketContext = createContext(null);

export const MarketProvider = ({ children }: { children: React.ReactNode }) => {
    const [marketData, setMarketData] = useState([{
        name: "Gold",
        symbol: "XAU",
        price: 0,
        change: 0,
        change_percent: 0,
        high: 0,
        low: 0,
        isUp: false
    }, {
        name: "Silver",
        symbol: "XAG",
        price: 0,
        change: 0,
        change_percent: 0,
        high: 0,
        low: 0,
        isUp: false
    }, {
        name: "Platinum",
        symbol: "XPT",
        price: 0,
        change: 0,
        change_percent: 0,
        high: 0,
        low: 0,
        isUp: false
    }, {
        name: "Palladium",
        symbol: "XPD",
        price: 0,
        change: 0,
        change_percent: 0,
        high: 0,
        low: 0,
        isUp: true
    }]);
    const [loading, setLoading] = useState(false);

    const updateMarketData = useCallback(async () => {
        setLoading(true);
        try {
            const marketDataList = await fetchMetalData();
            if (marketDataList && Array.isArray(marketDataList) && marketDataList.length > 0) {
                setMarketData(marketDataList);
            } else {
                console.warn("[MarketContext] Invalid market data received:", marketDataList);
                // Keep existing data if new data is invalid
            }
        } catch (error) {
            console.error("[MarketContext] Error fetching market data:", error);
            // Keep existing data on error - do NOT throw
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
        const interval = setInterval(() => {
            console.log("Updating market data");
            updateMarketData();
        }, 10000);

        updateMarketData();
        
        return () => clearInterval(interval);
    }, [updateMarketData]);

    return <MarketContext.Provider value={value}>{children}</MarketContext.Provider>;
};



// Custom hook for cleaner usage
// eslint-disable-next-line react-refresh/only-export-components
export const useMarket = () => useContext(MarketContext);