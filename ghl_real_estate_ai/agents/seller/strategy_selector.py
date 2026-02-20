"""
Strategy selection service for Jorge Seller Bot.

Enhanced with Track 3.1 Predictive Intelligence for optimal approach selection.
"""

from typing import Any, Dict, Literal, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.services.event_publisher import EventPublisher, get_event_publisher

try:
    from bots.shared.ml_analytics_engine import MLAnalyticsEngine, get_ml_analytics_engine
    ML_ANALYTICS_AVAILABLE = True
except ImportError:
    ML_ANALYTICS_AVAILABLE = False
    get_ml_analytics_engine = None

logger = get_logger(__name__)


class StrategySelector:
    """Service for selecting Jorge's conversation strategy."""

    def __init__(
        self,
        event_publisher: Optional[EventPublisher] = None,
        ml_analytics: Optional[Any] = None,
        tenant_id: str = "jorge_seller"
    ):
        self.event_publisher = event_publisher or get_event_publisher()
        self.ml_analytics = ml_analytics
        self.tenant_id = tenant_id

    async def select_strategy(self, state: JorgeSellerState) -> Dict[str, Any]:
        """
        Enhanced strategy selection with Track 3.1 Predictive Intelligence.

        Maintains Jorge's helpful methodology while adding:
        - Journey progression analysis for strategic timing
        - Behavioral pattern recognition for optimal approach
        - Market context injection for enhanced effectiveness
        - Conversion probability-driven decision making
        """
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="select_strategy_enhanced",
        )

        lead_id = state["lead_id"]
        pcs = state.get("psychological_commitment", 0)

        # FRIENDLY APPROACH: Jorge's helpful consultation foundation
        # Check for listing prep routing (qualified + address + listing_prep stage)
        if (
            state.get("is_qualified")
            and state.get("property_address")
            and state.get("current_journey_stage") == "listing_prep"
        ):
            base_strategy = {"current_tone": "ENTHUSIASTIC", "next_action": "listing_prep"}
        elif state.get("stall_detected"):
            base_strategy = {"current_tone": "UNDERSTANDING", "next_action": "respond"}
        elif pcs < 30:
            # Low commitment = Supportive approach (help them understand)
            base_strategy = {"current_tone": "EDUCATIONAL", "next_action": "respond"}
        elif pcs >= 70:
            # High commitment = Enthusiastic support + calendar booking
            base_strategy = {"current_tone": "ENTHUSIASTIC", "next_action": "respond", "adaptive_mode": "calendar_focused"}
        else:
            base_strategy = {"current_tone": "CONSULTATIVE", "next_action": "respond"}

        # If ML analytics not available, return base strategy
        if not ML_ANALYTICS_AVAILABLE or not self.ml_analytics:
            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_{state['lead_id']}",
                lead_id=state["lead_id"],
                stage="strategy_selected",
                message=f"Jorge tone: {base_strategy['current_tone']} (PCS: {pcs}) [No ML enhancement]",
            )
            return base_strategy

        try:
            # TRACK 3.1 ENHANCEMENT: Predictive Intelligence Layer
            logger.info(f"Applying Track 3.1 predictive intelligence for lead {lead_id}")

            # Get comprehensive predictive analysis
            journey_analysis = await self.ml_analytics.predict_lead_journey(lead_id)
            conversion_analysis = await self.ml_analytics.predict_conversion_probability(
                lead_id, state.get("current_journey_stage", "qualification")
            )
            touchpoint_analysis = await self.ml_analytics.predict_optimal_touchpoints(lead_id)

            # BEHAVIORAL ENHANCEMENT: Adjust strategy based on response patterns
            enhanced_strategy = self._apply_behavioral_intelligence(
                base_strategy, journey_analysis, conversion_analysis, touchpoint_analysis
            )

            # MARKET TIMING ENHANCEMENT: Add urgency and timing context
            final_strategy = self._apply_market_timing_intelligence(
                enhanced_strategy, journey_analysis, conversion_analysis
            )

            # Emit enhanced conversation event with predictive context
            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_{state['lead_id']}",
                lead_id=state["lead_id"],
                stage="strategy_selected_enhanced",
                message=f"Jorge tone: {final_strategy['current_tone']} (PCS: {pcs}) [Track 3.1: Conv={journey_analysis.conversion_probability:.2f}]",
            )

            # Emit Track 3.1 predictive insights event
            await self.event_publisher.publish_bot_status_update(
                bot_type="jorge-seller",
                contact_id=state["lead_id"],
                status="enhanced",
                current_step="predictive_analysis_complete",
                additional_data={
                    "conversion_probability": journey_analysis.conversion_probability,
                    "stage_progression_velocity": journey_analysis.stage_progression_velocity,
                    "response_pattern": touchpoint_analysis.response_pattern,
                    "urgency_score": conversion_analysis.urgency_score,
                    "optimal_action": conversion_analysis.optimal_action,
                    "enhancement_applied": True,
                },
            )

            logger.info(
                f"Track 3.1 enhanced strategy for {lead_id}: {final_strategy['current_tone']} "
                f"(conv_prob={journey_analysis.conversion_probability:.3f})"
            )

            return final_strategy

        except Exception as e:
            # GRACEFUL FALLBACK: Use Jorge's proven logic if Track 3.1 fails
            logger.warning(f"Track 3.1 enhancement failed for lead {lead_id}, using base strategy: {e}")

            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_{state['lead_id']}",
                lead_id=state["lead_id"],
                stage="strategy_selected",
                message=f"Jorge tone: {base_strategy['current_tone']} (PCS: {pcs}) [Fallback mode]",
            )

            return base_strategy

    def _apply_behavioral_intelligence(
        self, base_strategy: Dict, journey_analysis, conversion_analysis, touchpoint_analysis
    ) -> Dict:
        """Apply behavioral intelligence to enhance Jorge's approach."""
        enhanced_strategy = base_strategy.copy()

        # BEHAVIORAL PATTERN ANALYSIS
        response_pattern = touchpoint_analysis.response_pattern
        conversion_prob = journey_analysis.conversion_probability
        stage_velocity = journey_analysis.stage_progression_velocity

        # ENHANCEMENT 1: Response Pattern Optimization
        if response_pattern == "fast" and conversion_prob > 0.6:
            # Fast responders with high conversion probability = MORE ENTHUSIASTIC
            if enhanced_strategy["current_tone"] == "CONSULTATIVE":
                enhanced_strategy["current_tone"] = "ENTHUSIASTIC"
                enhanced_strategy["enhancement_reason"] = "fast_responder_high_conversion"
            elif enhanced_strategy["current_tone"] == "EDUCATIONAL":
                enhanced_strategy["current_tone"] = "CONSULTATIVE"
                enhanced_strategy["enhancement_reason"] = "fast_responder_upgrade"

        elif response_pattern == "slow" and conversion_prob < 0.3:
            # Slow responders with low conversion = MORE EDUCATIONAL
            if enhanced_strategy["current_tone"] == "CONSULTATIVE":
                enhanced_strategy["current_tone"] = "EDUCATIONAL"
                enhanced_strategy["enhancement_reason"] = "slow_responder_education_needed"
            elif enhanced_strategy["current_tone"] == "ENTHUSIASTIC":
                enhanced_strategy["current_tone"] = "CONSULTATIVE"
                enhanced_strategy["enhancement_reason"] = "slow_responder_gentle_approach"

        # ENHANCEMENT 2: Stage Progression Velocity
        if stage_velocity > 0.8:
            # Fast-moving leads = MAINTAIN MOMENTUM WITH ENTHUSIASM
            enhanced_strategy["enthusiasm_boost"] = True
            enhanced_strategy["momentum_factor"] = "high"
        elif stage_velocity < 0.3:
            # Stalled progression = PROVIDE MORE SUPPORT
            if enhanced_strategy["current_tone"] != "EDUCATIONAL":
                enhanced_strategy["support_increase"] = True
                enhanced_strategy["educational_focus"] = True

        # ENHANCEMENT 3: Conversion Probability Context
        if conversion_prob > 0.7:
            # High conversion probability = MAINTAIN CURRENT APPROACH
            enhanced_strategy["confidence_level"] = "high"
            enhanced_strategy["approach_validation"] = "maintain_course"
        elif conversion_prob < 0.3 and enhanced_strategy["current_tone"] != "EDUCATIONAL":
            # Low conversion probability = PROVIDE MORE EDUCATION
            enhanced_strategy["education_emphasis"] = True

        # Track behavioral intelligence application
        enhanced_strategy["track3_behavioral_applied"] = True
        enhanced_strategy["behavioral_factors"] = {
            "response_pattern": response_pattern,
            "conversion_probability": conversion_prob,
            "stage_progression_velocity": stage_velocity,
        }

        return enhanced_strategy

    def _apply_market_timing_intelligence(
        self, strategy: Dict, journey_analysis, conversion_analysis
    ) -> Dict:
        """Apply market timing intelligence to enhance strategic effectiveness."""
        final_strategy = strategy.copy()

        urgency_score = conversion_analysis.urgency_score
        optimal_action = conversion_analysis.optimal_action
        stage_bottlenecks = journey_analysis.stage_bottlenecks

        # MARKET TIMING ENHANCEMENT 1: Urgency-Based Support
        if urgency_score > 0.8:
            # HIGH URGENCY = MAXIMUM SUPPORT AND ENTHUSIASM
            final_strategy["market_urgency"] = "high"

            if final_strategy["current_tone"] == "CONSULTATIVE":
                final_strategy["current_tone"] = "ENTHUSIASTIC"
                final_strategy["timing_reason"] = "high_market_urgency"
            elif final_strategy["current_tone"] == "EDUCATIONAL":
                final_strategy["current_tone"] = "CONSULTATIVE"
                final_strategy["timing_reason"] = "urgency_upgrade_support"

        elif urgency_score < 0.3:
            # LOW URGENCY = PATIENT EDUCATION
            if final_strategy["current_tone"] == "ENTHUSIASTIC":
                final_strategy["current_tone"] = "CONSULTATIVE"
                final_strategy["timing_reason"] = "low_urgency_patience"

        # MARKET TIMING ENHANCEMENT 2: Optimal Action Integration
        jorge_action_mapping = {
            "schedule_qualification_call": "CONSULTATIVE",
            "schedule_appointment": "ENTHUSIASTIC",
            "clarify_requirements": "EDUCATIONAL",
            "nurture_relationship": "SUPPORTIVE",
            "follow_up_contact": "CONSULTATIVE",
        }

        suggested_tone = jorge_action_mapping.get(optimal_action)
        if suggested_tone and suggested_tone != final_strategy["current_tone"]:
            # Adjust to maintain helpfulness while being effective
            final_strategy["current_tone"] = suggested_tone
            final_strategy["action_alignment"] = True
            final_strategy["optimal_action_applied"] = optimal_action

        # MARKET TIMING ENHANCEMENT 3: Bottleneck-Based Strategy
        if "stalled_in_stage" in stage_bottlenecks or "slow_response_time" in stage_bottlenecks:
            # STALLS = SUPPORTIVE BREAKTHROUGH
            if final_strategy["current_tone"] == "CONSULTATIVE":
                final_strategy["current_tone"] = "UNDERSTANDING"
                final_strategy["bottleneck_reason"] = "stage_stall_detected"

        elif "price_misalignment" in stage_bottlenecks:
            # PRICE ISSUES = GENTLE EDUCATION
            final_strategy["current_tone"] = "EDUCATIONAL"
            final_strategy["bottleneck_reason"] = "price_education_needed"

        # Track market timing intelligence application
        final_strategy["track3_timing_applied"] = True
        final_strategy["timing_factors"] = {
            "urgency_score": urgency_score,
            "optimal_action": optimal_action,
            "stage_bottlenecks": stage_bottlenecks,
        }

        return final_strategy

    def route_seller_action(
        self, state: JorgeSellerState
    ) -> Literal["respond", "follow_up", "listing_prep", "end"]:
        """Determine if we should respond immediately or queue a follow-up."""
        next_action = state.get("next_action", "respond")
        if next_action == "follow_up":
            return "follow_up"
        if next_action == "end":
            return "end"
        if next_action == "listing_prep":
            return "listing_prep"
        return "respond"

    def route_after_stall_detection(
        self, state: JorgeSellerState
    ) -> Literal["defend_valuation", "negotiation_discovery", "select_strategy"]:
        """Route to valuation defense, QBQ discovery, or strategy selection after stall."""
        if (
            state.get("detected_stall_type") == "zestimate"
            and state.get("cma_report") is not None
        ):
            return "defend_valuation"
        # QBQ: Route surface objections to negotiation discovery (once per conversation)
        if (
            state.get("detected_stall_type") in ["zestimate", "price", "surface_objection"]
            and not state.get("qbq_attempted")
        ):
            return "negotiation_discovery"
        return "select_strategy"

    def route_after_objection(
        self, state: JorgeSellerState
    ) -> Literal["objection_response", "continue_normal"]:
        """Route based on objection detection."""
        if state.get("objection_detected") and state.get("objection_response_text"):
            return "objection_response"
        return "continue_normal"

    def route_adaptive_action(
        self, state: JorgeSellerState
    ) -> Literal["respond", "follow_up", "fast_track", "end"]:
        """Enhanced routing with fast-track capability."""
        if state.get("adaptive_mode") == "calendar_focused":
            return "fast_track"
        if state.get("next_action") == "follow_up":
            return "follow_up"
        if state.get("next_action") == "end":
            return "end"
        return "respond"
