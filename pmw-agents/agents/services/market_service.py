class MarketService:
    def __init__(self):
        pass 

    def get_spot_price(self, asset_class):
        '''Fetch live price from metal price API. Returns {price_gbp, price_usd, source, fetched_at}'''
        pass

    def get_price_trend(asset_class, days):
        '''Fetch historical price, compute % change'''
        pass 

    def get_recent_news(keyword, geography, days_back, min_results):
        '''News API fetch, filter by relevance to keyword'''
        pass 

    def derive_market_stance(price_data):
        '''Pure algorithmic — no API call. Applies trend thresholds → returns stance string'''
        pass