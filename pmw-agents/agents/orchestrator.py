# orchestrator.py
import asyncio
import uuid
import logging
from graphs.main_graph import MainGraph

logging.basicConfig(level=logging.INFO)


async def run_workflow(triggered_by: str = "scheduler") -> None:
    # Build once at startup — reuse for every run in production
    graph = await MainGraph.create()

    result = await graph.run({
        "workflow_id":  str(uuid.uuid4()),
        "triggered_by": triggered_by,
    })

    print(f"\nWorkflow {'succeeded' if result.succeeded else 'FAILED'}")
    print(f"  Status:  {result.status}")
    print(f"  Topic:   {result.meta.get('topic_title', 'none')}")
    print(f"  Phases:  {(result.output or {}).get('phase_statuses', {})}")
    print(f"  Cost:    ${result.cost_usd:.4f}")
    print(f"  Post ID: {(result.output or {}).get('wp_post_id', 'none')}")


if __name__ == "__main__":
    asyncio.run(run_workflow(triggered_by="manual"))