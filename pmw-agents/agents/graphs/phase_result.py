# graphs/phase_result.py

from dataclasses import dataclass, field


@dataclass
class PhaseResult:
    """
    What every subgraph.run() returns to the parent.

    The parent graph sees exactly this and nothing else.
    The subgraph's internal state never escapes this object.

    status:    "complete" | "failed" | "hitl"
    output:    The phase's primary output dict (research_bundle,
               content_plan, generation_result). None if failed.
    cost_usd:  Total LLM cost incurred by this phase run.
    errors:    List of error dicts — empty on success.
    meta:      Small set of values the parent needs to log or store
               (topic title, topic ID) without coupling to internal
               state field names.
    """
    run_id:   int         # workflow_runs.id
    status:   str
    output:   dict | None
    cost_usd: float = 0.0
    errors:   list = field(default_factory=list)
    meta:     dict = field(default_factory=dict)

    # def __iniit__(self, run_id: int, status: str, output: dict | None, cost_usd: float = 0.0, errors: list = field(default_factory=list), meta: dict = field(default_factory=dict)):
    #     self.run_id = run_id
    #     self.status = status
    #     self.output = output
    #     self.cost_usd = cost_usd
    #     self.errors = errors
    #     self.meta = meta

    @property
    def succeeded(self) -> bool:
        return self.status == "complete" and self.output is not None

    @property
    def needs_hitl(self) -> bool:
        return self.status == "hitl"