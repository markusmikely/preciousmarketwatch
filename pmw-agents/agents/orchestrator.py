# orchestrator.py
"""
Orchestrator for running workflows in a continuous loop.

Runs the pipeline every PIPELINE_INTERVAL_SECONDS (default 300 = 5 minutes).
Each cycle:
  1. Creates a new workflow_runs row (status=pending)
  2. Sets status=running before invoking the graph
  3. Runs the full pipeline
  4. Updates final status (complete/failed)
  5. Sleeps until the next cycle

If the pipeline finds no topics, it logs the result and waits for the next cycle.
Fatal errors are caught and logged — the loop continues.
"""
import asyncio
import logging
import argparse
import os
from datetime import datetime, timezone

from db.run import create_workflow_run

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("pmw.orchestrator")

# How often the pipeline loop runs (seconds). Default: 5 minutes.
PIPELINE_INTERVAL_SECONDS = int(os.environ.get("PIPELINE_INTERVAL_SECONDS", "300"))


async def run_single_workflow(triggered_by: str = "scheduler") -> bool:
    """
    Run a single workflow cycle.

    Returns True if the workflow completed successfully, False otherwise.
    Does NOT raise — all errors are caught and logged.
    """
    from graphs.main_graph import MainGraph
    from infrastructure import get_infrastructure

    run_id = None
    graph = None

    try:
        # 1. Create workflow_runs row — status='pending'
        run_id = create_workflow_run(triggered_by=triggered_by)
        log.info(f"Created workflow run | run_id={run_id}")

        # 2. Set status='running' BEFORE invoking the graph
        infra = get_infrastructure()
        await infra.postgres.execute(
            """
            UPDATE workflow_runs
            SET status = 'running', current_stage = 'initialising'
            WHERE id = $1
            """,
            run_id,
        )
        log.info(f"Workflow run {run_id} → status=running")

        # 3. Build and run the graph
        graph = await MainGraph.create()

        result = await graph.run({
            "run_id": run_id,
            "triggered_by": triggered_by,
        })

        # 4. Update final status in workflow_runs
        if result.succeeded:
            await infra.postgres.execute(
                """
                UPDATE workflow_runs
                SET status = 'complete',
                    completed_at = NOW(),
                    final_score = $1,
                    total_cost_usd = $2,
                    wp_post_id = $3
                WHERE id = $4
                """,
                result.cost_usd,  # using cost as a proxy for score for now
                result.cost_usd,
                (result.output or {}).get("wp_post_id"),
                run_id,
            )
        else:
            error_summary = "; ".join(
                e.get("error", str(e)) for e in (result.errors or [])
            )[:500]
            await infra.postgres.execute(
                """
                UPDATE workflow_runs
                SET status = 'failed',
                    failed_at = NOW(),
                    total_cost_usd = $1
                WHERE id = $2
                """,
                result.cost_usd,
                run_id,
            )

        # 5. Print results
        status_icon = "✅ SUCCEEDED" if result.succeeded else "❌ FAILED"
        log.info(
            f"Workflow {status_icon} | run_id={run_id} | "
            f"status={result.status} | cost=${result.cost_usd:.4f} | "
            f"topic={result.meta.get('topic_title', 'none')}"
        )

        return result.succeeded

    except Exception as e:
        log.error(f"Workflow run {run_id or '?'} failed with error: {e}", exc_info=True)

        # Mark the run as failed in DB if we have a run_id
        if run_id:
            try:
                infra = get_infrastructure()
                await infra.postgres.execute(
                    """
                    UPDATE workflow_runs
                    SET status = 'failed', failed_at = NOW()
                    WHERE id = $1 AND status NOT IN ('complete', 'failed')
                    """,
                    run_id,
                )
            except Exception:
                log.error(f"Failed to update run {run_id} status to failed")

        return False

    finally:
        # Clean up graph resources if they exist
        if graph and hasattr(graph, 'close'):
            try:
                await graph.close()
            except Exception:
                pass


async def run_pipeline_loop(triggered_by: str = "scheduler") -> None:
    """
    Continuous pipeline loop. Runs a workflow cycle every PIPELINE_INTERVAL_SECONDS.

    The loop never exits unless the process is killed.
    Individual cycle failures are logged but do not stop the loop.
    """
    log.info(
        f"Pipeline loop starting | interval={PIPELINE_INTERVAL_SECONDS}s "
        f"({PIPELINE_INTERVAL_SECONDS // 60}m) | triggered_by={triggered_by}"
    )

    cycle = 0
    while True:
        cycle += 1
        cycle_start = datetime.now(timezone.utc)

        log.info(f"━━━ Pipeline cycle {cycle} starting at {cycle_start.isoformat()} ━━━")

        try:
            success = await run_single_workflow(triggered_by=triggered_by)
            status = "succeeded" if success else "failed"
        except Exception as exc:
            # This should not happen (run_single_workflow catches everything)
            # but just in case:
            log.error(f"Unexpected error in pipeline cycle {cycle}: {exc}", exc_info=True)
            status = "error"

        elapsed = (datetime.now(timezone.utc) - cycle_start).total_seconds()
        log.info(
            f"━━━ Pipeline cycle {cycle} {status} in {elapsed:.1f}s | "
            f"next cycle in {PIPELINE_INTERVAL_SECONDS}s ━━━"
        )

        # Sleep until next cycle
        await asyncio.sleep(PIPELINE_INTERVAL_SECONDS)


# Legacy single-run function for backwards compatibility
async def run_workflow(triggered_by: str = "manual") -> None:
    """Run a single workflow (legacy interface). Use run_pipeline_loop() for continuous operation."""
    await run_single_workflow(triggered_by=triggered_by)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run PMW workflow")
    parser.add_argument(
        "--triggered-by",
        type=str,
        default="manual",
        help="Source that triggered the workflow",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single cycle instead of the continuous loop",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Override pipeline interval in seconds (default: 300)",
    )

    args = parser.parse_args()

    if args.interval:
        PIPELINE_INTERVAL_SECONDS = args.interval

    if args.once:
        asyncio.run(run_single_workflow(triggered_by=args.triggered_by))
    else:
        asyncio.run(run_pipeline_loop(triggered_by=args.triggered_by))