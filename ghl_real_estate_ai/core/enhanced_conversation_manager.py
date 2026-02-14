"""
Enhanced Conversation Manager with Competitive Intelligence

Extends the base conversation manager with:
1. Real-time competitor detection and analysis
2. Automatic competitive response generation
3. Alert system integration for Jorge
4. Competitive positioning and recovery strategies
5. Rancho Cucamonga market intelligence integration
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.core.conversation_manager import AIResponse, ConversationManager
from ghl_real_estate_ai.data.rancho_cucamonga_market_data import get_rancho_cucamonga_market_intelligence
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.prompts.competitive_responses import LeadProfile, get_competitive_response_system
from ghl_real_estate_ai.services.competitive_alert_system import get_competitive_alert_system
from ghl_real_estate_ai.services.competitor_intelligence import (
    CompetitiveAnalysis,
    CompetitorMention,
    RiskLevel,
    get_competitor_intelligence,
)

logger = get_logger(__name__)


@dataclass
class EnhancedAIResponse(AIResponse):
    """AI response with competitive intelligence"""

    competitive_analysis: Optional[CompetitiveAnalysis] = None
    competitive_response_applied: bool = False
    alert_sent: bool = False
    jorge_intervention_required: bool = False
    recovery_strategies: List[str] = None


class EnhancedConversationManager(ConversationManager):
    """
    Enhanced conversation manager with competitive intelligence

    Features:
    - Real-time competitor mention detection
    - Automatic competitive response generation
    - Jorge alert system for high-risk situations
    - Rancho Cucamonga market intelligence integration
    - Lead recovery strategies
    """

    def __init__(self):
        """Initialize enhanced conversation manager"""
        super().__init__()

        # Initialize competitive intelligence services
        self.competitor_intelligence = get_competitor_intelligence()
        self.competitive_response_system = get_competitive_response_system()
        self.competitive_alert_system = get_competitive_alert_system()
        self.rancho_cucamonga_market_intelligence = get_rancho_cucamonga_market_intelligence()

        logger.info("Enhanced conversation manager with competitive intelligence initialized")

    async def generate_response(
        self,
        user_message: str,
        contact_info: Dict[str, Any],
        context: Dict[str, Any],
        is_buyer: bool = True,
        tenant_config: Optional[Dict[str, Any]] = None,
        ghl_client: Optional[Any] = None,
    ) -> EnhancedAIResponse:
        """
        Generate enhanced AI response with competitive intelligence

        Args:
            user_message: User's latest message
            contact_info: Contact information from GHL
            context: Conversation context
            is_buyer: Whether the contact is a buyer
            tenant_config: Tenant-specific configuration
            ghl_client: GHL client for integrations

        Returns:
            EnhancedAIResponse with competitive intelligence
        """
        contact_name = contact_info.get("first_name", "there")
        lead_id = contact_info.get("id", "unknown")

        try:
            # Step 1: Analyze for competitor mentions
            logger.info(f"Analyzing message for competitor mentions: {user_message[:100]}...")

            competitive_analysis = await self.competitor_intelligence.analyze_conversation(
                message_text=user_message, conversation_history=context.get("conversation_history", [])
            )

            # Step 2: Generate base response using parent class
            base_response = await super().generate_response(
                user_message=user_message,
                contact_info=contact_info,
                context=context,
                is_buyer=is_buyer,
                tenant_config=tenant_config,
                ghl_client=ghl_client,
            )

            # Step 3: Apply competitive intelligence if needed
            competitive_response_applied = False
            alert_sent = False
            jorge_intervention_required = False
            recovery_strategies = []

            if competitive_analysis.has_competitor_risk:
                logger.info(
                    f"Competitor risk detected: {competitive_analysis.risk_level} - {len(competitive_analysis.mentions)} mentions"
                )

                # Determine lead profile for targeted response
                lead_profile = self._determine_lead_profile(context.get("extracted_preferences", {}))

                # Get competitive response strategy
                competitive_response = self.competitive_response_system.get_competitive_response(
                    risk_level=competitive_analysis.risk_level,
                    competitor_mentions=competitive_analysis.mentions,
                    lead_profile=lead_profile,
                    conversation_context={
                        "lead_name": contact_name,
                        "property_type": context.get("extracted_preferences", {}).get("property_type"),
                        "location": context.get("extracted_preferences", {}).get("location"),
                    },
                )

                # Apply competitive response if appropriate
                if competitive_analysis.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    # Override the base response with competitive positioning
                    base_response.message = competitive_response["message"]
                    competitive_response_applied = True
                    recovery_strategies = competitive_response.get("recovery_strategies", [])

                    # Add value proposition if provided
                    if competitive_response.get("value_proposition"):
                        value_prop = competitive_response["value_proposition"]
                        base_response.message += f"\n\n{value_prop['headline']}: {value_prop['description']}"

                    logger.info(f"Applied competitive response for {competitive_analysis.risk_level} risk situation")

                # Send alert to Jorge for medium+ risk situations
                if competitive_analysis.alert_required:
                    try:
                        alert = await self.competitive_alert_system.send_competitive_alert(
                            lead_id=lead_id,
                            lead_data=contact_info,
                            competitive_analysis=competitive_analysis,
                            conversation_context={
                                "message": user_message,
                                "conversation_history": context.get("conversation_history", []),
                            },
                        )
                        alert_sent = True
                        jorge_intervention_required = alert.human_intervention_required

                        logger.info(
                            f"Competitive alert sent: {alert.alert_id} - Channels: {[ch.value for ch in alert.channels_sent]}"
                        )

                    except Exception as e:
                        logger.error(f"Failed to send competitive alert: {e}")

                # Add Rancho Cucamonga market intelligence for local positioning
                if any(
                    mention.competitor_name in ["keller_williams", "remax", "coldwell_banker"]
                    for mention in competitive_analysis.mentions
                ):
                    market_advantage = self._get_rancho_cucamonga_market_advantage(competitive_analysis.mentions)
                    if market_advantage:
                        base_response.message += f"\n\n{market_advantage}"

            # Step 4: Track competitive situation in context
            await self._update_competitive_context(
                contact_id=lead_id,
                competitive_analysis=competitive_analysis,
                context=context,
                tenant_config=tenant_config,
            )

            # Step 5: Create enhanced response
            enhanced_response = EnhancedAIResponse(
                message=base_response.message,
                extracted_data=base_response.extracted_data,
                reasoning=base_response.reasoning,
                lead_score=base_response.lead_score,
                predictive_score=base_response.predictive_score,
                competitive_analysis=competitive_analysis,
                competitive_response_applied=competitive_response_applied,
                alert_sent=alert_sent,
                jorge_intervention_required=jorge_intervention_required,
                recovery_strategies=recovery_strategies,
            )

            logger.info(
                f"Enhanced response generated - Competitive risk: {competitive_analysis.risk_level if competitive_analysis.has_competitor_risk else 'None'}"
            )

            return enhanced_response

        except Exception as e:
            logger.error(f"Error in enhanced response generation: {e}")

            # Fallback to base response with error tracking
            base_response = await super().generate_response(
                user_message=user_message,
                contact_info=contact_info,
                context=context,
                is_buyer=is_buyer,
                tenant_config=tenant_config,
                ghl_client=ghl_client,
            )

            return EnhancedAIResponse(
                message=base_response.message,
                extracted_data=base_response.extracted_data,
                reasoning=f"{base_response.reasoning} (Competitive analysis failed: {str(e)})",
                lead_score=base_response.lead_score,
                predictive_score=base_response.predictive_score,
                competitive_analysis=None,
                competitive_response_applied=False,
                alert_sent=False,
                jorge_intervention_required=False,
                recovery_strategies=[],
            )

    def _determine_lead_profile(self, extracted_preferences: Dict[str, Any]) -> Optional[LeadProfile]:
        """Determine lead profile based on extracted preferences"""

        # Check for investor indicators
        if any(
            keyword in str(extracted_preferences).lower() for keyword in ["investment", "rental", "cash flow", "roi"]
        ):
            return LeadProfile.INVESTOR

        # Check for tech relocation indicators
        if any(
            keyword in str(extracted_preferences).lower() for keyword in ["apple", "tech", "relocating", "moving from"]
        ):
            return LeadProfile.RELOCATING

        # Check for luxury indicators
        budget = extracted_preferences.get("budget", 0)
        if budget > 750000:
            return LeadProfile.LUXURY_BUYER

        # Check for first-time buyer indicators
        financing = extracted_preferences.get("financing", "").lower()
        if "first time" in financing or budget < 400000:
            return LeadProfile.FIRST_TIME_BUYER

        # Check for seller indicators
        pathway = extracted_preferences.get("pathway")
        if pathway in ["listing", "wholesale"]:
            return LeadProfile.SELLER

        return None

    def _get_rancho_cucamonga_market_advantage(self, competitor_mentions: List[CompetitorMention]) -> Optional[str]:
        """Get Rancho Cucamonga market advantage messaging based on competitors mentioned"""

        for mention in competitor_mentions:
            if mention.competitor_name:
                competitor_insights = self.rancho_cucamonga_market_intelligence.get_competitor_positioning(
                    mention.competitor_name
                )
                if competitor_insights:
                    advantages = competitor_insights["positioning_strategy"]["jorge_advantages"]
                    if advantages:
                        return f"Here's what makes me different in Rancho Cucamonga: {advantages[0]}"

        # Generic Rancho Cucamonga advantage
        market_insights = self.rancho_cucamonga_market_intelligence.get_market_timing_insights()
        urgency_factors = market_insights.get("urgency_factors", [])
        if urgency_factors:
            return f"Rancho Cucamonga market insight: {urgency_factors[0]}"

        return None

    async def _update_competitive_context(
        self,
        contact_id: str,
        competitive_analysis: CompetitiveAnalysis,
        context: Dict[str, Any],
        tenant_config: Optional[Dict[str, Any]] = None,
    ):
        """Update conversation context with competitive intelligence"""

        if not competitive_analysis.has_competitor_risk:
            return

        # Add competitive data to context
        competitive_context = context.get("competitive_intelligence", {})

        # Track competitive mentions over time
        competitive_context["risk_history"] = competitive_context.get("risk_history", [])
        competitive_context["risk_history"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "risk_level": competitive_analysis.risk_level.value,
                "confidence_score": competitive_analysis.confidence_score,
                "mentions_count": len(competitive_analysis.mentions),
                "alert_sent": competitive_analysis.alert_required,
            }
        )

        # Keep only last 10 risk assessments
        competitive_context["risk_history"] = competitive_context["risk_history"][-10:]

        # Update current risk status
        competitive_context["current_risk_level"] = competitive_analysis.risk_level.value
        competitive_context["last_competitor_mention"] = datetime.now().isoformat()

        # Track competitor names mentioned
        competitors_mentioned = competitive_context.get("competitors_mentioned", set())
        for mention in competitive_analysis.mentions:
            if mention.competitor_name:
                competitors_mentioned.add(mention.competitor_name)
        competitive_context["competitors_mentioned"] = list(competitors_mentioned)

        # Store recovery strategies attempted
        if competitive_analysis.recovery_strategies:
            competitive_context["recovery_strategies_suggested"] = competitive_analysis.recovery_strategies

        # Update context
        context["competitive_intelligence"] = competitive_context

        # Save updated context
        location_id = tenant_config.get("location_id") if tenant_config else None
        await self.memory_service.save_context(contact_id, context, location_id=location_id)

    async def get_competitive_summary(self, contact_id: str, location_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive competitive summary for a lead"""

        context = await self.get_context(contact_id, location_id)
        competitive_context = context.get("competitive_intelligence", {})

        if not competitive_context:
            return {"has_competitive_risk": False, "summary": "No competitive risk detected"}

        risk_history = competitive_context.get("risk_history", [])
        current_risk = competitive_context.get("current_risk_level", "low")
        competitors = competitive_context.get("competitors_mentioned", [])

        # Calculate risk trend
        risk_trend = "stable"
        if len(risk_history) >= 2:
            recent_risks = [r["risk_level"] for r in risk_history[-3:]]
            if "critical" in recent_risks or "high" in recent_risks:
                risk_trend = "escalating"
            elif all(r == "low" for r in recent_risks):
                risk_trend = "decreasing"

        summary = {
            "has_competitive_risk": current_risk != "low",
            "current_risk_level": current_risk,
            "risk_trend": risk_trend,
            "competitors_mentioned": competitors,
            "total_risk_events": len(risk_history),
            "last_competitive_mention": competitive_context.get("last_competitor_mention"),
            "recovery_strategies_suggested": competitive_context.get("recovery_strategies_suggested", []),
            "summary": f"Risk Level: {current_risk.title()} | Trend: {risk_trend.title()} | Competitors: {', '.join(competitors) if competitors else 'None'}",
        }

        return summary

    async def mark_competitive_situation_resolved(
        self, contact_id: str, resolution_notes: str, location_id: Optional[str] = None
    ):
        """Mark competitive situation as resolved"""

        try:
            # Update context
            context = await self.get_context(contact_id, location_id)
            competitive_context = context.get("competitive_intelligence", {})

            competitive_context["resolved_at"] = datetime.now().isoformat()
            competitive_context["resolution_notes"] = resolution_notes
            competitive_context["current_risk_level"] = "resolved"

            context["competitive_intelligence"] = competitive_context
            await self.memory_service.save_context(contact_id, context, location_id=location_id)

            # Find and resolve any active alerts for this lead
            active_alerts = await self.competitive_alert_system.get_active_alerts()
            for alert_data in active_alerts:
                if alert_data.get("lead_id") == contact_id:
                    await self.competitive_alert_system.mark_alert_resolved(
                        alert_id=alert_data["alert_id"], resolution_notes=resolution_notes
                    )

            logger.info(f"Competitive situation resolved for {contact_id}: {resolution_notes}")

        except Exception as e:
            logger.error(f"Error resolving competitive situation: {e}")

    async def get_recovery_recommendations(self, contact_id: str, location_id: Optional[str] = None) -> List[str]:
        """Get competitive recovery recommendations for a lead"""

        try:
            context = await self.get_context(contact_id, location_id)
            competitive_context = context.get("competitive_intelligence", {})

            if not competitive_context or competitive_context.get("current_risk_level") == "low":
                return ["No competitive recovery needed - lead is not at risk"]

            current_risk = competitive_context.get("current_risk_level", "low")
            competitors = competitive_context.get("competitors_mentioned", [])

            # Get recommendations based on risk level and competitors
            recommendations = []

            if current_risk == "critical":
                recommendations = [
                    "Immediate Jorge intervention required",
                    "Position as backup resource for future opportunities",
                    "Add to long-term nurture campaign",
                    "Send quarterly Rancho Cucamonga market updates",
                ]
            elif current_risk == "high":
                recommendations = [
                    "Provide immediate value (market analysis, property insights)",
                    "Offer complimentary second opinion service",
                    "Share relevant success stories and testimonials",
                    "Schedule follow-up for market insights",
                ]
            elif current_risk == "medium":
                recommendations = [
                    "Demonstrate unique technology advantages",
                    "Highlight Jorge's Rancho Cucamonga expertise",
                    "Create urgency with market timing insights",
                    "Offer specialized services (investor analysis, tech relocation)",
                ]

            # Add competitor-specific strategies
            for competitor in competitors:
                competitor_insights = self.rancho_cucamonga_market_intelligence.get_competitor_positioning(competitor)
                if competitor_insights:
                    advantages = competitor_insights["positioning_strategy"]["jorge_advantages"]
                    recommendations.extend([f"Emphasize: {advantage}" for advantage in advantages[:2]])

            return recommendations

        except Exception as e:
            logger.error(f"Error getting recovery recommendations: {e}")
            return ["Error retrieving recommendations - manual review needed"]


# Factory function to get the enhanced conversation manager
def get_enhanced_conversation_manager() -> EnhancedConversationManager:
    """Get enhanced conversation manager with competitive intelligence"""
    return EnhancedConversationManager()
