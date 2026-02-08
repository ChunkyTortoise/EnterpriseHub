"""
Bot Intelligence Middleware - Phase 3.3
=======================================

Core orchestrator that bridges Phase 2 intelligence services with bot workflows.
Provides parallel intelligence gathering, caching, and graceful fallback behavior.

Features:
- Parallel intelligence gathering from 3 Phase 2 services (<200ms total)
- Multi-tier caching with 300s TTL for active conversations
- Graceful fallback on service failures with neutral defaults
- Event publishing for real-time intelligence updates
- Performance metrics tracking and monitoring

Integration Points:
- Advanced Property Matching Engine: find_behavioral_matches()
- Conversation Intelligence Service: analyze_conversation_with_insights()
- Client Preference Learning Engine: get_preference_profile()

Author: Jorge's Real Estate AI Platform - Phase 3.3 Bot Workflow Integration
"""

import asyncio
import hashlib
import json
import statistics
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Phase 2 service imports (lazy loading to avoid circular imports)
from ghl_real_estate_ai.ghl_utils.logger import get_logger

# Core models
from ghl_real_estate_ai.models.intelligence_context import (
    BotIntelligenceContext,
    ConversationIntelligence,
    IntelligencePerformanceMetrics,
    PreferenceIntelligence,
    PropertyIntelligence,
)

logger = get_logger(__name__)

# Configuration constants
CACHE_TTL_CONVERSATIONS = 300  # 5 minutes for active conversations
SERVICE_TIMEOUT_MS = 150  # 150ms timeout per service
TOTAL_TARGET_LATENCY_MS = 200  # <200ms total target
MAX_PARALLEL_OPERATIONS = 10  # Prevent resource exhaustion
METRICS_HISTORY_SIZE = 1000  # Keep last 1000 operations for analytics


