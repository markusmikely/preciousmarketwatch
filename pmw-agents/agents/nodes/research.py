# agents/nodes/research.py

async def run(state: PipelineState) -> PipelineState:
    topic   = state["topic"]
    attempt = state["attempt_number"]

    # ── Gather all data in parallel ───────────────────────────
    price_data, news_items, serp_data = await asyncio.gather(
        get_current_prices(topic["topic_name"]),
        search_recent_news(
            keyword  = topic["target_keyword"],
            days_back= 30 + (attempt * 15),
            min_results= 5
        ),
        fetch_serp_context(topic["target_keyword"]),  # NEW
    )

    # serp_data contains:
    # - top_result_formats: ["listicle", "guide", "comparison"]
    # - paa_questions: ["How much gold should I own?", ...]
    # - featured_snippet_type: "table" | "paragraph" | "list" | null
    # - competitor_titles: [str × 5]

    prompt_vars = {
        **build_base_vars(topic),
        "price_data":    json.dumps(price_data),
        "news_items":    json.dumps(news_items),
        "serp_context":  json.dumps(serp_data),  # NEW
    }

    output, usage = await tracked_llm_call(
        agent_name   = "research",
        template_key = "research",
        variables    = prompt_vars,
        run_id       = state["run_id"],
        attempt      = attempt,
    )

    # reader_intent extracted from research output and stored in state
    return {
        **state,
        "research_output": output,
        "reader_intent":   output.get("reader_intent"),  # NEW
        "current_stage":   "research",
        "model_usage":     state["model_usage"] + [usage],
    }