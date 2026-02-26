"""
Seed topics table with predefined topics.
Run from agents/ directory: python scripts/seed_topics.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db import get_session
from shared.models import Topic

SAMPLE_TOPICS = [
    {
        "topic_name": "Gold IRA Rollover Guide 2026",
        "affiliate_name": "GoldCo",
        "affiliate_url": "https://example.com/goldco",
        "target_keyword": "gold ira rollover",
    },
    {
        "topic_name": "Best Silver Coins for Investment",
        "affiliate_name": "SilverGoldBull",
        "affiliate_url": "https://example.com/sgb",
        "target_keyword": "best silver coins",
    },
]


def main():
    with get_session() as session:
        for t in SAMPLE_TOPICS:
            existing = session.query(Topic).filter(
                Topic.topic_name == t["topic_name"],
            ).first()
            if not existing:
                session.add(Topic(**t))
                print("Added:", t["topic_name"])
            else:
                print("Exists:", t["topic_name"])


if __name__ == "__main__":
    main()
