# agents/nodes/planning.py

async def run(state: PipelineState) -> PipelineState:
    topic          = state["topic"]
    research       = state["research_output"]
    reader_intent  = state["reader_intent"]

    # ── Fetch internal link opportunities ─────────────────────
    internal_links = await find_internal_links(
        keyword  = topic["target_keyword"],
        category = topic["topic_category"],
        limit    = 3,
    )
    # Calls WP REST API: GET /wp/v2/posts?search={keyword}&per_page=3

    # ── Select article template based on reader intent ─────────
    template_key = {
        "price_checker":       "planning_price_checker",
        "consideration_buyer": "planning_consideration",
        "curiosity_reader":    "planning_curiosity",
    }.get(reader_intent, "planning_consideration")  # default to consideration

    prompt_vars = {
        **build_base_vars(topic),
        "research_output_json": json.dumps(research),
        "internal_links":       json.dumps(internal_links),  # NEW
        "reader_intent":        reader_intent,                # NEW
        "serp_context":         json.dumps(
                                    research.get("serp_context", {})
                                ),
        "tool_links":           json.dumps(
                                    get_relevant_tool_links(
                                        topic["topic_category"]
                                    )
                                ),  # NEW
    }

    output, usage = await tracked_llm_call(
        agent_name   = "planning",
        template_key = template_key,
        variables    = prompt_vars,
        run_id       = state["run_id"],
        attempt      = state["attempt_number"],
    )

    return {
        **state,
        "planning_output": output,
        "current_stage":   "planning",
        "model_usage":     state["model_usage"] + [usage],
    }