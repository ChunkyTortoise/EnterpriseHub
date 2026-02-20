"""
Integration tests for ROADMAP-026 through ROADMAP-030:
Customer journey CRUD — create, read, update, delete (soft), step completion.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from ghl_real_estate_ai.api.routes.customer_journey import (
    CustomerJourney,
    JourneyStep,
    _complete_journey_step,
    _get_journey,
    _list_journeys,
    _save_journey,
    _soft_delete_journey,
    generate_mock_journey_steps,
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


def _make_journey(journey_id="j-1", customer_id="c-1", status="active") -> CustomerJourney:
    """Helper to build a test journey."""
    steps = generate_mock_journey_steps()
    return CustomerJourney(
        id=journey_id,
        customerId=customer_id,
        customerName="Test Customer",
        customerEmail="test@example.com",
        type="FIRST_TIME_BUYER",
        status=status,
        priority="medium",
        currentStep=0,
        totalSteps=len(steps),
        completionPercentage=0,
        startTime=datetime.now().isoformat(),
        steps=steps,
        analytics={"avgResponseTime": 0, "touchpoints": 0},
        context={"budget": 500000},
        notifications=[],
    )


# ============================================================================
# ROADMAP-026: Journey Create Tests
# ============================================================================


class TestJourneyCreate:
    """Tests for ROADMAP-026: Journey creation and persistence."""

    @pytest.mark.asyncio
    async def test_save_journey(self, mock_cache):
        """Test saving a journey persists to cache."""
        journey = _make_journey()
        await _save_journey(journey, mock_cache)

        stored = await mock_cache.get(f"journey:{journey.id}")
        assert stored is not None
        assert stored["id"] == journey.id
        assert stored["customerId"] == "c-1"

    @pytest.mark.asyncio
    async def test_save_updates_index(self, mock_cache):
        """Test saving a journey adds it to the index."""
        j1 = _make_journey("j-1")
        j2 = _make_journey("j-2", "c-2")
        await _save_journey(j1, mock_cache)
        await _save_journey(j2, mock_cache)

        index = await mock_cache.get("journey_index")
        assert "j-1" in index
        assert "j-2" in index

    @pytest.mark.asyncio
    async def test_save_same_journey_twice_no_duplicate_index(self, mock_cache):
        """Test saving the same journey ID does not duplicate index entry."""
        journey = _make_journey("j-1")
        await _save_journey(journey, mock_cache)
        await _save_journey(journey, mock_cache)

        index = await mock_cache.get("journey_index")
        assert index.count("j-1") == 1


# ============================================================================
# ROADMAP-027: Journey Read Tests
# ============================================================================


class TestJourneyRead:
    """Tests for ROADMAP-027: Journey retrieval."""

    @pytest.mark.asyncio
    async def test_get_journey_exists(self, mock_cache):
        """Test getting an existing journey."""
        journey = _make_journey()
        await _save_journey(journey, mock_cache)

        result = await _get_journey("j-1", mock_cache)
        assert result is not None
        assert result.id == "j-1"
        assert result.customerName == "Test Customer"

    @pytest.mark.asyncio
    async def test_get_journey_not_found(self, mock_cache):
        """Test getting a non-existent journey returns None."""
        result = await _get_journey("j-nonexistent", mock_cache)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_journey_excludes_deleted(self, mock_cache):
        """Test deleted journeys are not returned by _get_journey."""
        journey = _make_journey()
        await _save_journey(journey, mock_cache)
        await _soft_delete_journey("j-1", mock_cache)

        result = await _get_journey("j-1", mock_cache)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_journeys(self, mock_cache):
        """Test listing all journeys."""
        await _save_journey(_make_journey("j-1"), mock_cache)
        await _save_journey(_make_journey("j-2", "c-2"), mock_cache)
        await _save_journey(_make_journey("j-3", "c-3"), mock_cache)

        journeys = await _list_journeys(mock_cache)
        assert len(journeys) == 3

    @pytest.mark.asyncio
    async def test_list_journeys_excludes_deleted(self, mock_cache):
        """Test listing excludes soft-deleted journeys."""
        await _save_journey(_make_journey("j-1"), mock_cache)
        await _save_journey(_make_journey("j-2", "c-2"), mock_cache)
        await _soft_delete_journey("j-1", mock_cache)

        journeys = await _list_journeys(mock_cache)
        assert len(journeys) == 1
        assert journeys[0].id == "j-2"


# ============================================================================
# ROADMAP-028: Journey Update Tests
# ============================================================================


class TestJourneyUpdate:
    """Tests for ROADMAP-028: Journey update with status transitions."""

    @pytest.mark.asyncio
    async def test_update_journey_status(self, mock_cache):
        """Test updating journey status via save."""
        journey = _make_journey()
        await _save_journey(journey, mock_cache)

        journey.status = "paused"
        await _save_journey(journey, mock_cache)

        result = await _get_journey("j-1", mock_cache)
        assert result.status == "paused"

    @pytest.mark.asyncio
    async def test_update_journey_priority(self, mock_cache):
        """Test updating journey priority."""
        journey = _make_journey()
        await _save_journey(journey, mock_cache)

        journey.priority = "urgent"
        await _save_journey(journey, mock_cache)

        result = await _get_journey("j-1", mock_cache)
        assert result.priority == "urgent"

    @pytest.mark.asyncio
    async def test_update_journey_context(self, mock_cache):
        """Test updating journey context merges new data."""
        journey = _make_journey()
        journey.context = {"budget": 500000}
        await _save_journey(journey, mock_cache)

        journey.context["timeframe"] = "30 days"
        await _save_journey(journey, mock_cache)

        result = await _get_journey("j-1", mock_cache)
        assert result.context["budget"] == 500000
        assert result.context["timeframe"] == "30 days"


# ============================================================================
# ROADMAP-029: Journey Delete (Soft) Tests
# ============================================================================


class TestJourneyDelete:
    """Tests for ROADMAP-029: Soft-delete with audit trail."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_deleted_at(self, mock_cache):
        """Test soft-delete sets deleted_at timestamp."""
        journey = _make_journey()
        await _save_journey(journey, mock_cache)

        result = await _soft_delete_journey("j-1", mock_cache)
        assert result is True

        # Raw data still exists in cache with deleted_at
        raw = await mock_cache.get("journey:j-1")
        assert raw is not None
        assert "deleted_at" in raw
        assert raw["status"] == "abandoned"

    @pytest.mark.asyncio
    async def test_soft_delete_nonexistent_returns_false(self, mock_cache):
        """Test soft-deleting a non-existent journey returns False."""
        result = await _soft_delete_journey("j-nonexistent", mock_cache)
        assert result is False

    @pytest.mark.asyncio
    async def test_soft_delete_preserves_data(self, mock_cache):
        """Test soft-deleted journey data remains for auditing."""
        journey = _make_journey()
        await _save_journey(journey, mock_cache)
        await _soft_delete_journey("j-1", mock_cache)

        raw = await mock_cache.get("journey:j-1")
        assert raw["customerId"] == "c-1"
        assert raw["customerName"] == "Test Customer"


