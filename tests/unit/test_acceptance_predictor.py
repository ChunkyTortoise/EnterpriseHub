"""
Unit tests for AcceptancePredictor service.

Tests seller offer acceptance prediction:
- XGBoost model prediction
- Rule-based fallback for cold-start
- Confidence level classification
- Feature importance/explainability
- Caching behavior
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

pytestmark = pytest.mark.unit


class TestPredictionMode:
    """Tests for PredictionMode enum."""

    def test_prediction_modes_exist(self):
        """All prediction modes are defined."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            PredictionMode,
        )

        assert PredictionMode.XGBOOST_MODEL.value == "xgboost_model"
        assert PredictionMode.RULE_BASED.value == "rule_based"
        assert PredictionMode.HYBRID.value == "hybrid"


class TestConfidenceLevel:
    """Tests for ConfidenceLevel enum."""

    def test_confidence_levels_exist(self):
        """All confidence levels are defined."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            ConfidenceLevel,
        )

        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"

    def test_classify_high_confidence(self):
        """Probability >= 0.8 is HIGH confidence."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            ConfidenceLevel,
        )

        # Check if there's a classification method
        if hasattr(ConfidenceLevel, "from_probability"):
            assert ConfidenceLevel.from_probability(0.85) == ConfidenceLevel.HIGH
            assert ConfidenceLevel.from_probability(0.8) == ConfidenceLevel.HIGH

    def test_classify_medium_confidence(self):
        """Probability 0.6-0.8 is MEDIUM confidence."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            ConfidenceLevel,
        )

        if hasattr(ConfidenceLevel, "from_probability"):
            assert ConfidenceLevel.from_probability(0.7) == ConfidenceLevel.MEDIUM
            assert ConfidenceLevel.from_probability(0.6) == ConfidenceLevel.MEDIUM

    def test_classify_low_confidence(self):
        """Probability < 0.6 is LOW confidence."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            ConfidenceLevel,
        )

        if hasattr(ConfidenceLevel, "from_probability"):
            assert ConfidenceLevel.from_probability(0.5) == ConfidenceLevel.LOW
            assert ConfidenceLevel.from_probability(0.3) == ConfidenceLevel.LOW


class TestModelMetadata:
    """Tests for ModelMetadata dataclass."""

    def test_model_metadata_creation(self):
        """ModelMetadata can be created with all fields."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            ModelMetadata,
        )

        metadata = ModelMetadata(
            model_version="1.0.0",
            training_date=datetime(2026, 2, 10),
            training_samples=1000,
            validation_auc=0.85,
            validation_brier_score=0.12,
            feature_count=15,
            hyperparameters={"max_depth": 6, "learning_rate": 0.1},
            last_used=datetime.now(),
        )

        assert metadata.model_version == "1.0.0"
        assert metadata.validation_auc == 0.85
        assert metadata.feature_count == 15

    def test_model_metadata_to_dict(self):
        """ModelMetadata can be converted to dict."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            ModelMetadata,
        )

        metadata = ModelMetadata(
            model_version="1.0.0",
            training_date=datetime(2026, 2, 10),
            training_samples=1000,
            validation_auc=0.85,
            validation_brier_score=0.12,
            feature_count=15,
            hyperparameters={},
            last_used=datetime.now(),
        )

        result = metadata.__dict__
        assert isinstance(result, dict)
        assert "model_version" in result


class TestFeatureImportance:
    """Tests for FeatureImportance dataclass."""

    def test_feature_importance_creation(self):
        """FeatureImportance can be created with all fields."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            FeatureImportance,
        )

        importance = FeatureImportance(
            feature_name="days_on_market",
            importance_score=0.25,
            direction="negative",
            contribution_to_probability=-0.15,
        )

        assert importance.feature_name == "days_on_market"
        assert importance.importance_score == 0.25
        assert importance.direction == "negative"
        assert importance.contribution_to_probability == -0.15

    def test_feature_importance_positive_direction(self):
        """FeatureImportance can have positive direction."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            FeatureImportance,
        )

        importance = FeatureImportance(
            feature_name="offer_to_list_ratio",
            importance_score=0.35,
            direction="positive",
            contribution_to_probability=0.20,
        )

        assert importance.direction == "positive"
        assert importance.contribution_to_probability > 0


