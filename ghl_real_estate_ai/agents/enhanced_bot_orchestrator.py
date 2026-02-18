"""
Enhanced Bot Orchestrator - Track 1 Intelligence Integration
Coordinates AdaptiveJorgeBot, PredictiveLeadBot, and RealTimeIntentDecoder.
Production-ready orchestration layer for Jorge's AI ecosystem.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

try:
    from ghl_real_estate_ai.agents.adaptive_jorge_seller_bot import AdaptiveJorgeBot, get_adaptive_jorge_bot
except ImportError:
    AdaptiveJorgeBot = None
    get_adaptive_jorge_bot = None
from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
from ghl_real_estate_ai.agents.predictive_lead_bot import get_predictive_lead_bot
from ghl_real_estate_ai.agents.realtime_intent_decoder import get_realtime_intent_decoder
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)


class BotType(Enum):
    """Types of bots in the enhanced ecosystem."""

    ADAPTIVE_JORGE = "adaptive_jorge"
    PREDICTIVE_LEAD = "predictive_lead"
    REALTIME_INTENT = "realtime_intent"


@dataclass
class BotOrchestrationConfig:
    """Configuration for bot orchestration."""

    enable_realtime_analysis: bool = True
    enable_adaptive_questioning: bool = True
    enable_predictive_timing: bool = True
    realtime_threshold: float = 0.8  # Confidence threshold for real-time decisions
    max_concurrent_bots: int = 3
    fallback_to_original: bool = True  # Fallback to original bots if enhanced fail


@dataclass
class ConversationSession:
    """Tracks a conversation session across all bots."""

    session_id: str
    lead_id: str
    lead_name: str
    conversation_history: List[Dict]
    active_bots: List[BotType]
    session_start: datetime
    last_interaction: datetime
    intent_profile: Optional[Dict]
    orchestration_state: Dict[str, Any]


class EnhancedBotOrchestrator:
    """
    Orchestrates the enhanced bot ecosystem for optimal lead engagement.
    Coordinates real-time analysis, adaptive questioning, and predictive timing.
    """

    def __init__(self, config: Optional[BotOrchestrationConfig] = None):
        self.config = config or BotOrchestrationConfig()

        # Initialize enhanced bots
        self.adaptive_jorge = None
        self.predictive_lead = None
        self.realtime_intent = None

        try:
            if callable(get_adaptive_jorge_bot):
                self.adaptive_jorge = get_adaptive_jorge_bot()
        except Exception as exc:
            logger.warning(f"Adaptive Jorge bot unavailable, using fallback path: {exc}")

        try:
            if callable(get_predictive_lead_bot):
                self.predictive_lead = get_predictive_lead_bot()
        except Exception as exc:
            logger.warning(f"Predictive Lead bot unavailable, using fallback path: {exc}")

        try:
            if callable(get_realtime_intent_decoder):
                self.realtime_intent = get_realtime_intent_decoder()
        except Exception as exc:
            logger.warning(f"Realtime intent decoder unavailable, using fallback path: {exc}")

        self.event_publisher = get_event_publisher()

        # Session management
        self.active_sessions: Dict[str, ConversationSession] = {}

        # Performance tracking
        self.orchestration_metrics = {
            "total_sessions": 0,
            "adaptive_decisions": 0,
            "predictive_optimizations": 0,
            "realtime_interventions": 0,
            "fallbacks_triggered": 0,
        }

    async def orchestrate_conversation(
        self,
        lead_id: str,
        lead_name: str,
        message: str,
        conversation_type: Literal["seller", "buyer", "lead_sequence"],
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Main orchestration method for conversation processing.
        Routes to appropriate enhanced bot based on conversation type.
        """

        session_id = f"{conversation_type}_{lead_id}"
        session = await self._get_or_create_session(session_id, lead_id, lead_name, conversation_history or [])

        logger.info(f"Orchestrating {conversation_type} conversation for {lead_name} (Session: {session_id})")

        try:
            # Step 1: Real-time intent analysis
            intent_update = None
            if self.config.enable_realtime_analysis:
                intent_update = await self._perform_realtime_analysis(session, message)

            # Step 2: Route to appropriate enhanced bot
            if conversation_type == "seller":
                result = await self._orchestrate_seller_conversation(session, message, intent_update)
            elif conversation_type == "buyer":
                # Future: Enhanced buyer bot (not implemented in this phase)
                result = await self._orchestrate_buyer_conversation(session, message, intent_update)
            elif conversation_type == "lead_sequence":
                result = await self._orchestrate_lead_sequence(session, message, intent_update)
            else:
                raise ValueError(f"Unknown conversation type: {conversation_type}")

            # Step 3: Update session state
            await self._update_session_state(session, result, intent_update)

            # Step 4: Emit orchestration events
            await self._emit_orchestration_events(session, result, intent_update)

            # Update metrics
            self.orchestration_metrics["total_sessions"] = len(self.active_sessions)

            return result

        except Exception as e:
            logger.error(f"Orchestration error for session {session_id}: {e}")

            # Fallback to original bots if enabled
            if self.config.fallback_to_original:
                self.orchestration_metrics["fallbacks_triggered"] += 1
                return await self._fallback_to_original(
                    conversation_type, lead_id, lead_name, message, conversation_history
                )

            raise

    async def _perform_realtime_analysis(self, session: ConversationSession, message: str) -> Optional[Dict]:
        """Perform real-time intent analysis on incoming message."""
        if not self.realtime_intent:
            return None

        try:
            conversation_id = f"enhanced_{session.session_id}"
            intent_update = await self.realtime_intent.stream_intent_analysis(
                message=message, conversation_id=conversation_id, lead_id=session.lead_id
            )

            logger.info(f"Real-time analysis: FRS Δ{intent_update.frs_delta:.1f}, PCS Δ{intent_update.pcs_delta:.1f}")

            # Check for high-confidence interventions
            if intent_update.confidence > self.config.realtime_threshold:
                self.orchestration_metrics["realtime_interventions"] += 1

            return {
                "intent_update": intent_update,
                "high_confidence": intent_update.confidence > self.config.realtime_threshold,
                "recommended_action": intent_update.recommended_action,
            }

        except Exception as e:
            logger.error(f"Real-time analysis error: {e}")
            return None

    async def _orchestrate_seller_conversation(
        self, session: ConversationSession, message: str, intent_update: Optional[Dict]
    ) -> Dict[str, Any]:
        """Orchestrate seller conversation using AdaptiveJorgeBot."""

        # Update conversation history
        session.conversation_history.append({"role": "user", "content": message, "timestamp": datetime.now()})

        # Use adaptive Jorge bot
        if self.config.enable_adaptive_questioning and self.adaptive_jorge:
            result = await self.adaptive_jorge.process_adaptive_seller_message(
                lead_id=session.lead_id, lead_name=session.lead_name, history=session.conversation_history
            )

            self.orchestration_metrics["adaptive_decisions"] += 1

            # Enhance result with real-time insights
            if intent_update and intent_update.get("high_confidence"):
                result["realtime_insights"] = {
                    "signals_detected": intent_update["intent_update"].signals_detected,
                    "recommended_action": intent_update["recommended_action"],
                    "confidence": intent_update["intent_update"].confidence,
                }

            return {
                "bot_type": "adaptive_jorge",
                "response_content": result.get("response_content"),
                "adaptive_mode": result.get("adaptive_mode"),
                "adaptation_applied": result.get("adaptation_applied", False),
                "realtime_insights": result.get("realtime_insights"),
                "orchestration_metadata": {
                    "session_id": session.session_id,
                    "enhancement_level": "adaptive",
                    "processing_time": datetime.now(),
                },
            }

        # Fallback to original if adaptive is disabled
        return await self._fallback_jorge_conversation(session.lead_id, session.lead_name, session.conversation_history)

    async def _orchestrate_lead_sequence(
        self, session: ConversationSession, message: str, intent_update: Optional[Dict]
    ) -> Dict[str, Any]:
        """Orchestrate lead sequence using PredictiveLeadBot."""

        # Update conversation history
        session.conversation_history.append({"role": "user", "content": message, "timestamp": datetime.now()})

        if self.config.enable_predictive_timing and self.predictive_lead:
            # Determine sequence day from session state
            sequence_day = session.orchestration_state.get("current_sequence_day", 3)

            result = await self.predictive_lead.process_predictive_lead_sequence(
                lead_id=session.lead_id, sequence_day=sequence_day, conversation_history=session.conversation_history
            )

            self.orchestration_metrics["predictive_optimizations"] += 1

            # Enhance with real-time insights
            if intent_update and intent_update.get("high_confidence"):
                # Adjust sequence timing based on real-time analysis
                if "ACCELERATE" in intent_update.get("recommended_action", ""):
                    result["timing_adjustment"] = "accelerated"
                elif "RE_ENGAGEMENT" in intent_update.get("recommended_action", ""):
                    result["timing_adjustment"] = "intervention_mode"

            return {
                "bot_type": "predictive_lead",
                "sequence_day": sequence_day,
                "optimization_applied": True,
                "timing_adjustment": result.get("timing_adjustment"),
                "behavioral_insights": result.get("response_pattern"),
                "personality_adaptation": result.get("personality_type"),
                "realtime_insights": intent_update,
                "orchestration_metadata": {
                    "session_id": session.session_id,
                    "enhancement_level": "predictive",
                    "processing_time": datetime.now(),
                },
            }

        # Fallback to original lead bot
        return await self._fallback_lead_sequence(session.lead_id, session.conversation_history)

    async def _orchestrate_buyer_conversation(
        self, session: ConversationSession, message: str, intent_update: Optional[Dict]
    ) -> Dict[str, Any]:
        """Orchestrate buyer conversation using Jorge's buyer bot."""
        try:
            buyer_bot = JorgeBuyerBot(tenant_id=session.lead_id)

            # Process buyer conversation through complete qualification workflow
            result = await buyer_bot.process_buyer_conversation(
                buyer_id=session.lead_id,
                buyer_name=session.lead_name,
                conversation_history=session.conversation_history,
            )

            # Emit buyer-specific qualification progress
            if result.get("intent_profile"):
                await self.event_publisher.publish_buyer_qualification_progress(
                    contact_id=session.lead_id,
                    current_step=result.get("current_qualification_step", "discovery"),
                    financial_readiness_score=result.get("financial_readiness_score", 0),
                    motivation_score=result.get("buying_motivation_score", 0),
                    qualification_status="qualified" if result.get("is_qualified") else "in_progress",
                    properties_matched=len(result.get("matched_properties", [])),
                )

            return {
                "bot_type": "jorge_buyer",
                "message": result.get("response_content", "Let me help you find the right property."),
                "enhancement_level": "qualified_buyer_bot",
                "buyer_temperature": result.get("buyer_temperature", "cold"),
                "financial_readiness_score": result.get("financial_readiness_score", 0),
                "properties_matched": len(result.get("matched_properties", [])),
                "qualification_status": "qualified" if result.get("is_qualified") else "in_progress",
                "next_action": result.get("next_action", "continue_qualification"),
                "processing_time": datetime.now(),
                "workflow_result": result,
            }

        except Exception as e:
            logger.error(f"Error in buyer bot orchestration for {session.lead_id}: {str(e)}")
            return {
                "bot_type": "jorge_buyer_error",
                "message": "I'm having technical difficulties. Let me connect you with Jorge directly.",
                "enhancement_level": "error_fallback",
                "error": str(e),
            }

    async def _get_or_create_session(
        self, session_id: str, lead_id: str, lead_name: str, conversation_history: List[Dict]
    ) -> ConversationSession:
        """Get existing session or create new one."""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = ConversationSession(
                session_id=session_id,
                lead_id=lead_id,
                lead_name=lead_name,
                conversation_history=conversation_history.copy(),
                active_bots=[],
                session_start=datetime.now(),
                last_interaction=datetime.now(),
                intent_profile=None,
                orchestration_state={},
            )

        session = self.active_sessions[session_id]
        session.last_interaction = datetime.now()

        return session

    async def _update_session_state(
        self, session: ConversationSession, result: Dict[str, Any], intent_update: Optional[Dict]
    ):
        """Update session state with processing results."""

        # Update active bots list
        bot_type = result.get("bot_type")
        if bot_type:
            try:
                enum_bot = BotType(bot_type)
                if enum_bot not in session.active_bots:
                    session.active_bots.append(enum_bot)
            except ValueError:
                # Ignore non-enum bot labels from fallback and compatibility paths.
                pass

        # Update intent profile
        if intent_update and "intent_update" in intent_update:
            session.intent_profile = {
                "last_update": datetime.now(),
                "frs_delta": intent_update["intent_update"].frs_delta,
                "pcs_delta": intent_update["intent_update"].pcs_delta,
                "confidence": intent_update["intent_update"].confidence,
            }

        # Update orchestration state
        session.orchestration_state.update(
            {
                "last_processing_result": result,
                "enhancement_level": result.get("enhancement_level", "none"),
                "total_messages": len(session.conversation_history),
                "last_bot_used": bot_type,
            }
        )

    async def _emit_orchestration_events(
        self, session: ConversationSession, result: Dict[str, Any], intent_update: Optional[Dict]
    ):
        """Emit events for orchestration monitoring."""

        await self.event_publisher.publish_bot_orchestration_event(
            session_id=session.session_id,
            contact_id=session.lead_id,
            bot_type=result.get("bot_type"),
            enhancement_level=result.get("enhancement_level", "none"),
            realtime_analysis_applied=intent_update is not None,
            adaptive_features_used=result.get("adaptation_applied", False),
            predictive_features_used=result.get("optimization_applied", False),
            session_duration_minutes=(datetime.now() - session.session_start).seconds / 60,
        )

    async def _fallback_to_original(
        self, conversation_type: str, lead_id: str, lead_name: str, message: str, conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """Fallback to original bot implementations."""
        logger.info(f"Falling back to original {conversation_type} bot for lead {lead_id}")

        if conversation_type == "seller":
            return await self._fallback_jorge_conversation(lead_id, lead_name, conversation_history)
        elif conversation_type == "lead_sequence":
            return await self._fallback_lead_sequence(lead_id, conversation_history)
        else:
            return {"error": "Fallback not available for this conversation type"}

    async def _fallback_jorge_conversation(
        self, lead_id: str, lead_name: str, conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """Fallback to original Jorge seller bot."""
        from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

        original_jorge = JorgeSellerBot()
        result = await original_jorge.process_seller_message(lead_id, lead_name, conversation_history)

        return {
            "bot_type": "original_jorge",
            "response_content": result.get("response_content"),
            "enhancement_level": "fallback",
            "fallback_reason": "Enhanced bot failure",
        }

    async def _fallback_lead_sequence(self, lead_id: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Fallback to original lead bot."""
        from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow

        original_lead_bot = LeadBotWorkflow()
        # Mock sequence execution for fallback

        return {"bot_type": "original_lead", "enhancement_level": "fallback", "fallback_reason": "Enhanced bot failure"}

    async def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get orchestration performance metrics."""
        return {
            **self.orchestration_metrics,
            "active_sessions": len(self.active_sessions),
            "enhancement_adoption": {
                "realtime_analysis": self.config.enable_realtime_analysis,
                "adaptive_questioning": self.config.enable_adaptive_questioning,
                "predictive_timing": self.config.enable_predictive_timing,
            },
            "session_details": [
                {
                    "session_id": session.session_id,
                    "lead_id": session.lead_id,
                    "active_bots": [bot.value for bot in session.active_bots],
                    "duration_minutes": (datetime.now() - session.session_start).seconds / 60,
                }
                for session in self.active_sessions.values()
            ],
        }

    async def cleanup_stale_sessions(self, max_age_hours: int = 24):
        """Clean up sessions older than specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        stale_sessions = [
            session_id for session_id, session in self.active_sessions.items() if session.last_interaction < cutoff_time
        ]

        for session_id in stale_sessions:
            del self.active_sessions[session_id]

        logger.info(f"Cleaned up {len(stale_sessions)} stale sessions")


# --- Singleton Factory ---

_orchestrator_instance: Optional[EnhancedBotOrchestrator] = None


def get_enhanced_bot_orchestrator(config: Optional[BotOrchestrationConfig] = None) -> EnhancedBotOrchestrator:
    """Get singleton enhanced bot orchestrator instance."""
    global _orchestrator_instance

    if _orchestrator_instance is None:
        _orchestrator_instance = EnhancedBotOrchestrator(config)

    return _orchestrator_instance


# --- Event Publisher Extensions ---


async def publish_bot_orchestration_event(event_publisher, **kwargs):
    """Publish bot orchestration event."""
    await event_publisher.publish_event(event_type="bot_orchestration_event", data=kwargs)


# --- Configuration Presets ---


class OrchestrationPresets:
    """Predefined orchestration configurations."""

    @staticmethod
    def production_config() -> BotOrchestrationConfig:
        """Production-ready configuration with all enhancements enabled."""
        return BotOrchestrationConfig(
            enable_realtime_analysis=True,
            enable_adaptive_questioning=True,
            enable_predictive_timing=True,
            realtime_threshold=0.8,
            max_concurrent_bots=3,
            fallback_to_original=True,
        )

    @staticmethod
    def conservative_config() -> BotOrchestrationConfig:
        """Conservative configuration with higher thresholds."""
        return BotOrchestrationConfig(
            enable_realtime_analysis=True,
            enable_adaptive_questioning=False,  # Disabled for safety
            enable_predictive_timing=True,
            realtime_threshold=0.9,
            max_concurrent_bots=2,
            fallback_to_original=True,
        )

    @staticmethod
    def testing_config() -> BotOrchestrationConfig:
        """Configuration for testing and development."""
        return BotOrchestrationConfig(
            enable_realtime_analysis=True,
            enable_adaptive_questioning=True,
            enable_predictive_timing=True,
            realtime_threshold=0.5,  # Lower threshold for testing
            max_concurrent_bots=5,
            fallback_to_original=False,  # Force enhanced bots for testing
        )
