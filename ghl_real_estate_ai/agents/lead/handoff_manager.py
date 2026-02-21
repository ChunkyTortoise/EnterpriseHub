"""
Handoff Manager for coordinating cross-bot handoffs.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from ghl_real_estate_ai.ghl_utils.logger import get_logger

if TYPE_CHECKING:
    from ghl_real_estate_ai.models.workflows import LeadFollowUpState

logger = get_logger(__name__)


class HandoffManager:
    """Manages cross-bot handoff coordination"""

    def __init__(self, event_publisher=None):
        self.event_publisher = event_publisher

    async def publish_jorge_handoff_recommendation(
        self, state: "LeadFollowUpState", journey_analysis, conversion_analysis
    ) -> None:
        """Publish Jorge handoff recommendation event"""
        if not self.event_publisher:
            logger.warning("Event publisher not available for handoff recommendation")
            return

        await self.event_publisher.publish_strategy_recommendation(
            recommendation_id=f"handoff_{state['lead_id']}",
            contact_id=state["lead_id"],
            strategy_type="jorge_seller_handoff",
            data={
                "conversion_probability": journey_analysis.conversion_probability,
                "stage_conversion_probability": conversion_analysis.stage_conversion_probability,
                "recommendation": "Consider Jorge Seller Bot engagement for qualification",
            },
        )

    async def publish_jorge_handoff_request(
        self, state: "LeadFollowUpState", journey_analysis, conversion_analysis
    ) -> None:
        """Publish Jorge handoff request event"""
        if not self.event_publisher:
            logger.warning("Event publisher not available for handoff request")
            return

        await self.event_publisher.publish_bot_handoff_request(
            handoff_id=str(uuid4()),
            from_bot="enhanced-lead-bot",
            to_bot="jorge-seller-bot",
            contact_id=state["lead_id"],
            data={
                "handoff_type": "day_30_qualification",
                "handoff_data": {
                    "conversion_probability": journey_analysis.conversion_probability,
                    "stage_conversion_probability": conversion_analysis.stage_conversion_probability,
                    "lead_temperature": state.get("temperature_prediction", {}).get("current_temperature", 0),
                    "sequence_completion": "day_30_reached",
                    "recommendation": "Jorge confrontational qualification recommended",
                },
            },
        )

    async def publish_intelligent_jorge_handoff_request(
        self,
        state: "LeadFollowUpState",
        intelligence_context: Optional[Any],
        handoff_type: str,
        intelligence_score: float,
        handoff_reasoning: List[str],
    ) -> None:
        """Publish enhanced Jorge handoff request with comprehensive intelligence context."""
        if not self.event_publisher:
            logger.warning("Event publisher not available for intelligent handoff request")
            return

        handoff_data: Dict[str, Any] = {
            "handoff_type": handoff_type,
            "intelligence_score": intelligence_score,
            "handoff_reasoning": handoff_reasoning,
            "sequence_completion": "day_30_reached",
            "recommendation": f"Jorge {handoff_type} recommended based on comprehensive intelligence analysis",
        }

        # Add intelligence context details if available
        if intelligence_context:
            handoff_data.update(
                {
                    "engagement_score": intelligence_context.composite_engagement_score,
                    "property_matches": intelligence_context.property_intelligence.match_count,
                    "objections_count": len(intelligence_context.conversation_intelligence.objections_detected),
                    "sentiment": intelligence_context.conversation_intelligence.overall_sentiment,
                    "preference_completeness": intelligence_context.preference_intelligence.profile_completeness,
                    "recommended_approach": intelligence_context.recommended_approach,
                    "priority_insights": intelligence_context.priority_insights,
                }
            )

        # Add traditional analytics if available
        churn_risk = state.get("churn_risk_score")
        if churn_risk:
            handoff_data["churn_risk_score"] = churn_risk

        await self.event_publisher.publish_bot_handoff_request(
            handoff_id=str(uuid4()),
            from_bot="enhanced-lead-bot",
            to_bot="jorge-seller-bot",
            contact_id=state["lead_id"],
            data=handoff_data,
        )

        logger.info(
            f"Intelligent Jorge handoff request published for {state['lead_name']} "
            f"(type: {handoff_type}, score: {intelligence_score:.2f})"
        )

    @staticmethod
    def extract_handoff_signals(user_message: str) -> Dict[str, Any]:
        """Extract intent signals for cross-bot handoff detection."""
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

        return JorgeHandoffService.extract_intent_signals(user_message)

    @staticmethod
    def calculate_intelligence_score(intelligence_context: Any, churn_risk: float) -> float:
        """Calculate comprehensive intelligence score for handoff decision."""
        if not intelligence_context:
            return 0.5  # Default neutral

        engagement_score = intelligence_context.composite_engagement_score
        property_matches = intelligence_context.property_intelligence.match_count
        objections_count = len(intelligence_context.conversation_intelligence.objections_detected)
        sentiment = intelligence_context.conversation_intelligence.overall_sentiment
        preference_completeness = intelligence_context.preference_intelligence.profile_completeness

        # Calculate weighted score
        intelligence_score = (
            engagement_score * 0.3
            + min(property_matches / 5.0, 1.0) * 0.2  # Normalize to 0-1
            + max(0, (5 - objections_count) / 5.0) * 0.2  # Fewer objections = better
            + max(0, (sentiment + 1) / 2.0) * 0.15  # Normalize sentiment to 0-1
            + preference_completeness * 0.15
        )

        # Adjust for churn risk (inverse relationship)
        intelligence_score = intelligence_score * (1 - churn_risk * 0.5)

        return min(1.0, max(0.0, intelligence_score))

    def determine_final_strategy(
        self,
        intelligence_score: float,
        churn_risk: float,
        property_matches: int,
        sentiment: float,
        journey_analysis: Optional[Any] = None,
        conversion_analysis: Optional[Any] = None,
    ) -> str:
        """Determine final engagement strategy based on intelligence analysis."""
        # Enhanced decision logic using comprehensive intelligence
        if intelligence_score > 0.7 and churn_risk < 0.4:
            return "jorge_qualification"

        elif intelligence_score > 0.5 and property_matches > 2 and sentiment > 0:
            return "jorge_consultation"

        elif intelligence_score < 0.3 or churn_risk > 0.8:
            return "graceful_disengage"

        # Traditional Track 3.1 logic as backup
        if journey_analysis and conversion_analysis:
            if journey_analysis.conversion_probability > 0.5 and conversion_analysis.stage_conversion_probability > 0.4:
                return "jorge_qualification"
            elif journey_analysis.conversion_probability < 0.2 and conversion_analysis.drop_off_risk > 0.8:
                return "graceful_disengage"

        return "nurture"
