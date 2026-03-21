"""
agents/services/__init__.py — ServiceContainer

    from services import services
    await services.research_results.save(run_id, topic_wp_id, ...)
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
from services.research_results_service import ResearchResultsService


class ServiceContainer:
    def __init__(self) -> None:
        self.llm              = LLMService()
        self.events           = EventService()
        self.costs            = CostTrackingService()
        self.workflows        = WorkflowService()
        self.topics           = TopicService()
        self.affiliates       = AffiliateService()
        self.serp             = SerpService()
        self.market           = MarketService()
        self.buyer            = BuyerResearchService()
        self.competitors      = CompetitorService()
        self.tools            = ToolsService()
        self.pages            = PageManagementService()
        self.research_results = ResearchResultsService()


services = ServiceContainer()