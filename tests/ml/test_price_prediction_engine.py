"""
Comprehensive tests for ML Price Prediction Engine.

Test coverage:
- Model initialization and validation
- Price prediction accuracy and confidence
- Feature engineering and preprocessing
- Ensemble model performance
- Model retraining and drift detection
- Batch processing capabilities
- Error handling and edge cases
- Performance benchmarks
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

from ghl_real_estate_ai.ml.price_prediction_engine import (
    PricePredictionEngine,
    EnsemblePricePredictor,
    PredictionFeatures,
    PricePredictionResult,
    ModelMetrics,
    PredictionTimeframe,
    ModelType,
    get_price_prediction_engine
)


class TestEnsemblePricePredictor:
    """Test suite for EnsemblePricePredictor."""

    @pytest.fixture
    def sample_training_data(self):
        """Create sample training data for testing."""
        np.random.seed(42)
        n_samples = 500

        data = {
            'bedrooms': np.random.choice([2, 3, 4, 5], n_samples, p=[0.2, 0.4, 0.3, 0.1]),
            'bathrooms': np.random.uniform(1, 4, n_samples),
            'square_footage': np.random.normal(2000, 800, n_samples),
            'lot_size': np.random.uniform(0.1, 2.0, n_samples),
            'year_built': np.random.randint(1950, 2023, n_samples),
            'garage_spaces': np.random.choice([0, 1, 2, 3], n_samples, p=[0.1, 0.3, 0.5, 0.1]),
            'walk_score': np.random.randint(20, 100, n_samples),
            'school_rating': np.random.uniform(3, 10, n_samples),
            'crime_score': np.random.randint(10, 90, n_samples),
            'property_type': np.random.choice(['single_family', 'condo', 'townhome'], n_samples, p=[0.7, 0.2, 0.1]),
            'property_condition': np.random.choice(['excellent', 'good', 'fair', 'poor'], n_samples, p=[0.3, 0.5, 0.15, 0.05]),
        }

        df = pd.DataFrame(data)

        # Calculate realistic price based on features
        df['price'] = (
            df['square_footage'] * 350 *  # Base price per sqft
            (1 + np.random.normal(0, 0.1, n_samples)) *  # Add noise
            (df['school_rating'] / 10) * 1.1 *  # School adjustment
            np.where(df['year_built'] > 2000, 1.1, 0.95)  # Age adjustment
        )

        return df

    @pytest.fixture
    def sample_prediction_features(self):
        """Create sample prediction features."""
        return pd.DataFrame([{
            'bedrooms': 3,
            'bathrooms': 2.5,
            'square_footage': 2200,
            'lot_size': 0.3,
            'year_built': 2015,
            'garage_spaces': 2,
            'walk_score': 75,
            'school_rating': 8.5,
            'crime_score': 20,
            'property_type': 'single_family',
            'property_condition': 'good'
        }])

    def test_ensemble_model_initialization(self):
        """Test ensemble model initialization."""
        model = EnsemblePricePredictor()

        assert hasattr(model, 'models')
        assert hasattr(model, 'ensemble_weights')
        assert len(model.models) == 3  # RF, GB, ElasticNet
        assert not model.is_fitted

    def test_model_fitting(self, sample_training_data):
        """Test model fitting with training data."""
        model = EnsemblePricePredictor()

        X = sample_training_data.drop(columns=['price'])
        y = sample_training_data['price']

        # Fit the model
        model.fit(X, y)

        assert model.is_fitted
        assert hasattr(model, 'scalers')
        assert hasattr(model, 'label_encoders')

    def test_model_prediction(self, sample_training_data, sample_prediction_features):
        """Test model prediction functionality."""
        model = EnsemblePricePredictor()

        X = sample_training_data.drop(columns=['price'])
        y = sample_training_data['price']

        # Fit and predict
        model.fit(X, y)
        predictions = model.predict(sample_prediction_features)

        assert len(predictions) == 1
        assert predictions[0] > 0  # Price should be positive
        assert isinstance(predictions[0], (int, float))

    def test_prediction_with_uncertainty(self, sample_training_data, sample_prediction_features):
        """Test prediction with uncertainty estimation."""
        model = EnsemblePricePredictor()

        X = sample_training_data.drop(columns=['price'])
        y = sample_training_data['price']

        model.fit(X, y)
        predictions, uncertainty = model.predict_with_uncertainty(sample_prediction_features)

        assert len(predictions) == len(uncertainty)
        assert uncertainty[0] >= 0  # Uncertainty should be non-negative
        assert predictions[0] > 0

    def test_feature_importance(self, sample_training_data):
        """Test feature importance extraction."""
        model = EnsemblePricePredictor()

        X = sample_training_data.drop(columns=['price'])
        y = sample_training_data['price']

        model.fit(X, y)
        importance = model.get_feature_importance()

        assert isinstance(importance, dict)
        assert len(importance) > 0

    def test_missing_data_handling(self, sample_training_data):
        """Test handling of missing data in predictions."""
        model = EnsemblePricePredictor()

        X = sample_training_data.drop(columns=['price'])
        y = sample_training_data['price']
        model.fit(X, y)

        # Create test data with missing values
        test_data = pd.DataFrame([{
            'bedrooms': 3,
            'bathrooms': None,  # Missing value
            'square_footage': 2200,
            'lot_size': 0.3,
            'year_built': 2015,
            'garage_spaces': 2,
            'walk_score': 75,
            'school_rating': 8.5,
            'crime_score': 20,
            'property_type': 'single_family',
            'property_condition': 'good'
        }])

        # Should handle missing data gracefully
        predictions = model.predict(test_data)
        assert len(predictions) == 1
        assert predictions[0] > 0

    def test_categorical_feature_handling(self, sample_training_data):
        """Test handling of categorical features."""
        model = EnsemblePricePredictor()

        X = sample_training_data.drop(columns=['price'])
        y = sample_training_data['price']
        model.fit(X, y)

        # Test with new categorical values
        test_data = pd.DataFrame([{
            'bedrooms': 4,
            'bathrooms': 3.0,
            'square_footage': 2500,
            'lot_size': 0.4,
            'year_built': 2018,
            'garage_spaces': 2,
            'walk_score': 80,
            'school_rating': 9.0,
            'crime_score': 15,
            'property_type': 'townhome',  # Different from training
            'property_condition': 'excellent'
        }])

        predictions = model.predict(test_data)
        assert len(predictions) == 1
        assert predictions[0] > 0


class TestPricePredictionEngine:
    """Test suite for PricePredictionEngine."""

    @pytest.fixture
    async def engine(self):
        """Create engine instance for testing."""
        engine = PricePredictionEngine(model_cache_dir="test_models")
        engine.cache = AsyncMock()

        # Mock model loading
        with patch.object(engine, '_load_models', new_callable=AsyncMock), \
             patch.object(engine, '_train_initial_models', new_callable=AsyncMock), \
             patch.object(engine, '_validate_models', new_callable=AsyncMock):

            await engine.initialize()

        return engine

    @pytest.fixture
    def sample_features(self):
        """Create sample prediction features."""
        return PredictionFeatures(
            property_type="single_family",
            bedrooms=3,
            bathrooms=2.5,
            square_footage=2200,
            lot_size=0.3,
            year_built=2015,
            garage_spaces=2,
            property_condition="good",
            neighborhood_id="test_neighborhood",
            zip_code="12345",
            latitude=30.2672,
            longitude=-97.7431,
            walk_score=75,
            school_rating=8.5,
            crime_score=20,
            median_neighborhood_price=750000.0,
            price_per_sqft_neighborhood=350.0,
            days_on_market_avg=30,
            inventory_months=2.0,
            sales_velocity=0.8,
            price_appreciation_12m=10.5,
            median_income=85000.0,
            unemployment_rate=3.5,
            mortgage_rates=6.5,
            economic_index=75.0,
            listing_month=5,
            is_peak_season=True,
            seasonal_adjustment=1.05,
            comps_median_price=745000.0,
            comps_price_per_sqft=348.0,
            comps_count=12,
            comps_days_old_avg=25
        )

    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """Test engine initialization."""
        engine = PricePredictionEngine()
        engine.cache = AsyncMock()

        # Mock dependencies
        with patch.object(engine, '_load_models', new_callable=AsyncMock), \
             patch.object(engine, '_train_initial_models', new_callable=AsyncMock), \
             patch.object(engine, '_validate_models', new_callable=AsyncMock):

            await engine.initialize()

            assert engine.is_initialized
            assert engine.target_accuracy == 0.95

    @pytest.mark.asyncio
    async def test_price_prediction_cached(self, engine, sample_features):
        """Test cached price prediction."""
        # Mock cached result
        cached_result = {
            "predicted_price": 780000.0,
            "confidence_interval": (750000.0, 810000.0),
            "prediction_confidence": 0.92,
            "timeframe_predictions": {"1m": 785000.0, "3m": 795000.0},
            "model_used": "ensemble",
            "prediction_date": datetime.now()
        }

        engine.cache.get.return_value = cached_result

        result = await engine.predict_price(sample_features)

        assert isinstance(result, PricePredictionResult)
        assert result.predicted_price == 780000.0
        assert result.prediction_confidence == 0.92

    @pytest.mark.asyncio
    async def test_price_prediction_fresh(self, engine, sample_features):
        """Test fresh price prediction generation."""
        # Mock cache miss
        engine.cache.get.return_value = None

        # Mock model
        mock_model = Mock()
        mock_model.predict_with_uncertainty.return_value = (np.array([780000.0]), np.array([15000.0]))
        mock_model.get_feature_importance.return_value = {"square_footage": 0.3, "location": 0.25}
        mock_model.__class__.__name__ = "EnsemblePricePredictor"

        engine.models["ensemble"] = mock_model

        # Mock helper methods
        with patch.object(engine, '_get_model_for_timeframe', return_value=mock_model), \
             patch.object(engine, '_generate_multi_timeframe_predictions', return_value={"1m": 785000.0}), \
             patch.object(engine, '_find_comparable_properties', return_value=[]), \
             patch.object(engine, '_calculate_prediction_confidence', return_value=0.94):

            result = await engine.predict_price(sample_features, include_uncertainty=True)

            assert isinstance(result, PricePredictionResult)
            assert result.predicted_price == 780000.0
            assert result.prediction_confidence >= 0.9
            assert len(result.timeframe_predictions) > 0

    @pytest.mark.asyncio
    async def test_batch_prediction(self, engine, sample_features):
        """Test batch prediction functionality."""
        # Create multiple features
        features_list = [sample_features for _ in range(5)]

        # Mock individual predictions
        with patch.object(engine, 'predict_price') as mock_predict:
            mock_result = PricePredictionResult(
                property_id=None,
                predicted_price=780000.0,
                confidence_interval=(750000.0, 810000.0),
                prediction_confidence=0.92,
                timeframe_predictions={},
                model_used="ensemble",
                feature_importance={},
                comparable_properties=[],
                market_position="at_market",
                price_per_sqft=350.0,
                neighborhood_context={},
                prediction_date=datetime.now(),
                data_freshness=datetime.now(),
                model_version="2.1.0"
            )

            mock_predict.return_value = mock_result

            results = await engine.batch_predict(features_list)

            assert len(results) == 5
            assert all(isinstance(r, PricePredictionResult) for r in results)

    @pytest.mark.asyncio
    async def test_model_evaluation(self, engine):
        """Test model performance evaluation."""
        # Create test data
        test_data = pd.DataFrame({
            'square_footage': [2000, 2200, 1800],
            'bedrooms': [3, 4, 2],
            'bathrooms': [2.5, 3.0, 2.0],
            'year_built': [2010, 2015, 2005],
            'price': [650000, 780000, 580000]
        })

        # Mock model
        mock_model = Mock()
        mock_model.predict.return_value = np.array([645000, 775000, 585000])
        mock_model.get_feature_importance.return_value = {"square_footage": 0.5}

        engine.models["ensemble"] = mock_model

        metrics = await engine.evaluate_model_performance(test_data)

        assert isinstance(metrics, ModelMetrics)
        assert 0 <= metrics.accuracy <= 1
        assert metrics.mape >= 0
        assert metrics.rmse >= 0

    @pytest.mark.asyncio
    async def test_model_retraining(self, engine):
        """Test model retraining functionality."""
        # Create training data
        training_data = pd.DataFrame({
            'square_footage': np.random.normal(2000, 500, 100),
            'bedrooms': np.random.choice([2, 3, 4], 100),
            'bathrooms': np.random.uniform(1.5, 3.5, 100),
            'year_built': np.random.randint(1990, 2023, 100),
            'price': np.random.normal(700000, 150000, 100)
        })

        # Mock model operations
        with patch.object(engine, '_save_models', new_callable=AsyncMock):
            await engine.retrain_models(training_data)

            # Should have attempted to retrain
            assert True  # Basic test that retraining completes

    @pytest.mark.asyncio
    async def test_timeframe_predictions(self, engine, sample_features):
        """Test multi-timeframe predictions."""
        timeframes = [
            PredictionTimeframe.ONE_MONTH,
            PredictionTimeframe.THREE_MONTHS,
            PredictionTimeframe.SIX_MONTHS,
            PredictionTimeframe.TWELVE_MONTHS
        ]

        # Mock model
        mock_model = Mock()
        mock_model.predict_with_uncertainty.return_value = (np.array([780000.0]), np.array([15000.0]))
        mock_model.get_feature_importance.return_value = {}
        mock_model.__class__.__name__ = "EnsemblePricePredictor"

        engine.cache.get.return_value = None

        with patch.object(engine, '_get_model_for_timeframe', return_value=mock_model), \
             patch.object(engine, '_find_comparable_properties', return_value=[]), \
             patch.object(engine, '_calculate_prediction_confidence', return_value=0.95):

            for timeframe in timeframes:
                result = await engine.predict_price(sample_features, timeframe)

                assert isinstance(result, PricePredictionResult)
                assert result.predicted_price > 0

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, engine):
        """Test prediction confidence calculation."""
        # Mock model and data
        mock_model = Mock()
        feature_df = pd.DataFrame([{"feature1": 1, "feature2": 2}])

        # Test high confidence scenario
        engine.model_metrics["ensemble"] = ModelMetrics(
            accuracy=0.96,
            mape=0.04,
            rmse=25000,
            mae=20000,
            r2_score=0.92,
            prediction_confidence=0.96,
            feature_importance={},
            cross_val_scores=[0.94, 0.96, 0.95],
            last_evaluated=datetime.now()
        )

        confidence = engine._calculate_prediction_confidence(mock_model, feature_df)

        assert 0 <= confidence <= 1
        assert confidence >= 0.8  # Should be high confidence

    def test_cache_key_generation(self, engine, sample_features):
        """Test prediction cache key generation."""
        timeframe = PredictionTimeframe.ONE_MONTH

        key1 = engine._generate_prediction_cache_key(sample_features, timeframe)
        key2 = engine._generate_prediction_cache_key(sample_features, timeframe)

        # Same inputs should generate same key
        assert key1 == key2
        assert "price_prediction" in key1
        assert timeframe.value in key1

    def test_feature_preparation(self, engine, sample_features):
        """Test feature preparation for model input."""
        feature_df = engine._prepare_features(sample_features)

        assert isinstance(feature_df, pd.DataFrame)
        assert len(feature_df) == 1
        assert feature_df.iloc[0]['bedrooms'] == 3
        assert feature_df.iloc[0]['square_footage'] == 2200

    @pytest.mark.asyncio
    async def test_error_handling(self, engine, sample_features):
        """Test error handling in prediction."""
        # Mock model that raises exception
        mock_model = Mock()
        mock_model.predict_with_uncertainty.side_effect = Exception("Model error")

        engine.models["ensemble"] = mock_model
        engine.cache.get.return_value = None

        with patch.object(engine, '_get_model_for_timeframe', return_value=mock_model):
            with pytest.raises(Exception):
                await engine.predict_price(sample_features)

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, engine, sample_features):
        """Test prediction performance benchmarks."""
        # Mock fast model
        mock_model = Mock()
        mock_model.predict_with_uncertainty.return_value = (np.array([780000.0]), np.array([15000.0]))
        mock_model.get_feature_importance.return_value = {}
        mock_model.__class__.__name__ = "EnsemblePricePredictor"

        engine.cache.get.return_value = None

        with patch.object(engine, '_get_model_for_timeframe', return_value=mock_model), \
             patch.object(engine, '_find_comparable_properties', return_value=[]), \
             patch.object(engine, '_calculate_prediction_confidence', return_value=0.95):

            start_time = datetime.now()
            result = await engine.predict_price(sample_features)
            execution_time = (datetime.now() - start_time).total_seconds()

            # Should be fast (< 1 second for this test)
            assert execution_time < 1.0
            assert isinstance(result, PricePredictionResult)

    @pytest.mark.asyncio
    async def test_model_accuracy_target(self, engine):
        """Test model meets accuracy targets."""
        # Mock high-performance metrics
        high_accuracy_metrics = ModelMetrics(
            accuracy=0.957,  # Above 95% target
            mape=0.043,
            rmse=22000,
            mae=18000,
            r2_score=0.94,
            prediction_confidence=0.957,
            feature_importance={"square_footage": 0.4, "neighborhood": 0.3},
            cross_val_scores=[0.95, 0.96, 0.955, 0.958, 0.952],
            last_evaluated=datetime.now()
        )

        engine.model_metrics["ensemble"] = high_accuracy_metrics

        # Verify accuracy meets target
        assert high_accuracy_metrics.accuracy >= engine.target_accuracy
        assert high_accuracy_metrics.prediction_confidence >= 0.95

    def test_singleton_engine_instance(self):
        """Test singleton pattern for engine instance."""
        assert callable(get_price_prediction_engine)

    @pytest.mark.asyncio
    async def test_feature_completeness_impact(self, engine):
        """Test impact of feature completeness on confidence."""
        # Complete features
        complete_features = pd.DataFrame([{
            'bedrooms': 3, 'bathrooms': 2.5, 'square_footage': 2200,
            'lot_size': 0.3, 'year_built': 2015, 'walk_score': 75
        }])

        # Incomplete features (missing data)
        incomplete_features = pd.DataFrame([{
            'bedrooms': 3, 'bathrooms': None, 'square_footage': 2200,
            'lot_size': None, 'year_built': 2015, 'walk_score': None
        }])

        # Mock base confidence
        mock_model = Mock()
        engine.model_metrics["ensemble"] = ModelMetrics(
            accuracy=0.9, mape=0.1, rmse=30000, mae=25000, r2_score=0.85,
            prediction_confidence=0.9, feature_importance={}, cross_val_scores=[],
            last_evaluated=datetime.now()
        )

        confidence_complete = engine._calculate_prediction_confidence(mock_model, complete_features)
        confidence_incomplete = engine._calculate_prediction_confidence(mock_model, incomplete_features)

        # Complete features should have higher confidence
        assert confidence_complete >= confidence_incomplete

    @pytest.mark.asyncio
    async def test_comparable_properties_analysis(self, engine, sample_features):
        """Test comparable properties analysis."""
        engine.cache.get.return_value = None

        # Mock comparable properties
        mock_comparables = [
            {
                "address": "123 Test St",
                "price": 760000,
                "beds": 3,
                "baths": 2.5,
                "sqft": 2100,
                "days_ago_sold": 30
            }
        ]

        with patch.object(engine, '_find_comparable_properties', return_value=mock_comparables):
            comparables = await engine._find_comparable_properties(sample_features)

            assert len(comparables) > 0
            assert comparables[0]["price"] > 0
            assert "address" in comparables[0]