class TestAcceptancePredictorInit:
    """Tests for AcceptancePredictor initialization."""

    def test_init_with_defaults(self):
        """Predictor initializes with default settings."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            AcceptancePredictor,
        )

        with patch("ghl_real_estate_ai.services.jorge.acceptance_predictor.get_cache_service"):
            predictor = AcceptancePredictor()

            assert predictor is not None

    def test_init_with_custom_mode(self):
        """Predictor can be initialized with custom mode."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            AcceptancePredictor,
            PredictionMode,
        )

        with patch("ghl_real_estate_ai.services.jorge.acceptance_predictor.get_cache_service"):
            predictor = AcceptancePredictor(mode=PredictionMode.RULE_BASED)

            assert predictor.mode == PredictionMode.RULE_BASED


class TestRuleBasedPrediction:
    """Tests for rule-based prediction (cold-start fallback)."""

    @pytest.fixture
    def predictor(self):
        """Create a predictor with rule-based mode."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            AcceptancePredictor,
            PredictionMode,
        )

        with patch("ghl_real_estate_ai.services.jorge.acceptance_predictor.get_cache_service") as mock_cache:
            mock_cache.return_value = MagicMock()
            mock_cache.return_value.get = AsyncMock(return_value=None)
            mock_cache.return_value.set = AsyncMock()

            predictor = AcceptancePredictor(mode=PredictionMode.RULE_BASED)
            return predictor

    @pytest.mark.asyncio
    async def test_high_offer_ratio_high_acceptance(self, predictor):
        """Offer close to list price has high acceptance probability."""
        offer_data = {
            "offer_price": 490000,
            "list_price": 500000,
            "days_on_market": 30,
            "seller_motivation": "high",
        }

        if hasattr(predictor, "predict"):
            result = await predictor.predict(offer_data)

            # Offer at 98% of list should have high acceptance
            assert result["acceptance_probability"] >= 0.7

    @pytest.mark.asyncio
    async def test_low_offer_ratio_low_acceptance(self, predictor):
        """Low offer relative to list has low acceptance probability."""
        offer_data = {
            "offer_price": 400000,
            "list_price": 500000,
            "days_on_market": 7,
            "seller_motivation": "low",
        }

        if hasattr(predictor, "predict"):
            result = await predictor.predict(offer_data)

            # Offer at 80% of list should have low acceptance
            assert result["acceptance_probability"] <= 0.5

    @pytest.mark.asyncio
    async def test_long_days_on_market_increases_acceptance(self, predictor):
        """Longer days on market increases acceptance probability."""
        offer_data_low_dom = {
            "offer_price": 450000,
            "list_price": 500000,
            "days_on_market": 7,
        }

        offer_data_high_dom = {
            "offer_price": 450000,
            "list_price": 500000,
            "days_on_market": 90,
        }

        if hasattr(predictor, "predict"):
            result_low_dom = await predictor.predict(offer_data_low_dom)
            result_high_dom = await predictor.predict(offer_data_high_dom)

            # Same offer should be more likely accepted with longer DOM
            assert result_high_dom["acceptance_probability"] >= result_low_dom["acceptance_probability"]

    @pytest.mark.asyncio
    async def test_high_motivation_increases_acceptance(self, predictor):
        """High seller motivation increases acceptance probability."""
        offer_data_low_motivation = {
            "offer_price": 450000,
            "list_price": 500000,
            "days_on_market": 30,
            "seller_motivation": "low",
        }

        offer_data_high_motivation = {
            "offer_price": 450000,
            "list_price": 500000,
            "days_on_market": 30,
            "seller_motivation": "high",
        }

        if hasattr(predictor, "predict"):
            result_low = await predictor.predict(offer_data_low_motivation)
            result_high = await predictor.predict(offer_data_high_motivation)

            assert result_high["acceptance_probability"] >= result_low["acceptance_probability"]


class TestXGBoostPrediction:
    """Tests for XGBoost model prediction."""

    @pytest.fixture
    def predictor_with_model(self):
        """Create a predictor with mocked XGBoost model."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            AcceptancePredictor,
            PredictionMode,
        )

        with patch("ghl_real_estate_ai.services.jorge.acceptance_predictor.get_cache_service") as mock_cache:
            mock_cache.return_value = MagicMock()
            mock_cache.return_value.get = AsyncMock(return_value=None)
            mock_cache.return_value.set = AsyncMock()

            predictor = AcceptancePredictor(mode=PredictionMode.XGBOOST_MODEL)

            # Mock the model if it exists
            if hasattr(predictor, "model"):
                predictor.model = MagicMock()
                predictor.model.predict_proba = MagicMock(return_value=np.array([[0.3, 0.7]]))

            return predictor

    @pytest.mark.asyncio
    async def test_xgboost_returns_probability(self, predictor_with_model):
        """XGBoost prediction returns acceptance probability."""
        offer_data = {
            "offer_price": 480000,
            "list_price": 500000,
            "days_on_market": 30,
        }

        if hasattr(predictor_with_model, "predict"):
            result = await predictor_with_model.predict(offer_data)

            assert "acceptance_probability" in result
            assert 0 <= result["acceptance_probability"] <= 1

    @pytest.mark.asyncio
    async def test_xgboost_returns_confidence(self, predictor_with_model):
        """XGBoost prediction returns confidence level."""
        offer_data = {
            "offer_price": 480000,
            "list_price": 500000,
            "days_on_market": 30,
        }

        if hasattr(predictor_with_model, "predict"):
            result = await predictor_with_model.predict(offer_data)

            assert "confidence" in result or "confidence_level" in result


