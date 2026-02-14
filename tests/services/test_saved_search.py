import pytest
pytestmark = pytest.mark.integration

"""Tests for Buyer Saved Search & Alerts Service.

Covers search creation, new-only match detection, SMS notification format,
deactivation, message length constraint, and multiple searches per buyer.
"""

import pytest

from ghl_real_estate_ai.services.saved_search import (

    SavedSearchService,
    SearchCriteria,
)

SAMPLE_LISTINGS = [
    {
        "id": "L001",
        "address": "123 Oak St",
        "price": 550_000,
        "bedrooms": 3,
        "bathrooms": 2,
        "neighborhood": "Rancho Cucamonga",
        "days_on_market": 5,
    },
    {
        "id": "L002",
        "address": "456 Maple Ave",
        "price": 800_000,
        "bedrooms": 4,
        "bathrooms": 3,
        "neighborhood": "Rancho Cucamonga",
        "days_on_market": 12,
    },
    {
        "id": "L003",
        "address": "789 Pine Rd",
        "price": 420_000,
        "bedrooms": 2,
        "bathrooms": 1,
        "neighborhood": "Upland",
        "days_on_market": 30,
    },
]


@pytest.fixture
def service() -> SavedSearchService:
    """Fresh SavedSearchService for each test."""
    return SavedSearchService()


@pytest.fixture
def default_criteria() -> SearchCriteria:
    """Criteria matching middle-range Rancho Cucamonga homes."""
    return SearchCriteria(
        budget_min=400_000,
        budget_max=600_000,
        beds_min=3,
        baths_min=2,
        neighborhoods=["Rancho Cucamonga"],
        max_dom=14,
    )


class TestSavedSearchService:
    """Tests for SavedSearchService."""

    @pytest.mark.asyncio
    async def test_create_search_from_criteria(
        self, service: SavedSearchService, default_criteria: SearchCriteria
    ) -> None:
        """Creates search with valid ID and criteria stored."""
        search = await service.create_search("buyer-1", default_criteria)

        assert search.id.startswith("search-")
        assert search.buyer_id == "buyer-1"
        assert search.criteria is default_criteria
        assert search.active is True
        assert search.matches_sent == 0

    @pytest.mark.asyncio
    async def test_check_new_matches_returns_only_new(
        self, service: SavedSearchService, default_criteria: SearchCriteria
    ) -> None:
        """Same listing not returned twice after notification."""
        search = await service.create_search("buyer-1", default_criteria)

        # First check -- L001 matches criteria
        matches_1 = await service.check_new_matches(search.id, SAMPLE_LISTINGS)
        assert len(matches_1) >= 1
        assert any(m["id"] == "L001" for m in matches_1)

        # Notify buyer about first batch (marks them as notified)
        await service.notify_buyer(search, matches_1)

        # Second check with the same listings -- previously matched should be excluded
        matches_2 = await service.check_new_matches(search.id, SAMPLE_LISTINGS)
        notified_ids = {m["id"] for m in matches_1}
        for m in matches_2:
            assert m["id"] not in notified_ids

    @pytest.mark.asyncio
    async def test_notify_buyer_sms_format(
        self, service: SavedSearchService, default_criteria: SearchCriteria
    ) -> None:
        """Notification message is a non-empty string."""
        search = await service.create_search("buyer-1", default_criteria)
        matches = await service.check_new_matches(search.id, SAMPLE_LISTINGS)
        assert len(matches) > 0

        messages = await service.notify_buyer(search, matches)
        assert len(messages) == len(matches)
        for msg in messages:
            assert isinstance(msg, str)
            assert len(msg) > 0

    @pytest.mark.asyncio
    async def test_deactivate_search(
        self, service: SavedSearchService, default_criteria: SearchCriteria
    ) -> None:
        """Deactivated search returns no matches."""
        search = await service.create_search("buyer-1", default_criteria)
        result = await service.deactivate_search(search.id)
        assert result is True

        matches = await service.check_new_matches(search.id, SAMPLE_LISTINGS)
        assert matches == []

    @pytest.mark.asyncio
    async def test_notification_under_160_chars(
        self, service: SavedSearchService, default_criteria: SearchCriteria
    ) -> None:
        """Alert message <= 160 chars (SMS limit)."""
        search = await service.create_search("buyer-1", default_criteria)
        matches = await service.check_new_matches(search.id, SAMPLE_LISTINGS)
        messages = await service.notify_buyer(search, matches)

        for msg in messages:
            assert len(msg) <= SavedSearchService.SMS_MAX_LENGTH, (
                f"Message exceeds {SavedSearchService.SMS_MAX_LENGTH} chars: "
                f"({len(msg)}) {msg!r}"
            )

    @pytest.mark.asyncio
    async def test_multiple_searches_per_buyer(
        self, service: SavedSearchService
    ) -> None:
        """Buyer can have multiple active searches."""
        criteria_a = SearchCriteria(budget_max=500_000, beds_min=2)
        criteria_b = SearchCriteria(budget_max=900_000, beds_min=4)

        search_a = await service.create_search("buyer-1", criteria_a)
        search_b = await service.create_search("buyer-1", criteria_b)

        active = await service.get_active_searches("buyer-1")
        assert len(active) == 2
        ids = {s.id for s in active}
        assert search_a.id in ids
        assert search_b.id in ids