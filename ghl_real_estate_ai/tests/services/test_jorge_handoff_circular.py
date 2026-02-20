"""
Tests for Jorge Handoff Service Circular Prevention.

Validates circular handoff detection, rate limiting, and conflict resolution.
"""

import time

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    HandoffDecision,
    JorgeHandoffService,
)
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker


@pytest.fixture(autouse=True)
def reset_handoff_service():
    """Reset handoff service state before each test."""
    JorgeHandoffService._handoff_history = {}
    JorgeHandoffService._handoff_outcomes = {}
    JorgeHandoffService._active_handoffs = {}
    JorgeHandoffService.reset_analytics()
    PerformanceTracker.reset()
    yield
    JorgeHandoffService._handoff_history = {}
    JorgeHandoffService._handoff_outcomes = {}
    JorgeHandoffService._active_handoffs = {}
    JorgeHandoffService.reset_analytics()
    PerformanceTracker.reset()


@pytest.fixture
def handoff_service():
    """Create a fresh JorgeHandoffService instance."""
    return JorgeHandoffService()


class TestJorgeHandoffCircularPrevention:
    """Test suite for handoff circular prevention."""

    @pytest.mark.asyncio
    async def test_evaluate_handoff_success(self, handoff_service):
        """Test successful handoff evaluation."""
        intent_signals = {
            "buyer_intent_score": 0.85,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": ["looking to buy"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="contact_123",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is not None
        assert decision.source_bot == "lead"
        assert decision.target_bot == "buyer"
        assert decision.confidence == 0.85

    @pytest.mark.asyncio
    async def test_circular_handoff_prevention(self, handoff_service):
        """Test that circular handoffs are prevented."""
        contact_id = "contact_123"

        intent_signals = {
            "buyer_intent_score": 0.85,
            "seller_intent_score": 0.1,
        }
        decision1 = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[],
            intent_signals=intent_signals,
        )
        assert decision1 is not None

        result1 = await handoff_service.execute_handoff(decision1, contact_id)
        assert result1 is not None

        decision2 = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[],
            intent_signals=intent_signals,
        )
        assert decision2 is None

    @pytest.mark.asyncio
    async def test_rate_limit_hourly(self, handoff_service):
        """Test hourly rate limiting (3 handoffs/hour)."""
        contact_id = "contact_123"

        bot_pairs = [
            ("lead", "buyer"),
            ("buyer", "seller"),
            ("lead", "seller"),
        ]

        for source, target in bot_pairs:
            decision = HandoffDecision(
                source_bot=source,
                target_bot=target,
                reason="intent_detected",
                confidence=0.8,
            )
            result = await handoff_service.execute_handoff(decision, contact_id)
            assert result is not None

        decision4 = HandoffDecision(
            source_bot="seller",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.9,
        )
        result = await handoff_service.execute_handoff(decision4, contact_id)
        assert result is not None
        assert len(result) > 0
        assert result[0]["handoff_executed"] is False
        assert "rate limit" in result[0]["reason"].lower()

    @pytest.mark.asyncio
    async def test_rate_limit_daily(self, handoff_service):
        """Test daily rate limiting (10 handoffs/day)."""
        contact_id = "contact_123"

        bot_pairs = [
            ("lead", "buyer"),
            ("buyer", "seller"),
            ("lead", "seller"),
            ("seller", "buyer"),
            ("buyer", "lead"),
            ("lead", "buyer"),
            ("seller", "lead"),
            ("buyer", "seller"),
            ("seller", "buyer"),
            ("lead", "seller"),
        ]

        for i, (source, target) in enumerate(bot_pairs):
            decision = HandoffDecision(
                source_bot=source,
                target_bot=target,
                reason=f"intent_detected_{i}",
                confidence=0.8,
            )
            result = await handoff_service.execute_handoff(decision, contact_id)
            assert result is not None

        decision11 = HandoffDecision(
            source_bot="buyer",
            target_bot="lead",
            reason="buyer_intent_detected",
            confidence=0.9,
        )
        result = await handoff_service.execute_handoff(decision11, contact_id)
        assert result is not None
        assert len(result) > 0
        assert result[0]["handoff_executed"] is False
        assert "rate limit" in result[0]["reason"].lower()

    @pytest.mark.asyncio
    async def test_contact_level_locking(self, handoff_service):
        """Test contact-level locking prevents concurrent handoffs."""
        contact_id = "contact_123"

        handoff_service._acquire_handoff_lock(contact_id)

        decision = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.8,
        )
        result = await handoff_service.execute_handoff(decision, contact_id)
        assert result is not None
        assert len(result) > 0
        assert result[0]["handoff_executed"] is False
        assert "concurrent" in result[0]["reason"].lower()

    @pytest.mark.asyncio
    async def test_handoff_conflict_resolution(self, handoff_service):
        """Test that handoff conflicts are resolved properly."""
        contact_id = "contact_123"

        decision1 = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.8,
        )
        result1 = await handoff_service.execute_handoff(decision1, contact_id)
        assert result1 is not None
        assert len(result1) > 0

        handoff_service._release_handoff_lock(contact_id)

        decision2 = HandoffDecision(
            source_bot="buyer",
            target_bot="seller",
            reason="seller_intent_detected",
            confidence=0.7,
        )
        result2 = await handoff_service.execute_handoff(decision2, contact_id)
        assert result2 is not None
        assert len(result2) > 0