"""
Integration tests for ROADMAP-031 through ROADMAP-035:
Property intelligence — analysis CRUD, cache, versioning, comparison.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from ghl_real_estate_ai.api.routes.property_intelligence import (
    PropertyAnalysisRequest,
    _compare_properties_from_cache,
    _get_analysis,
    _save_analysis,
    _soft_delete_analysis,
    _update_analysis_in_cache,
    generate_mock_property_analysis,
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


def _make_request(property_id="prop-1", level="STANDARD", strategy="BUY_AND_HOLD"):
    return PropertyAnalysisRequest(
        propertyId=property_id,
        address="123 Test St, Test City, TS 12345",
        analysisLevel=level,
        investmentStrategy=strategy,
    )


# ============================================================================
# ROADMAP-031: Property Analysis Creation + Caching
# ============================================================================


class TestPropertyAnalysisCreate:
    """Tests for ROADMAP-031: Analysis creation and caching."""

    @pytest.mark.asyncio
    async def test_save_analysis(self, mock_cache):
        """Test saving analysis persists to cache."""
        request = _make_request()
        analysis = generate_mock_property_analysis(request)
        await _save_analysis(analysis, mock_cache)

        stored = await mock_cache.get(f"property_analysis:{analysis.propertyId}")
        assert stored is not None
        assert stored["propertyId"] == analysis.propertyId

    @pytest.mark.asyncio
    async def test_save_updates_index(self, mock_cache):
        """Test saving adds property ID to index."""
        for i in range(3):
            req = _make_request(f"prop-{i}")
            analysis = generate_mock_property_analysis(req)
            await _save_analysis(analysis, mock_cache)

        index = await mock_cache.get("property_analysis_index")
        assert len(index) == 3

    @pytest.mark.asyncio
    async def test_save_no_duplicate_index(self, mock_cache):
        """Test saving same ID twice does not duplicate index."""
        req = _make_request("prop-1")
        analysis = generate_mock_property_analysis(req)
        await _save_analysis(analysis, mock_cache)
        await _save_analysis(analysis, mock_cache)

        index = await mock_cache.get("property_analysis_index")
        assert index.count("prop-1") == 1


# ============================================================================
# ROADMAP-032: Property Analysis Retrieval
# ============================================================================


class TestPropertyAnalysisRead:
    """Tests for ROADMAP-032: Cache retrieval."""

    @pytest.mark.asyncio
    async def test_get_analysis_exists(self, mock_cache):
        """Test retrieving an existing analysis."""
        req = _make_request()
        analysis = generate_mock_property_analysis(req)
        await _save_analysis(analysis, mock_cache)

        result = await _get_analysis("prop-1", mock_cache)
        assert result is not None
        assert result.propertyId == "prop-1"
        assert result.analysisLevel == "STANDARD"

    @pytest.mark.asyncio
    async def test_get_analysis_not_found(self, mock_cache):
        """Test retrieval of non-existent analysis returns None."""
        result = await _get_analysis("prop-nonexistent", mock_cache)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_analysis_excludes_deleted(self, mock_cache):
        """Test deleted analysis not returned."""
        req = _make_request()
        analysis = generate_mock_property_analysis(req)
        await _save_analysis(analysis, mock_cache)
        await _soft_delete_analysis("prop-1", mock_cache)

        result = await _get_analysis("prop-1", mock_cache)
        assert result is None


# ============================================================================
# ROADMAP-033: Property Analysis Update with Versioning
# ============================================================================


class TestPropertyAnalysisUpdate:
    """Tests for ROADMAP-033: Update with version history."""

    @pytest.mark.asyncio
    async def test_update_creates_new_analysis(self, mock_cache):
        """Test update on new property creates analysis."""
        req = _make_request("prop-new", "PREMIUM", "FIX_AND_FLIP")
        result = await _update_analysis_in_cache("prop-new", req, mock_cache)

        assert result is not None
        assert result.propertyId == "prop-new"
        assert result.analysisLevel == "PREMIUM"

    @pytest.mark.asyncio
    async def test_update_archives_previous_version(self, mock_cache):
        """Test update archives the old version."""
        req1 = _make_request("prop-1", "BASIC", "RENTAL_INCOME")
        analysis1 = generate_mock_property_analysis(req1)
        await _save_analysis(analysis1, mock_cache)

        req2 = _make_request("prop-1", "PREMIUM", "FIX_AND_FLIP")
        await _update_analysis_in_cache("prop-1", req2, mock_cache)

        history = await mock_cache.get("property_analysis_history:prop-1")
        assert history is not None
        assert len(history) == 1
        assert history[0]["analysisLevel"] == "BASIC"
        assert "archived_at" in history[0]

    @pytest.mark.asyncio
    async def test_update_replaces_cached_analysis(self, mock_cache):
        """Test update overwrites cached analysis."""
        req1 = _make_request("prop-1", "BASIC", "RENTAL_INCOME")
        analysis1 = generate_mock_property_analysis(req1)
        await _save_analysis(analysis1, mock_cache)

        req2 = _make_request("prop-1", "INSTITUTIONAL", "COMMERCIAL")
        await _update_analysis_in_cache("prop-1", req2, mock_cache)

        result = await _get_analysis("prop-1", mock_cache)
        assert result.analysisLevel == "INSTITUTIONAL"
        assert result.investmentStrategy == "COMMERCIAL"


# ============================================================================
# ROADMAP-034: Property Analysis Soft-Delete
# ============================================================================


class TestPropertyAnalysisDelete:
    """Tests for ROADMAP-034: Soft-delete with archive."""

    @pytest.mark.asyncio
    async def test_soft_delete(self, mock_cache):
        """Test soft-delete sets deleted_at."""
        req = _make_request()
        analysis = generate_mock_property_analysis(req)
        await _save_analysis(analysis, mock_cache)

        result = await _soft_delete_analysis("prop-1", mock_cache)
        assert result is True

        raw = await mock_cache.get("property_analysis:prop-1")
        assert "deleted_at" in raw

    @pytest.mark.asyncio
    async def test_soft_delete_archives_history(self, mock_cache):
        """Test soft-delete archives the analysis."""
        req = _make_request()
        analysis = generate_mock_property_analysis(req)
        await _save_analysis(analysis, mock_cache)

        await _soft_delete_analysis("prop-1", mock_cache)

        history = await mock_cache.get("property_analysis_history:prop-1")
        assert len(history) == 1
        assert "archived_at" in history[0]

    @pytest.mark.asyncio
    async def test_soft_delete_nonexistent_returns_false(self, mock_cache):
        """Test deleting non-existent analysis returns False."""
        result = await _soft_delete_analysis("prop-nonexistent", mock_cache)
        assert result is False


# ============================================================================
# ROADMAP-035: Property Comparison
# ============================================================================


class TestPropertyComparison:
    """Tests for ROADMAP-035: Multi-property comparison with ranking."""

    @pytest.mark.asyncio
    async def test_compare_two_properties(self, mock_cache):
        """Test comparing two cached properties."""
        for i in range(2):
            req = _make_request(f"prop-{i}")
            analysis = generate_mock_property_analysis(req)
            await _save_analysis(analysis, mock_cache)

        result = await _compare_properties_from_cache(["prop-0", "prop-1"], mock_cache)
        assert len(result["properties"]) == 2
        assert "bestOverall" in result["recommendation"]
        assert "bestCashFlow" in result["recommendation"]
        assert "lowestRisk" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_compare_no_cached_analyses(self, mock_cache):
        """Test comparison with no cached data returns empty."""
        result = await _compare_properties_from_cache(["prop-x", "prop-y"], mock_cache)
        assert result["properties"] == []
        assert "No analyses found" in result["recommendation"]["explanation"]

    @pytest.mark.asyncio
    async def test_compare_partial_cache(self, mock_cache):
        """Test comparison with some missing analyses only includes found."""
        req = _make_request("prop-0")
        analysis = generate_mock_property_analysis(req)
        await _save_analysis(analysis, mock_cache)

        result = await _compare_properties_from_cache(["prop-0", "prop-missing"], mock_cache)
        assert len(result["properties"]) == 1
        assert result["properties"][0]["propertyId"] == "prop-0"

    @pytest.mark.asyncio
    async def test_compare_limits_to_five(self, mock_cache):
        """Test comparison caps at 5 properties."""
        for i in range(7):
            req = _make_request(f"prop-{i}")
            analysis = generate_mock_property_analysis(req)
            await _save_analysis(analysis, mock_cache)

        result = await _compare_properties_from_cache([f"prop-{i}" for i in range(7)], mock_cache)
        assert len(result["properties"]) == 5

    @pytest.mark.asyncio
    async def test_compare_ranking_accuracy(self, mock_cache):
        """Test comparison ranking identifies correct best properties."""
        req = _make_request("prop-0")
        analysis = generate_mock_property_analysis(req)
        await _save_analysis(analysis, mock_cache)

        result = await _compare_properties_from_cache(["prop-0"], mock_cache)
        # Single property should be best in all categories
        rec = result["recommendation"]
        assert rec["bestOverall"] == "prop-0"
        assert rec["bestCashFlow"] == "prop-0"
        assert rec["lowestRisk"] == "prop-0"
