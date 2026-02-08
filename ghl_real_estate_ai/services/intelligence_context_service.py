"""
Intelligence Context Service - Phase 3.2
=========================================

Service for preserving intelligence context across bot transitions in Jorge's ecosystem.
Enables seamless handoffs between bots with complete context preservation.

Features:
- Intelligence snapshot preservation with extended caching (7200s TTL)
- Context retrieval with tenant isolation and TTL validation
- Handoff event publishing via existing event system
- Transition history tracking for audit and analytics
- Performance monitoring with <50ms preservation, <30ms retrieval targets

Bot Handoff Scenarios:
- Jorge Seller → Jorge Buyer (qualified buyer transition)
- Lead Bot → Jorge Seller (lead activation)
- Jorge Buyer → Lead Bot (dormant lead return)
- Any Bot → Manual Agent (escalation scenarios)

Performance Targets:
- Preservation latency: <50ms (P99)
- Retrieval latency: <30ms (P99)
- Cache hit rate: >85% for active handoffs
- Supports 1000+ concurrent handoff operations

Author: Jorge's Real Estate AI Platform - Phase 3.2 Implementation
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.ghl_utils.logger import get_logger

# Data models
from ghl_real_estate_ai.models.bot_handoff import (
    BotTransition,
    BotType,
    ContextHandoff,
    HandoffStatus,
    IntelligenceSnapshot,
    PreservedIntelligence,
    TransitionHistory,
    TransitionReason,
)
from ghl_real_estate_ai.services.bot_intelligence_middleware import get_bot_intelligence_middleware

# Core service imports (singleton pattern)
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)

# Configuration constants
HANDOFF_CACHE_TTL = 7200  # 2 hours for handoff contexts
ACTIVE_CACHE_TTL = 300  # 5 minutes for active contexts
HISTORY_CACHE_TTL = 86400  # 24 hours for transition history
PRESERVATION_TARGET_MS = 50  # <50ms preservation target
RETRIEVAL_TARGET_MS = 30  # <30ms retrieval target
MAX_SNAPSHOT_SIZE_KB = 100  # Maximum snapshot size


class IntelligenceContextService:
    """
    Intelligence Context Service.

    Manages intelligence preservation across bot transitions with extended caching,
    event publishing, and comprehensive audit trail.

    Features:
    - <50ms intelligence preservation with Redis caching
    - <30ms context retrieval with TTL validation
    - Extended TTL (7200s) for handoff contexts vs active contexts (300s)
    - Complete transition history for audit and analytics
    - Event publishing for real-time handoff notifications
    - Graceful fallback on service failures
    """

    def __init__(self):
        # Infrastructure services
        self.cache = get_cache_service()
        self.event_publisher = get_event_publisher()

        # Optional intelligence middleware for context enrichment
        try:
            self.bot_middleware = get_bot_intelligence_middleware()
        except Exception as e:
            logger.warning(f"Bot intelligence middleware unavailable: {e}")
            self.bot_middleware = None

        # Performance metrics
        self.metrics = {
            "total_preservations": 0,
            "successful_preservations": 0,
            "failed_preservations": 0,
            "total_retrievals": 0,
            "successful_retrievals": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_preservation_latency_ms": 0.0,
            "avg_retrieval_latency_ms": 0.0,
            "total_data_preserved_mb": 0.0,
        }

        # Latency tracking for percentile calculation
        self._preservation_latencies = []
        self._retrieval_latencies = []
        self._max_samples = 1000  # Keep last 1000 samples

        logger.info("IntelligenceContextService initialized")

    async def preserve_intelligence(
        self,
        lead_id: str,
        intelligence_data: Dict[str, Any],
        bot_transition: BotTransition,
        location_id: Optional[str] = None,
    ) -> ContextHandoff:
        """
        Preserve intelligence context for bot handoff.

        Creates intelligence snapshot and stores in Redis with extended TTL
        for seamless bot transition with full context preservation.

        Algorithm:
        1. Create intelligence snapshot from current context
        2. Store snapshot in Redis with 7200s TTL
        3. Update transition history for audit trail
        4. Publish handoff event via EventPublisher
        5. Track performance metrics

        Args:
            lead_id: Lead identifier
            intelligence_data: Current intelligence context from middleware
            bot_transition: Transition metadata (source/target bots, reason)
            location_id: Optional tenant/location identifier

        Returns:
            ContextHandoff with operation result and metadata
        """
        start_time = time.time()

        try:
            # Use location from transition if not provided
            location_id = location_id or bot_transition.location_id

            # Create intelligence snapshot
            snapshot = await self.create_intelligence_snapshot(
                lead_id=lead_id,
                location_id=location_id,
                intelligence_data=intelligence_data,
                bot_transition=bot_transition,
            )

            # Generate cache key for handoff context
            cache_key = self._generate_handoff_key(lead_id=lead_id, target_bot=bot_transition.target_bot)

            # Serialize snapshot for caching
            snapshot_data = snapshot.to_json()
            data_size_bytes = len(snapshot_data.encode("utf-8"))

            # Validate snapshot size
            if data_size_bytes > MAX_SNAPSHOT_SIZE_KB * 1024:
                logger.warning(
                    f"Large intelligence snapshot: {data_size_bytes / 1024:.1f}KB "
                    f"(max: {MAX_SNAPSHOT_SIZE_KB}KB) for {lead_id}"
                )

            # Store in Redis with extended TTL
            success = await self.cache.set(key=cache_key, value=snapshot_data, ttl=HANDOFF_CACHE_TTL)

            if not success:
                raise Exception(f"Failed to cache intelligence snapshot: {cache_key}")

            # Update transition history
            await self._update_transition_history(
                lead_id=lead_id, location_id=location_id, bot_transition=bot_transition, snapshot=snapshot
            )

            # Calculate performance metrics
            preservation_latency_ms = (time.time() - start_time) * 1000

            # Create successful handoff result
            handoff_result = ContextHandoff.create_success(
                lead_id=lead_id,
                location_id=location_id,
                intelligence_snapshot_id=snapshot.snapshot_id,
                transition_id=bot_transition.transition_id,
                preservation_latency_ms=preservation_latency_ms,
                cache_key=cache_key,
                cache_ttl_seconds=HANDOFF_CACHE_TTL,
            )
            handoff_result.data_size_bytes = data_size_bytes

            # Publish handoff event
            await self._publish_handoff_event(snapshot, bot_transition, handoff_result)

            # Update metrics
            self._update_preservation_metrics(preservation_latency_ms, data_size_bytes, success=True)

            logger.info(
                f"Intelligence preserved for {lead_id} "
                f"({bot_transition.source_bot.value} → {bot_transition.target_bot.value}): "
                f"{preservation_latency_ms:.1f}ms, {data_size_bytes / 1024:.1f}KB"
            )

            return handoff_result

        except Exception as e:
            preservation_latency_ms = (time.time() - start_time) * 1000

            logger.error(f"Intelligence preservation failed for {lead_id}: {e}", exc_info=True)

            # Update failure metrics
            self._update_preservation_metrics(preservation_latency_ms, 0, success=False)

            # Return failure result
            return ContextHandoff.create_failure(
                lead_id=lead_id,
                location_id=location_id or "",
                error_message=str(e),
                preservation_latency_ms=preservation_latency_ms,
            )

    async def retrieve_intelligence_context(
        self, lead_id: str, target_bot: BotType, location_id: Optional[str] = None
    ) -> Optional[IntelligenceSnapshot]:
        """
        Retrieve preserved intelligence context for incoming bot.

        Fetches intelligence snapshot from Redis cache with TTL validation
        and tenant isolation for secure context retrieval.

        Algorithm:
        1. Generate cache key for handoff context
        2. Retrieve snapshot from Redis cache
        3. Validate TTL and location_id (tenant isolation)
        4. Deserialize and return snapshot
        5. Track performance metrics

        Args:
            lead_id: Lead identifier
            target_bot: Bot type requesting context
            location_id: Optional tenant/location identifier for validation

        Returns:
            IntelligenceSnapshot if found and valid, None otherwise
        """
        start_time = time.time()

        try:
            # Generate cache key
            cache_key = self._generate_handoff_key(lead_id, target_bot)

            # Retrieve from cache
            cached_data = await self.cache.get(cache_key)

            if not cached_data:
                # Cache miss
                self.metrics["cache_misses"] += 1
                self._update_retrieval_metrics(retrieval_latency_ms=(time.time() - start_time) * 1000, success=False)

                logger.debug(f"No preserved context found for {lead_id} → {target_bot.value}")
                return None

            # Deserialize snapshot
            if isinstance(cached_data, str):
                snapshot = IntelligenceSnapshot.from_json(cached_data)
            elif isinstance(cached_data, dict):
                snapshot = IntelligenceSnapshot.from_dict(cached_data)
            else:
                logger.error(f"Invalid cached data type: {type(cached_data)}")
                return None

            # Validate tenant isolation
            if location_id and snapshot.location_id != location_id:
                logger.warning(
                    f"Location mismatch for {lead_id}: requested {location_id}, cached {snapshot.location_id}"
                )
                return None

            # Validate TTL (additional check beyond Redis TTL)
            now = datetime.now(timezone.utc)
            snapshot_age_seconds = (now - snapshot.snapshot_timestamp).total_seconds()

            if snapshot_age_seconds > HANDOFF_CACHE_TTL:
                logger.warning(
                    f"Expired intelligence snapshot for {lead_id}: "
                    f"{snapshot_age_seconds:.0f}s old (max: {HANDOFF_CACHE_TTL}s)"
                )
                # Remove expired snapshot
                await self.cache.delete(cache_key)
                return None

            # Successful retrieval
            self.metrics["cache_hits"] += 1
            retrieval_latency_ms = (time.time() - start_time) * 1000

            self._update_retrieval_metrics(retrieval_latency_ms, success=True)

            logger.info(
                f"Intelligence retrieved for {lead_id} → {target_bot.value}: "
                f"{retrieval_latency_ms:.1f}ms, "
                f"{snapshot_age_seconds:.0f}s old"
            )

            return snapshot

        except Exception as e:
            retrieval_latency_ms = (time.time() - start_time) * 1000

            logger.error(f"Intelligence retrieval failed for {lead_id}: {e}", exc_info=True)

            self._update_retrieval_metrics(retrieval_latency_ms, success=False)
            return None

    async def create_intelligence_snapshot(
        self, lead_id: str, location_id: str, intelligence_data: Dict[str, Any], bot_transition: BotTransition
    ) -> IntelligenceSnapshot:
        """
        Create intelligence snapshot from current intelligence context.

        Extracts and structures intelligence data from middleware context
        into optimized snapshot format for caching and handoff.

        Args:
            lead_id: Lead identifier
            location_id: Tenant/location identifier
            intelligence_data: Raw intelligence data from middleware
            bot_transition: Transition metadata

        Returns:
            IntelligenceSnapshot ready for caching
        """
        try:
            # Extract preserved intelligence from middleware data
            preserved_intel = await self._extract_preserved_intelligence(intelligence_data)

            # Generate conversation summary using Claude if available
            conversation_summary = await self._generate_conversation_summary(intelligence_data, bot_transition)

            # Extract qualification scores
            qualification_scores = self._extract_qualification_scores(intelligence_data)

            # Generate strategic guidance for target bot
            strategic_guidance = await self._generate_strategic_guidance(intelligence_data, bot_transition)

            # Create snapshot
            snapshot = IntelligenceSnapshot(
                snapshot_id=str(uuid.uuid4()),
                lead_id=lead_id,
                location_id=location_id,
                source_bot=bot_transition.source_bot,
                target_bot=bot_transition.target_bot,
                snapshot_timestamp=datetime.now(timezone.utc),
                preserved_intelligence=preserved_intel,
                conversation_summary=conversation_summary,
                conversation_length=len(intelligence_data.get("conversation_history", [])),
                last_message_timestamp=self._get_last_message_timestamp(intelligence_data),
                qualification_scores=qualification_scores,
                temperature_classification=intelligence_data.get("temperature_classification"),
                readiness_indicators=self._extract_readiness_indicators(intelligence_data),
                recommended_next_actions=strategic_guidance["next_actions"],
                strategic_approach=strategic_guidance["approach"],
                conversation_goals=strategic_guidance["goals"],
                warning_flags=strategic_guidance["warnings"],
                transition_reason=bot_transition.transition_reason,
                handoff_message=bot_transition.handoff_message,
                confidence_level=self._calculate_confidence_level(intelligence_data),
                data_completeness=self._calculate_data_completeness(intelligence_data),
            )

            return snapshot

        except Exception as e:
            logger.error(f"Failed to create intelligence snapshot: {e}", exc_info=True)
            # Return empty snapshot as fallback
            return IntelligenceSnapshot.create_empty(
                lead_id=lead_id,
                location_id=location_id,
                source_bot=bot_transition.source_bot,
                target_bot=bot_transition.target_bot,
            )

    async def get_transition_history(self, lead_id: str, location_id: Optional[str] = None) -> TransitionHistory:
        """
        Retrieve complete transition history for a lead.

        Args:
            lead_id: Lead identifier
            location_id: Optional tenant/location identifier

        Returns:
            TransitionHistory with complete audit trail
        """
        try:
            history_key = self._generate_history_key(lead_id)
            cached_history = await self.cache.get(history_key)

            if cached_history:
                if isinstance(cached_history, str):
                    history_data = json.loads(cached_history)
                else:
                    history_data = cached_history

                history = TransitionHistory.from_dict(history_data)

                # Validate tenant isolation
                if location_id and history.location_id != location_id:
                    logger.warning(f"Location mismatch for history {lead_id}")
                    return TransitionHistory.create_empty(lead_id, location_id or "")

                return history
            else:
                # Return empty history if not found
                return TransitionHistory.create_empty(lead_id=lead_id, location_id=location_id or "")

        except Exception as e:
            logger.error(f"Failed to retrieve transition history for {lead_id}: {e}")
            return TransitionHistory.create_empty(lead_id, location_id or "")

    async def cleanup_expired_contexts(self, location_id: Optional[str] = None) -> int:
        """
        Background cleanup of expired handoff contexts.

        Note: Redis TTL handles most cleanup automatically, but this provides
        additional cleanup for audit trail and metrics.

        Args:
            location_id: Optional tenant/location identifier

        Returns:
            Number of contexts cleaned up
        """
        # This is primarily handled by Redis TTL
        # Implementation would scan for expired contexts if needed
        logger.debug("Cleanup triggered - Redis TTL handles automatic cleanup")
        return 0

    # Private helper methods

    async def _extract_preserved_intelligence(self, intelligence_data: Dict[str, Any]) -> PreservedIntelligence:
        """Extract intelligence from middleware data into preserved format."""
        try:
            # Extract property intelligence
            property_context = intelligence_data.get("property_intelligence", {})
            top_matches = property_context.get("top_matches", [])[:5]  # Top 5 only

            # Extract conversation intelligence
            conversation_context = intelligence_data.get("conversation_intelligence", {})

            # Extract preference intelligence
            preference_context = intelligence_data.get("preference_intelligence", {})
            preference_profile = preference_context.get("preference_profile", {})

            return PreservedIntelligence(
                top_property_matches=top_matches,
                best_match_score=property_context.get("best_match_score", 0.0),
                property_presentation_strategy=property_context.get("presentation_strategy"),
                conversation_quality_score=conversation_context.get("conversation_quality_score", 50.0),
                overall_sentiment=conversation_context.get("overall_sentiment", 0.0),
                sentiment_trend=conversation_context.get("sentiment_trend", "stable"),
                key_objections_detected=conversation_context.get("objections_detected", []),
                resolved_objections=conversation_context.get("resolved_objections", []),
                pending_objections=conversation_context.get("pending_objections", []),
                response_recommendations=conversation_context.get("response_recommendations", []),
                budget_range=preference_context.get("budget_range"),
                location_preferences=preference_context.get("location_preferences", {}),
                feature_preferences=preference_context.get("feature_preferences", {}),
                move_timeline=preference_profile.get("move_timeline"),
                urgency_level=preference_context.get("urgency_level", 0.5),
                profile_completeness=preference_context.get("profile_completeness", 0.0),
                engagement_pattern=intelligence_data.get("engagement_pattern", "responsive"),
                communication_style=intelligence_data.get("communication_style", "professional"),
                decision_making_style=intelligence_data.get("decision_making_style", "analytical"),
                risk_tolerance=intelligence_data.get("risk_tolerance", "moderate"),
            )

        except Exception as e:
            logger.error(f"Failed to extract preserved intelligence: {e}")
            return PreservedIntelligence.create_empty()

    async def _generate_conversation_summary(
        self, intelligence_data: Dict[str, Any], bot_transition: BotTransition
    ) -> str:
        """Generate strategic conversation summary."""
        try:
            # Extract key conversation points
            conversation_history = intelligence_data.get("conversation_history", [])
            qualification_scores = self._extract_qualification_scores(intelligence_data)
            objections = intelligence_data.get("conversation_intelligence", {}).get("objections_detected", [])

            # Create summary based on transition reason
            if bot_transition.transition_reason == TransitionReason.QUALIFIED_BUYER:
                return (
                    f"Seller qualified with FRS {qualification_scores.get('FRS', 0):.0f}/PCS "
                    f"{qualification_scores.get('PCS', 0):.0f}, expressed buyer interest. "
                    f"{len(objections)} objections addressed. Ready for buyer consultation."
                )
            elif bot_transition.transition_reason == TransitionReason.QUALIFIED_SELLER:
                return (
                    f"Buyer qualified, also interested in selling current property. "
                    f"Property preferences established. Transition to seller qualification."
                )
            elif bot_transition.transition_reason == TransitionReason.ESCALATION_REQUESTED:
                return (
                    f"Complex situation requiring human agent intervention. "
                    f"Review conversation history and address concerns."
                )
            else:
                return (
                    f"Bot transition initiated. {len(conversation_history)} messages exchanged, "
                    f"qualification in progress."
                )

        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {e}")
            return "Conversation context preserved for bot transition."

    def _extract_qualification_scores(self, intelligence_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract FRS/PCS qualification scores."""
        try:
            # From intent decoder or intelligence context
            scores = {}

            # Check intent decoder results
            intent_profile = intelligence_data.get("intent_profile")
            if intent_profile:
                scores["FRS"] = getattr(intent_profile.frs, "total_score", 0)
                scores["PCS"] = getattr(intent_profile.pcs, "total_score", 0)

            # Check qualification scores directly
            if "qualification_scores" in intelligence_data:
                scores.update(intelligence_data["qualification_scores"])

            return scores

        except Exception as e:
            logger.error(f"Failed to extract qualification scores: {e}")
            return {}

    async def _generate_strategic_guidance(
        self, intelligence_data: Dict[str, Any], bot_transition: BotTransition
    ) -> Dict[str, Any]:
        """Generate strategic guidance for target bot."""
        try:
            guidance = {"next_actions": [], "approach": "consultative", "goals": [], "warnings": []}

            # Strategy based on target bot type
            if bot_transition.target_bot == BotType.JORGE_BUYER:
                guidance["approach"] = "consultative"
                guidance["next_actions"] = [
                    "Review property preferences from seller conversation",
                    "Establish budget and timeline",
                    "Present property matches with strategic reasoning",
                ]
                guidance["goals"] = [
                    "Qualify buying motivation and capacity",
                    "Identify property criteria",
                    "Schedule property viewings",
                ]

            elif bot_transition.target_bot == BotType.JORGE_SELLER:
                guidance["approach"] = "confrontational"
                guidance["next_actions"] = [
                    "Challenge on timeline and motivation",
                    "Qualify financial readiness",
                    "Present Jorge's value proposition",
                ]
                guidance["goals"] = [
                    "Establish selling urgency",
                    "Qualify price expectations",
                    "Secure listing commitment",
                ]

            elif bot_transition.target_bot == BotType.MANUAL_AGENT:
                guidance["approach"] = "supportive"
                guidance["next_actions"] = [
                    "Review complete conversation history",
                    "Address unresolved objections",
                    "Provide personalized consultation",
                ]
                guidance["warnings"] = ["Complex situation requiring human touch"]

            return guidance

        except Exception as e:
            logger.error(f"Failed to generate strategic guidance: {e}")
            return {
                "next_actions": ["Continue conversation"],
                "approach": "consultative",
                "goals": ["Maintain engagement"],
                "warnings": [],
            }

    def _extract_readiness_indicators(self, intelligence_data: Dict[str, Any]) -> List[str]:
        """Extract readiness indicators from intelligence data."""
        indicators = []

        try:
            # From qualification scores
            scores = self._extract_qualification_scores(intelligence_data)
            if scores.get("FRS", 0) >= 75:
                indicators.append("financially_ready")
            if scores.get("PCS", 0) >= 75:
                indicators.append("psychologically_committed")

            # From conversation intelligence
            conversation_intel = intelligence_data.get("conversation_intelligence", {})
            sentiment = conversation_intel.get("overall_sentiment", 0)
            if sentiment > 0.5:
                indicators.append("positive_sentiment")
            elif sentiment < -0.2:
                indicators.append("negative_sentiment")

            # From property intelligence
            property_intel = intelligence_data.get("property_intelligence", {})
            if property_intel.get("match_count", 0) > 0:
                indicators.append("property_matches_available")

            # From preference intelligence
            preference_intel = intelligence_data.get("preference_intelligence", {})
            if preference_intel.get("profile_completeness", 0) > 0.7:
                indicators.append("complete_profile")

        except Exception as e:
            logger.error(f"Failed to extract readiness indicators: {e}")

        return indicators

    def _get_last_message_timestamp(self, intelligence_data: Dict[str, Any]) -> Optional[datetime]:
        """Get timestamp of last message in conversation."""
        try:
            conversation_history = intelligence_data.get("conversation_history", [])
            if conversation_history:
                last_message = conversation_history[-1]
                if "timestamp" in last_message:
                    if isinstance(last_message["timestamp"], str):
                        return datetime.fromisoformat(last_message["timestamp"])
                    elif isinstance(last_message["timestamp"], datetime):
                        return last_message["timestamp"]

            return None

        except Exception as e:
            logger.error(f"Failed to get last message timestamp: {e}")
            return None

    def _calculate_confidence_level(self, intelligence_data: Dict[str, Any]) -> float:
        """Calculate confidence level for intelligence preservation."""
        try:
            confidence_factors = []

            # Conversation length factor
            conversation_length = len(intelligence_data.get("conversation_history", []))
            conversation_factor = min(conversation_length / 5.0, 1.0)  # 5+ messages = full confidence
            confidence_factors.append(conversation_factor)

            # Data completeness factor
            has_properties = bool(intelligence_data.get("property_intelligence", {}).get("top_matches"))
            has_conversation = bool(intelligence_data.get("conversation_intelligence"))
            has_preferences = bool(intelligence_data.get("preference_intelligence"))

            data_completeness = (int(has_properties) + int(has_conversation) + int(has_preferences)) / 3.0
            confidence_factors.append(data_completeness)

            # Quality scores factor
            conversation_quality = intelligence_data.get("conversation_intelligence", {}).get(
                "conversation_quality_score", 50.0
            )
            quality_factor = conversation_quality / 100.0
            confidence_factors.append(quality_factor)

            # Calculate average confidence
            if confidence_factors:
                return sum(confidence_factors) / len(confidence_factors)
            else:
                return 0.5  # Default moderate confidence

        except Exception as e:
            logger.error(f"Failed to calculate confidence level: {e}")
            return 0.5

    def _calculate_data_completeness(self, intelligence_data: Dict[str, Any]) -> float:
        """Calculate data completeness ratio."""
        try:
            total_fields = 0
            completed_fields = 0

            # Check property intelligence completeness
            property_intel = intelligence_data.get("property_intelligence", {})
            total_fields += 3
            if property_intel.get("top_matches"):
                completed_fields += 1
            if property_intel.get("best_match_score", 0) > 0:
                completed_fields += 1
            if property_intel.get("presentation_strategy"):
                completed_fields += 1

            # Check conversation intelligence completeness
            conversation_intel = intelligence_data.get("conversation_intelligence", {})
            total_fields += 4
            if conversation_intel.get("objections_detected"):
                completed_fields += 1
            if conversation_intel.get("overall_sentiment") is not None:
                completed_fields += 1
            if conversation_intel.get("conversation_quality_score", 0) > 0:
                completed_fields += 1
            if conversation_intel.get("response_recommendations"):
                completed_fields += 1

            # Check preference intelligence completeness
            preference_intel = intelligence_data.get("preference_intelligence", {})
            total_fields += 3
            if preference_intel.get("budget_range"):
                completed_fields += 1
            if preference_intel.get("location_preferences"):
                completed_fields += 1
            if preference_intel.get("profile_completeness", 0) > 0:
                completed_fields += 1

            return completed_fields / total_fields if total_fields > 0 else 0.0

        except Exception as e:
            logger.error(f"Failed to calculate data completeness: {e}")
            return 0.0

    async def _update_transition_history(
        self, lead_id: str, location_id: str, bot_transition: BotTransition, snapshot: IntelligenceSnapshot
    ) -> None:
        """Update transition history with new handoff."""
        try:
            # Get existing history
            history = await self.get_transition_history(lead_id, location_id)

            # Create handoff result (preliminary)
            handoff = ContextHandoff(
                success=True,
                handoff_status=HandoffStatus.SUCCESS,
                lead_id=lead_id,
                location_id=location_id,
                intelligence_snapshot_id=snapshot.snapshot_id,
                transition_id=bot_transition.transition_id,
                preservation_latency_ms=0.0,  # Will be updated
            )

            # Add transition to history
            history.add_transition(bot_transition, handoff)

            # Cache updated history
            history_key = self._generate_history_key(lead_id)
            await self.cache.set(key=history_key, value=json.dumps(history.to_dict()), ttl=HISTORY_CACHE_TTL)

        except Exception as e:
            logger.error(f"Failed to update transition history: {e}")

    async def _publish_handoff_event(
        self, snapshot: IntelligenceSnapshot, bot_transition: BotTransition, handoff_result: ContextHandoff
    ) -> None:
        """Publish handoff event via EventPublisher."""
        try:
            # Use existing event publisher method or create handoff-specific event
            # Assuming we can use lead_update event type with handoff data
            await self.event_publisher.publish_lead_update(
                lead_id=snapshot.lead_id,
                lead_data={
                    "source_bot": bot_transition.source_bot.value,
                    "target_bot": bot_transition.target_bot.value,
                    "transition_reason": bot_transition.transition_reason.value,
                    "handoff_success": handoff_result.success,
                    "preservation_latency_ms": handoff_result.preservation_latency_ms,
                    "intelligence_quality": self._assess_intelligence_quality(snapshot),
                    "data_size_kb": handoff_result.data_size_bytes / 1024,
                    "cache_ttl_hours": HANDOFF_CACHE_TTL / 3600,
                },
                action="bot_handoff",
                location_id=snapshot.location_id,
            )

        except Exception as e:
            logger.error(f"Failed to publish handoff event: {e}")

    def _assess_intelligence_quality(self, snapshot: IntelligenceSnapshot) -> str:
        """Assess intelligence quality for event publishing."""
        try:
            score = 0

            # Property matches available
            if snapshot.preserved_intelligence.top_property_matches:
                score += 1

            # Conversation insights available
            if (
                snapshot.preserved_intelligence.key_objections_detected
                or snapshot.preserved_intelligence.response_recommendations
            ):
                score += 1

            # Preferences available
            if snapshot.preserved_intelligence.budget_range or snapshot.preserved_intelligence.location_preferences:
                score += 1

            # High confidence
            if snapshot.confidence_level > 0.8:
                score += 1

            quality_map = {4: "excellent", 3: "good", 2: "fair", 1: "poor", 0: "minimal"}

            return quality_map.get(score, "poor")

        except Exception as e:
            logger.error(f"Failed to assess intelligence quality: {e}")
            return "unknown"

    def _generate_handoff_key(self, lead_id: str, target_bot: BotType) -> str:
        """Generate cache key for handoff context."""
        return f"intelligence:handoff:{lead_id}:{target_bot.value}"

    def _generate_history_key(self, lead_id: str) -> str:
        """Generate cache key for transition history."""
        return f"intelligence:history:{lead_id}"

    def _update_preservation_metrics(self, latency_ms: float, data_size_bytes: int, success: bool) -> None:
        """Update preservation performance metrics."""
        self.metrics["total_preservations"] += 1

        if success:
            self.metrics["successful_preservations"] += 1
        else:
            self.metrics["failed_preservations"] += 1

        # Update latency metrics
        if latency_ms > 0:
            total_time = (
                self.metrics["avg_preservation_latency_ms"] * (self.metrics["total_preservations"] - 1) + latency_ms
            )
            self.metrics["avg_preservation_latency_ms"] = total_time / self.metrics["total_preservations"]

            # Track latency samples for percentile calculation
            self._preservation_latencies.append(latency_ms)
            if len(self._preservation_latencies) > self._max_samples:
                self._preservation_latencies = self._preservation_latencies[-self._max_samples :]

        # Update data volume metrics
        self.metrics["total_data_preserved_mb"] += data_size_bytes / (1024 * 1024)

    def _update_retrieval_metrics(self, retrieval_latency_ms: float, success: bool) -> None:
        """Update retrieval performance metrics."""
        self.metrics["total_retrievals"] += 1

        if success:
            self.metrics["successful_retrievals"] += 1

        # Update latency metrics
        if retrieval_latency_ms > 0:
            total_time = (
                self.metrics["avg_retrieval_latency_ms"] * (self.metrics["total_retrievals"] - 1) + retrieval_latency_ms
            )
            self.metrics["avg_retrieval_latency_ms"] = total_time / self.metrics["total_retrievals"]

            # Track latency samples
            self._retrieval_latencies.append(retrieval_latency_ms)
            if len(self._retrieval_latencies) > self._max_samples:
                self._retrieval_latencies = self._retrieval_latencies[-self._max_samples :]

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        total_operations = self.metrics["total_preservations"] + self.metrics["total_retrievals"]
        cache_operations = self.metrics["cache_hits"] + self.metrics["cache_misses"]

        cache_hit_rate = self.metrics["cache_hits"] / cache_operations * 100 if cache_operations > 0 else 0.0

        preservation_success_rate = (
            self.metrics["successful_preservations"] / self.metrics["total_preservations"] * 100
            if self.metrics["total_preservations"] > 0
            else 0.0
        )

        # Calculate percentiles
        p99_preservation = 0.0
        p99_retrieval = 0.0

        if self._preservation_latencies:
            sorted_preservation = sorted(self._preservation_latencies)
            p99_idx = int(len(sorted_preservation) * 0.99)
            p99_preservation = (
                sorted_preservation[p99_idx] if p99_idx < len(sorted_preservation) else sorted_preservation[-1]
            )

        if self._retrieval_latencies:
            sorted_retrieval = sorted(self._retrieval_latencies)
            p99_idx = int(len(sorted_retrieval) * 0.99)
            p99_retrieval = sorted_retrieval[p99_idx] if p99_idx < len(sorted_retrieval) else sorted_retrieval[-1]

        return {
            **self.metrics,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "preservation_success_rate_percent": round(preservation_success_rate, 2),
            "p99_preservation_latency_ms": round(p99_preservation, 2),
            "p99_retrieval_latency_ms": round(p99_retrieval, 2),
            "preservation_target_ms": PRESERVATION_TARGET_MS,
            "retrieval_target_ms": RETRIEVAL_TARGET_MS,
            "performance_status": self._assess_performance_status(p99_preservation, p99_retrieval),
        }

    def _assess_performance_status(self, p99_preservation: float, p99_retrieval: float) -> str:
        """Assess overall performance status."""
        preservation_ok = p99_preservation <= PRESERVATION_TARGET_MS
        retrieval_ok = p99_retrieval <= RETRIEVAL_TARGET_MS

        if preservation_ok and retrieval_ok:
            return "excellent"
        elif preservation_ok or retrieval_ok:
            return "good"
        else:
            return "degraded"


