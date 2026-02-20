"""
Lead Bot - Modular Implementation

This package contains the decomposed lead bot modules.
Import LeadBotWorkflow from the parent module: `from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow`

Available modules:
- config: Configuration classes (LeadBotConfig, ResponsePattern, SequenceOptimization)
- cache: TTL-aware LRU cache (TTLLRUCache)
- behavioral_analytics: Lead behavior pattern analysis (BehavioralAnalyticsEngine)
- personality_adapter: Personality-based message adaptation (PersonalityAdapter)
- temperature_engine: Lead temperature prediction (TemperaturePredictionEngine)
- workflow_nodes: LangGraph workflow node implementations (WorkflowNodes)
- workflow_nodes_enhanced: Enhanced workflow nodes (EnhancedWorkflowNodes)
- workflow_builder: Workflow graph construction (WorkflowBuilder)
- response_generator: Message construction and response generation (ResponseGenerator)
- handoff_manager: Cross-bot handoff coordination (HandoffManager)
- routing: Lead routing and classification logic (LeadRouter)
- constants: Shared constants and enums
"""

# Export key components for advanced usage
# NOTE: LeadBotWorkflow should be imported from ghl_real_estate_ai.agents.lead_bot
# to avoid circular imports

from ghl_real_estate_ai.agents.lead.behavioral_analytics import BehavioralAnalyticsEngine
from ghl_real_estate_ai.agents.lead.cache import TTLLRUCache
from ghl_real_estate_ai.agents.lead.config import (
    LeadBotConfig,
    LeadProcessingResult,
    ResponsePattern,
    SequenceOptimization,
)
from ghl_real_estate_ai.agents.lead.constants import (
    BUYING_SIGNALS,
    CACHE_MAX_ENTRIES,
    CACHE_TTL_SECONDS,
    DEFAULT_BEST_CONTACT_TIMES,
    DEFAULT_CHANNEL_PREFS,
    MAX_CONVERSATION_HISTORY,
    MILESTONE_MESSAGES,
    SMS_MAX_LENGTH,
    STALL_BREAKER_MAPPING,
)
from ghl_real_estate_ai.agents.lead.handoff_manager import HandoffManager
from ghl_real_estate_ai.agents.lead.personality_adapter import PersonalityAdapter
from ghl_real_estate_ai.agents.lead.response_generator import ResponseGenerator
from ghl_real_estate_ai.agents.lead.routing import LeadRouter
from ghl_real_estate_ai.agents.lead.temperature_engine import TemperaturePredictionEngine
from ghl_real_estate_ai.agents.lead.workflow_builder import WorkflowBuilder
from ghl_real_estate_ai.agents.lead.workflow_nodes import WorkflowNodes
from ghl_real_estate_ai.agents.lead.workflow_nodes_enhanced import EnhancedWorkflowNodes

__all__ = [
    # NOTE: Import LeadBotWorkflow from ghl_real_estate_ai.agents.lead_bot
    # Configuration
    "LeadBotConfig",
    "LeadProcessingResult",
    "ResponsePattern",
    "SequenceOptimization",
    # Cache
    "TTLLRUCache",
    # Analytics & Adaptation
    "BehavioralAnalyticsEngine",
    "PersonalityAdapter",
    "TemperaturePredictionEngine",
    # Workflow Components
    "WorkflowNodes",
    "EnhancedWorkflowNodes",
    "WorkflowBuilder",
    "ResponseGenerator",
    "HandoffManager",
    "LeadRouter",
    # Constants
    "MAX_CONVERSATION_HISTORY",
    "SMS_MAX_LENGTH",
    "CACHE_MAX_ENTRIES",
    "CACHE_TTL_SECONDS",
    "DEFAULT_CHANNEL_PREFS",
    "DEFAULT_BEST_CONTACT_TIMES",
    "MILESTONE_MESSAGES",
    "STALL_BREAKER_MAPPING",
    "BUYING_SIGNALS",
]