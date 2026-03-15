# load/score/update affiliates
class AffiliateService:
    def __init__(self):
        pass 

    def get_active_affiliates(self):
        '''SELECT * FROM affiliates WHERE active=true'''
        pass
    
    def get_affiliate(self, affiliate_id):
        '''Single affiliate by Postgres ID'''
        pass

    def score_affiliates_for_topic(self, topic, affiliates):
        '''Apply scoring formula, return sorted ScoredAffiliate list'''
        pass

    def append_intelligence_run(self, affiliate_id, run_id, data):
        '''INSERT INTO affiliate_intelligence_runs (append-only)'''
        pass

    def rebuild_intelligence_summary(self, affiliate_id):
        '''SELECT all runs, apply aggregation rules, UPSERT affiliate_intelligence_summary'''
        pass

    def get_intelligence_summary(self, affiliate_id):
        '''Read current summary row'''
        pass