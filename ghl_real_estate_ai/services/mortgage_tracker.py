"""Mortgage pre-qualification tracking service."""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MortgageReadiness:
    """Assessment of a buyer's mortgage readiness."""
    status: str  # "pre_approved", "pre_qualified", "needs_prequalification", "unknown"
    estimated_buying_power: Optional[float] = None
    recommended_action: str = ""
    lender_suggestions: List[str] = field(default_factory=list)


@dataclass
class Referral:
    """A lender referral record."""
    referral_id: str
    buyer_id: str
    lender: str
    status: str = "pending"  # pending, contacted, approved, declined
    created_at: datetime = field(default_factory=datetime.now)


class MortgageTracker:
    """Tracks mortgage pre-qualification status and referrals."""

    # Trusted local lenders for Rancho Cucamonga
    DEFAULT_LENDERS = [
        "Inland Empire Mortgage",
        "Pacific Premier Lending",
        "SoCal Home Loans",
    ]

    # Conversation templates
    TEMPLATES = {
        "needs_prequalification": (
            "Getting pre-approved is a great first step! It shows sellers "
            "you're serious. Want me to connect you with a trusted lender "
            "in the Rancho Cucamonga area?"
        ),
        "in_progress": (
            "Great that you're working on pre-approval! Have you heard "
            "back from your lender yet?"
        ),
        "pre_approved": (
            "Awesome, you're pre-approved! That puts you in a strong "
            "position. Let's find your perfect home."
        ),
    }

    def __init__(self, ghl_client=None):
        self.ghl_client = ghl_client
        self._referrals: Dict[str, Referral] = {}

    async def assess_readiness(self, buyer_data: Dict) -> MortgageReadiness:
        """Assess mortgage readiness from buyer conversation data."""
        financing_status = buyer_data.get("financing_status", "unknown")
        financial_readiness = buyer_data.get("financial_readiness_score", 0)
        budget_max = buyer_data.get("budget_max", 0)

        if financing_status == "pre_approved" or financial_readiness >= 75:
            buying_power = budget_max if budget_max > 0 else None
            return MortgageReadiness(
                status="pre_approved",
                estimated_buying_power=buying_power,
                recommended_action="Start property search",
                lender_suggestions=[],
            )

        if financing_status == "pre_qualified" or financial_readiness >= 50:
            return MortgageReadiness(
                status="pre_qualified",
                estimated_buying_power=budget_max if budget_max > 0 else None,
                recommended_action="Complete full pre-approval",
                lender_suggestions=self.DEFAULT_LENDERS[:2],
            )

        if financing_status == "cash":
            return MortgageReadiness(
                status="pre_approved",
                estimated_buying_power=budget_max,
                recommended_action="Start property search — cash buyer",
                lender_suggestions=[],
            )

        # Estimate buying power from budget if available
        estimated_power = None
        if budget_max > 0:
            estimated_power = budget_max

        return MortgageReadiness(
            status="needs_prequalification",
            estimated_buying_power=estimated_power,
            recommended_action="Get pre-approved with a lender",
            lender_suggestions=self.DEFAULT_LENDERS,
        )

    async def create_prequalification_referral(
        self, buyer_id: str, lender: str
    ) -> Referral:
        """Create a lender referral for a buyer."""
        referral_id = f"ref-{uuid.uuid4().hex[:8]}"
        referral = Referral(
            referral_id=referral_id,
            buyer_id=buyer_id,
            lender=lender,
        )
        self._referrals[referral_id] = referral

        # Update CRM
        if self.ghl_client:
            try:
                await self.ghl_client.add_tags(buyer_id, ["Pre-Qualification-Sent"])
            except Exception as e:
                logger.warning("Failed to update CRM tag: %s", e)

        logger.info("Referral %s created for buyer %s → %s", referral_id, buyer_id, lender)
        return referral

    async def check_status(self, referral_id: str) -> Optional[str]:
        """Check status of a referral."""
        referral = self._referrals.get(referral_id)
        if not referral:
            return None
        return referral.status

    def get_lender_recommendation(self, buyer_profile: Dict) -> str:
        """Recommend a lender based on buyer profile."""
        financing = buyer_profile.get("financing_status", "unknown")
        budget = buyer_profile.get("budget_max", 0)

        if financing == "cash":
            return ""  # Cash buyers don't need lenders

        # Simple recommendation logic
        if budget and budget >= 1000000:
            return self.DEFAULT_LENDERS[1]  # Luxury lender
        return self.DEFAULT_LENDERS[0]  # Default lender

    def get_conversation_template(self, status: str) -> str:
        """Get appropriate conversation template for mortgage status."""
        return self.TEMPLATES.get(status, self.TEMPLATES["needs_prequalification"])