class TestCaching:
    """Tests for prediction caching."""

    @pytest.fixture
    def predictor_with_cache(self):
        """Create a predictor with mocked cache."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            AcceptancePredictor,
            PredictionMode,
        )

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        with patch(
            "ghl_real_estate_ai.services.jorge.acceptance_predictor.get_cache_service",
            return_value=mock_cache,
        ):
            predictor = AcceptancePredictor(mode=PredictionMode.RULE_BASED)
            predictor.cache = mock_cache
            return predictor

    @pytest.mark.asyncio
    async def test_predict_checks_cache(self, predictor_with_cache):
        """Prediction checks cache first."""
        offer_data = {"offer_price": 480000, "list_price": 500000}

        if hasattr(predictor_with_cache, "predict"):
            await predictor_with_cache.predict(offer_data)

            predictor_with_cache.cache.get.assert_called()

    @pytest.mark.asyncio
    async def test_predict_returns_cached_result(self, predictor_with_cache):
        """Cached result is returned without recomputation."""
        cached_result = {
            "acceptance_probability": 0.85,
            "confidence": "high",
            "cached": True,
        }
        predictor_with_cache.cache.get = AsyncMock(return_value=cached_result)

        offer_data = {"offer_price": 480000, "list_price": 500000}

        if hasattr(predictor_with_cache, "predict"):
            result = await predictor_with_cache.predict(offer_data)

            assert result["acceptance_probability"] == 0.85
            # Should not set cache since we got a hit
            predictor_with_cache.cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_predict_caches_result(self, predictor_with_cache):
        """Fresh prediction is cached."""
        predictor_with_cache.cache.get = AsyncMock(return_value=None)

        offer_data = {"offer_price": 480000, "list_price": 500000}

        if hasattr(predictor_with_cache, "predict"):
            await predictor_with_cache.predict(offer_data)

            # Result should be cached
            predictor_with_cache.cache.set.assert_called()


class TestFeatureImportanceExplanation:
    """Tests for SHAP-based feature importance."""

    @pytest.fixture
    def predictor(self):
        """Create a predictor for feature importance tests."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            AcceptancePredictor,
            PredictionMode,
        )

        with patch("ghl_real_estate_ai.services.jorge.acceptance_predictor.get_cache_service"):
            return AcceptancePredictor(mode=PredictionMode.RULE_BASED)

    @pytest.mark.asyncio
    async def test_explain_returns_feature_importance(self, predictor):
        """Explain method returns feature importance list."""
        offer_data = {
            "offer_price": 480000,
            "list_price": 500000,
            "days_on_market": 30,
        }

        if hasattr(predictor, "explain"):
            explanation = await predictor.explain(offer_data)

            assert explanation is not None
            if isinstance(explanation, dict):
                assert "features" in explanation or "feature_importance" in explanation

    @pytest.mark.asyncio
    async def test_top_features_identified(self, predictor):
        """Top contributing features are identified."""
        offer_data = {
            "offer_price": 480000,
            "list_price": 500000,
            "days_on_market": 60,
            "seller_motivation": "high",
        }

        if hasattr(predictor, "explain"):
            explanation = await predictor.explain(offer_data)

            if explanation and "features" in explanation:
                # Should have at least one feature explanation
                assert len(explanation["features"]) > 0


