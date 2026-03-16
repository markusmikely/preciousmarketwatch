"""
agents/services/__init__.py — ServiceContainer

Exposes all services as attributes of a single `services` object.
Import this everywhere instead of importing individual service classes:

    from services import services

    # In an agent:
    result = await services.llm.generate(model_config, prompt, run_id, stage, attempt)
    await services.events.emit(event_type, run_id, agent, stage, payload)

    # In a node:
    topics     = await services.topics.get_eligible_topics()
    affiliates = await services.affiliates.get_active_affiliates()
    serp       = await services.serp.research_keyword("gold isa uk")

All services are stateless — they hold no connections themselves.
Every service resolves infrastructure via get_infrastructure() at call time.
The ServiceContainer is a plain object; it does not need connect()/close().
"""

from services.llm_service import LLMService
from services.event_service import EventService
from services.cost_tracking_service import CostTrackingService

from services.workflow_service import WorkflowService
from services.topic_service import TopicService
from services.affiliate_service import AffiliateService
from services.serp_service import SerpService
from services.market_service import MarketService
from services.buyer_service import BuyerResearchService
from services.competitor_service import CompetitorService
from services.tools_service import ToolsService
from services.page_service import PageManagementService


class ServiceContainer:
    """
    Single container for all PMW services.

    Instantiated once at module level as `services`.
    Each attribute is a stateless service instance.

    Adding a new service:
      1. Create agents/services/my_service.py
      2. Import and add as an attribute here
      3. Access via services.my_service anywhere in the codebase
    """

    def __init__(self) -> None:
        # ── Core pipeline services ─────────────────────────────────────
        self.llm    = LLMService()
        self.events = EventService()
        self.costs  = CostTrackingService()

        # ── Workflow management ────────────────────────────────────────
        self.workflows = WorkflowService()

        # ── Research flow services ─────────────────────────────────────
        self.topics      = TopicService()
        self.affiliates  = AffiliateService()
        self.serp        = SerpService()
        self.market      = MarketService()
        self.buyer       = BuyerResearchService()
        self.competitors = CompetitorService()
        self.tools       = ToolsService()
        self.pages       = PageManagementService()


# Single global instance — import this, not the class
services = ServiceContainer()