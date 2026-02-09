"""
Claude Assistant Service - Centralized AI Intelligence for the GHL Platform
Provides context-aware insights, action recommendations, and interactive support.

ENHANCED: Now includes multi-market awareness and churn recovery integration.

REFACTORED: This module is now a thin facade that delegates to focused service modules
in ghl_real_estate_ai.services.assistant/. The public API is fully preserved.
"""

from typing import Any, Dict, List, Optional

import streamlit as st

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.assistant.market_context_service import MarketContextService
from ghl_real_estate_ai.services.assistant.proactive_intelligence_service import ProactiveIntelligenceService
from ghl_real_estate_ai.services.assistant.response_generation_service import ResponseGenerationService
from ghl_real_estate_ai.services.assistant.retention_script_service import RetentionScriptService
from ghl_real_estate_ai.services.assistant.semantic_cache_service import (
    SemanticCacheMatchService,
    SemanticResponseCache,
)
from ghl_real_estate_ai.services.assistant.ui_rendering_service import UIRenderingService
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.churn_prediction_engine import ChurnEventTracker, ChurnReason
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.reengagement_engine import ReengagementEngine

logger = get_logger(__name__)


class ClaudeAssistant:
    """
    The brain of the platform's UI.
    Maintains state and provides context-specific intelligence using Claude Orchestrator.

    ENHANCED: Now includes multi-market awareness, churn recovery integration, and semantic response caching.

    This class is a facade that delegates to focused service modules:
    - MarketContextService
    - UIRenderingService
    - ResponseGenerationService
    - ProactiveIntelligenceService
    - RetentionScriptService
    - SemanticCacheMatchService
    """

    def __init__(self, context_type: str = "general", market_id: Optional[str] = None, proactive_mode: bool = False):
        self.context_type = context_type
        self.market_id = market_id
        self.proactive_mode = proactive_mode

        # Import here to avoid circular dependencies
        try:
            from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

            self.orchestrator = get_claude_orchestrator()
        except ImportError:
            self.orchestrator = None

        self.memory_service = MemoryService()
        self.analytics = AnalyticsService()

        # PERFORMANCE: Initialize caching service
        self.cache = get_cache_service()
        self.semantic_cache = SemanticResponseCache()

        # ENHANCED: Initialize market-aware components
        self.reengagement_engine = ReengagementEngine()
        self.churn_tracker = ChurnEventTracker(self.memory_service)

        # Initialize delegate services
        self._market_ctx = MarketContextService(market_id)
        # Expose market_registry from the delegate for backward compat
        self.market_registry = self._market_ctx.market_registry
        self._market_context_cache = self._market_ctx._market_context_cache

        self._ui = UIRenderingService(self.orchestrator, self.memory_service, self.analytics, self._market_ctx)

        self._response = ResponseGenerationService(self.orchestrator)

        # AI CONCIERGE: Initialize proactive intelligence if enabled
        self.proactive_intelligence = None
        if proactive_mode:
            try:
                from ghl_real_estate_ai.services.proactive_conversation_intelligence import (
                    ProactiveConversationIntelligence,
                )

                self.proactive_intelligence = ProactiveConversationIntelligence(self)
                logger.info("AI Concierge proactive intelligence enabled")
            except ImportError as e:
                logger.warning(f"Failed to initialize proactive intelligence: {e}")
                self.proactive_mode = False

        self._proactive = ProactiveIntelligenceService(self.proactive_intelligence, self.proactive_mode)

        self._retention = RetentionScriptService(self._market_ctx, market_id)

        self._semantic_match = SemanticCacheMatchService(
            self.orchestrator, self.analytics, self.semantic_cache, market_id
        )

        self._ui.initialize_state()

    def _initialize_state(self):
        if "assistant_greeted" not in st.session_state:
            st.session_state.assistant_greeted = False
        if "claude_history" not in st.session_state:
            st.session_state.claude_history = []

    # -- Market Context delegates --

    async def get_market_context(self, market_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._market_ctx.get_market_context(market_id)

    def _format_market_context_for_messaging(self, market_context: Dict[str, Any]) -> str:
        return self._market_ctx.format_market_context_for_messaging(market_context)

    # -- UI Rendering delegates --

    def render_sidebar_panel(self, hub_name: str, market: str, leads: Dict[str, Any]):
        self._ui.render_sidebar_panel(hub_name, market, leads)

    def get_insight(self, hub_name: str, leads: Dict[str, Any]) -> str:
        return self._ui.get_insight(hub_name, leads)

    def render_chat_interface(self, leads: Dict[str, Any], market: str):
        self._ui.render_chat_interface(leads, market)

    def greet_user(self, name: str = "Jorge"):
        self._ui.greet_user(name)

    # -- Response Generation delegates --

    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        return await self._response.generate_response(prompt, context)

    async def analyze_with_context(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._response.analyze_with_context(prompt, context)

    async def generate_automated_report(
        self, data: Dict[str, Any], report_type: str = "Weekly Performance"
    ) -> Dict[str, Any]:
        return await self._response.generate_automated_report(data, report_type)

    # -- Proactive Intelligence delegates --

    async def enable_proactive_insights(self, conversation_id: str) -> Dict[str, Any]:
        return await self._proactive.enable_proactive_insights(conversation_id)

    async def generate_automated_report_with_insights(
        self, data: Dict[str, Any], report_type: str = "Weekly Performance"
    ) -> Dict[str, Any]:
        return await self._proactive.generate_automated_report_with_insights(
            data, report_type, self._response.generate_automated_report
        )

    async def _aggregate_proactive_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._proactive._aggregate_proactive_insights(data)

    async def _get_top_coaching_categories(self) -> List:
        return await self._proactive._get_top_coaching_categories()

    async def _generate_improvement_recommendations(self) -> List[str]:
        return await self._proactive._generate_improvement_recommendations()

    # -- Retention Script delegates --

    async def generate_market_aware_retention_script(
        self,
        lead_data: Dict[str, Any],
        risk_data: Optional[Dict[str, Any]] = None,
        market_id: Optional[str] = None,
        churn_reason: Optional[ChurnReason] = None,
    ) -> Dict[str, Any]:
        return await self._retention.generate_market_aware_retention_script(lead_data, risk_data, market_id, churn_reason)

    def _get_recovery_template(self, clv_tier, churn_reason):
        return self._retention._get_recovery_template(clv_tier, churn_reason)

    async def generate_retention_script(
        self, lead_data: Dict[str, Any], risk_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return await self._retention.generate_retention_script(lead_data, risk_data)

    # -- Semantic Cache delegates --

    async def explain_match_with_claude(
        self,
        property_data: Dict[str, Any],
        lead_preferences: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None,
    ) -> str:
        return await self._semantic_match.explain_match_with_claude(property_data, lead_preferences, conversation_history)

    def _generate_semantic_key(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> str:
        return self._semantic_match._generate_semantic_key(property_data, lead_preferences)

    def _normalize_price(self, price) -> str:
        return self._semantic_match._normalize_price(price)

    def _normalize_location(self, zip_code: str) -> str:
        return self._semantic_match._normalize_location(zip_code)


def get_claude_assistant(**kwargs) -> ClaudeAssistant:
    """Factory function for creating ClaudeAssistant instances."""
    return ClaudeAssistant(**kwargs)
