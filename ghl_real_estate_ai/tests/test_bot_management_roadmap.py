"""
Integration tests for ROADMAP-016 through ROADMAP-020:
Bot management qualification tracking, stall detection, effectiveness scoring,
handoff coordination, and coordination events.
"""

import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.api.routes.bot_management import (
    CoordinationEvent,
    EffectivenessScore,
    QuestionProgress,
    StallDetectionResult,
    _calculate_effectiveness_score,
    _detect_stall,
    _emit_coordination_event,
    _get_question_progress,
    _save_question_progress,
    _update_question_progress,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_cache():
    """Mock CacheService with dict-backed storage."""
    storage = {}

    cache = AsyncMock()

    async def mock_get(key):
        return storage.get(key)

    async def mock_set(key, value, ttl=300):
        storage[key] = value
        return True

    async def mock_delete(key):
        storage.pop(key, None)
        return True

    cache.get = AsyncMock(side_effect=mock_get)
    cache.set = AsyncMock(side_effect=mock_set)
    cache.delete = AsyncMock(side_effect=mock_delete)
    cache._storage = storage
    return cache


@pytest.fixture
def mock_event_publisher():
    """Mock EventPublisher."""
    publisher = AsyncMock()
    publisher.publish_event = AsyncMock()
    return publisher


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing."""
    return [
        {"role": "bot", "content": "Hey, Jorge here. What's your timeline for selling?"},
        {"role": "user", "content": "I'm thinking about selling my house in the next 30 days"},
        {"role": "bot", "content": "30 days? That's tight but doable. What's your price expectation?"},
        {"role": "user", "content": "I was hoping to get around $450,000 for it"},
        {"role": "bot", "content": "Let's talk about the condition. Any repairs needed?"},
        {"role": "user", "content": "The roof needs some work and the HVAC is old"},
    ]


@pytest.fixture
def stalled_conversation_history():
    """Conversation history with vague answers."""
    return [
        {"role": "bot", "content": "What's your timeline?"},
        {"role": "user", "content": "maybe"},
        {"role": "bot", "content": "Are you serious about selling?"},
        {"role": "user", "content": "i guess"},
        {"role": "bot", "content": "What price are you looking for?"},
        {"role": "user", "content": "not sure"},
    ]


@pytest.fixture
def repetitive_conversation_history():
    """Conversation history with repeated messages (non-vague, substantive)."""
    return [
        {"role": "bot", "content": "What's your timeline?"},
        {"role": "user", "content": "I already told you my timeline is flexible"},
        {"role": "bot", "content": "I need your timeline. 30, 60, or 90 days?"},
        {"role": "user", "content": "I already told you my timeline is flexible"},
        {"role": "bot", "content": "Look, are you serious or not?"},
        {"role": "user", "content": "I already told you my timeline is flexible"},
    ]


# ============================================================================
# ROADMAP-016: Question Progress Tracking Tests
# ============================================================================


class TestQuestionProgress:
    """Tests for ROADMAP-016: Question progress tracking."""

    @pytest.mark.asyncio
    async def test_get_question_progress_empty(self, mock_cache):
        """Test getting progress when no data exists."""
        result = await _get_question_progress("lead-123", mock_cache)
        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_retrieve_progress(self, mock_cache):
        """Test saving and retrieving question progress."""
        progress = QuestionProgress(
            lead_id="lead-123",
            conversation_id="conv-456",
            current_question_index=2,
            answers={"0": {"message": "30 days"}, "1": {"message": "$450k"}},
            last_message_at=datetime.now().isoformat(),
            started_at=datetime.now().isoformat(),
        )
        await _save_question_progress(progress, mock_cache)

        result = await _get_question_progress("lead-123", mock_cache)
        assert result is not None
        assert result.lead_id == "lead-123"
        assert result.current_question_index == 2
        assert len(result.answers) == 2

    @pytest.mark.asyncio
    async def test_update_question_progress_creates_new(self, mock_cache):
        """Test updating progress creates new record if none exists."""
        result = await _update_question_progress(
            lead_id="lead-new",
            conversation_id="conv-new",
            question_index=0,
            answer={"message": "first answer"},
            cache=mock_cache,
        )
        assert result.lead_id == "lead-new"
        assert result.current_question_index == 0
        assert "0" in result.answers
        assert result.started_at is not None

    @pytest.mark.asyncio
    async def test_update_question_progress_increments(self, mock_cache):
        """Test progress updates increment properly."""
        await _update_question_progress("lead-1", "conv-1", 0, {"message": "a1"}, mock_cache)
        await _update_question_progress("lead-1", "conv-1", 1, {"message": "a2"}, mock_cache)
        await _update_question_progress("lead-1", "conv-1", 2, {"message": "a3"}, mock_cache)

        result = await _get_question_progress("lead-1", mock_cache)
        assert result.current_question_index == 2
        assert len(result.answers) == 3

    @pytest.mark.asyncio
    async def test_question_progress_model_defaults(self):
        """Test QuestionProgress Pydantic model defaults."""
        progress = QuestionProgress(lead_id="x", conversation_id="y")
        assert progress.current_question_index == 0
        assert progress.total_questions == 5
        assert progress.answers == {}
        assert progress.last_message_at is None


# ============================================================================
# ROADMAP-017: Stall Detection Tests
# ============================================================================


class TestStallDetection:
    """Tests for ROADMAP-017: Stall detection algorithm."""

    @pytest.mark.asyncio
    async def test_no_stall_healthy_conversation(self, mock_cache, sample_conversation_history):
        """Test no stall detected in a healthy conversation."""
        # Set up recent progress
        progress = QuestionProgress(
            lead_id="lead-healthy",
            conversation_id="conv-1",
            last_message_at=datetime.now().isoformat(),
            started_at=(datetime.now() - timedelta(minutes=10)).isoformat(),
        )
        await _save_question_progress(progress, mock_cache)

        result = await _detect_stall("lead-healthy", sample_conversation_history, mock_cache)
        assert result.stall_detected is False

    @pytest.mark.asyncio
    async def test_timeout_stall_detected(self, mock_cache):
        """Test timeout stall detected when no message for > 24h."""
        progress = QuestionProgress(
            lead_id="lead-timeout",
            conversation_id="conv-1",
            last_message_at=(datetime.now() - timedelta(hours=25)).isoformat(),
            started_at=(datetime.now() - timedelta(hours=26)).isoformat(),
        )
        await _save_question_progress(progress, mock_cache)

        result = await _detect_stall("lead-timeout", [], mock_cache)
        assert result.stall_detected is True
        assert result.stall_type == "timeout"
        assert result.time_since_last_message_seconds > 24 * 3600

    @pytest.mark.asyncio
    async def test_vague_answers_stall_detected(self, mock_cache, stalled_conversation_history):
        """Test vague answer stall detection."""
        result = await _detect_stall("lead-vague", stalled_conversation_history, mock_cache)
        assert result.stall_detected is True
        assert result.stall_type == "vague_answers"
        assert result.recommendation is not None

    @pytest.mark.asyncio
    async def test_repetition_stall_detected(self, mock_cache, repetitive_conversation_history):
        """Test repetition stall detection."""
        result = await _detect_stall("lead-repeat", repetitive_conversation_history, mock_cache)
        assert result.stall_detected is True
        assert result.stall_type == "repetition"
        assert result.stall_score == 0.8

    @pytest.mark.asyncio
    async def test_disengagement_stall_detected(self, mock_cache):
        """Test disengagement stall (progressively shorter responses)."""
        history = [
            {"role": "user", "content": "I am really interested in selling my home soon and want to explore options"},
            {"role": "user", "content": "yeah that sounds good to me honestly"},
            {"role": "user", "content": "fine whatever works"},
            {"role": "user", "content": "ok"},
        ]
        result = await _detect_stall("lead-disengage", history, mock_cache)
        assert result.stall_detected is True
        assert result.stall_type == "disengagement"

    @pytest.mark.asyncio
    async def test_stall_result_model_defaults(self):
        """Test StallDetectionResult defaults."""
        result = StallDetectionResult()
        assert result.stall_detected is False
        assert result.stall_type is None
        assert result.stall_score == 0.0


# ============================================================================
# ROADMAP-018: Effectiveness Score Tests
# ============================================================================


class TestEffectivenessScore:
    """Tests for ROADMAP-018: Effectiveness score calculation."""

    @pytest.mark.asyncio
    async def test_effectiveness_score_no_data(self, mock_cache):
        """Test effectiveness score with no prior data."""
        result = await _calculate_effectiveness_score("lead-new", [], mock_cache)
        assert isinstance(result, EffectivenessScore)
        assert 0 <= result.score <= 100

    @pytest.mark.asyncio
    async def test_effectiveness_score_with_progress(self, mock_cache, sample_conversation_history):
        """Test effectiveness score with question progress."""
        progress = QuestionProgress(
            lead_id="lead-eff",
            conversation_id="conv-1",
            current_question_index=3,
            answers={"0": {}, "1": {}, "2": {}},
            started_at=(datetime.now() - timedelta(minutes=15)).isoformat(),
            last_message_at=datetime.now().isoformat(),
        )
        await _save_question_progress(progress, mock_cache)

        result = await _calculate_effectiveness_score("lead-eff", sample_conversation_history, mock_cache)
        assert result.score > 0
        assert result.completion_rate == 0.6  # 3/5
        assert result.engagement_depth > 0

    @pytest.mark.asyncio
    async def test_effectiveness_penalized_by_stall(self, mock_cache, stalled_conversation_history):
        """Test effectiveness score is penalized when stall detected."""
        stall = StallDetectionResult(stall_detected=True, stall_type="vague_answers", stall_score=0.8)

        result = await _calculate_effectiveness_score("lead-stall", stalled_conversation_history, mock_cache, stall)
        # Score should be lower due to stall penalty
        assert result.score < 100
        assert result.breakdown["stall_penalty"] > 0

    @pytest.mark.asyncio
    async def test_effectiveness_score_complete_qualification(self, mock_cache, sample_conversation_history):
        """Test effectiveness score for completed qualification."""
        progress = QuestionProgress(
            lead_id="lead-complete",
            conversation_id="conv-1",
            current_question_index=5,
            answers={"0": {}, "1": {}, "2": {}, "3": {}, "4": {}},
            started_at=(datetime.now() - timedelta(minutes=20)).isoformat(),
            last_message_at=datetime.now().isoformat(),
        )
        await _save_question_progress(progress, mock_cache)

        result = await _calculate_effectiveness_score("lead-complete", sample_conversation_history, mock_cache)
        assert result.completion_rate == 1.0
        assert result.score >= 50  # Should be high for complete qualification


# ============================================================================
# ROADMAP-020: CoordinationEvent Tests
# ============================================================================


class TestCoordinationEvent:
    """Tests for ROADMAP-020: CoordinationEvent model and emission."""

    def test_coordination_event_model(self):
        """Test CoordinationEvent Pydantic model."""
        event = CoordinationEvent(
            event_id="coord_123",
            event_type="handoff",
            source_bot="seller",
            target_bot="buyer",
            lead_id="lead-1",
            timestamp=datetime.now().isoformat(),
            confidence=0.85,
            metadata={"reason": "buyer_intent_detected"},
        )
        assert event.event_type == "handoff"
        assert event.confidence == 0.85

    def test_coordination_event_defaults(self):
        """Test CoordinationEvent defaults."""
        event = CoordinationEvent(
            event_id="x",
            event_type="stall_detected",
            source_bot="seller",
            lead_id="y",
            timestamp="2026-01-01T00:00:00",
        )
        assert event.target_bot is None
        assert event.confidence == 0.0
        assert event.metadata == {}

    @pytest.mark.asyncio
    async def test_emit_coordination_event(self, mock_event_publisher):
        """Test emitting a coordination event via event publisher."""
        event = await _emit_coordination_event(
            event_type="handoff",
            source_bot="seller",
            lead_id="lead-abc",
            event_publisher=mock_event_publisher,
            target_bot="buyer",
            confidence=0.9,
            metadata={"handoff_id": "h123"},
        )
        assert event.event_type == "handoff"
        assert event.source_bot == "seller"
        assert event.target_bot == "buyer"
        assert event.confidence == 0.9
        mock_event_publisher.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_stall_coordination_event(self, mock_event_publisher):
        """Test emitting a stall coordination event."""
        event = await _emit_coordination_event(
            event_type="stall_detected",
            source_bot="jorge-seller-bot",
            lead_id="lead-stall",
            event_publisher=mock_event_publisher,
            confidence=0.7,
            metadata={"stall_type": "timeout"},
        )
        assert event.event_type == "stall_detected"
        assert event.lead_id == "lead-stall"

    @pytest.mark.asyncio
    async def test_emit_qualification_complete_event(self, mock_event_publisher):
        """Test emitting a qualification complete event."""
        event = await _emit_coordination_event(
            event_type="qualification_complete",
            source_bot="jorge-seller-bot",
            lead_id="lead-done",
            event_publisher=mock_event_publisher,
            confidence=0.95,
            metadata={"temperature": "hot", "score": 90},
        )
        assert event.event_type == "qualification_complete"
        assert "temperature" in event.metadata
