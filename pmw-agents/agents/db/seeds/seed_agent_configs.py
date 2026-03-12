"""
Seed agent_configs display metadata.
Run: python -m agents.db.seeds.seed_agent_configs

IMPORTANT: Set wp_agent_post_id values to match your WP CPT 'agents' post IDs.
Leave as None until you have confirmed the WP post IDs.
"""
import asyncio
import os
import asyncpg

# Map agent_name → display metadata
# wp_agent_post_id: fill in from WP admin → CPT Agents → check post URL for ?post=NNN
AGENT_METADATA = [
    {
        "agent_name": "research-analyst",
        "display_title": "The Research Analyst",
        "description": (
            "Monitors live price feeds, news sources, and market signals before every "
            "article enters production. Gathers authoritative sources, identifies recent "
            "developments, and maps reader problems to recommended services."
        ),
        "tier": "intelligence",
        "is_public": True,
        "specialisms": ["Market Research", "SERP Analysis", "Buyer Psychology", "Data Sourcing"],
        "wp_agent_post_id": None,  # TODO: set from WP admin
    },
    {
        "agent_name": "planning",
        "display_title": "The Content Strategist",
        "description": (
            "Transforms research bundles into structured article blueprints. "
            "Selects the best content format for reader intent and maps internal links."
        ),
        "tier": "editorial",
        "is_public": True,
        "specialisms": ["Content Architecture", "SEO Planning", "Reader Intent", "Internal Linking"],
        "wp_agent_post_id": None,
    },
    {
        "agent_name": "content",
        "display_title": "The Writer",
        "description": (
            "Produces full article drafts with E-E-A-T compliance, affiliate integration, "
            "and reader-intent alignment. Every claim is sourced from the research bundle."
        ),
        "tier": "editorial",
        "is_public": True,
        "specialisms": ["Long-form Writing", "E-E-A-T", "Affiliate Integration", "SEO Copywriting"],
        "wp_agent_post_id": None,
    },
    {
        "agent_name": "judge",
        "display_title": "The Editor",
        "description": (
            "Reviews every stage output against strict quality thresholds before "
            "the pipeline advances. Provides structured feedback for retry loops."
        ),
        "tier": "editorial",
        "is_public": True,
        "specialisms": ["Quality Assurance", "Scoring", "Editorial Standards"],
        "wp_agent_post_id": None,
    },
    {
        "agent_name": "media",
        "display_title": "The Visual Producer",
        "description": (
            "Generates featured images and infographics to complement article content. "
            "Uploads directly to WordPress media library."
        ),
        "tier": "editorial",
        "is_public": True,
        "specialisms": ["Image Generation", "Infographics", "Visual Design"],
        "wp_agent_post_id": None,
    },
    {
        "agent_name": "publishing",
        "display_title": "The Publisher",
        "description": (
            "Assembles the final WordPress payload and creates the article draft, "
            "attaching media, categories, tags, and affiliate disclosures."
        ),
        "tier": "editorial",
        "is_public": False,
        "specialisms": ["WordPress API", "Content Publishing"],
        "wp_agent_post_id": None,
    },
    {
        "agent_name": "social",
        "display_title": "The Social Strategist",
        "description": (
            "Generates platform-specific social posts for each published article, "
            "applying emotional trigger classification for maximum engagement."
        ),
        "tier": "distribution",
        "is_public": True,
        "specialisms": ["Twitter/X", "LinkedIn", "Facebook", "Emotional Triggers"],
        "wp_agent_post_id": None,
    },
    {
        "agent_name": "performance-intel",
        "display_title": "The Analytics Specialist",
        "description": (
            "Pulls GA4, Clarity, and Search Console data weekly to generate "
            "actionable recommendations and validate scoring model accuracy."
        ),
        "tier": "analysis",
        "is_public": True,
        "specialisms": ["Google Analytics", "Search Console", "Heatmaps", "Conversion Optimisation"],
        "wp_agent_post_id": None,
    },
]


async def seed():
    dsn = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn)

    for meta in AGENT_METADATA:
        # Upsert — insert if not exists, update if exists
        result = await conn.execute(
            """
            INSERT INTO agent_configs (agent_name, model, display_title, description,
                                       tier, is_public, specialisms, wp_agent_post_id,
                                       updated_at)
            VALUES ($1, 'claude-sonnet-4-6', $2, $3, $4, $5, $6, $7, NOW())
            ON CONFLICT (agent_name) DO UPDATE SET
                display_title    = EXCLUDED.display_title,
                description      = EXCLUDED.description,
                tier             = EXCLUDED.tier,
                is_public        = EXCLUDED.is_public,
                specialisms      = EXCLUDED.specialisms,
                wp_agent_post_id = EXCLUDED.wp_agent_post_id,
                updated_at       = NOW()
            """,
            meta["agent_name"],
            meta["display_title"],
            meta["description"],
            meta["tier"],
            meta["is_public"],
            meta["specialisms"],
            meta["wp_agent_post_id"],
        )
        print(f"  ✓ {meta['agent_name']} — {result}")

    await conn.close()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(seed())