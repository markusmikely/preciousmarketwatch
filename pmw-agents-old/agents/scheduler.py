"""
PMW Scheduler — Worker loop
BLPOP agent:queue, load stage from DB, process, update DB, signal next stage.
Postgres = source of truth. Redis = signal bus.
"""
import json
import os
import time

# Ensure agents/ is on path when run as main
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import redis
from shared.config import REDIS_URL, QUEUE_AGENT, CHANNEL_EVENTS
from shared.db import get_session
from shared.models import WorkflowRun, WorkflowStage, Topic

from worker import process_stage


def main():
    r = redis.from_url(REDIS_URL)
    print("[scheduler] Listening on", QUEUE_AGENT)

    while True:
        # BLPOP blocks until a message arrives
        result = r.blpop(QUEUE_AGENT, timeout=30)
        if not result:
            continue

        _, payload_raw = result
        try:
            payload = json.loads(payload_raw)
            stage_id = payload.get("stage_id")
            if not stage_id:
                print("[scheduler] Invalid payload: missing stage_id")
                continue
        except json.JSONDecodeError:
            print("[scheduler] Invalid JSON payload")
            continue

        with get_session() as session:
            stage = (
                session.query(WorkflowStage)
                .filter(
                    WorkflowStage.id == stage_id,
                    WorkflowStage.status == "pending",
                )
                .with_for_update(skip_locked=True)
                .first()
            )
            if not stage:
                # Idempotency: already claimed or processed
                continue

            stage.status = "running"
            session.flush()

        try:
            process_stage(stage_id)
        except Exception as e:
            print(f"[scheduler] Error processing stage {stage_id}: {e}")
            with get_session() as session:
                s = session.query(WorkflowStage).filter(WorkflowStage.id == stage_id).first()
                if s:
                    s.status = "failed"
                    s.judge_feedback = str(e)


if __name__ == "__main__":
    main()
