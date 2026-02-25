"""
PMW Worker — Process a single workflow stage
Research → Plan → Content → Publish (V1 pipeline)
"""
import json

import redis
from shared.config import REDIS_URL, QUEUE_AGENT, CHANNEL_EVENTS
from shared.db import get_session
from shared.models import WorkflowRun, WorkflowStage, Topic

# Stage order for V1
STAGE_ORDER = ["research", "planning", "content", "publish"]


def _get_next_stage(current: str) -> str | None:
    try:
        i = STAGE_ORDER.index(current)
        if i + 1 < len(STAGE_ORDER):
            return STAGE_ORDER[i + 1]
    except ValueError:
        pass
    return None


def _publish(r: redis.Redis, event_type: str, payload: dict):
    r.publish(CHANNEL_EVENTS, json.dumps({"type": event_type, "payload": payload}))


def process_stage(stage_id: int):
    with get_session() as session:
        stage = session.query(WorkflowStage).filter(WorkflowStage.id == stage_id).first()
        if not stage or stage.status != "running":
            return

        run = session.query(WorkflowRun).filter(WorkflowRun.id == stage.run_id).first()
        if not run:
            return

        topic = session.query(Topic).filter(Topic.id == run.topic_id).first()
        if not topic:
            return

    # Run agent (placeholder — calls pipeline nodes)
    output, score, passed = _run_stage_agent(stage, run, topic)

    r = redis.from_url(REDIS_URL)
    try:
        with get_session() as session:
            stage = session.query(WorkflowStage).filter(WorkflowStage.id == stage_id).first()
            if not stage:
                return

            stage.output_json = json.dumps(output) if isinstance(output, dict) else str(output)
            stage.score = score
            stage.status = "completed" if passed else "failed"
            session.flush()

            run = session.query(WorkflowRun).filter(WorkflowRun.id == stage.run_id).first()
            run.current_stage = stage.stage_name

            if passed:
                next_stage_name = _get_next_stage(stage.stage_name)
                if next_stage_name:
                    next_stage = WorkflowStage(
                        run_id=run.id,
                        stage_name=next_stage_name,
                        status="pending",
                        attempt_number=1,
                    )
                    session.add(next_stage)
                    session.flush()
                    run.current_stage = next_stage_name

                    # Signal next stage
                    r.lpush(QUEUE_AGENT, json.dumps({"stage_id": next_stage.id, "run_id": run.id}))
                    _publish(r, "stage.complete", {
                        "stage_id": stage.id,
                        "run_id": run.id,
                        "next_stage_id": next_stage.id,
                        "score": score,
                    })
                else:
                    # Pipeline complete
                    run.status = "completed"
                    run.final_score = score
                    from datetime import datetime
                    run.completed_at = datetime.utcnow()
                    _publish(r, "run.complete", {"run_id": run.id, "final_score": score})
            else:
                run.status = "failed"
                _publish(r, "stage.failed", {"stage_id": stage.id, "run_id": run.id, "score": score})
    finally:
        r.close()


def _run_stage_agent(stage: WorkflowStage, run: WorkflowRun, topic: Topic) -> tuple[dict | str, float, bool]:
    """Execute the agent for this stage. Returns (output, score, passed)."""
    # V1 placeholder: return mock output and pass
    # Real impl: call Research/Planning/Content/Publisher nodes + Judge
    output = {"placeholder": True, "stage": stage.stage_name}
    score = 0.85
    threshold = 0.75 if stage.stage_name == "research" else 0.80
    passed = score >= threshold
    return output, score, passed
