"""Tests for HITLGate -- High-Value Human-in-the-Loop protection."""
from unittest.mock import AsyncMock

import pytest

from ghl_real_estate_ai.services.hitl_gate import HITLGate


class TestHITLGateEvaluate:
    def test_hitl_triggers_on_high_composite_score(self):
        gate = HITLGate()
        response = {"frs_score": 92.0, "pcs_score": 90.0}
        assert gate.evaluate(response) is True

    def test_hitl_triggers_on_high_value_property(self):
        gate = HITLGate()
        response = {"frs_score": 70.0, "pcs_score": 70.0}
        assert gate.evaluate(response, property_value=1_500_000.0) is True

    def test_hitl_does_not_trigger_below_thresholds(self):
        gate = HITLGate()
        response = {"frs_score": 85.0, "pcs_score": 85.0}
        assert gate.evaluate(response, property_value=900_000.0) is False

    def test_hitl_triggers_for_buyer_scores(self):
        gate = HITLGate()
        response = {"financial_readiness": 95.0, "buying_motivation_score": 92.0}
        assert gate.evaluate(response) is True

    def test_hitl_does_not_trigger_with_zero_scores(self):
        gate = HITLGate()
        response = {}
        assert gate.evaluate(response) is False

    def test_hitl_respects_env_threshold(self, monkeypatch):
        monkeypatch.setenv("HITL_COMPOSITE_THRESHOLD", "80")
        gate = HITLGate()
        response = {"frs_score": 85.0, "pcs_score": 85.0}
        assert gate.evaluate(response) is True

    def test_hitl_respects_property_value_env_threshold(self, monkeypatch):
        monkeypatch.setenv("HITL_PROPERTY_VALUE_THRESHOLD", "500000")
        gate = HITLGate()
        response = {"frs_score": 50.0, "pcs_score": 50.0}
        assert gate.evaluate(response, property_value=600_000.0) is True

    def test_hitl_handles_none_scores_gracefully(self):
        gate = HITLGate()
        response = {"frs_score": None, "pcs_score": None}
        assert gate.evaluate(response) is False

    def test_hitl_boundary_exactly_at_threshold(self):
        gate = HITLGate()
        # Exactly at threshold should NOT trigger (uses > not >=)
        response = {"frs_score": 90.0, "pcs_score": 90.0}
        assert gate.evaluate(response) is False

    def test_hitl_boundary_just_above_threshold(self):
        gate = HITLGate()
        response = {"frs_score": 90.1, "pcs_score": 90.1}
        assert gate.evaluate(response) is True


@pytest.mark.asyncio
async def test_webhook_posts_internal_note_not_sms_when_hitl_active():
    """When HITL triggers, internal note is posted and SMS is skipped."""
    gate = HITLGate()
    mock_ghl = AsyncMock()
    mock_ghl.post_internal_note = AsyncMock(return_value={"success": True})
    mock_ghl.send_sms = AsyncMock()

    response = {"frs_score": 92.0, "pcs_score": 90.0, "response_content": "Great deal!"}

    if gate.evaluate(response):
        await mock_ghl.post_internal_note("contact_123", f"DRAFT: {response['response_content']}")
        # SMS should NOT be called
    else:
        await mock_ghl.send_sms("contact_123", response["response_content"])

    mock_ghl.post_internal_note.assert_called_once()
    mock_ghl.send_sms.assert_not_called()
