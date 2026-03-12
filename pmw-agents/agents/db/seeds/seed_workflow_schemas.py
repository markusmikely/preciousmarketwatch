"""
Seed workflow_schemas, workflow_schema_nodes, workflow_schema_edges.
Run: python -m agents.db.seeds.seed_workflow_schemas
"""
import asyncio
import os
import asyncpg

SCHEMAS = [
    {
        "slug": "research_pipeline",
        "display_name": "Research Pipeline",
        "description": (
            "8-stage research workflow. Selects a topic, scores affiliates, builds a brief, "
            "runs parallel keyword/market/competitor research, synthesises buyer psychology, "
            "maps tools, and assembles a validated research bundle."
        ),
        "version": "1.0",
        "wp_persona_post_id": None,  # TODO: set to WP post ID of your 'Research Analyst' agent CPT
        "nodes": [
            # Stage 1 — sequential
            {"key": "stage1.topic_loader",      "name": "Topic Loader",           "type": "agent",   "description": "Fetches candidate topics from WordPress REST API"},
            {"key": "stage1.topic_selector",    "name": "Topic Selector",         "type": "agent",   "description": "Scores and selects best topic by priority and schedule"},
            {"key": "stage1.affiliate_loader",  "name": "Affiliate Loader",       "type": "agent",   "description": "Loads active affiliates from Postgres"},
            {"key": "stage1.affiliate_scorer",  "name": "Affiliate Scorer",       "type": "agent",   "description": "Ranks affiliates against the selected topic"},
            {"key": "stage1.brief_locker",      "name": "Brief Locker",           "type": "agent",   "description": "Acquires topic lock, assembles and validates brief via LLM"},
            # Conditional after brief
            {"key": "route.after_brief",        "name": "Route after Brief",      "type": "conditional_router", "description": "Fan-out to parallel stages, or route to HITL/failure"},
            # Parallel wave 1
            {"key": "stage2.keyword_research",  "name": "Keyword Research",       "type": "agent",   "description": "SERP expansion, PAA capture, intent confirmation"},
            {"key": "stage3.market_context",    "name": "Market Context",         "type": "agent",   "description": "Live price fetch, trend, news, market stance"},
            {"key": "stage5.competitor_analysis","name": "Competitor Analysis",   "type": "agent",   "description": "Top ranking pages, content gaps, monetisation"},
            # Barriers
            {"key": "barrier.stage4",           "name": "Barrier: Stage 4",       "type": "barrier", "description": "Waits for stage2 + stage3"},
            {"key": "barrier.stage6",           "name": "Barrier: Stage 6",       "type": "barrier", "description": "Waits for stage4 + stage5"},
            {"key": "barrier.stage7",           "name": "Barrier: Stage 7",       "type": "barrier", "description": "Waits for stage2 + stage4 + stage6b"},
            {"key": "barrier.stage8",           "name": "Barrier: Stage 8",       "type": "barrier", "description": "Waits for stage5 + stage7"},
            # Stage 4, 6, 7, 8
            {"key": "stage4.top_factors",           "name": "Top Factors",            "type": "agent",   "description": "5 buyer decision factors with current data points"},
            {"key": "stage6.data_fetcher",          "name": "Data Fetcher",           "type": "agent",   "description": "Fetches Reddit, MSE, PAA, affiliate FAQ content"},
            {"key": "stage6.psychology_synthesis",  "name": "Psychology Synthesis",   "type": "agent",   "description": "Synthesises buyer objections, motivations, verbatims"},
            {"key": "stage7.tool_loader",           "name": "Tool Loader",            "type": "agent",   "description": "Loads available tools for topic category"},
            {"key": "stage7.tool_mapping",          "name": "Tool Mapping",           "type": "agent",   "description": "Maps tools to article sections"},
            {"key": "stage8.arc_coherence",         "name": "Arc Coherence Check",    "type": "agent",   "description": "LLM validates research forms a buying intent story"},
            {"key": "stage8.bundle_assembler",      "name": "Bundle Assembler",       "type": "agent",   "description": "Assembles validated research bundle for content pipeline"},
            # Terminals
            {"key": "hitl_gate",    "name": "HITL Gate",    "type": "hitl_gate",  "description": "Halts pipeline — operator review required"},
            {"key": "handle_failure","name": "Handle Failure","type": "terminal",  "description": "Records failure, releases topic lock"},
        ],
        "edges": [
            # Stage 1 sequential
            {"from": "stage1.topic_loader",      "to": "stage1.topic_selector",    "condition": None,  "label": None,                    "happy": True},
            {"from": "stage1.topic_selector",    "to": "stage1.affiliate_loader",  "condition": None,  "label": None,                    "happy": True},
            {"from": "stage1.affiliate_loader",  "to": "stage1.affiliate_scorer",  "condition": None,  "label": None,                    "happy": True},
            {"from": "stage1.affiliate_scorer",  "to": "stage1.brief_locker",      "condition": None,  "label": None,                    "happy": True},
            {"from": "stage1.brief_locker",      "to": "route.after_brief",        "condition": None,  "label": None,                    "happy": True},
            # Conditional fan-out
            {"from": "route.after_brief", "to": "stage2.keyword_research",   "condition": "continue", "label": "Brief valid",     "happy": True},
            {"from": "route.after_brief", "to": "stage3.market_context",     "condition": "continue", "label": "Brief valid",     "happy": True},
            {"from": "route.after_brief", "to": "stage5.competitor_analysis","condition": "continue", "label": "Brief valid",     "happy": True},
            {"from": "route.after_brief", "to": "hitl_gate",                 "condition": "hitl",     "label": "Coherence fail",  "happy": False},
            {"from": "route.after_brief", "to": "handle_failure",            "condition": "failed",   "label": "Fatal error",     "happy": False},
            # Into barrier.stage4
            {"from": "stage2.keyword_research",  "to": "barrier.stage4", "condition": None, "label": None, "happy": True},
            {"from": "stage3.market_context",    "to": "barrier.stage4", "condition": None, "label": None, "happy": True},
            {"from": "barrier.stage4",           "to": "stage4.top_factors", "condition": None, "label": None, "happy": True},
            # Into barrier.stage6
            {"from": "stage4.top_factors",       "to": "barrier.stage6", "condition": None, "label": None, "happy": True},
            {"from": "stage5.competitor_analysis","to": "barrier.stage6", "condition": None, "label": None, "happy": True},
            {"from": "barrier.stage6",           "to": "stage6.data_fetcher", "condition": None, "label": None, "happy": True},
            {"from": "stage6.data_fetcher",      "to": "stage6.psychology_synthesis", "condition": None, "label": None, "happy": True},
            # Into barrier.stage7
            {"from": "stage2.keyword_research",      "to": "barrier.stage7", "condition": None, "label": None, "happy": True},
            {"from": "stage4.top_factors",           "to": "barrier.stage7", "condition": None, "label": None, "happy": True},
            {"from": "stage6.psychology_synthesis",  "to": "barrier.stage7", "condition": None, "label": None, "happy": True},
            {"from": "barrier.stage7",           "to": "stage7.tool_loader",  "condition": None, "label": None, "happy": True},
            {"from": "stage7.tool_loader",       "to": "stage7.tool_mapping", "condition": None, "label": None, "happy": True},
            # Into barrier.stage8
            {"from": "stage5.competitor_analysis","to": "barrier.stage8", "condition": None, "label": None, "happy": True},
            {"from": "stage7.tool_mapping",       "to": "barrier.stage8", "condition": None, "label": None, "happy": True},
            {"from": "barrier.stage8",            "to": "stage8.arc_coherence", "condition": None, "label": None, "happy": True},
            # Arc coherence conditional
            {"from": "stage8.arc_coherence", "to": "stage8.bundle_assembler", "condition": "continue", "label": "Arc valid",    "happy": True},
            {"from": "stage8.arc_coherence", "to": "hitl_gate",               "condition": "hitl",     "label": "Arc incoherent","happy": False},
            {"from": "stage8.arc_coherence", "to": "handle_failure",          "condition": "failed",   "label": "Fatal error",  "happy": False},
        ],
    },
]