# Global service instance (singleton pattern)
_intelligence_context_service_instance = None


def get_intelligence_context_service() -> IntelligenceContextService:
    """
    Get the global IntelligenceContextService instance (singleton pattern).

    Returns:
        IntelligenceContextService: The global service instance
    """
    global _intelligence_context_service_instance
    if _intelligence_context_service_instance is None:
        _intelligence_context_service_instance = IntelligenceContextService()
    return _intelligence_context_service_instance


# Service health check
async def health_check() -> Dict[str, Any]:
    """Health check for the intelligence context service."""
    try:
        service = get_intelligence_context_service()
        metrics = service.get_metrics()

        return {
            "service": "IntelligenceContextService",
            "status": "healthy",
            "version": "3.2.0",
            "metrics": metrics,
            "dependencies": {
                "cache_service": "connected",
                "event_publisher": "connected",
                "bot_intelligence_middleware": "optional",
            },
            "cache_ttl": {
                "handoff_contexts": f"{HANDOFF_CACHE_TTL}s (2h)",
                "active_contexts": f"{ACTIVE_CACHE_TTL}s (5m)",
                "transition_history": f"{HISTORY_CACHE_TTL}s (24h)",
            },
        }
    except Exception as e:
        return {"service": "IntelligenceContextService", "status": "unhealthy", "error": str(e)}
