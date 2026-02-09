import pytest
pytestmark = pytest.mark.integration

"""Tests for offer strategy advisor service.

Validates market-aware offer recommendations including pricing,
contingencies, escalation clauses, and competitive assessments.
"""

import pytest

from ghl_real_estate_ai.services.offer_advisor import OfferAdvisor, OfferStrategy

@pytest.mark.unit


@pytest.fixture
def advisor():
    """Create an OfferAdvisor instance."""
    return OfferAdvisor()


@pytest.fixture
def base_property():
    """Standard property data for testing."""
    return {"price": 500_000, "days_on_market": 10}


@pytest.fixture
def base_buyer():
    """Standard buyer profile for testing."""
    return {
        "financing_status": "pre-approved",
        "budget_max": 550_000,
    }


@pytest.mark.asyncio
async def test_sellers_market_suggests_above_list(advisor, base_buyer):
    """Seller's market should suggest a price above list price."""
    property_data = {"price": 500_000, "days_on_market": 5}
    market = {"market_type": "sellers"}

    result = await advisor.analyze_offer_position(
        property_data, base_buyer, market_conditions=market
    )

    assert isinstance(result, OfferStrategy)
    assert result.suggested_price > 500_000
    assert "above list" in result.price_rationale.lower()


@pytest.mark.asyncio
async def test_buyers_market_suggests_below_list(advisor, base_buyer):
    """Buyer's market should suggest a price below list price."""
    property_data = {"price": 500_000, "days_on_market": 50}
    market = {"market_type": "buyers"}

    result = await advisor.analyze_offer_position(
        property_data, base_buyer, market_conditions=market
    )

    assert result.suggested_price < 500_000
    assert "below list" in result.price_rationale.lower()


@pytest.mark.asyncio
async def test_high_dom_more_aggressive(advisor, base_buyer):
    """Properties with >60 DOM should get a bigger discount than DOM 30."""
    market = {"market_type": "buyers"}

    prop_30 = {"price": 500_000, "days_on_market": 30}
    result_30 = await advisor.analyze_offer_position(
        prop_30, base_buyer, market_conditions=market
    )

    prop_70 = {"price": 500_000, "days_on_market": 70}
    result_70 = await advisor.analyze_offer_position(
        prop_70, base_buyer, market_conditions=market
    )

    # Higher DOM should produce a lower suggested price
    assert result_70.suggested_price < result_30.suggested_price


@pytest.mark.asyncio
async def test_earnest_money_percentage(advisor, base_property, base_buyer):
    """Earnest money: sellers=3%, buyers=1%, balanced=2%."""
    for market_type, expected_pct in [
        ("sellers", 3.0),
        ("buyers", 1.0),
        ("balanced", 2.0),
    ]:
        result = await advisor.analyze_offer_position(
            base_property, base_buyer, market_conditions={"market_type": market_type}
        )
        assert result.earnest_money_pct == expected_pct, (
            f"Expected {expected_pct}% for {market_type} market, "
            f"got {result.earnest_money_pct}%"
        )


@pytest.mark.asyncio
async def test_contingency_recommendations(advisor, base_property, base_buyer):
    """Seller's market should have fewer contingencies than buyer's market."""
    sellers_result = await advisor.analyze_offer_position(
        base_property, base_buyer, market_conditions={"market_type": "sellers"}
    )
    buyers_result = await advisor.analyze_offer_position(
        base_property, base_buyer, market_conditions={"market_type": "buyers"}
    )

    assert len(sellers_result.contingencies) < len(buyers_result.contingencies)
    assert "inspection" in sellers_result.contingencies
    assert "inspection" in buyers_result.contingencies
    assert "appraisal" in buyers_result.contingencies


@pytest.mark.asyncio
async def test_escalation_clause_generation(advisor, base_property):
    """Seller's market with budget headroom should generate an escalation clause."""
    buyer_with_headroom = {
        "financing_status": "pre-approved",
        "budget_max": 600_000,
    }

    result = await advisor.analyze_offer_position(
        base_property, buyer_with_headroom, market_conditions={"market_type": "sellers"}
    )

    assert result.escalation_clause is not None
    assert "max_price" in result.escalation_clause
    assert "increment" in result.escalation_clause
    assert result.escalation_clause["max_price"] <= 600_000

    # No escalation when budget <= list price
    buyer_tight = {"financing_status": "pre-approved", "budget_max": 400_000}
    result_tight = await advisor.analyze_offer_position(
        base_property, buyer_tight, market_conditions={"market_type": "sellers"}
    )
    assert result_tight.escalation_clause is None


@pytest.mark.asyncio
async def test_competitive_assessment(advisor, base_buyer):
    """Strong/moderate/weak classification based on offer components."""
    # Seller's market with cash buyer (strong offer: high price + few contingencies + high earnest)
    cash_buyer = {"financing_status": "cash", "budget_max": 600_000}
    prop = {"price": 500_000, "days_on_market": 5}
    result = await advisor.analyze_offer_position(
        prop, cash_buyer, market_conditions={"market_type": "sellers"}
    )
    assert result.competitive_assessment == "strong"

    # Buyer's market offer (weak: low price, many contingencies, low earnest)
    buyer_with_home = {
        "financing_status": "pre-approved",
        "budget_max": 400_000,
        "has_home_to_sell": True,
    }
    prop_stale = {"price": 500_000, "days_on_market": 70}
    result_weak = await advisor.analyze_offer_position(
        prop_stale, buyer_with_home, market_conditions={"market_type": "buyers"}
    )
    assert result_weak.competitive_assessment == "weak"


@pytest.mark.asyncio
async def test_closing_timeline_reasonable(advisor, base_property):
    """Cash=14d, sellers market=21d, standard=30d."""
    cash_buyer = {"financing_status": "cash", "budget_max": 600_000}
    result_cash = await advisor.analyze_offer_position(
        base_property, cash_buyer, market_conditions={"market_type": "balanced"}
    )
    assert result_cash.closing_timeline_days == 14

    financed_buyer = {"financing_status": "pre-approved", "budget_max": 600_000}
    result_sellers = await advisor.analyze_offer_position(
        base_property, financed_buyer, market_conditions={"market_type": "sellers"}
    )
    assert result_sellers.closing_timeline_days == 21

    result_standard = await advisor.analyze_offer_position(
        base_property, financed_buyer, market_conditions={"market_type": "balanced"}
    )
    assert result_standard.closing_timeline_days == 30