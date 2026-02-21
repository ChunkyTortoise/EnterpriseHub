import pytest

pytestmark = pytest.mark.integration

"""Tests for XGBoost Life-Event Propensity Engine."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.xgboost_propensity_engine import (
    LIFE_EVENT_CONVERSION_RATES,
    LifeEventSignal,
    LifeEventType,
    PropensityScore,
    XGBoostPropensityEngine,
)


@pytest.fixture
def engine():
    return XGBoostPropensityEngine()


@pytest.fixture
def mock_attom_dna():
    return {
        "address": "123 Haven Ave, Rancho Cucamonga",
        "characteristics": {"bedrooms": 4, "bathrooms": 3, "sqft": 2800},
        "assessment": {"market_value": 750000, "tax_amount": 12000},
        "summary": {"absentee_owner": True, "years_owned": 15, "last_transfer_date": "2011-03-15"},
    }


@pytest.fixture
def mock_attom_triggers():
    return {
        "probate": True,
        "tax_delinquent": False,
        "liens": 0,
        "last_transfer_date": "2011-03-15",
    }


# -------------------------------------------------------------------------
# Life event detection
# -------------------------------------------------------------------------


class TestLifeEventDetection:
    @pytest.mark.asyncio
    async def test_probate_detected(self, engine, mock_attom_dna, mock_attom_triggers):
        with patch("ghl_real_estate_ai.services.attom_client.get_attom_client") as mock_get:
            client = MagicMock()
            client.get_property_dna = AsyncMock(return_value=mock_attom_dna)
            client.get_life_event_triggers = AsyncMock(return_value=mock_attom_triggers)
            mock_get.return_value = client

            events = await engine._detect_life_events("123 Haven Ave")
            probate = [e for e in events if e.event_type == LifeEventType.PROBATE]
            assert len(probate) == 1
            assert probate[0].confidence >= 0.85

    @pytest.mark.asyncio
    async def test_absentee_owner_detected(self, engine, mock_attom_dna, mock_attom_triggers):
        with patch("ghl_real_estate_ai.services.attom_client.get_attom_client") as mock_get:
            client = MagicMock()
            client.get_property_dna = AsyncMock(return_value=mock_attom_dna)
            client.get_life_event_triggers = AsyncMock(return_value=mock_attom_triggers)
            mock_get.return_value = client

            events = await engine._detect_life_events("123 Haven Ave")
            absentee = [e for e in events if e.event_type == LifeEventType.ABSENTEE_OWNER]
            assert len(absentee) == 1

    @pytest.mark.asyncio
    async def test_long_ownership_detected(self, engine, mock_attom_dna, mock_attom_triggers):
        with patch("ghl_real_estate_ai.services.attom_client.get_attom_client") as mock_get:
            client = MagicMock()
            client.get_property_dna = AsyncMock(return_value=mock_attom_dna)
            client.get_life_event_triggers = AsyncMock(return_value=mock_attom_triggers)
            mock_get.return_value = client

            events = await engine._detect_life_events("123 Haven Ave")
            long_own = [e for e in events if e.event_type == LifeEventType.LONG_OWNERSHIP]
            assert len(long_own) == 1
            assert long_own[0].details["years_owned"] == 15

    @pytest.mark.asyncio
    async def test_pre_foreclosure_from_liens(self, engine):
        dna = {"summary": {"absentee_owner": False, "years_owned": 3}}
        triggers = {"probate": False, "tax_delinquent": False, "liens": 3}

        with patch("ghl_real_estate_ai.services.attom_client.get_attom_client") as mock_get:
            client = MagicMock()
            client.get_property_dna = AsyncMock(return_value=dna)
            client.get_life_event_triggers = AsyncMock(return_value=triggers)
            mock_get.return_value = client

            events = await engine._detect_life_events("456 Main St")
            foreclosure = [e for e in events if e.event_type == LifeEventType.PRE_FORECLOSURE]
            assert len(foreclosure) == 1
            assert foreclosure[0].confidence >= 0.80

    @pytest.mark.asyncio
    async def test_no_address_returns_empty(self, engine):
        events = await engine._detect_life_events(None)
        assert events == []


# -------------------------------------------------------------------------
# Scoring
# -------------------------------------------------------------------------


class TestPropensityScoring:
    @pytest.mark.asyncio
    async def test_score_with_life_events(self, engine, mock_attom_dna, mock_attom_triggers):
        with patch("ghl_real_estate_ai.services.attom_client.get_attom_client") as mock_get:
            client = MagicMock()
            client.get_property_dna = AsyncMock(return_value=mock_attom_dna)
            client.get_life_event_triggers = AsyncMock(return_value=mock_attom_triggers)
            mock_get.return_value = client

            score = await engine.score_lead(
                contact_id="c_1",
                address="123 Haven Ave",
                conversation_context={"message_count": 10, "engagement_score": 0.8},
            )
            assert isinstance(score, PropensityScore)
            assert score.conversion_probability > 0
            assert score.primary_event == LifeEventType.PROBATE

    @pytest.mark.asyncio
    async def test_score_without_address(self, engine):
        score = await engine.score_lead(
            contact_id="c_2",
            conversation_context={"message_count": 5, "engagement_score": 0.5},
        )
        assert score.conversion_probability >= 0.05
        assert score.life_events == []

    @pytest.mark.asyncio
    async def test_temperature_classification(self, engine):
        assert engine._classify_temperature(0.85) == "hot"
        assert engine._classify_temperature(0.55) == "warm"
        assert engine._classify_temperature(0.20) == "cold"

    @pytest.mark.asyncio
    async def test_scoring_latency_tracked(self, engine):
        score = await engine.score_lead(contact_id="c_3")
        assert score.scoring_latency_ms >= 0

    @pytest.mark.asyncio
    async def test_cache_returns_same_score(self, engine):
        score1 = await engine.score_lead(contact_id="c_cache")
        score2 = await engine.score_lead(contact_id="c_cache")
        assert score1.conversion_probability == score2.conversion_probability


# -------------------------------------------------------------------------
# Timeline prediction
# -------------------------------------------------------------------------


class TestTimelinePrediction:
    def test_urgent_events_immediate(self, engine):
        events = [
            LifeEventSignal(
                event_type=LifeEventType.PROBATE,
                detected=True,
                confidence=0.9,
                source="attom",
            )
        ]
        assert engine._predict_timeline(0.5, events) == "immediate"

    def test_high_probability_immediate(self, engine):
        assert engine._predict_timeline(0.85, []) == "immediate"

    def test_moderate_probability_30_days(self, engine):
        assert engine._predict_timeline(0.65, []) == "30_days"

    def test_low_probability_long_term(self, engine):
        assert engine._predict_timeline(0.15, []) == "long_term"


# -------------------------------------------------------------------------
# Recommended approach
# -------------------------------------------------------------------------


class TestApproachRecommendation:
    def test_probate_approach(self, engine):
        approach = engine._recommend_approach(LifeEventType.PROBATE, "hot")
        assert "empathetic" in approach.lower()

    def test_divorce_approach(self, engine):
        approach = engine._recommend_approach(LifeEventType.DIVORCE, "warm")
        assert "neutral" in approach.lower()

    def test_hot_no_event(self, engine):
        approach = engine._recommend_approach(None, "hot")
        assert "qualification" in approach.lower() or "direct" in approach.lower()

    def test_cold_no_event(self, engine):
        approach = engine._recommend_approach(None, "cold")
        assert "drip" in approach.lower() or "long-term" in approach.lower()


# -------------------------------------------------------------------------
# Heuristic scoring
# -------------------------------------------------------------------------


class TestHeuristicScoring:
    def test_heuristic_with_probate(self, engine):
        import numpy as np

        events = [
            LifeEventSignal(
                event_type=LifeEventType.PROBATE,
                detected=True,
                confidence=0.90,
                source="attom",
            )
        ]
        features = np.zeros(26)
        score = engine._heuristic_score(events, features)
        assert score > 0.30  # Probate has 0.85 base rate

    def test_heuristic_bounded(self, engine):
        import numpy as np

        events = [
            LifeEventSignal(
                event_type=LifeEventType.PROBATE,
                detected=True,
                confidence=1.0,
                source="attom",
            )
        ]
        features = np.ones(26)
        score = engine._heuristic_score(events, features)
        assert 0.0 <= score <= 1.0

    def test_heuristic_minimum(self, engine):
        import numpy as np

        score = engine._heuristic_score([], np.zeros(26))
        assert score >= 0.05


# -------------------------------------------------------------------------
# Feature construction
# -------------------------------------------------------------------------


class TestFeatureConstruction:
    def test_feature_vector_length(self, engine):
        events = [
            LifeEventSignal(
                event_type=LifeEventType.PROBATE,
                detected=True,
                confidence=0.9,
                source="attom",
            )
        ]
        vec = engine._build_feature_vector(events, {}, {})
        assert len(vec) == 26

    def test_feature_vector_normalised(self, engine):
        vec = engine._build_feature_vector([], {"message_count": 100}, {})
        assert all(0.0 <= v <= 1.5 for v in vec)  # Allows slight overshoot from market_value


# -------------------------------------------------------------------------
# Cache
# -------------------------------------------------------------------------


class TestCacheManagement:
    def test_clear_cache(self, engine):
        engine._cache["propensity:x"] = PropensityScore(
            contact_id="x",
            conversion_probability=0.5,
            confidence=0.5,
            temperature="warm",
        )
        engine.clear_cache()
        assert len(engine._cache) == 0