# ============================================================================
# ROADMAP-030: Step Completion Tests
# ============================================================================


class TestStepCompletion:
    """Tests for ROADMAP-030: Step completion with auto-advance."""

    @pytest.mark.asyncio
    async def test_complete_step_basic(self, mock_cache):
        """Test basic step completion."""
        journey = _make_journey()
        # Set step-1 to active so it can be completed
        journey.steps[0].status = "active"
        journey.steps[0].startTime = datetime.now().isoformat()
        await _save_journey(journey, mock_cache)

        result = await _complete_journey_step("j-1", "step-1", {"rapport_score": 9.0}, mock_cache)
        assert result is not None
        assert result["step_status"] == "completed"
        assert result["journey_completion_percentage"] == 20  # 1 of 5

    @pytest.mark.asyncio
    async def test_complete_step_auto_activates_next(self, mock_cache):
        """Test completing a step auto-activates the next pending step."""
        journey = _make_journey()
        journey.steps[0].status = "active"
        journey.steps[0].startTime = datetime.now().isoformat()
        # steps[1] is pending
        journey.steps[1].status = "pending"
        await _save_journey(journey, mock_cache)

        result = await _complete_journey_step("j-1", "step-1", {}, mock_cache)
        assert result["next_step_activated"] == "step-2"

        # Verify next step is now active
        updated = await mock_cache.get("journey:j-1")
        assert updated["steps"][1]["status"] == "active"
        assert updated["steps"][1]["startTime"] is not None

    @pytest.mark.asyncio
    async def test_complete_step_not_found(self, mock_cache):
        """Test completing a non-existent step returns None."""
        journey = _make_journey()
        await _save_journey(journey, mock_cache)

        result = await _complete_journey_step("j-1", "step-nonexistent", {}, mock_cache)
        assert result is None

    @pytest.mark.asyncio
    async def test_complete_step_journey_not_found(self, mock_cache):
        """Test completing step for non-existent journey returns None."""
        result = await _complete_journey_step("j-nonexistent", "step-1", {}, mock_cache)
        assert result is None

    @pytest.mark.asyncio
    async def test_complete_all_steps_completes_journey(self, mock_cache):
        """Test completing all steps marks journey as completed."""
        journey = _make_journey()
        # Set all steps to active with start times
        for step in journey.steps:
            step.status = "active"
            step.startTime = datetime.now().isoformat()
        await _save_journey(journey, mock_cache)

        # Complete each step
        for step in journey.steps:
            await _complete_journey_step("j-1", step.id, {"done": True}, mock_cache)

        updated = await mock_cache.get("journey:j-1")
        assert updated["status"] == "completed"
        assert updated["completionPercentage"] == 100
        assert updated["actualCompletion"] is not None

    @pytest.mark.asyncio
    async def test_complete_step_stores_output(self, mock_cache):
        """Test step output is stored after completion."""
        journey = _make_journey()
        journey.steps[0].status = "active"
        journey.steps[0].startTime = datetime.now().isoformat()
        await _save_journey(journey, mock_cache)

        output_data = {"rapport_score": 8.5, "notes": "Great conversation"}
        await _complete_journey_step("j-1", "step-1", output_data, mock_cache)

        updated = await mock_cache.get("journey:j-1")
        completed_step = updated["steps"][0]
        assert completed_step["output"]["rapport_score"] == 8.5
        assert completed_step["endTime"] is not None
