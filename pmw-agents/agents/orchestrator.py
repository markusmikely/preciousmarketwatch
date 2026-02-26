# agents/orchestrator.py
def build_content_pipeline(checkpointer) -> StateGraph:
    g = StateGraph(PipelineState)

    g.add_node("task_loader",    task_loader.run)
    g.add_node("research",       research.run)
    g.add_node("judge_research", judge.evaluate_research)
    g.add_node("planning",       planning.run)
    g.add_node("judge_planning", judge.evaluate_planning)
    g.add_node("content",        content.run)
    g.add_node("judge_content",  judge.evaluate_content)
    g.add_node("media",          media.run)          # NEW — no Judge needed
    g.add_node("publishing",     publishing.run)
    g.add_node("handle_failure", handle_max_retries)

    g.set_entry_point("task_loader")
    g.add_edge("task_loader",    "research")
    g.add_edge("research",       "judge_research")

    g.add_conditional_edges("judge_research", route_after_judge, {
        "pass":        "planning",
        "retry":       "research",
        "max_retries": "handle_failure",
    })
    g.add_edge("planning",       "judge_planning")
    g.add_conditional_edges("judge_planning", route_after_judge, {
        "pass":        "content",
        "retry":       "planning",
        "max_retries": "handle_failure",
    })
    g.add_edge("content",        "judge_content")
    g.add_conditional_edges("judge_content", route_after_judge, {
        "pass":        "media",          # content → media before publishing
        "retry":       "content",
        "max_retries": "handle_failure",
    })
    g.add_edge("media",          "publishing")  # media always proceeds
    g.add_edge("publishing",     END)
    g.add_edge("handle_failure", END)

    return g.compile(
        checkpointer=checkpointer,
        interrupt_before=["handle_failure"]
    )