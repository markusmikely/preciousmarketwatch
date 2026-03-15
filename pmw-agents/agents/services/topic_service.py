# fetch topics, update WP display status

"""This service is responsible for fetching new topics from the wordpress database
and returning them to the caller. It also updates the display status of the topics
in the wordpress database."""

# from dataclasses import dataclass
# from datetime import datetime
# from typing import List, Optional

# from agents.config import settings
# from agents.models.topic import Topic
# from agents.providers.wordpress import WordPressProvider

class TopicService:
    """Service for fetching and updating topics in the wordpress database."""
    def __init__(self):
        pass

    def get_eligible_topics(self):
        '''GET /wp/v2/pmw-topics?status=publish → list of raw WP topic dicts'''
        pass

    def filter_locked_topics(self, topics):
        '''Query Postgres: exclude topics with active workflow_runs lock'''
        pass

    def select_next_topic(self, candidates):
        '''Priority sort → exclude topics run in last 24h → return best'''
        pass    

    def mark_topic_running(self, topic_id, run_id):
        '''run_id)PATCH /pmw-topics/{id} meta: pmw_agent_status=running (display only, fire-and-forget)'''
        pass

    def mark_topic_complete(self, topic_id, run_id, wp_post_id):
        '''PATCH /pmw-topics/{id} meta: status=idle, run_count+1, last_wp_post_id'''
        pass

    def mark_topic_failed(self, topic_id, error):
        '''PATCH /pmw-topics/{id} meta: status=failed'''
        pass