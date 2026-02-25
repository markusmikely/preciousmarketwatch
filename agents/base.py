"""
PMW Agent Base — Cost logging and tracked LLM calls
Every LLM call logs tokens and cost before returning.
"""
import json
from datetime import datetime
from functools import wraps

import redis

REDIS_URL = "redis://localhost:6379"
CHANNEL = "pmw:events"
COST_LOG_KEY = "pmw:cost_log"


def _get_redis():
    return redis.from_url(REDIS_URL)


def calculate_cost(model: str, input_t: int, output_t: int) -> float:
    """Cost per million tokens (update as pricing changes)."""
    rates = {
        "claude-opus-4": {"in": 15.00, "out": 75.00},
        "claude-sonnet-4": {"in": 3.00, "out": 15.00},
        "gpt-4o": {"in": 5.00, "out": 15.00},
    }
    r = rates.get(model, {"in": 5.00, "out": 15.00})
    return (input_t / 1_000_000) * r["in"] + (output_t / 1_000_000) * r["out"]


def log_cost(entry: dict):
    """Append to Redis cost log and publish event."""
    entry["timestamp"] = datetime.utcnow().isoformat()
    r = _get_redis()
    r.lpush(COST_LOG_KEY, json.dumps(entry))
    r.publish(CHANNEL, json.dumps({"type": "cost_update", "payload": entry}))


def current_task_id() -> str | None:
    """Return current LangGraph task/thread ID if available."""
    return None


def tracked_llm_call(agent_name: str, prompt: str, model: str = "claude-sonnet-4"):
    """
    Call Anthropic/OpenAI and log cost. Returns response text.
    Use via LangGraph nodes — agent_name for attribution.
    """
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    usage = response.usage
    cost_usd = calculate_cost(
        model,
        usage.input_tokens,
        usage.output_tokens,
    )
    text = response.content[0].text if response.content else ""

    log_cost({
        "agent": agent_name,
        "model": model,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cost_usd": cost_usd,
        "task_id": current_task_id(),
    })

    return text
