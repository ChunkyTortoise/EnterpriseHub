"""Tests for Buyer Journey Stage Tracking Service.

Covers stage determination from buyer state, progression tracking,
GHL tag management, and recommended actions per stage.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ghl_real_estate_ai.services.buyer_journey import (
    STAGE_ACTIONS,
    STAGE_TAGS,
    BuyerJourneyTracker,
    JourneyStage,
)


class TestBuyerJourneyStageDetection:
    """Tests for automatic stage determination from buyer state."""

    def test_awareness_stage_low_scores(self):
        """Low financial/budget scores map to AWARENESS."""
        tracker = BuyerJourneyTracker()
        state = {
            "financial_readiness_score": 10,
            "budget_clarity": 5,
            "preference_clarity": 10,
            "urgency_score": 0,
            "financing_status": "unknown",
        }
        assert tracker.determine_stage(state) == JourneyStage.AWARENESS

    def test_consideration_stage_has_budget(self):
        """Budget clarity > 40 maps to CONSIDERATION."""
        tracker = BuyerJourneyTracker()
        state = {
            "financial_readiness_score": 20,
            "budget_clarity": 50,
            "preference_clarity": 20,
            "urgency_score": 10,
            "financing_status": "unknown",
        }
        assert tracker.determine_stage(state) == JourneyStage.CONSIDERATION

    def test_active_search_pre_approved(self):
        """Pre-approved financing with urgency > 50 maps to ACTIVE_SEARCH."""
        tracker = BuyerJourneyTracker()
        state = {
            "financial_readiness_score": 80,
            "budget_clarity": 90,
            "preference_clarity": 70,
            "urgency_score": 75,
            "financing_status": "pre_approved",
        }
        assert tracker.determine_stage(state) == JourneyStage.ACTIVE_SEARCH


class TestBuyerJourneyProgression:
    """Tests for stage transition tracking and CRM integration."""

    @pytest.mark.asyncio
    async def test_stage_progression_tracking(self):
        """track_progression stores transition and updates current stage."""
        tracker = BuyerJourneyTracker()
        transition = await tracker.track_progression(
            buyer_id="buyer-001",
            from_stage="awareness",
            to_stage="consideration",
            reason="budget discussed",
        )

        assert transition.buyer_id == "buyer-001"
        assert transition.from_stage == "awareness"
        assert transition.to_stage == "consideration"
        assert transition.reason == "budget discussed"
        assert tracker.get_buyer_stage("buyer-001") == JourneyStage.CONSIDERATION

        history = tracker.get_transition_history("buyer-001")
        assert len(history) == 1
        assert history[0] is transition

    @pytest.mark.asyncio
    async def test_ghl_tag_updated_on_stage_change(self):
        """GHL client add_tags and remove_tags are called on progression."""
        mock_ghl = AsyncMock()
        tracker = BuyerJourneyTracker(ghl_client=mock_ghl)

        await tracker.track_progression(
            buyer_id="buyer-002",
            from_stage="consideration",
            to_stage="pre_approval",
        )

        mock_ghl.remove_tags.assert_called_once_with(
            "buyer-002", ["Stage-Consideration"]
        )
        mock_ghl.add_tags.assert_called_once_with(
            "buyer-002", ["Stage-Pre-Approval"]
        )


class TestBuyerJourneyActions:
    """Tests for stage-specific recommended actions."""

    def test_stage_actions_appropriate(self):
        """Each journey stage returns a non-empty list of actions."""
        tracker = BuyerJourneyTracker()
        for stage in JourneyStage:
            actions = tracker.get_stage_actions(stage)
            assert len(actions) > 0, f"Stage {stage.value} has no actions"
            assert all(
                isinstance(a, str) for a in actions
            ), f"Stage {stage.value} has non-string actions"
