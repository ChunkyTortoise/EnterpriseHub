"""Buyer journey stage tracking service."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class JourneyStage(str, Enum):
    """Stages of the buyer purchase funnel."""
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    PRE_APPROVAL = "pre_approval"
    ACTIVE_SEARCH = "active_search"
    UNDER_CONTRACT = "under_contract"
    CLOSED = "closed"


# GHL tags for each stage
STAGE_TAGS = {
    JourneyStage.AWARENESS: "Stage-Awareness",
    JourneyStage.CONSIDERATION: "Stage-Consideration",
    JourneyStage.PRE_APPROVAL: "Stage-Pre-Approval",
    JourneyStage.ACTIVE_SEARCH: "Stage-Active-Search",
    JourneyStage.UNDER_CONTRACT: "Stage-Under-Contract",
    JourneyStage.CLOSED: "Stage-Closed",
}

# Recommended actions per stage
STAGE_ACTIONS = {
    JourneyStage.AWARENESS: [
        "Send market education content",
        "Share neighborhood guides",
        "Invite to open houses",
    ],
    JourneyStage.CONSIDERATION: [
        "Discuss budget and financing options",
        "Share property search criteria questionnaire",
        "Introduce preferred lenders",
    ],
    JourneyStage.PRE_APPROVAL: [
        "Connect with lender",
        "Follow up on pre-approval progress",
        "Begin preliminary property search",
    ],
    JourneyStage.ACTIVE_SEARCH: [
        "Schedule property tours",
        "Send new listing alerts",
        "Prepare offer strategy",
    ],
    JourneyStage.UNDER_CONTRACT: [
        "Coordinate inspection",
        "Monitor appraisal process",
        "Prepare for closing",
    ],
    JourneyStage.CLOSED: [
        "Send closing congratulations",
        "Request referrals and reviews",
        "Schedule 30-day check-in",
    ],
}


@dataclass
class StageTransition:
    """Records a stage transition."""
    buyer_id: str
    from_stage: str
    to_stage: str
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""


class BuyerJourneyTracker:
    """Tracks buyer progression through the purchase funnel."""

    # Stage ordering for progression validation
    STAGE_ORDER = list(JourneyStage)

    def __init__(self, ghl_client=None):
        self.ghl_client = ghl_client
        self._transitions: List[StageTransition] = []
        self._current_stages: Dict[str, JourneyStage] = {}

    def determine_stage(self, buyer_state: Dict) -> JourneyStage:
        """Determine the buyer's current journey stage from their state data."""
        # Check for terminal stages first (from CRM flags)
        if buyer_state.get("transaction_closed"):
            return JourneyStage.CLOSED
        if buyer_state.get("offer_accepted"):
            return JourneyStage.UNDER_CONTRACT

        financing_status = buyer_state.get("financing_status", "unknown")
        financial_readiness = buyer_state.get("financial_readiness_score", 0)
        budget_clarity = buyer_state.get("budget_clarity", 0)
        preference_clarity = buyer_state.get("preference_clarity", 0)
        urgency = buyer_state.get("urgency_score", 0)

        # Active search: pre-approved and actively looking
        if financing_status in ("pre_approved", "cash") and urgency > 50:
            return JourneyStage.ACTIVE_SEARCH

        # Pre-approval: working on financing
        if financing_status in ("needs_approval", "in_progress") or (
            financial_readiness >= 40 and financing_status != "pre_approved"
        ):
            return JourneyStage.PRE_APPROVAL

        # Consideration: has budget, comparing options
        if budget_clarity > 40 or preference_clarity > 30:
            return JourneyStage.CONSIDERATION

        # Default: awareness
        return JourneyStage.AWARENESS

    def get_stage_actions(self, stage: JourneyStage) -> List[str]:
        """Get recommended actions for a journey stage."""
        return STAGE_ACTIONS.get(stage, [])

    async def track_progression(
        self, buyer_id: str, from_stage: str, to_stage: str, reason: str = ""
    ) -> StageTransition:
        """Record a stage transition and update CRM tags."""
        transition = StageTransition(
            buyer_id=buyer_id,
            from_stage=from_stage,
            to_stage=to_stage,
            reason=reason,
        )
        self._transitions.append(transition)
        self._current_stages[buyer_id] = JourneyStage(to_stage)

        # Update GHL tags
        if self.ghl_client:
            try:
                # Remove old stage tag
                old_tag = STAGE_TAGS.get(JourneyStage(from_stage))
                if old_tag:
                    await self.ghl_client.remove_tags(buyer_id, [old_tag])

                # Add new stage tag
                new_tag = STAGE_TAGS.get(JourneyStage(to_stage))
                if new_tag:
                    await self.ghl_client.add_tags(buyer_id, [new_tag])
            except Exception as e:
                logger.warning("Failed to update stage tags: %s", e)

        logger.info(
            "Buyer %s progressed: %s → %s (reason: %s)",
            buyer_id, from_stage, to_stage, reason or "auto",
        )
        return transition

    def get_buyer_stage(self, buyer_id: str) -> Optional[JourneyStage]:
        """Get the current stage for a buyer."""
        return self._current_stages.get(buyer_id)

    def get_transition_history(self, buyer_id: str) -> List[StageTransition]:
        """Get all transitions for a buyer."""
        return [t for t in self._transitions if t.buyer_id == buyer_id]
