# GET /workflow/schemas
@router.get("/workflow/schemas")
async def list_workflow_schemas(db=Depends(get_db)):
    schemas = await db.fetch(
        """
        SELECT ws.id, ws.slug, ws.display_name, ws.description, ws.version,
               ws.wp_persona_post_id, ws.is_active,
               json_agg(DISTINCT jsonb_build_object(
                   'node_key', n.node_key, 'display_name', n.display_name,
                   'node_type', n.node_type, 'description', n.description
               )) AS nodes,
               json_agg(DISTINCT jsonb_build_object(
                   'from', e.from_node_key, 'to', e.to_node_key,
                   'condition', e.condition, 'label', e.label,
                   'is_happy_path', e.is_happy_path
               )) AS edges
        FROM workflow_schemas ws
        LEFT JOIN workflow_schema_nodes n ON n.schema_id = ws.id
        LEFT JOIN workflow_schema_edges e ON e.schema_id = ws.id
        WHERE ws.is_active = true
        GROUP BY ws.id
        """
    )
    return [dict(s) for s in schemas]


# GET /runs/{run_id}/logs
@router.get("/runs/{run_id}/logs")
async def get_run_logs(run_id: int, level: str = None, limit: int = 200, db=Depends(get_db)):
    query = """
        SELECT id, level, source, agent_name, stage_name, message, payload, created_at
        FROM workflow_logs
        WHERE run_id = $1
    """
    params = [run_id]
    if level:
        query += " AND level = $2"
        params.append(level.upper())
    query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
    params.append(limit)
    rows = await db.fetch(query, *params)
    return [dict(r) for r in rows]


# GET /runs/{run_id}/llm-calls
@router.get("/runs/{run_id}/llm-calls")
async def get_run_llm_calls(run_id: int, db=Depends(get_db)):
    rows = await db.fetch(
        """
        SELECT id, agent_name, stage_name, attempt, provider, model,
               input_tokens, output_tokens, cost_usd, latency_ms, success, error, called_at
        FROM llm_call_logs
        WHERE run_id = $1
        ORDER BY called_at
        """,
        run_id,
    )
    return [dict(r) for r in rows]


# GET /agents/public  — now DB-driven (replaces hardcoded list)
@router.get("/agents/public")
async def get_public_agents(db=Depends(get_db)):
    rows = await db.fetch(
        """
        SELECT agent_name, display_title, description, tier, specialisms,
               wp_agent_post_id, active
        FROM agent_configs
        WHERE is_public = true AND active = true
        ORDER BY tier, agent_name
        """
    )
    return [dict(r) for r in rows]