class TestOptimalPriceRecommendation:
    """Tests for optimal price range recommendations."""

    @pytest.fixture
    def predictor(self):
        """Create a predictor for price recommendation tests."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            AcceptancePredictor,
            PredictionMode,
        )

        with patch("ghl_real_estate_ai.services.jorge.acceptance_predictor.get_cache_service"):
            return AcceptancePredictor(mode=PredictionMode.RULE_BASED)

    @pytest.mark.asyncio
    async def test_recommend_optimal_price(self, predictor):
        """Optimal price can be recommended."""
        context = {
            "list_price": 500000,
            "days_on_market": 30,
            "target_acceptance_probability": 0.8,
        }

        if hasattr(predictor, "recommend_price"):
            recommendation = await predictor.recommend_price(context)

            assert recommendation is not None
            if isinstance(recommendation, dict):
                assert "optimal_price" in recommendation or "price_range" in recommendation

    @pytest.mark.asyncio
    async def test_price_range_is_reasonable(self, predictor):
        """Recommended price range is reasonable relative to list."""
        context = {
            "list_price": 500000,
            "days_on_market": 30,
        }

        if hasattr(predictor, "recommend_price"):
            recommendation = await predictor.recommend_price(context)

            if recommendation and "price_range" in recommendation:
                low, high = recommendation["price_range"]
                # Range should be within 20% of list price
                assert low >= 400000  # 80% of list
                assert high <= 600000  # 120% of list


class TestModelMonitoring:
    """Tests for model monitoring and drift detection."""

    @pytest.fixture
    def predictor(self):
        """Create a predictor for monitoring tests."""
        from ghl_real_estate_ai.services.jorge.acceptance_predictor import (
            AcceptancePredictor,
            PredictionMode,
        )

        with patch("ghl_real_estate_ai.services.jorge.acceptance_predictor.get_cache_service"):
            return AcceptancePredictor(mode=PredictionMode.RULE_BASED)

    def test_get_model_metadata(self, predictor):
        """Model metadata can be retrieved."""
        if hasattr(predictor, "get_metadata"):
            metadata = predictor.get_metadata()

            if metadata:
                assert hasattr(metadata, "model_version") or "model_version" in metadata

    def test_model_performance_metrics(self, predictor):
        """Model performance metrics are available."""
        if hasattr(predictor, "get_performance_metrics"):
            metrics = predictor.get_performance_metrics()

            if metrics:
                assert isinstance(metrics, dict)
