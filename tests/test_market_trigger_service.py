import pytest
pytestmark = pytest.mark.integration

"""Tests for market trigger re-engagement service (Phase 5B)."""

import pytest

from ghl_real_estate_ai.services.jorge.market_trigger_service import (

    ContactWatchlist,
    MarketTriggerService,
    TriggerPriority,
    TriggerType,
)


@pytest.fixture
def service():
    svc = MarketTriggerService()
    svc.register_watchlist(
        ContactWatchlist(
            contact_id="buyer_1",
            watched_zips=["91730"],
            max_price=700_000,
            min_beds=3,
            preferred_areas=["Victoria", "Haven"],
        )
    )
    svc.register_watchlist(
        ContactWatchlist(
            contact_id="buyer_2",
            max_price=500_000,
            preferred_areas=["Victoria"],
        )
    )
    return svc


class TestPriceDrop:
    def test_triggers_for_matching_contact(self, service):
        triggers = service.evaluate_price_drop(
            area="Victoria",
            original_price=650_000,
            new_price=585_000,
        )
        assert len(triggers) >= 1
        assert any(t.contact_id == "buyer_1" for t in triggers)
        assert all(t.trigger_type == TriggerType.PRICE_DROP for t in triggers)

    def test_ignores_trivial_drop(self, service):
        triggers = service.evaluate_price_drop(
            area="Victoria",
            original_price=650_000,
            new_price=645_000,  # < 3%
        )
        assert len(triggers) == 0

    def test_filters_by_max_price(self, service):
        triggers = service.evaluate_price_drop(
            area="Victoria",
            original_price=900_000,
            new_price=800_000,  # Still above buyer_2's $500K max
        )
        # buyer_2 max=$500K, so this shouldn't match them
        buyer_2_triggers = [t for t in triggers if t.contact_id == "buyer_2"]
        assert len(buyer_2_triggers) == 0

    def test_filters_by_preferred_area(self, service):
        triggers = service.evaluate_price_drop(
            area="Upland",  # Not in any watchlist
            original_price=500_000,
            new_price=400_000,
        )
        assert len(triggers) == 0

    def test_high_priority_for_large_drop(self, service):
        triggers = service.evaluate_price_drop(
            area="Victoria",
            original_price=700_000,
            new_price=600_000,  # ~14% drop
        )
        high_priority = [t for t in triggers if t.priority == TriggerPriority.HIGH]
        assert len(high_priority) > 0


class TestRateChange:
    def test_triggers_on_significant_change(self, service):
        triggers = service.evaluate_rate_change(new_rate=6.5, previous_rate=7.0)
        assert len(triggers) == 2  # Both watchlisted contacts
        assert all(t.trigger_type == TriggerType.RATE_CHANGE for t in triggers)

    def test_ignores_tiny_change(self, service):
        triggers = service.evaluate_rate_change(new_rate=6.95, previous_rate=7.0)
        assert len(triggers) == 0

    def test_payment_impact_in_data(self, service):
        triggers = service.evaluate_rate_change(new_rate=6.0, previous_rate=7.0)
        for t in triggers:
            assert "estimated_payment_change" in t.data
            assert t.data["rate_delta"] == -1.0


class TestNeighborhoodSale:
    def test_triggers_for_watched_area(self, service):
        triggers = service.evaluate_neighborhood_sale(
            neighborhood="Victoria",
            sold_price=650_000,
            price_per_sqft=350,
            area_avg_per_sqft=325,
        )
        assert len(triggers) >= 1

    def test_no_trigger_for_unwatched_area(self, service):
        triggers = service.evaluate_neighborhood_sale(
            neighborhood="Fontana",
            sold_price=400_000,
            price_per_sqft=250,
            area_avg_per_sqft=260,
        )
        assert len(triggers) == 0


class TestWatchlistManagement:
    def test_register_and_get(self, service):
        wl = service.get_watchlist("buyer_1")
        assert wl is not None
        assert wl.max_price == 700_000

    def test_remove_watchlist(self, service):
        service.remove_watchlist("buyer_1")
        assert service.get_watchlist("buyer_1") is None

    def test_get_active_watchlists(self, service):
        watchlists = service.get_active_watchlists()
        assert len(watchlists) == 2

    def test_stats(self, service):
        stats = service.get_trigger_stats()
        assert stats["active_watchlists"] == 2

    def test_trigger_to_dict(self, service):
        triggers = service.evaluate_price_drop(
            area="Victoria", original_price=700_000, new_price=600_000
        )
        assert len(triggers) > 0
        d = triggers[0].to_dict()
        assert d["trigger_type"] == "price_drop"
        assert "contact_id" in d