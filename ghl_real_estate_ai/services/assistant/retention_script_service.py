"""
Retention Script Service - Market-aware retention and re-engagement scripts.

Extracted from ClaudeAssistant god class.
"""

from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.churn_prediction_engine import ChurnReason
from ghl_real_estate_ai.services.reengagement_engine import CLVEstimate, CLVTier

logger = get_logger(__name__)


class RetentionScriptService:
    """Generates market-aware retention and re-engagement scripts."""

    def __init__(self, market_context_service, market_id: Optional[str] = None):
        self.market_context_service = market_context_service
        self.market_id = market_id

    async def generate_market_aware_retention_script(
        self,
        lead_data: Dict[str, Any],
        risk_data: Optional[Dict[str, Any]] = None,
        market_id: Optional[str] = None,
        churn_reason: Optional[ChurnReason] = None,
    ) -> Dict[str, Any]:
        """
        Market-Aware Retention Script Generation.
        Generates personalized retention scripts with market-specific context and churn recovery intelligence.
        """
        try:
            market_context = await self.market_context_service.get_market_context(market_id)
            market_narrative = self.market_context_service.format_market_context_for_messaging(market_context)

            estimated_transaction = lead_data.get("estimated_property_value", 500000)
            clv_estimate = CLVEstimate(
                lead_id=lead_data.get("lead_id", "demo_lead"),
                estimated_transaction_value=estimated_transaction,
                commission_rate=0.03,
                probability_multiplier=lead_data.get("conversion_probability", 0.7),
            )

            if not churn_reason:
                last_interaction_days = lead_data.get("last_interaction_days", 7)
                if last_interaction_days > 14:
                    churn_reason = ChurnReason.TIMING
                else:
                    churn_reason = ChurnReason.COMMUNICATION

            recovery_template = self._get_recovery_template(clv_estimate.clv_tier, churn_reason)

            from ghl_real_estate_ai.services.claude_automation_engine import ClaudeAutomationEngine, ScriptType

            lead_name = lead_data.get("lead_name", "Client")
            lead_id = lead_data.get("lead_id", f"demo_{lead_name.lower().replace(' ', '_')}")
            risk_score = risk_data.get("risk_score", 0) if risk_data else lead_data.get("risk_score_14d", 0)

            automation_engine = ClaudeAutomationEngine()

            enhanced_context = {
                "churn_risk": risk_score,
                "market_context": market_narrative,
                "recovery_campaign_type": recovery_template["campaign_type"] if recovery_template else "nurture",
                "clv_tier": clv_estimate.clv_tier.value,
                "estimated_commission": f"${clv_estimate.estimated_clv:,.0f}",
                "market_neighborhoods": [n["name"] for n in market_context.get("top_neighborhoods", [])[:3]],
                "market_employers": [e["name"] for e in market_context.get("major_employers", [])[:3]],
                "churn_reason": churn_reason.value if churn_reason else "timing",
                **lead_data,
            }

            script_type = ScriptType.RE_ENGAGEMENT
            if risk_score > 80 and clv_estimate.clv_tier == CLVTier.HIGH_VALUE:
                channel = "sms"
            elif clv_estimate.clv_tier == CLVTier.HIGH_VALUE:
                channel = "sms"
            else:
                channel = "email"

            automated_script = await automation_engine.generate_personalized_script(
                script_type=script_type,
                lead_id=lead_id,
                channel=channel,
                context_override=enhanced_context,
                variants=2,
            )

            return {
                "lead_name": lead_name,
                "risk_score": risk_score,
                "market_context": market_context,
                "script": automated_script.primary_script,
                "strategy": f"Market-Aware {recovery_template['campaign_type'].replace('_', ' ').title()}"
                if recovery_template
                else "Market-Aware Re-engagement",
                "reasoning": f"{automated_script.personalization_notes}\n\nMarket Context: {market_narrative}",
                "channel_recommendation": automated_script.channel.upper(),
                "alternative_scripts": automated_script.alternative_scripts,
                "objection_responses": automated_script.objection_responses,
                "success_probability": automated_script.success_probability,
                "expected_response_rate": automated_script.expected_response_rate,
                "generation_time_ms": automated_script.generation_time_ms,
                "a_b_variants": automated_script.a_b_testing_variants,
                "clv_estimate": clv_estimate.estimated_clv,
                "clv_tier": clv_estimate.clv_tier.value,
                "recovery_template_used": recovery_template["campaign_type"] if recovery_template else None,
                "market_advantages": market_context.get("specializations", {}).get("unique_advantages", []),
            }

        except Exception as e:
            market_context = await self.market_context_service.get_market_context(market_id)
            market_name = market_context.get("market_name", "the local market")

            lead_name = lead_data.get("lead_name", "Client")
            risk_score = risk_data.get("risk_score", 0) if risk_data else lead_data.get("risk_score_14d", 0)

            last_interaction = lead_data.get("last_interaction_days", 5)

            reasoning = f"Lead {lead_name} has a {risk_score:.1f}% churn risk in the {market_name} market. "
            reasoning += f"After {last_interaction} days of inactivity, they need market-specific re-engagement highlighting current opportunities."

            if risk_score > 80:
                top_areas = market_context.get("top_neighborhoods", [])
                area_mention = f" in {top_areas[0]['name']}" if top_areas else ""

                script = f"Hi {lead_name}, it's Jorge. I just had an exclusive property become available{area_mention} that matches exactly what we discussed. Given the current {market_name} market conditions, this won't last long. Can we schedule a quick call today?"
                strategy = f"Urgent Market-Specific Intervention - {market_name}"
            else:
                market_type = market_context.get("market_type", "mixed")
                script = f"Hey {lead_name}, hope you're doing well! I wanted to share some interesting developments in the {market_name} {market_type} market that might interest you. The timing might be perfect for your move. Worth a quick chat?"
                strategy = f"Market-Aware Nurture - {market_name} Focus"

            return {
                "lead_name": lead_name,
                "risk_score": risk_score,
                "market_context": market_context,
                "script": script,
                "strategy": strategy,
                "reasoning": reasoning,
                "channel_recommendation": "SMS (High Response Probability)" if risk_score > 60 else "Email",
                "error": f"Claude service unavailable, using market-aware fallback: {str(e)}",
            }

    async def generate_retention_script(
        self, lead_data: Dict[str, Any], risk_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Legacy wrapper - delegates to market-aware retention script generation."""
        return await self.generate_market_aware_retention_script(
            lead_data=lead_data,
            risk_data=risk_data,
            market_id=self.market_id,
        )

    def _get_recovery_template(self, clv_tier: CLVTier, churn_reason: ChurnReason) -> Optional[Dict[str, Any]]:
        """Get appropriate recovery campaign template based on CLV and churn reason."""
        if clv_tier == CLVTier.HIGH_VALUE:
            if churn_reason in [ChurnReason.TIMING, ChurnReason.BUDGET]:
                return {"campaign_type": "win_back_aggressive"}
            else:
                return {"campaign_type": "value_proposition"}
        elif clv_tier == CLVTier.MEDIUM_VALUE:
            return {"campaign_type": "win_back_nurture"}
        else:
            return {"campaign_type": "market_comeback"}
