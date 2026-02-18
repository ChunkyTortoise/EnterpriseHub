import pytest
pytestmark = pytest.mark.integration

"""
Tests for closing probability ML model.
"""

import asyncio
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score

from ghl_real_estate_ai.ml.closing_probability_model import ClosingProbabilityModel, ModelMetrics, ModelPrediction



class TestClosingProbabilityModel:
    """Test suite for ClosingProbabilityModel class."""

    @pytest.fixture
    def temp_model_dir(self):
        """Create temporary directory for model files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def ml_model(self, temp_model_dir):
        """Create ClosingProbabilityModel instance for testing."""
        return ClosingProbabilityModel(model_dir=temp_model_dir)

    @pytest.fixture
    def sample_training_data(self):
        """Create sample training data for testing."""
        np.random.seed(42)  # For reproducible tests

        # Generate features
        n_samples = 200
        features = np.random.random((n_samples, 23))  # 23 features from feature engineer

        # Generate realistic targets based on features
        # Higher qualification and engagement should lead to higher closing rates
        qualification_scores = features[:, 12]  # qualification_completeness
        engagement_scores = features[:, 5]  # engagement_score
        urgency_scores = features[:, 4]  # urgency_score

        # Create closing probability based on realistic patterns
        closing_probs = qualification_scores * 0.4 + engagement_scores * 0.3 + urgency_scores * 0.3
        # Add some noise
        closing_probs += np.random.normal(0, 0.1, n_samples)
        closing_probs = np.clip(closing_probs, 0, 1)

        # Convert to binary outcomes
        targets = (closing_probs > 0.6).astype(int)

        # Create feature names
        feature_names = [
            "message_count_norm",
            "avg_response_time_norm",
            "conversation_duration_norm",
            "sentiment_norm",
            "urgency_score",
            "engagement_score",
            "question_frequency",
            "price_mentions_norm",
            "urgency_signals_norm",
            "location_specificity",
            "budget_market_ratio",
            "budget_confidence",
            "qualification_completeness",
            "message_variance_norm",
            "response_consistency",
            "weekend_activity",
            "late_night_activity",
            "inventory_level",
            "days_on_market_norm",
            "price_trend_norm",
            "seasonal_factor",
            "competition_level",
            "interest_rate_norm",
        ]

        # Create DataFrame
        df = pd.DataFrame(features, columns=feature_names)
        df["closed"] = targets

        return df

    @pytest.fixture
    def mock_conversation_context(self):
        """Create mock conversation context for prediction testing."""
        return {
            "conversation_history": [
                {"role": "user", "text": "I'm looking for a 3-bedroom house"},
                {"role": "assistant", "text": "I can help you with that!"},
                {"role": "user", "text": "My budget is $500,000 and I need to move quickly"},
                {"role": "assistant", "text": "Great! Let me find some options for you."},
            ],
            "extracted_preferences": {
                "budget": "$500,000",
                "bedrooms": "3",
                "timeline": "quickly",
                "location": "suburbs",
            },
            "created_at": datetime.now().isoformat(),
        }

    @pytest.mark.asyncio
    async def test_model_initialization(self, temp_model_dir):
        """Test model initialization."""
        model = ClosingProbabilityModel(model_dir=temp_model_dir)

        assert model.model_dir == temp_model_dir
        assert model.model is None  # No model trained yet
        assert model.scaler is None
        assert model.last_training_date is None
        assert os.path.exists(temp_model_dir)

    @pytest.mark.asyncio
    async def test_train_model_success(self, ml_model, sample_training_data):
        """Test successful model training."""
        metrics = await ml_model.train_model(sample_training_data)

        assert isinstance(metrics, ModelMetrics)
        assert metrics.accuracy > 0.5  # Should be better than random
        assert metrics.auc_score > 0.5
        assert 0.0 <= metrics.precision <= 1.0
        assert 0.0 <= metrics.recall <= 1.0
        assert 0.0 <= metrics.f1_score <= 1.0
        assert ml_model.model is not None
        assert ml_model.scaler is not None
        assert ml_model.last_training_date is not None

    @pytest.mark.asyncio
    async def test_train_model_with_invalid_data(self, ml_model):
        """Test model training with invalid data."""
        # Missing target column
        invalid_data = pd.DataFrame({"feature1": [1, 2, 3], "feature2": [4, 5, 6]})

        with pytest.raises(ValueError):
            await ml_model.train_model(invalid_data)

    @pytest.mark.asyncio
    async def test_model_save_and_load(self, ml_model, sample_training_data):
        """Test model saving and loading."""
        # Train model
        await ml_model.train_model(sample_training_data)
        original_features = ml_model.feature_names.copy()

        # Create new model instance and load
        new_model = ClosingProbabilityModel(model_dir=ml_model.model_dir)
        await new_model._load_model()

        # Check that model was loaded correctly
        assert new_model.model is not None
        assert new_model.scaler is not None
        assert new_model.feature_names == original_features
        assert new_model.last_training_date is not None

    @pytest.mark.asyncio
    async def test_predict_closing_probability_with_trained_model(
        self, ml_model, sample_training_data, mock_conversation_context
    ):
        """Test prediction with trained model."""
        # Train model first
        await ml_model.train_model(sample_training_data)

        # Make prediction
        prediction = await ml_model.predict_closing_probability(mock_conversation_context)

        assert isinstance(prediction, ModelPrediction)
        assert 0.0 <= prediction.closing_probability <= 1.0
        assert len(prediction.confidence_interval) == 2
        assert prediction.confidence_interval[0] <= prediction.confidence_interval[1]
        assert 0.0 <= prediction.model_confidence <= 1.0
        assert isinstance(prediction.risk_factors, list)
        assert isinstance(prediction.positive_signals, list)

    @pytest.mark.asyncio
    async def test_predict_closing_probability_without_trained_model(self, ml_model, mock_conversation_context):
        """Test prediction without trained model (baseline)."""
        prediction = await ml_model.predict_closing_probability(mock_conversation_context)

        assert isinstance(prediction, ModelPrediction)
        assert 0.0 <= prediction.closing_probability <= 1.0
        # Should use baseline prediction
        assert "Model not trained" in prediction.risk_factors

    @pytest.mark.asyncio
    async def test_baseline_prediction(self, ml_model, mock_conversation_context):
        """Test baseline prediction logic."""
        prediction = await ml_model._baseline_prediction(mock_conversation_context)

        assert isinstance(prediction, ModelPrediction)
        assert 0.0 <= prediction.closing_probability <= 1.0
        assert len(prediction.confidence_interval) == 2
        assert "Limited historical data" in prediction.risk_factors

    @pytest.mark.asyncio
    async def test_analyze_prediction_factors(self, ml_model, sample_training_data):
        """Test prediction factor analysis."""
        # Train model first
        await ml_model.train_model(sample_training_data)

        # Create test feature vector
        feature_vector = np.array([0.5] * 23)  # Mid-range values
        feature_importances = dict(zip(ml_model.feature_names, np.random.random(23)))

        # Mock conversation features
        from ghl_real_estate_ai.ml.feature_engineering import ConversationFeatures

        conv_features = ConversationFeatures(
            message_count=10,
            avg_response_time=300.0,
            conversation_duration_minutes=60.0,
            overall_sentiment=0.5,
            urgency_score=0.8,
            engagement_score=0.7,
            question_asking_frequency=0.3,
            price_mention_count=2,
            timeline_urgency_signals=1,
            location_specificity=0.9,
            budget_to_market_ratio=0.8,
            budget_confidence=0.9,
            qualification_completeness=0.9,  # High qualification
            missing_critical_info=[],
            message_length_variance=500.0,
            response_consistency=0.8,
            weekend_activity=False,
            late_night_activity=False,
        )

        risk_factors, positive_signals = await ml_model._analyze_prediction_factors(
            feature_vector, feature_importances, conv_features
        )

        assert isinstance(risk_factors, list)
        assert isinstance(positive_signals, list)
        # High qualification should lead to positive signals
        assert "Highly qualified lead" in positive_signals

    @pytest.mark.asyncio
    async def test_get_model_performance(self, ml_model, sample_training_data):
        """Test model performance retrieval."""
        # No model trained yet
        performance = await ml_model.get_model_performance()
        assert performance is None

        # Train model
        metrics = await ml_model.train_model(sample_training_data)

        # Get performance
        performance = await ml_model.get_model_performance()
        assert performance is not None
        assert performance.accuracy == metrics.accuracy
        assert performance.auc_score == metrics.auc_score

    @pytest.mark.asyncio
    async def test_needs_retraining(self, ml_model, sample_training_data):
        """Test retraining necessity check."""
        # No model trained
        needs_training = await ml_model.needs_retraining()
        assert needs_training is True

        # Train model
        await ml_model.train_model(sample_training_data)

        # Fresh model shouldn't need retraining
        needs_training = await ml_model.needs_retraining()
        assert needs_training is False

        # Old model should need retraining
        needs_training = await ml_model.needs_retraining(max_age_days=0)
        assert needs_training is True

    def test_generate_synthetic_training_data(self, ml_model):
        """Test synthetic training data generation."""
        num_samples = 100
        positive_rate = 0.3

        data = ml_model.generate_synthetic_training_data(num_samples=num_samples, positive_rate=positive_rate)

        assert isinstance(data, pd.DataFrame)
        assert len(data) == num_samples
        assert "closed" in data.columns

        # Check positive rate is approximately correct
        actual_positive_rate = data["closed"].mean()
        assert abs(actual_positive_rate - positive_rate) < 0.1

        # Check feature names are correct
        feature_names = ml_model.feature_engineer.get_feature_names()
        for feature in feature_names:
            assert feature in data.columns

    @pytest.mark.asyncio
    async def test_feature_vector_mismatch_handling(self, ml_model, sample_training_data, mock_conversation_context):
        """Test handling of feature vector size mismatch."""
        # Train model with sample data
        await ml_model.train_model(sample_training_data)

        # Mock feature engineer to return wrong number of features
        with patch.object(
            ml_model.feature_engineer,
            "create_feature_vector",
            return_value=np.array([0.5] * 10),  # Wrong size (should be 23)
        ):
            prediction = await ml_model.predict_closing_probability(mock_conversation_context)

            # Should fall back to baseline
            assert (
                "Limited historical data" in prediction.risk_factors or "Model not trained" in prediction.risk_factors
            )

    @pytest.mark.asyncio
    async def test_prediction_caching(self, ml_model, mock_conversation_context):
        """Test that predictions are properly cached."""
        # First prediction
        prediction1 = await ml_model.predict_closing_probability(mock_conversation_context)

        # Second prediction with same context should be cached
        prediction2 = await ml_model.predict_closing_probability(mock_conversation_context)

        # Results should be identical
        assert prediction1.closing_probability == prediction2.closing_probability
        assert prediction1.model_confidence == prediction2.model_confidence

    @pytest.mark.asyncio
    async def test_model_training_with_imbalanced_data(self, ml_model):
        """Test model training with imbalanced dataset."""
        # Create highly imbalanced dataset (90% negative, 10% positive)
        imbalanced_data = ml_model.generate_synthetic_training_data(num_samples=200, positive_rate=0.1)

        metrics = await ml_model.train_model(imbalanced_data)

        # Model should still train successfully
        assert isinstance(metrics, ModelMetrics)
        assert metrics.accuracy > 0.5  # Should be better than random
        # With class balancing, recall should be reasonable
        assert metrics.recall > 0.3

    @pytest.mark.asyncio
    async def test_error_handling_in_prediction(self, ml_model):
        """Test error handling during prediction."""
        # Test with None context
        prediction = await ml_model.predict_closing_probability(None)
        assert isinstance(prediction, ModelPrediction)

        # Test with malformed context
        malformed_context = {"invalid": "data"}
        prediction = await ml_model.predict_closing_probability(malformed_context)
        assert isinstance(prediction, ModelPrediction)

    @pytest.mark.asyncio
    async def test_model_file_permissions_error(self, ml_model, sample_training_data):
        """Test handling of file permission errors during save/load."""
        # Train model
        await ml_model.train_model(sample_training_data)

        # Mock os.path.exists to simulate permission error
        with patch("os.path.exists", side_effect=PermissionError("Permission denied")):
            # Should handle gracefully
            load_success = await ml_model._load_model()
            assert load_success is False

    @pytest.mark.asyncio
    async def test_cross_validation_performance(self, ml_model, sample_training_data):
        """Test model performance with cross-validation patterns."""
        # Use larger dataset for more reliable cross-validation
        large_dataset = ml_model.generate_synthetic_training_data(num_samples=500, positive_rate=0.25)

        metrics = await ml_model.train_model(large_dataset, validation_split=0.3)

        # With larger dataset, performance should be reasonable
        assert metrics.accuracy > 0.6
        assert metrics.auc_score > 0.6
        assert metrics.f1_score > 0.4

    def test_feature_importance_analysis(self, ml_model, sample_training_data):
        """Test that feature importance is properly calculated."""
        # Use synchronous approach for this test
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            metrics = loop.run_until_complete(ml_model.train_model(sample_training_data))

            # Check that feature importances sum to ~1.0
            importance_sum = sum(metrics.feature_importances.values())
            assert abs(importance_sum - 1.0) < 0.01

            # Check that all features have non-negative importance
            assert all(importance >= 0 for importance in metrics.feature_importances.values())

            # Check that we have importance for all features
            assert len(metrics.feature_importances) == len(ml_model.feature_names)

        finally:
            loop.close()

    @pytest.mark.asyncio
    async def test_prediction_confidence_intervals(self, ml_model, sample_training_data, mock_conversation_context):
        """Test that prediction confidence intervals are reasonable."""
        # Train model
        await ml_model.train_model(sample_training_data)

        prediction = await ml_model.predict_closing_probability(mock_conversation_context)

        lower, upper = prediction.confidence_interval

        # Confidence interval should be valid
        assert lower <= prediction.closing_probability <= upper
        assert 0.0 <= lower <= 1.0
        assert 0.0 <= upper <= 1.0
        assert upper - lower >= 0  # Interval should be non-negative width

        # Interval shouldn't be too wide (indicating reasonable confidence)
        assert upper - lower <= 0.8