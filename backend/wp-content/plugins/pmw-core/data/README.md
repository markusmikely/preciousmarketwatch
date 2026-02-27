# Content Topics Seed Data

## pmw_topics_seed_100.json

JSON array of topic objects. Each object:

```json
{
  "title": "How to Invest in Gold",
  "status": "publish",
  "meta": {
    "pmw_target_keyword": "how to invest in gold",
    "pmw_summary": "Comprehensive guide about How to Invest in Gold.",
    "pmw_include_keywords": "gold bullion, gold coins, gold bars",
    "pmw_exclude_keywords": "",
    "pmw_asset_class": "gold",
    "pmw_product_type": "bars",
    "pmw_geography": "global",
    "pmw_is_buy_side": true,
    "pmw_intent_stage": "consideration",
    "pmw_priority": 1,
    "pmw_schedule_cron": "",
    "pmw_agent_status": "idle",
    "pmw_last_run_at": "",
    "pmw_run_count": 0,
    "pmw_last_run_id": 0,
    "pmw_last_wp_post_id": 0,
    "pmw_wp_category_id": 0,
    "pmw_affiliate_page_id": 0
  }
}
```

## Seeding

Use **Content Topics → Seed & Reset** in the WordPress admin to:

- **Seed topics from JSON** — Add topics from this file (skips existing by title)
- **Reset all topics to seed state** — Delete all topics, then seed from JSON
- **Unlink all articles from topics** — Clear `pmw_topic_id` from posts and News & Analysis

The seed path is filterable: `pmw_topics_seed_json_path`.
