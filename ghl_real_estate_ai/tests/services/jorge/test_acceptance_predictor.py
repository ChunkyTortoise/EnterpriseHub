"""
Tests for Seller Offer Acceptance Prediction Service

Validates rule-based heuristics, optimal price calculations, and caching behavior.
Tests cold-start scenarios and prepares for future XGBoost integration.

Author: Claude Code Assistant (ml-predictor-dev agent)
Created: 2026-02-10
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
    AcceptancePrediction,
    AcceptancePredictorService,
    ConfidenceLevel,
    FeatureImportance,
    OptimalPriceRange,
    PredictionMode,
    get_acceptance_predictor,
)


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    return mock


@pytest.fixture
def predictor_service(mock_cache_service):
    """Create predictor service with mocked cache."""
    with patch("ghl_real_estate_ai.services.jorge.acceptance_predictor.get_cache_service") as mock_get_cache:
        mock_get_cache.return_value = mock_cache_service
        service = AcceptancePredictorService(
            force_rule_based=True,  # Force rule-based for testing
            enable_caching=True,
        )
        yield service


@pytest.fixture
def seller_state_hot():
    """High-quality seller with strong acceptance signals."""
    return {
        "seller_id": "seller_001",
        "psychological_commitment": 85.0,
        "listing_price_recommendation": 500000.0,
        "estimated_value": 495000.0,
        "seller_intent_profile": {
            "motivation_strength": 80.0,
            "listing_urgency": 75.0,
        },
    }


@pytest.fixture
def seller_state_cold():
    """Low-quality seller with weak acceptance signals."""
    return {
        "seller_id": "seller_002",
        "psychological_commitment": 30.0,
        "listing_price_recommendation": 600000.0,
        "seller_intent_profile": {
            "motivation_strength": 35.0,
            "listing_urgency": 25.0,
        },
    }


@pytest.fixture
def seller_state_minimal():
    """Minimal seller state with insufficient data."""
    return {"seller_id": "seller_003"}


# ============================================================================
# BASIC PREDICTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_predict_hot_seller_high_offer(predictor_service, seller_state_hot):
    """Test prediction for hot seller with strong offer (95% of listing)."""
    prediction = await predictor_service.predict_acceptance_probability(
        seller_id="seller_001",
        offer_price=475000,  # 95% of $500k listing
        seller_state=seller_state_hot,
    )

    assert isinstance(prediction, AcceptancePrediction)
    assert prediction.seller_id == "seller_001"
    assert prediction.offer_price == 475000
    assert prediction.acceptance_probability > 0.75  # Should be high
    assert prediction.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]
    assert prediction.prediction_mode == PredictionMode.RULE_BASED
    assert not prediction.cached
    assert len(prediction.key_factors) == 3
    assert len(prediction.feature_importances) == 4


@pytest.mark.asyncio
async def test_predict_cold_seller_low_offer(predictor_service, seller_state_cold):
    """Test prediction for cold seller with low offer (75% of listing)."""
    prediction = await predictor_service.predict_acceptance_probability(
        seller_id="seller_002",
        offer_price=450000,  # 75% of $600k listing
        seller_state=seller_state_cold,
    )

    assert prediction.acceptance_probability < 0.50  # Should be low
    assert prediction.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM]
    assert prediction.data_sufficiency in ["limited", "sufficient"]


@pytest.mark.asyncio
async def test_predict_minimal_data(predictor_service, seller_state_minimal):
    """Test prediction with minimal seller data."""
    prediction = await predictor_service.predict_acceptance_probability(
        seller_id="seller_003",
        offer_price=400000,
        seller_state=seller_state_minimal,
    )

    assert prediction.acceptance_probability > 0.0
    assert prediction.data_sufficiency == "insufficient"
    assert prediction.confidence_level == ConfidenceLevel.LOW


@pytest.mark.asyncio
async def test_predict_no_seller_state(predictor_service):
    """Test prediction without seller state (cold start)."""
    prediction = await predictor_service.predict_acceptance_probability(
        seller_id="seller_004",
        offer_price=500000,
        seller_state=None,
    )

    assert prediction.acceptance_probability > 0.0
    assert prediction.data_sufficiency == "insufficient"


# ============================================================================
# PRICE RATIO IMPACT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_price_ratio_impact(predictor_service, seller_state_hot):
    """Test that higher offer prices increase acceptance probability."""
    # Test multiple price points
    prices = [400000, 450000, 475000, 490000]  # 80%, 90%, 95%, 98% of $500k
    predictions = []

    for price in prices:
        pred = await predictor_service.predict_acceptance_probability(
            seller_id="seller_001",
            offer_price=price,
            seller_state=seller_state_hot,
        )
        predictions.append(pred)

    # Probabilities should increase with price
    probabilities = [p.acceptance_probability for p in predictions]
    assert probabilities == sorted(probabilities), "Probability should increase with offer price"


# ============================================================================
# OPTIMAL PRICE RANGE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_optimal_price_range_default_target(predictor_service, seller_state_hot):
    """Test optimal price range calculation with default 75% target."""
    price_range = await predictor_service.get_optimal_price_range(
        seller_id="seller_001",
        seller_state=seller_state_hot,
    )

    assert isinstance(price_range, OptimalPriceRange)
    assert price_range.target_probability == 0.75
    assert price_range.min_price < price_range.max_price
    assert price_range.min_price <= price_range.recommended_price <= price_range.max_price
    assert len(price_range.price_steps) == 16  # 0 to 15 inclusive
    assert price_range.confidence_score > 0.0


@pytest.mark.asyncio
async def test_get_optimal_price_range_high_target(predictor_service, seller_state_hot):
    """Test optimal price range with high target probability (90%)."""
    price_range = await predictor_service.get_optimal_price_range(
        seller_id="seller_001",
        target_probability=0.90,
        seller_state=seller_state_hot,
    )

    assert price_range.target_probability == 0.90
    # Higher target should push recommended price higher
    assert price_range.recommended_price > 0


@pytest.mark.asyncio
async def test_get_optimal_price_range_invalid_target(predictor_service, seller_state_hot):
    """Test that invalid target probability raises ValueError."""
    with pytest.raises(ValueError, match="target_probability must be in"):
        await predictor_service.get_optimal_price_range(
            seller_id="seller_001",
            target_probability=1.5,  # Invalid
            seller_state=seller_state_hot,
        )


# ============================================================================
# EXPLANATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_explain_prediction(predictor_service, seller_state_hot):
    """Test prediction explanation generation."""
    explanation = await predictor_service.explain_prediction(
        seller_id="seller_001",
        offer_price=475000,
        seller_state=seller_state_hot,
    )

    assert isinstance(explanation, dict)
    assert explanation["seller_id"] == "seller_001"
    assert explanation["offer_price"] == 475000
    assert "acceptance_probability" in explanation
    assert "confidence_level" in explanation
    assert "feature_importances" in explanation
    assert "key_factors" in explanation
    assert "explanation_text" in explanation
    assert "data_sufficiency" in explanation

    # Check explanation text structure
    assert "Predicted acceptance probability:" in explanation["explanation_text"]
    assert "Key factors:" in explanation["explanation_text"]
    assert "Recommended offer:" in explanation["explanation_text"]


# ============================================================================
# FEATURE EXTRACTION TESTS
# ============================================================================


def test_extract_pcs_score(predictor_service, seller_state_hot):
    """Test PCS score extraction from seller state."""
    pcs = predictor_service._extract_pcs_score(seller_state_hot)
    assert pcs == 85.0


def test_extract_pcs_score_nested(predictor_service):
    """Test PCS extraction from nested intent_profile."""
    state = {"intent_profile": {"pcs": {"total_score": 70.0}}}
    pcs = predictor_service._extract_pcs_score(state)
    assert pcs == 70.0


def test_extract_pcs_score_missing(predictor_service):
    """Test PCS extraction with missing data."""
    pcs = predictor_service._extract_pcs_score({})
    assert pcs == 50.0  # Default


def test_extract_listing_price(predictor_service, seller_state_hot):
    """Test listing price extraction."""
    price = predictor_service._extract_listing_price(seller_state_hot)
    assert price == 500000.0


def test_extract_property_value(predictor_service, seller_state_hot):
    """Test property value extraction."""
    value = predictor_service._extract_property_value(seller_state_hot)
    assert value == 495000.0


def test_extract_motivation_strength(predictor_service, seller_state_hot):
    """Test motivation strength extraction."""
    motivation = predictor_service._extract_motivation_strength(seller_state_hot)
    assert motivation == 80.0


def test_extract_timeline_urgency(predictor_service, seller_state_hot):
    """Test timeline urgency extraction."""
    timeline = predictor_service._extract_timeline_urgency(seller_state_hot)
    assert timeline == 75.0


# ============================================================================
# CONFIDENCE CLASSIFICATION TESTS
# ============================================================================


def test_classify_confidence_high(predictor_service, seller_state_hot):
    """Test high confidence classification."""
    confidence = predictor_service._classify_confidence(0.85, seller_state_hot)
    assert confidence == ConfidenceLevel.HIGH


def test_classify_confidence_medium(predictor_service, seller_state_hot):
    """Test medium confidence classification."""
    confidence = predictor_service._classify_confidence(0.65, seller_state_hot)
    assert confidence == ConfidenceLevel.MEDIUM


def test_classify_confidence_low(predictor_service, seller_state_hot):
    """Test low confidence classification."""
    confidence = predictor_service._classify_confidence(0.50, seller_state_hot)
    assert confidence == ConfidenceLevel.LOW


def test_classify_confidence_insufficient_data(predictor_service):
    """Test that insufficient data forces low confidence."""
    confidence = predictor_service._classify_confidence(0.85, {})
    assert confidence == ConfidenceLevel.LOW


# ============================================================================
# DATA SUFFICIENCY TESTS
# ============================================================================


def test_assess_data_sufficiency_sufficient(predictor_service, seller_state_hot):
    """Test sufficient data assessment."""
    sufficiency = predictor_service._assess_data_sufficiency(seller_state_hot)
    assert sufficiency == "sufficient"


def test_assess_data_sufficiency_limited(predictor_service):
    """Test limited data assessment."""
    state = {
        "psychological_commitment": 60.0,  # Non-default
        "listing_price_recommendation": 500000.0,  # Has price
        # Missing motivation (defaults to 50.0)
    }
    sufficiency = predictor_service._assess_data_sufficiency(state)
    assert sufficiency == "limited"  # 2 out of 3 data points


def test_assess_data_sufficiency_insufficient(predictor_service):
    """Test insufficient data assessment."""
    sufficiency = predictor_service._assess_data_sufficiency({})
    assert sufficiency == "insufficient"


def test_assess_data_sufficiency_none(predictor_service):
    """Test None state assessment."""
    sufficiency = predictor_service._assess_data_sufficiency(None)
    assert sufficiency == "insufficient"


# ============================================================================
# CACHING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_caching_enabled(mock_cache_service):
    """Test that predictions are cached when caching is enabled."""
    with patch("ghl_real_estate_ai.services.jorge.acceptance_predictor.get_cache_service") as mock_get_cache:
        mock_get_cache.return_value = mock_cache_service
        service = AcceptancePredictorService(force_rule_based=True, enable_caching=True)

        await service.predict_acceptance_probability(
            seller_id="seller_001",
            offer_price=475000,
            seller_state={"psychological_commitment": 70.0},
        )

        # Verify cache.set was called
        mock_cache_service.set.assert_called_once()


@pytest.mark.asyncio
async def test_cache_hit(mock_cache_service, seller_state_hot):
    """Test cache hit returns cached prediction."""
    import json

    # Setup cached prediction
    cached_prediction = {
        "seller_id": "seller_001",
        "offer_price": 475000,
        "acceptance_probability": 0.82,
        "confidence_level": "high",
        "prediction_mode": "rule_based",
        "optimal_price_range": [470000, 490000],
        "recommended_offer": 480000,
        "expected_value": 389500,
        "feature_importances": [],
        "key_factors": ["Strong offer"],
        "prediction_timestamp": "2026-02-10T12:00:00",
        "model_version": "rule_based_v1.0",
        "data_sufficiency": "sufficient",
        "confidence_interval": [0.70, 0.94],
    }

    mock_cache_service.get = AsyncMock(return_value=json.dumps(cached_prediction))

    with patch("ghl_real_estate_ai.services.jorge.acceptance_predictor.get_cache_service") as mock_get_cache:
        mock_get_cache.return_value = mock_cache_service
        service = AcceptancePredictorService(force_rule_based=True, enable_caching=True)

        prediction = await service.predict_acceptance_probability(
            seller_id="seller_001",
            offer_price=475000,
            seller_state=seller_state_hot,
        )

        assert prediction.cached
        assert prediction.acceptance_probability == 0.82


@pytest.mark.asyncio
async def test_caching_disabled():
    """Test that caching can be disabled."""
    service = AcceptancePredictorService(force_rule_based=True, enable_caching=False)
    assert service.cache_service is None


# ============================================================================
# VALIDATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_invalid_seller_id(predictor_service):
    """Test that empty seller_id raises ValueError."""
    with pytest.raises(ValueError, match="seller_id is required"):
        await predictor_service.predict_acceptance_probability(
            seller_id="",
            offer_price=500000,
        )


@pytest.mark.asyncio
async def test_invalid_offer_price_negative(predictor_service):
    """Test that negative offer price raises ValueError."""
    with pytest.raises(ValueError, match="Invalid offer_price"):
        await predictor_service.predict_acceptance_probability(
            seller_id="seller_001",
            offer_price=-100000,
        )


@pytest.mark.asyncio
async def test_invalid_offer_price_zero(predictor_service):
    """Test that zero offer price raises ValueError."""
    with pytest.raises(ValueError, match="Invalid offer_price"):
        await predictor_service.predict_acceptance_probability(
            seller_id="seller_001",
            offer_price=0,
        )


# ============================================================================
# KEY FACTORS GENERATION TESTS
# ============================================================================


def test_generate_key_factors_strong_offer(predictor_service):
    """Test key factors for strong offer."""
    factors = predictor_service._generate_key_factors(
        price_ratio=0.97,
        pcs=80.0,
        motivation=75.0,
        timeline=70.0,
    )

    assert len(factors) == 3
    assert any("Strong offer" in f for f in factors)
    assert any("High seller engagement" in f for f in factors)


def test_generate_key_factors_weak_offer(predictor_service):
    """Test key factors for weak offer."""
    factors = predictor_service._generate_key_factors(
        price_ratio=0.75,
        pcs=35.0,
        motivation=30.0,
        timeline=25.0,
    )

    assert len(factors) == 3
    assert any("Below-market offer" in f for f in factors)
    assert any("Low seller engagement" in f for f in factors)


# ============================================================================
# SIGMOID SCORE TESTS
# ============================================================================


def test_sigmoid_score(predictor_service):
    """Test sigmoid scoring function."""
    # At midpoint, should be ~0.5
    score_mid = predictor_service._sigmoid_score(0.90, midpoint=0.90, steepness=20)
    assert 0.45 < score_mid < 0.55

    # Above midpoint, should be higher
    score_high = predictor_service._sigmoid_score(0.95, midpoint=0.90, steepness=20)
    assert score_high > 0.70

    # Below midpoint, should be lower
    score_low = predictor_service._sigmoid_score(0.80, midpoint=0.90, steepness=20)
    assert score_low < 0.30


# ============================================================================
# FACTORY FUNCTION TEST
# ============================================================================


def test_get_acceptance_predictor_factory():
    """Test factory function creates service correctly."""
    service = get_acceptance_predictor(
        enable_caching=False,
        force_rule_based=True,
    )

    assert isinstance(service, AcceptancePredictorService)
    assert service.force_rule_based
    assert not service.enable_caching


# ============================================================================
# INTEGRATION TEST
# ============================================================================


@pytest.mark.asyncio
async def test_full_workflow_integration(predictor_service, seller_state_hot):
    """Test complete prediction workflow: predict → explain → optimize."""
    # Step 1: Get prediction
    prediction = await predictor_service.predict_acceptance_probability(
        seller_id="seller_001",
        offer_price=475000,
        seller_state=seller_state_hot,
    )

    assert prediction.acceptance_probability > 0.0

    # Step 2: Get explanation
    explanation = await predictor_service.explain_prediction(
        seller_id="seller_001",
        offer_price=475000,
        seller_state=seller_state_hot,
    )

    assert explanation["acceptance_probability"] == prediction.acceptance_probability

    # Step 3: Get optimal price range
    price_range = await predictor_service.get_optimal_price_range(
        seller_id="seller_001",
        target_probability=0.75,
        seller_state=seller_state_hot,
    )

    assert price_range.min_price > 0
    assert price_range.recommended_price > 0
