# orchestrator.py
"""
Orchestrator for running workflows.
Can be used by main.py or run manually for testing.
"""
import asyncio
import logging
import argparse
from graphs.main_graph import MainGraph
from db.run import create_workflow_run

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("pmw.orchestrator")


async def run_workflow(triggered_by: str = "manual") -> None:
    """
    Run a single workflow.
    
    Args:
        triggered_by: Source that triggered the workflow (manual, scheduler, etc.)
    """
    log.info(f"Starting workflow (triggered_by={triggered_by})...")
    
    try:
        # Create workflow_runs row — run_id = workflow_runs.id
        run_id = create_workflow_run(triggered_by=triggered_by)
        log.info(f"Created workflow run | run_id={run_id}")

        # Build the graph
        graph = await MainGraph.create()
        
        # Run the workflow
        result = await graph.run({
            "run_id": run_id,
            "triggered_by": triggered_by,
        })
        
        # Print results
        print("\n" + "="*50)
        print(f"Workflow {'✅ SUCCEEDED' if result.succeeded else '❌ FAILED'}")
        print("="*50)
        print(f"Run ID:  {result.run_id}")
        print(f"Status:  {result.status}")
        print(f"Topic:   {result.meta.get('topic_title', 'none')}")
        print(f"Phases:  {(result.output or {}).get('phase_statuses', {})}")
        print(f"Cost:    ${result.cost_usd:.4f}")
        print(f"Post ID: {(result.output or {}).get('wp_post_id', 'none')}")
        print("="*50)
        
        # Clean up
        if hasattr(graph, 'close'):
            await graph.close()
            
    except Exception as e:
        log.error(f"Workflow failed with error: {e}")
        raise


if __name__ == "__main__":
    # Allow orchestrator to be run directly for testing
    parser = argparse.ArgumentParser(description="Run PMW workflow manually")
    parser.add_argument(
        "--triggered-by", 
        type=str, 
        default="manual",
        help="Source that triggered the workflow (manual, scheduler, etc.)"
    )
    
    args = parser.parse_args()
    asyncio.run(run_workflow(triggered_by=args.triggered_by))