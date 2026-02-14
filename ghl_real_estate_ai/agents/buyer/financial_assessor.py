"""
Financial assessment module for buyer bot.
Handles financial readiness scoring and affordability calculations.
"""

from typing import Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.jorge_config import BuyerBudgetConfig
from ghl_real_estate_ai.agents.buyer.utils import (
    extract_budget_range,
    assess_financial_from_conversation,
)
from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState

logger = get_logger(__name__)


class FinancialAssessor:
    """Handles financial readiness assessment and affordability calculations."""

    def __init__(self, budget_config: Optional[BuyerBudgetConfig] = None):
        self.budget_config = budget_config or BuyerBudgetConfig.from_environment()

    async def assess_financial_readiness(
        self,
        state: BuyerBotState,
        skip_qualification: bool = False
    ) -> Dict:
        """Assess buyer's financial preparedness using budget_config thresholds."""
        try:
            # Skip financial assessment if handoff context already populated state
            if skip_qualification and state.get("handoff_context_used"):
                logger.info(f"Skipping financial assessment for {state.get('buyer_id')} - using handoff context")
                # Return existing state values from handoff context
                return {
                    "budget_range": state.get("budget_range"),
                    "financing_status": state.get("financing_status", "pre_qualified_handoff"),
                    "financial_readiness_score": state.get("financial_readiness_score", 70),
                    "current_qualification_step": "property_matching",
                }

            profile = state.get("intent_profile", {})
            budget_range = state.get("budget_range")
            state.get("intelligence_context")

            # Check budget ranges first
            if not budget_range:
                # Try to extract from conversation
                extracted = await extract_budget_range(
                    state.get("conversation_history", []),
                    self.budget_config
                )
                if extracted:
                    budget_range = extracted

            # Use profile for additional signals
            financing_status = profile.get("financing_status", "unknown") if isinstance(profile, dict) else "unknown"
            urgency_score = state.get("urgency_score", 25)

            # Apply thresholds from budget_config
            if financing_status == "pre_approved":
                score = self.budget_config.FINANCING_PRE_APPROVED_THRESHOLD
            elif financing_status == "cash":
                score = self.budget_config.FINANCING_CASH_BUDGET_THRESHOLD
            elif financing_status == "needs_approval":
                score = self.budget_config.FINANCING_NEEDS_APPROVAL_THRESHOLD
            else:
                # Default based on budget clarity and urgency
                score = min(100, urgency_score + (50 if budget_range else 0))

            return {
                "budget_range": budget_range,
                "financing_status": financing_status,
                "financial_readiness_score": min(100, score),
                "current_qualification_step": "property",
            }
        except Exception as e:
            logger.error(f"Error assessing financial readiness for {state.get('buyer_id')}: {str(e)}")
            return {
                "budget_range": None,
                "financing_status": "assessment_error",
                "financial_readiness_score": 25,
                "current_qualification_step": "error",
            }

    async def calculate_affordability(self, state: BuyerBotState) -> Dict:
        """Calculate affordability analysis from buyer's budget range."""
        budget_range = state.get("budget_range")
        if not budget_range:
            return {}

        try:
            max_price = budget_range.get("max", 0)
            if max_price <= 0:
                return {}

            # Standard mortgage calculations (Rancho Cucamonga rates)
            down_payment_pct = 0.20
            interest_rate = 0.0685  # Current 30-yr fixed rate
            loan_term_years = 30
            property_tax_rate = 0.0115  # California / San Bernardino County
            insurance_annual = 1800  # Average annual homeowner's insurance

            down_payment = max_price * down_payment_pct
            loan_amount = max_price - down_payment

            # Monthly mortgage (standard amortization formula)
            monthly_rate = interest_rate / 12
            num_payments = loan_term_years * 12
            if monthly_rate > 0:
                monthly_mortgage = loan_amount * (
                    monthly_rate * (1 + monthly_rate) ** num_payments
                ) / ((1 + monthly_rate) ** num_payments - 1)
            else:
                monthly_mortgage = loan_amount / num_payments

            monthly_tax = (max_price * property_tax_rate) / 12
            monthly_insurance = insurance_annual / 12
            total_monthly = monthly_mortgage + monthly_tax + monthly_insurance

            affordability_analysis = {
                "max_price": max_price,
                "down_payment": round(down_payment, 2),
                "loan_amount": round(loan_amount, 2),
                "monthly_mortgage": round(monthly_mortgage, 2),
                "monthly_tax": round(monthly_tax, 2),
                "monthly_insurance": round(monthly_insurance, 2),
                "total_monthly_payment": round(total_monthly, 2),
            }

            mortgage_details = {
                "rate": interest_rate,
                "term_years": loan_term_years,
                "type": "30-year fixed",
                "down_payment_pct": down_payment_pct,
            }

            return {
                "affordability_analysis": affordability_analysis,
                "mortgage_details": mortgage_details,
                "max_monthly_payment": round(total_monthly, 2),
            }

        except Exception as e:
            logger.error(f"Error calculating affordability: {str(e)}")
            return {}

    async def fallback_financial_assessment(self, state: BuyerBotState) -> Dict:
        """
        Multi-tier fallback for financial assessment when primary service fails.

        Tier 1: Conversation history heuristics (pre-approval, budget mentions)
        Tier 2: Conservative default assessment
        Tier 3: Queue for manual review, continue conversation

        Never fails - always returns a reasonable assessment with confidence score.
        """
        buyer_id = state.get("buyer_id", "unknown")
        conversation_history = state.get("conversation_history", [])
        conversation_text = " ".join(
            msg.get("content", "").lower() for msg in conversation_history if msg.get("role") == "user"
        )

        # Tier 1: Conversation heuristics
        try:
            heuristic_result = assess_financial_from_conversation(conversation_text)
            if heuristic_result:
                logger.info(
                    f"Financial fallback Tier 1 (heuristic) used for buyer {buyer_id}",
                    extra={"fallback_tier": 1, "buyer_id": buyer_id},
                )
                return {
                    "financing_status": heuristic_result["financing_status"],
                    "budget_range": heuristic_result.get("budget_range"),
                    "financial_readiness_score": heuristic_result["confidence"],
                    "fallback_tier": 1,
                    "fallback_source": "conversation_heuristic",
                }
        except Exception as e:
            logger.warning(f"Tier 1 fallback failed for {buyer_id}: {e}")

        # Tier 2: Conservative default
        logger.info(
            f"Financial fallback Tier 2 (conservative default) used for buyer {buyer_id}",
            extra={"fallback_tier": 2, "buyer_id": buyer_id},
        )
        return {
            "financing_status": "assessment_pending",
            "budget_range": None,
            "financial_readiness_score": 25.0,
            "requires_manual_review": True,
            "fallback_tier": 2,
            "fallback_source": "conservative_default",
            "confidence": 0.3,
        }