# fetch topics, update WP display status

"""This service is responsible for fetching new topics from the wordpress database
and returning them to the caller. It also updates the display status of the topics
in the wordpress database."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from agents.config import settings
from agents.models.topic import Topic
from agents.providers.wordpress import WordPressProvider

class TopicService:
    """Service for fetching and updating topics in the wordpress database."""
    def __init__(self):
        self.wordpress = WordPressProvider()

    def fetch_topics(self) -> List[Topic]:
        """Fetch new topics from the wordpress database."""
        return self.wordpress.get_all(endpoint="topics")
