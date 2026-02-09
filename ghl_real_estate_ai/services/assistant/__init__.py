"""
Assistant Service Package - Decomposed from the ClaudeAssistant god class.

Provides focused service modules:
- MarketContextService: Market-aware intelligence for messaging
- UIRenderingService: Streamlit sidebar panel and chat interface
- ResponseGenerationService: AI response generation and reporting
- ProactiveIntelligenceService: AI Concierge proactive insights
- RetentionScriptService: Market-aware retention scripts
- SemanticCacheMatchService: Property match explanations with caching
- SemanticResponseCache: High-performance semantic cache for AI responses
"""

from ghl_real_estate_ai.services.assistant.market_context_service import MarketContextService
from ghl_real_estate_ai.services.assistant.proactive_intelligence_service import ProactiveIntelligenceService
from ghl_real_estate_ai.services.assistant.response_generation_service import ResponseGenerationService
from ghl_real_estate_ai.services.assistant.retention_script_service import RetentionScriptService
from ghl_real_estate_ai.services.assistant.semantic_cache_service import (
    SemanticCacheMatchService,
    SemanticResponseCache,
)
from ghl_real_estate_ai.services.assistant.ui_rendering_service import UIRenderingService

__all__ = [
    "MarketContextService",
    "UIRenderingService",
    "ResponseGenerationService",
    "ProactiveIntelligenceService",
    "RetentionScriptService",
    "SemanticCacheMatchService",
    "SemanticResponseCache",
]
