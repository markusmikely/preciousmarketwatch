class BuyerResearchService:
    def __init__(self):
        pass 

    def fetch_reddit(self, keyword, geography):
        '''infra.reddit.search() across approved subreddits → returns list[dict]'''
        pass 

    def fetch_mse(self, keyword):
        '''infra.http.get() MSE search + BeautifulSoup parse → returns list[dict]'''
        pass 

    def fetch_affiliate_faq(self, faq_url):
        '''infra.http.get(faq_url) + BS4 text extraction, 3000 word limit → returns {content, source, available}'''
        pass 

    def cache_sources(self, run_id, sources):
        '''infra.redis.set(f"pmw:sources:{run_id}", json.dumps(sources), ex=3600) → returns cache key'''
        pass 

    def load_cached_sources(self, cache_key):
        '''infra.redis.get(cache_key) → returns parsed dict'''
        pass