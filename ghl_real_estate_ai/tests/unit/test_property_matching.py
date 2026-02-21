"""Unit tests for JorgePropertyMatchingService — filtering and scoring logic."""

import pytest

pytest.importorskip("torch", reason="PyTorch not installed in CI environment")

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.models.jorge_property_models import (
    LeadPropertyPreferences,
    Property,
    PropertyAddress,
    PropertyFeatures,
    PropertyType,
)
from ghl_real_estate_ai.services.enhanced_smart_lead_scorer import (
    BuyingStage,
    LeadPriority,
    LeadScoreBreakdown,
)
from ghl_real_estate_ai.services.jorge_property_matching_service import (
    JorgePropertyMatchingService,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_property(
    *,
    id: str = "prop_test",
    price: float = 600000,
    bedrooms: int = 3,
    bathrooms: float = 2.0,
    zip_code: str = "91737",
    neighborhood: str = "Alta Loma",
    has_pool: bool = False,
    updated_kitchen: bool = False,
    granite_counters: bool = False,
    fireplace: bool = False,
) -> Property:
    """Build a minimal Property for testing."""
    return Property(
        id=id,
        tenant_id="t1",
        address=PropertyAddress(street="123 Test St", zip_code=zip_code, neighborhood=neighborhood),
        price=price,
        features=PropertyFeatures(
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            sqft=2000,
            has_pool=has_pool,
            updated_kitchen=updated_kitchen,
            granite_counters=granite_counters,
            fireplace=fireplace,
        ),
        property_type=PropertyType.SINGLE_FAMILY,
        days_on_market=10,
        price_per_sqft=round(price / 2000, 2),
        listing_date=datetime.now() - timedelta(days=10),
    )


def _make_lead_context(**overrides) -> LeadScoreBreakdown:
    defaults = dict(
        intent_score=50.0,
        financial_readiness=60.0,
        timeline_urgency=50.0,
        engagement_quality=50.0,
        referral_potential=50.0,
        local_connection=50.0,
        overall_score=50.0,
        priority_level=LeadPriority.MEDIUM,
        buying_stage=BuyingStage.GETTING_SERIOUS,
        recommended_actions=["Test"],
        jorge_talking_points=["Test"],
        risk_factors=[],
    )
    defaults.update(overrides)
    return LeadScoreBreakdown(**defaults)


@pytest.fixture
def service():
    """Create a JorgePropertyMatchingService with mocked dependencies."""
    with (
        patch(
            "ghl_real_estate_ai.services.jorge_property_matching_service.EnhancedSmartLeadScorer"
        ),
        patch(
            "ghl_real_estate_ai.services.jorge_property_matching_service.ClaudeAssistant"
        ),
    ):
        svc = JorgePropertyMatchingService()
    return svc


@pytest.fixture
def mock_inventory():
    """Standard set of 4 properties spanning different price/size/location."""
    return [
        _make_property(id="cheap", price=250000, bedrooms=2, bathrooms=1.5, zip_code="91730", neighborhood="Central Rancho"),
        _make_property(id="mid", price=500000, bedrooms=3, bathrooms=2.0, zip_code="91737", neighborhood="Alta Loma"),
        _make_property(id="upper", price=700000, bedrooms=4, bathrooms=3.0, zip_code="91739", neighborhood="Victoria Arbors"),
        _make_property(id="luxury", price=950000, bedrooms=5, bathrooms=4.0, zip_code="91737", neighborhood="Etiwanda Heights"),
    ]


# ---------------------------------------------------------------------------
# Change 1 — _get_real_inventory filtering tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_price_filter_excludes_over_budget(service, mock_inventory):
    """Properties above budget_max are excluded."""
    service._get_mock_inventory = AsyncMock(return_value=mock_inventory)
    prefs = LeadPropertyPreferences(budget_max=500000)

    result = await service._get_real_inventory("t1", prefs)

    ids = {p.id for p in result}
    assert "luxury" not in ids
    assert "upper" not in ids
    assert "mid" in ids
    assert "cheap" in ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_price_filter_excludes_under_min(service, mock_inventory):
    """Properties below budget_min are excluded."""
    service._get_mock_inventory = AsyncMock(return_value=mock_inventory)
    prefs = LeadPropertyPreferences(budget_min=300000)

    result = await service._get_real_inventory("t1", prefs)

    ids = {p.id for p in result}
    assert "cheap" not in ids
    assert "mid" in ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_bedroom_filter_allows_plus_minus_one(service, mock_inventory):
    """min_bedrooms=3 excludes 1BR but accepts 2BR (3-1=2)."""
    service._get_mock_inventory = AsyncMock(return_value=mock_inventory)
    prefs = LeadPropertyPreferences(min_bedrooms=3)

    result = await service._get_real_inventory("t1", prefs)

    ids = {p.id for p in result}
    # cheap has 2BR: 2 >= 3-1=2 → kept
    assert "cheap" in ids
    # mid has 3BR → kept
    assert "mid" in ids
    # upper has 4BR → kept
    assert "upper" in ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_zip_filter_restricts_results(service, mock_inventory):
    """Only properties in preferred_neighborhoods are returned."""
    service._get_mock_inventory = AsyncMock(return_value=mock_inventory)
    prefs = LeadPropertyPreferences(preferred_neighborhoods=["Alta Loma"])

    result = await service._get_real_inventory("t1", prefs)

    ids = {p.id for p in result}
    assert ids == {"mid"}  # Only Alta Loma property


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_filters_returns_all(service, mock_inventory):
    """No preference constraints returns the full mock inventory."""
    service._get_mock_inventory = AsyncMock(return_value=mock_inventory)
    prefs = LeadPropertyPreferences()

    result = await service._get_real_inventory("t1", prefs)

    assert len(result) == len(mock_inventory)


# ---------------------------------------------------------------------------
# Change 2 — must-have feature scoring tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_must_haves_full_match_adds_full_score(service):
    """All must-have features present → score contribution = 0.2."""
    prop = _make_property(has_pool=True, updated_kitchen=True)
    lead_ctx = _make_lead_context()
    prefs = LeadPropertyPreferences(
        must_have_features=["has_pool", "updated_kitchen"],
        preferred_bedrooms=3,
    )

    score = service._score_lifestyle_fit(prop, lead_ctx, prefs)

    # bedroom_match = 1.0 - 0/3 = 1.0 → 0.3 * 1.0 = 0.3
    # must_have: 2/2 = 1.0 → 0.2 * 1.0 = 0.2
    # neighborhood: Alta Loma is in premium_neighborhoods → elif branch = 0.2
    # property type: not set → 0
    # Total = 0.7
    assert abs(score - 0.7) < 0.01


@pytest.mark.unit
def test_must_haves_partial_match_prorates_score(service):
    """1 of 2 features present → contribution = 0.1."""
    prop = _make_property(has_pool=True, updated_kitchen=False)
    lead_ctx = _make_lead_context()
    prefs = LeadPropertyPreferences(
        must_have_features=["has_pool", "updated_kitchen"],
        preferred_bedrooms=3,
    )

    score = service._score_lifestyle_fit(prop, lead_ctx, prefs)

    # bedroom: 0.3, must_have: 0.5 * 0.2 = 0.1, neighborhood: 0.2, total = 0.6
    assert abs(score - 0.6) < 0.01


@pytest.mark.unit
def test_must_haves_no_match_adds_zero(service):
    """None of the must-have features present → contribution = 0.0."""
    prop = _make_property(has_pool=False, updated_kitchen=False, granite_counters=False)
    lead_ctx = _make_lead_context()
    prefs = LeadPropertyPreferences(
        must_have_features=["has_pool", "updated_kitchen"],
        preferred_bedrooms=3,
    )

    score = service._score_lifestyle_fit(prop, lead_ctx, prefs)

    # bedroom: 0.3, must_have: 0/2 = 0.0, neighborhood: 0.2, total = 0.5
    assert abs(score - 0.5) < 0.01
