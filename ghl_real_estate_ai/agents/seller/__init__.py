"""
Jorge Seller Bot - Modular Implementation

This package contains the decomposed seller bot modules.
Import JorgeSellerBot from the parent module: `from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot`

Available modules:
- config: Configuration classes (JorgeFeatureConfig, QualificationResult)
- cma_service: CMA generation and valuation defense (CMAService)
- market_analyzer: Market conditions and pricing guidance (MarketAnalyzer)
- stall_detector: Stall detection and property condition extraction (StallDetector)
- response_generator: Response generation with sentiment and persona (ResponseGenerator)
- strategy_selector: Strategy selection with Track 3.1 intelligence (StrategySelector)
- listing_service: Listing preparation and staging recommendations (ListingService)
- followup_service: Automated follow-up execution (FollowUpService)
- handoff_manager: Handoff context management (HandoffManager)
- conversation_memory: Conversation memory and adaptive questioning (ConversationMemory, AdaptiveQuestionEngine)
- executive_service: Executive brief generation (ExecutiveService)
- objection_handler: Objection handling with graduated responses (ObjectionHandler)
"""

# Export key components for advanced usage
# NOTE: JorgeSellerBot should be imported from ghl_real_estate_ai.agents.jorge_seller_bot
# to avoid circular imports

from ghl_real_estate_ai.agents.seller.cma_service import CMAService
from ghl_real_estate_ai.agents.seller.config import JorgeFeatureConfig, QualificationResult
from ghl_real_estate_ai.agents.seller.conversation_memory import AdaptiveQuestionEngine, ConversationMemory
from ghl_real_estate_ai.agents.seller.executive_service import ExecutiveService
from ghl_real_estate_ai.agents.seller.followup_service import FollowUpService
from ghl_real_estate_ai.agents.seller.handoff_manager import HandoffManager
from ghl_real_estate_ai.agents.seller.listing_service import ListingService
from ghl_real_estate_ai.agents.seller.market_analyzer import MarketAnalyzer
from ghl_real_estate_ai.agents.seller.objection_handler import ObjectionHandler
from ghl_real_estate_ai.agents.seller.response_generator import ResponseGenerator
from ghl_real_estate_ai.agents.seller.stall_detector import StallDetector
from ghl_real_estate_ai.agents.seller.strategy_selector import StrategySelector

__all__ = [
    # NOTE: Import JorgeSellerBot from ghl_real_estate_ai.agents.jorge_seller_bot
    # Configuration
    "JorgeFeatureConfig",
    "QualificationResult",
    # Services
    "CMAService",
    "MarketAnalyzer",
    "StallDetector",
    "ResponseGenerator",
    "StrategySelector",
    "ListingService",
    "FollowUpService",
    "HandoffManager",
    "ConversationMemory",
    "AdaptiveQuestionEngine",
    "ExecutiveService",
    "ObjectionHandler",
]
