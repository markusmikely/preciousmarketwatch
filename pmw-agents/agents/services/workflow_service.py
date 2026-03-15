class WorkflowService:
    def __init__(self):
        pass

    def create_run(self, topic_id, triggered_by):
        '''INSERT INTO workflow_runs, return run_id'''
        pass

    def acquire_topic_lock(self, topic_wp_id, run_id, expires_minutes=120):
        '''Expire stale lock → check active lock → claim lock. Returns bool.'''
        pass

    def release_topic_lock(self, topic_wp_id, run_id, success, wp_post_id):
        '''`UPDATE workflow_runs SET status=complete'''
        pass

    def fail_run(self, run_id, error):
        '''UPDATE workflow_runs SET status=failed, error_message'''
        pass

    def recover_stale_runs(self, stale_after_minutes=120):
        '''Reset expired locks on worker startup'''
        pass

    def get_run(self, run_id):
        '''Fetch single run row for Bridge API'''
        pass