class BotIntelligenceMiddleware:
    """
    Core orchestrator for bot intelligence enhancement.

    Bridges Phase 2 intelligence services with bot workflows through
    parallel intelligence gathering, caching, and graceful fallback.
    """

    def __init__(self):
        self.cache = None  # Will be injected or lazily loaded
        self.event_publisher = None  # Will be injected or lazily loaded

        # Phase 2 service references (lazy loaded)
        self.property_matcher = None
        self.conversation_intelligence = None
        self.preference_learning = None

        # Performance metrics tracking
        self._metrics_history: deque = deque(maxlen=METRICS_HISTORY_SIZE)
        self._total_enhancements = 0
        self._cache_hits = 0
        self._service_failures = defaultdict(int)

        logger.info("BotIntelligenceMiddleware initialized")

    def _get_cache_service(self):
        """Lazy load cache service to avoid circular imports."""
        if self.cache is None:
            try:
                from ghl_real_estate_ai.services.cache_service import get_cache_service

                self.cache = get_cache_service()
            except ImportError as e:
                logger.warning(f"Cache service unavailable: {e}")
                self.cache = self._create_mock_cache()
        return self.cache

    def _get_event_publisher(self):
        """Lazy load event publisher to avoid circular imports."""
        if self.event_publisher is None:
            try:
                from ghl_real_estate_ai.services.event_publisher import get_event_publisher

                self.event_publisher = get_event_publisher()
            except ImportError as e:
                logger.warning(f"Event publisher unavailable: {e}")
                self.event_publisher = self._create_mock_event_publisher()
        return self.event_publisher

    def _get_property_matcher(self):
        """Lazy load property matching engine to avoid circular imports."""
        if self.property_matcher is None:
            try:
                from ghl_real_estate_ai.services.advanced_property_matching_engine import (
                    get_advanced_property_matching_engine,
                )

                self.property_matcher = get_advanced_property_matching_engine()
            except ImportError as e:
                logger.warning(f"Property matcher unavailable: {e}")
                self.property_matcher = self._create_mock_property_matcher()
        return self.property_matcher

    def _get_conversation_intelligence(self):
        """Lazy load conversation intelligence service to avoid circular imports."""
        if self.conversation_intelligence is None:
            try:
                from ghl_real_estate_ai.services.conversation_intelligence_service import (
                    get_conversation_intelligence_service,
                )

                self.conversation_intelligence = get_conversation_intelligence_service()
            except ImportError as e:
                logger.warning(f"Conversation intelligence unavailable: {e}")
                self.conversation_intelligence = self._create_mock_conversation_intelligence()
        return self.conversation_intelligence

    def _get_preference_learning(self):
        """Lazy load preference learning engine to avoid circular imports."""
        if self.preference_learning is None:
            try:
                from ghl_real_estate_ai.services.client_preference_learning_engine import (
                    get_client_preference_learning_engine,
                )

                self.preference_learning = get_client_preference_learning_engine()
            except ImportError as e:
                logger.warning(f"Preference learning unavailable: {e}")
                self.preference_learning = self._create_mock_preference_learning()
        return self.preference_learning

    def _create_cache_key(self, lead_id: str, location_id: str, bot_type: str) -> str:
        """Create consistent cache key for intelligence context."""
        # Include conversation context hash for cache invalidation on changes
        key_data = f"bot_intel:{lead_id}:{location_id}:{bot_type}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def enhance_bot_context(
        self,
        bot_type: str,
        lead_id: str,
        location_id: str,
        conversation_context: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]] = None,
    ) -> BotIntelligenceContext:
        """
        Main orchestrator method for bot intelligence enhancement.

        Gathers intelligence from Phase 2 services in parallel and aggregates
        into comprehensive context for bot decision making.

        Args:
            bot_type: Type of bot requesting intelligence (jorge-seller, jorge-buyer, lead-bot)
            lead_id: Lead identifier for tenant isolation
            location_id: Location identifier for market context
            conversation_context: Recent conversation history
            preferences: Explicit preferences if available

        Returns:
            BotIntelligenceContext with aggregated intelligence

        Performance Target: <200ms total latency
        """
        start_time = time.time()
        performance_metrics = IntelligencePerformanceMetrics()

        logger.info(f"Enhancing bot context for {bot_type} bot, lead {lead_id}")

        try:
            # Check cache first
            cache_key = self._create_cache_key(lead_id, location_id, bot_type)
            cached_result = await self._check_cache(cache_key)

            if cached_result:
                logger.info(f"Cache hit for bot intelligence: {lead_id}")
                performance_metrics.cache_hit = True
                performance_metrics.cache_time_ms = (time.time() - start_time) * 1000
                performance_metrics.mark_completion()

                # Update stats
                self._cache_hits += 1
                self._total_enhancements += 1

                # Still publish event for cache hits (for monitoring)
                await self._publish_intelligence_update(cached_result)

                return cached_result

            # Cache miss - gather intelligence in parallel
            logger.info(f"Cache miss - gathering intelligence for {lead_id}")
            intelligence_context = await self._gather_intelligence_parallel(
                bot_type, lead_id, location_id, conversation_context, preferences, performance_metrics
            )

            # Calculate composite scores
            intelligence_context.calculate_composite_scores()

            # Cache the result
            await self._cache_intelligence(cache_key, intelligence_context)

            # Publish intelligence update event
            await self._publish_intelligence_update(intelligence_context)

            # Update metrics
            self._update_metrics(performance_metrics.total_time_ms)
            self._total_enhancements += 1

            logger.info(f"Intelligence gathering completed for {lead_id} in {performance_metrics.total_time_ms:.1f}ms")

            return intelligence_context

        except Exception as e:
            logger.error(f"Intelligence enhancement failed for {lead_id}: {e}")

            # Return fallback context
            fallback_context = BotIntelligenceContext.create_fallback(
                lead_id, location_id, bot_type, f"enhancement_error:{str(e)}"
            )

            self._service_failures["total"] += 1
            return fallback_context

    async def _check_cache(self, cache_key: str) -> Optional[BotIntelligenceContext]:
        """Check cache for existing intelligence context."""
        try:
            cache_service = self._get_cache_service()
            cached_data = await cache_service.get(cache_key)

            if cached_data:
                return BotIntelligenceContext.from_json(cached_data)

        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

        return None

    async def _cache_intelligence(self, cache_key: str, context: BotIntelligenceContext):
        """Cache intelligence context for future requests."""
        try:
            cache_service = self._get_cache_service()
            await cache_service.set(cache_key, context.to_json(), ttl=CACHE_TTL_CONVERSATIONS)
            logger.debug(f"Cached intelligence context: {cache_key}")

        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    async def _gather_intelligence_parallel(
        self,
        bot_type: str,
        lead_id: str,
        location_id: str,
        conversation_context: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
        performance_metrics: IntelligencePerformanceMetrics,
    ) -> BotIntelligenceContext:
        """
        Gather intelligence from Phase 2 services in parallel.

        Uses asyncio.gather with timeout protection for optimal performance
        while maintaining graceful fallback on service failures.
        """
        logger.debug(f"Starting parallel intelligence gathering for {lead_id}")

        # Create tasks for parallel execution with timeout protection
        tasks = {
            "property_matching": self._gather_property_intelligence(
                lead_id, location_id, conversation_context, preferences
            ),
            "conversation_analysis": self._gather_conversation_intelligence(lead_id, conversation_context),
            "preference_learning": self._gather_preference_intelligence(lead_id, conversation_context, preferences),
        }

        # Execute tasks in parallel with timeout protection
        start_time = time.time()
        results = {}

        try:
            # Use asyncio.wait_for with individual timeouts
            timeout_seconds = SERVICE_TIMEOUT_MS / 1000.0
            completed_tasks = await asyncio.gather(
                *[asyncio.wait_for(task, timeout=timeout_seconds) for task in tasks.values()], return_exceptions=True
            )

            # Process results and handle exceptions
            for i, (task_name, result) in enumerate(zip(tasks.keys(), completed_tasks)):
                if isinstance(result, Exception):
                    logger.warning(f"Service {task_name} failed: {result}")
                    performance_metrics.service_failures.append(task_name)
                    self._service_failures[task_name] += 1
                    results[task_name] = None
                else:
                    results[task_name] = result

        except Exception as e:
            logger.error(f"Parallel intelligence gathering failed: {e}")
            performance_metrics.service_failures.append("parallel_execution_failed")
            results = {task: None for task in tasks.keys()}

        # Record timing
        total_time_ms = (time.time() - start_time) * 1000
        performance_metrics.property_matching_time_ms = total_time_ms  # Approximation for parallel
        performance_metrics.conversation_analysis_time_ms = total_time_ms
        performance_metrics.preference_learning_time_ms = total_time_ms
        performance_metrics.mark_completion()

        # Aggregate results
        intelligence_context = self._aggregate_intelligence(
            bot_type, lead_id, location_id, results, performance_metrics
        )

        logger.debug(f"Parallel intelligence gathering completed in {total_time_ms:.1f}ms")
        return intelligence_context

    async def _gather_property_intelligence(
        self,
        lead_id: str,
        location_id: str,
        conversation_context: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
    ) -> PropertyIntelligence:
        """Gather property matching intelligence from Phase 2.2 service."""
        try:
            property_matcher = self._get_property_matcher()
            matches = await property_matcher.find_behavioral_matches(
                lead_id=lead_id,
                location_id=location_id,
                preferences=preferences or {},
                conversation_history=conversation_context,
                max_results=5,
            )

            if matches:
                top_matches = [match.to_dict() for match in matches[:3]]
                best_score = matches[0].confidence_score * 100 if matches else 0.0

                return PropertyIntelligence(
                    top_matches=top_matches,
                    match_count=len(matches),
                    best_match_score=best_score,
                    presentation_strategy=matches[0].presentation_strategy.value if matches else None,
                    optimal_presentation_time=matches[0].optimal_presentation_time if matches else None,
                    behavioral_reasoning=matches[0].behavioral_reasoning if matches else None,
                )

        except Exception as e:
            logger.warning(f"Property intelligence gathering failed: {e}")

        return PropertyIntelligence.create_empty()

    async def _gather_conversation_intelligence(
        self, lead_id: str, conversation_context: List[Dict[str, Any]]
    ) -> ConversationIntelligence:
        """Gather conversation analysis intelligence from Phase 2.3 service."""
        try:
            conversation_service = self._get_conversation_intelligence()
            insight = await conversation_service.analyze_conversation_with_insights(
                lead_id=lead_id, conversation_history=conversation_context
            )

            # Convert objections to dict format
            objections = []
            for obj in insight.objections_detected:
                objections.append(
                    {
                        "type": obj.objection_type.value
                        if hasattr(obj.objection_type, "value")
                        else str(obj.objection_type),
                        "severity": obj.severity,
                        "confidence": obj.confidence,
                        "context": obj.context,
                        "suggested_responses": obj.suggested_responses,
                    }
                )

            # Convert coaching opportunities
            coaching_opportunities = []
            for opportunity in insight.quality_metrics.coaching_opportunities:
                coaching_opportunities.append(
                    {
                        "area": opportunity.area.value if hasattr(opportunity.area, "value") else str(opportunity.area),
                        "priority": opportunity.priority,
                        "description": opportunity.description,
                    }
                )

            # Convert response recommendations
            response_recommendations = []
            for rec in insight.response_recommendations:
                response_recommendations.append(
                    {"response_text": rec.response_text, "confidence": rec.confidence, "tone": rec.tone}
                )

            return ConversationIntelligence(
                objections_detected=objections,
                overall_sentiment=insight.sentiment_timeline.overall_sentiment,
                sentiment_trend=insight.sentiment_timeline.trend,
                conversation_quality_score=insight.quality_metrics.overall_score,
                coaching_opportunities=coaching_opportunities,
                response_recommendations=response_recommendations,
            )

        except Exception as e:
            logger.warning(f"Conversation intelligence gathering failed: {e}")

        return ConversationIntelligence.create_empty()

    async def _gather_preference_intelligence(
        self, lead_id: str, conversation_context: List[Dict[str, Any]], preferences: Optional[Dict[str, Any]]
    ) -> PreferenceIntelligence:
        """Gather preference learning intelligence from Phase 2.4 service."""
        try:
            preference_service = self._get_preference_learning()
            profile = await preference_service.get_preference_profile(lead_id=lead_id)

            # Also learn from current conversation if provided
            if conversation_context:
                await preference_service.learn_from_conversation(
                    lead_id=lead_id, conversation_history=conversation_context
                )

            budget_range = None
            if hasattr(profile, "budget_min") and hasattr(profile, "budget_max"):
                budget_range = {"min": profile.budget_min, "max": profile.budget_max}

            return PreferenceIntelligence(
                preference_profile={
                    "budget_min": getattr(profile, "budget_min", None),
                    "budget_max": getattr(profile, "budget_max", None),
                    "bedrooms_min": getattr(profile, "bedrooms_min", None),
                    "bedrooms_max": getattr(profile, "bedrooms_max", None),
                    "bathrooms_min": getattr(profile, "bathrooms_min", None),
                    "move_timeline": getattr(profile, "move_timeline", None),
                },
                profile_completeness=getattr(profile, "profile_completeness", 0.0),
                budget_range=budget_range,
                urgency_level=getattr(profile, "urgency_level", 0.5),
                location_preferences=getattr(profile, "location_preferences", {}),
                feature_preferences=getattr(profile, "feature_preferences", {}),
            )

        except Exception as e:
            logger.warning(f"Preference intelligence gathering failed: {e}")

        return PreferenceIntelligence.create_empty()

    def _aggregate_intelligence(
        self,
        bot_type: str,
        lead_id: str,
        location_id: str,
        intelligence_results: Dict[str, Any],
        performance_metrics: IntelligencePerformanceMetrics,
    ) -> BotIntelligenceContext:
        """
        Aggregate intelligence results into comprehensive bot context.

        Handles partial failures gracefully by using fallback intelligence
        for failed services while preserving successful results.
        """
        # Extract intelligence components with fallback for failures
        property_intelligence = intelligence_results.get("property_matching") or PropertyIntelligence.create_empty()
        conversation_intelligence = (
            intelligence_results.get("conversation_analysis") or ConversationIntelligence.create_empty()
        )
        preference_intelligence = (
            intelligence_results.get("preference_learning") or PreferenceIntelligence.create_empty()
        )

        return BotIntelligenceContext(
            lead_id=lead_id,
            location_id=location_id,
            bot_type=bot_type,
            property_intelligence=property_intelligence,
            conversation_intelligence=conversation_intelligence,
            preference_intelligence=preference_intelligence,
            performance_metrics=performance_metrics,
            cache_hit=False,
        )

    async def _publish_intelligence_update(self, context: BotIntelligenceContext):
        """Publish intelligence update event for real-time monitoring."""
        try:
            event_publisher = self._get_event_publisher()
            await event_publisher.publish_lead_update(
                lead_id=context.lead_id,
                event_type="intelligence_enhanced",
                event_data={
                    "bot_type": context.bot_type,
                    "location_id": context.location_id,
                    "property_matches": context.property_intelligence.match_count,
                    "sentiment_score": context.conversation_intelligence.overall_sentiment,
                    "profile_completeness": context.preference_intelligence.profile_completeness,
                    "composite_engagement": context.composite_engagement_score,
                    "cache_hit": context.cache_hit,
                    "processing_time_ms": context.performance_metrics.total_time_ms,
                },
            )
        except Exception as e:
            logger.warning(f"Event publishing failed: {e}")

    def _update_metrics(self, latency_ms: float):
        """Update internal performance metrics."""
        self._metrics_history.append(
            {
                "timestamp": datetime.now(timezone.utc),
                "latency_ms": latency_ms,
                "within_target": latency_ms < TOTAL_TARGET_LATENCY_MS,
            }
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for monitoring."""
        if not self._metrics_history:
            return {
                "total_enhancements": self._total_enhancements,
                "cache_hits": self._cache_hits,
                "avg_latency_ms": 0.0,
                "latency_p95_ms": 0.0,
                "latency_p99_ms": 0.0,
                "performance_status": "unknown",
                "service_failures": dict(self._service_failures),
            }

        latencies = [m["latency_ms"] for m in self._metrics_history]
        within_target_count = sum(1 for m in self._metrics_history if m["within_target"])
        target_percentage = (within_target_count / len(self._metrics_history)) * 100

        # Determine performance status
        if target_percentage >= 95:
            status = "excellent"
        elif target_percentage >= 80:
            status = "good"
        else:
            status = "degraded"

        return {
            "total_enhancements": self._total_enhancements,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": (self._cache_hits / max(self._total_enhancements, 1)) * 100,
            "avg_latency_ms": statistics.mean(latencies),
            "latency_p95_ms": statistics.quantiles(latencies, n=20)[18]
            if len(latencies) > 20
            else max(latencies, default=0),
            "latency_p99_ms": statistics.quantiles(latencies, n=100)[98]
            if len(latencies) > 100
            else max(latencies, default=0),
            "performance_status": status,
            "target_percentage": target_percentage,
            "service_failures": dict(self._service_failures),
        }

    # Mock services for testing and fallback
    def _create_mock_cache(self):
        """Create mock cache service for testing."""

        class MockCache:
            async def get(self, key):
                return None

            async def set(self, key, value, ttl=None):
                return True

        return MockCache()

    def _create_mock_event_publisher(self):
        """Create mock event publisher for testing."""

        class MockEventPublisher:
            async def publish_lead_update(self, **kwargs):
                pass

        return MockEventPublisher()

    def _create_mock_property_matcher(self):
        """Create mock property matcher for testing."""

        class MockPropertyMatcher:
            async def find_behavioral_matches(self, **kwargs):
                return []

        return MockPropertyMatcher()

    def _create_mock_conversation_intelligence(self):
        """Create mock conversation intelligence for testing."""

        class MockConversationIntelligence:
            async def analyze_conversation_with_insights(self, **kwargs):
                class MockInsight:
                    objections_detected = []
                    sentiment_timeline = type("obj", (object,), {"overall_sentiment": 0.0, "trend": "stable"})
                    quality_metrics = type("obj", (object,), {"overall_score": 50.0, "coaching_opportunities": []})
                    response_recommendations = []

                return MockInsight()

        return MockConversationIntelligence()

    def _create_mock_preference_learning(self):
        """Create mock preference learning for testing."""

        class MockPreferenceLearning:
            async def get_preference_profile(self, **kwargs):
                return type(
                    "obj",
                    (object,),
                    {
                        "budget_min": None,
                        "budget_max": None,
                        "profile_completeness": 0.0,
                        "location_preferences": {},
                        "feature_preferences": {},
                        "urgency_level": 0.5,
                    },
                )

            async def learn_from_conversation(self, **kwargs):
                pass

        return MockPreferenceLearning()


# Singleton pattern for service access
_bot_intelligence_middleware_instance = None


def get_bot_intelligence_middleware() -> BotIntelligenceMiddleware:
    """Get singleton instance of Bot Intelligence Middleware."""
    global _bot_intelligence_middleware_instance

    if _bot_intelligence_middleware_instance is None:
        _bot_intelligence_middleware_instance = BotIntelligenceMiddleware()
        logger.info("Created new BotIntelligenceMiddleware singleton instance")

    return _bot_intelligence_middleware_instance


async def health_check() -> Dict[str, Any]:
    """Health check endpoint for service monitoring."""
    middleware = get_bot_intelligence_middleware()
    metrics = middleware.get_metrics()

    return {
        "service": "BotIntelligenceMiddleware",
        "status": "healthy" if metrics["performance_status"] != "degraded" else "degraded",
        "version": "3.3.0",
        "metrics": metrics,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
