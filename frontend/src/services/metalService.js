// Set VITE_IS_PRODUCTION=true in .env (or via GitHub Actions secret) to use live data
const IS_PRODUCTION = import.meta.env.VITE_IS_PRODUCTION === 'true';
const API_KEY = import.meta.env.VITE_METALS_DEV_API_KEY;

const mockData = {
    gold: {
        "timestamp": "2026-02-11T11:55:01.825Z",
        "currency": "USD",
        "unit": "toz",
        "metal": "gold",
        "price": 5112.945,
        "ask": 5113.35,
        "bid": 5112.32,
        "high": 5116.805,
        "low": 5025.485,
        "change": 87.46,
        "change_percent": 1.74,
        "name": "Gold", 
        "symbol": "XAU",
        "isUp": true
    },
    silver: {
        "timestamp": "2026-02-11T11:55:01.912Z",
        "currency": "USD",
        "unit": "toz",
        "metal": "silver",
        "price": 86.232,
        "ask": 86.262,
        "bid": 86.201,
        "high": 86.2385,
        "low": 80.815,
        "change": 5.417,
        "change_percent": 6.7,
        "name": "Silver", 
        "symbol": "XAG",
        "isUp": true
    },
    platinum: {
        "timestamp": "2026-02-11T11:53:01.818Z",
        "currency": "USD",
        "unit": "toz",
        "metal": "platinum",
        "price": 2184.096,
        "ask": 2191.574,
        "bid": 2183.856,
        "high": 2191.385,
        "low": 2087.436,
        "change": 95.02,
        "change_percent": 4.55,
        "name": "Platinum", 
        "symbol": "XPT",
        "isUp": true
    },
    palladium: {
        "timestamp": "2026-02-11T14:38:02.414Z",
        "currency": "USD",
        "unit": "toz",
        "metal": "palladium",
        "price": 1758.453,
        "ask": 1762.267,
        "bid": 1757.223,
        "high": 1772.4,
        "low": 1702.452,
        "change": 54.45,
        "change_percent": 3.2,
        "name": "Palladium", 
        "symbol": "XPD",
        "isUp": false
    }
};
  

const metalList = ["gold", "silver", "platinum", "palladium"];

export const fetchMetalData = async () => {
    if (!IS_PRODUCTION) {
        console.log("[metalService] Using mock data (dev mode)");
        return metalList.map(metal => mockData[metal]);
    }

    try {
        if (!API_KEY) {
            if (import.meta.env.DEV) {
                console.debug("[metalService] No VITE_METALS_DEV_API_KEY set, using mock data");
            }
            return metalList.map(metal => mockData[metal]);
        }

        const metalData = await Promise.all(metalList.map(async(metal) => {
            try {
                const response = await fetch(`https://api.metals.dev/v1/metal/spot?api_key=${API_KEY}&metal=${metal}&currency=USD`, {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' },
                    timeout: 5000
                });
                
                if (!response.ok) {
                    console.error(`[metalService] API error for ${metal}: ${response.status} ${response.statusText}`);
                    throw new Error(`HTTP ${response.status}`);
                }

                const result = await response.json();

                if (!result.rate) {
                    console.error(`[metalService] Invalid response for ${metal}:`, result);
                    throw new Error("No rate in response");
                }

                // metals.dev /v1/metal/spot returns: { rate: number }
                // Map to the shape the FE expects
                return {
                    metal,
                    currency: "USD",
                    unit: "toz",
                    price: result.rate,
                    ask: result.rate,   // Spot endpoint doesn't return ask/bid/high/low
                    bid: result.rate,   // Upgrade to /v1/latest for full OHLC data
                    high: result.rate,
                    low: result.rate,
                    change: 0,
                    change_percent: 0,
                    name: metal.charAt(0).toUpperCase() + metal.slice(1),
                    symbol: mockData[metal]?.symbol ?? metal.toUpperCase(),
                    isUp: true,
                    timestamp: new Date().toISOString(),
                };
            } catch (metalError) {
                console.error(`[metalService] Failed to fetch ${metal}:`, metalError);
                // Fall back to mock data for this metal
                return mockData[metal];
            }
        }));
        return metalData;
    
    } catch (error) {
        console.error("[metalService] Unexpected error, falling back to mock data:", error);
        return metalList.map(metal => mockData[metal]);
    }
};