async def seed():
    dsn = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn)

    for schema in SCHEMAS:
        # Upsert schema row
        schema_id = await conn.fetchval(
            """
            INSERT INTO workflow_schemas (slug, display_name, description, version, wp_persona_post_id)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (slug) DO UPDATE SET
                display_name      = EXCLUDED.display_name,
                description       = EXCLUDED.description,
                version           = EXCLUDED.version,
                wp_persona_post_id = EXCLUDED.wp_persona_post_id,
                updated_at        = NOW()
            RETURNING id
            """,
            schema["slug"],
            schema["display_name"],
            schema["description"],
            schema["version"],
            schema["wp_persona_post_id"],
        )
        print(f"  schema '{schema['slug']}' → id={schema_id}")

        # Delete and re-insert nodes (idempotent)
        await conn.execute("DELETE FROM workflow_schema_nodes WHERE schema_id = $1", schema_id)
        for node in schema["nodes"]:
            await conn.execute(
                """
                INSERT INTO workflow_schema_nodes
                    (schema_id, node_key, display_name, description, node_type)
                VALUES ($1, $2, $3, $4, $5)
                """,
                schema_id, node["key"], node["name"], node["description"], node["type"],
            )

        # Delete and re-insert edges
        await conn.execute("DELETE FROM workflow_schema_edges WHERE schema_id = $1", schema_id)
        for edge in schema["edges"]:
            await conn.execute(
                """
                INSERT INTO workflow_schema_edges
                    (schema_id, from_node_key, to_node_key, condition, label, is_happy_path)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                schema_id, edge["from"], edge["to"],
                edge["condition"], edge["label"], edge["happy"],
            )

        print(f"    {len(schema['nodes'])} nodes, {len(schema['edges'])} edges seeded")

    await conn.close()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(seed())