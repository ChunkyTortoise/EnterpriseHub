"""
Test suite for the Deep Learning Forecaster.

Tests the advanced neural network-based forecasting system for
competitive intelligence predictions.

Author: Claude
Date: January 2026
"""

import pytest
import pandas as pd
import numpy as np
import torch
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.prediction.deep_learning_forecaster import (

@pytest.mark.integration
    DeepLearningForecaster,
    DeepLearningConfig,
    ModelType,
    PredictionHorizon,
    FeatureType,
    ModelMetrics,
    LSTMForecaster,
    GRUForecaster,
    EnsembleForecaster,
    AdvancedFeatureEngineer
)


class TestDeepLearningConfig:
    """Test configuration class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = DeepLearningConfig()
        
        assert config.model_type == ModelType.LSTM
        assert config.hidden_size == 128
        assert config.num_layers == 2
        assert config.dropout == 0.2
        assert config.batch_size == 32
        assert config.learning_rate == 0.001
        assert config.sequence_length == 60
        assert len(config.feature_types) == 3
        assert FeatureType.PRICING in config.feature_types
        assert FeatureType.MARKET_SHARE in config.feature_types
        assert FeatureType.SENTIMENT in config.feature_types
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = DeepLearningConfig(
            model_type=ModelType.GRU,
            hidden_size=256,
            num_layers=3,
            dropout=0.3,
            sequence_length=120,
            feature_types=[FeatureType.PRICING, FeatureType.TECHNICAL]
        )
        
        assert config.model_type == ModelType.GRU
        assert config.hidden_size == 256
        assert config.num_layers == 3
        assert config.dropout == 0.3
        assert config.sequence_length == 120
        assert len(config.feature_types) == 2


class TestLSTMForecaster:
    """Test LSTM model."""
    
    def test_lstm_initialization(self):
        """Test LSTM model initialization."""
        model = LSTMForecaster(
            input_size=10,
            hidden_size=64,
            num_layers=2,
            output_size=1
        )
        
        assert isinstance(model, torch.nn.Module)
        assert model.hidden_size == 64
        assert model.num_layers == 2
    
    def test_lstm_forward_pass(self):
        """Test LSTM forward pass."""
        model = LSTMForecaster(
            input_size=10,
            hidden_size=64,
            num_layers=2,
            output_size=1
        )
        
        # Create test input
        batch_size, seq_length, input_size = 4, 30, 10
        x = torch.randn(batch_size, seq_length, input_size)
        
        # Forward pass
        output = model(x)
        
        assert output.shape == (batch_size, 1)
        assert not torch.isnan(output).any()
    
    def test_bidirectional_lstm(self):
        """Test bidirectional LSTM."""
        model = LSTMForecaster(
            input_size=10,
            hidden_size=64,
            num_layers=2,
            output_size=1,
            bidirectional=True
        )
        
        batch_size, seq_length, input_size = 4, 30, 10
        x = torch.randn(batch_size, seq_length, input_size)
        output = model(x)
        
        assert output.shape == (batch_size, 1)


class TestGRUForecaster:
    """Test GRU model."""
    
    def test_gru_initialization(self):
        """Test GRU model initialization."""
        model = GRUForecaster(
            input_size=10,
            hidden_size=64,
            num_layers=2,
            output_size=1
        )
        
        assert isinstance(model, torch.nn.Module)
        assert model.hidden_size == 64
        assert model.num_layers == 2
    
    def test_gru_forward_pass(self):
        """Test GRU forward pass."""
        model = GRUForecaster(
            input_size=10,
            hidden_size=64,
            num_layers=2,
            output_size=1
        )
        
        batch_size, seq_length, input_size = 4, 30, 10
        x = torch.randn(batch_size, seq_length, input_size)
        output = model(x)
        
        assert output.shape == (batch_size, 1)
        assert not torch.isnan(output).any()


class TestEnsembleForecaster:
    """Test ensemble model."""
    
    def test_ensemble_initialization(self):
        """Test ensemble initialization."""
        lstm_model = LSTMForecaster(10, 64, 2, 1)
        gru_model = GRUForecaster(10, 64, 2, 1)
        
        ensemble = EnsembleForecaster({
            'lstm': lstm_model,
            'gru': gru_model
        })
        
        assert len(ensemble.models) == 2
        assert 'lstm' in ensemble.models
        assert 'gru' in ensemble.models
        assert len(ensemble.weights) == 2
        assert sum(ensemble.weights) == pytest.approx(1.0)
    
    def test_ensemble_prediction(self):
        """Test ensemble prediction."""
        lstm_model = LSTMForecaster(10, 64, 2, 1)
        gru_model = GRUForecaster(10, 64, 2, 1)
        
        ensemble = EnsembleForecaster({
            'lstm': lstm_model,
            'gru': gru_model
        })
        
        batch_size, seq_length, input_size = 4, 30, 10
        x = torch.randn(batch_size, seq_length, input_size)
        
        prediction = ensemble.predict(x)
        
        assert prediction.shape == (batch_size, 1)
        assert not torch.isnan(prediction).any()


class TestAdvancedFeatureEngineer:
    """Test feature engineering."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        data = pd.DataFrame({
            'price': 100 + np.cumsum(np.random.randn(100) * 0.1),
            'market_share': 0.2 + np.cumsum(np.random.randn(100) * 0.001),
            'sentiment_score': np.random.randn(100),
            'competitor_count': np.random.randint(3, 10, 100)
        }, index=dates)
        return data
    
    def test_feature_engineer_initialization(self):
        """Test feature engineer initialization."""
        engineer = AdvancedFeatureEngineer()
        
        assert hasattr(engineer, 'scalers')
        assert hasattr(engineer, 'feature_names')
        assert hasattr(engineer, 'window_sizes')
        assert len(engineer.window_sizes) > 0
    
    def test_pricing_features(self, sample_data):
        """Test pricing feature engineering."""
        engineer = AdvancedFeatureEngineer()
        
        features = engineer._add_pricing_features(sample_data.copy())
        
        # Check for expected pricing features
        assert 'price_return' in features.columns
        assert 'price_change' in features.columns
        assert 'price_ma_5' in features.columns
        assert 'price_volatility_5' in features.columns
        assert 'price_support' in features.columns
        assert 'price_resistance' in features.columns
    
    def test_market_share_features(self, sample_data):
        """Test market share feature engineering."""
        engineer = AdvancedFeatureEngineer()
        
        features = engineer._add_market_share_features(sample_data.copy())
        
        assert 'market_share_change' in features.columns
        assert 'market_share_pct_change' in features.columns
        assert 'market_share_ma_5' in features.columns
    
    def test_sentiment_features(self, sample_data):
        """Test sentiment feature engineering."""
        engineer = AdvancedFeatureEngineer()
        
        features = engineer._add_sentiment_features(sample_data.copy())
        
        assert 'sentiment_change' in features.columns
        assert 'sentiment_ma_5' in features.columns
        assert 'sentiment_momentum' in features.columns
    
    def test_technical_features(self, sample_data):
        """Test technical feature engineering."""
        engineer = AdvancedFeatureEngineer()
        
        features = engineer._add_technical_features(sample_data.copy())
        
        assert 'rsi' in features.columns
        assert 'macd' in features.columns
        assert 'macd_signal' in features.columns
        assert 'bollinger_upper' in features.columns
        assert 'bollinger_lower' in features.columns
    
    def test_seasonal_features(self, sample_data):
        """Test seasonal feature engineering."""
        engineer = AdvancedFeatureEngineer()
        
        features = engineer._add_seasonal_features(sample_data.copy())
        
        assert 'hour' in features.columns
        assert 'day_of_week' in features.columns
        assert 'month' in features.columns
        assert 'hour_sin' in features.columns
        assert 'hour_cos' in features.columns
        assert 'day_sin' in features.columns
        assert 'day_cos' in features.columns
    
    def test_feature_scaling(self, sample_data):
        """Test feature scaling."""
        engineer = AdvancedFeatureEngineer()
        
        # Test MinMax scaling
        scaled_data = engineer.scale_features(sample_data, method="minmax")
        
        assert scaled_data.shape == sample_data.shape
        assert scaled_data.min().min() >= 0
        assert scaled_data.max().max() <= 1
        
        # Test Standard scaling
        scaled_data_std = engineer.scale_features(sample_data, method="standard")
        
        assert scaled_data_std.shape == sample_data.shape
        # Standard scaling should have approximately 0 mean and 1 std
        assert abs(scaled_data_std.mean().mean()) < 0.1
    
    def test_comprehensive_feature_engineering(self, sample_data):
        """Test comprehensive feature engineering."""
        engineer = AdvancedFeatureEngineer()
        
        feature_types = [
            FeatureType.PRICING,
            FeatureType.MARKET_SHARE,
            FeatureType.SENTIMENT,
            FeatureType.TECHNICAL,
            FeatureType.SEASONAL
        ]
        
        features = engineer.engineer_features(sample_data, feature_types)
        
        # Should have more columns than original
        assert features.shape[1] > sample_data.shape[1]
        
        # Should not have NaN values after dropna
        assert not features.isna().any().any()
        
        # Check that feature names are stored
        assert len(engineer.feature_names) == features.shape[1]


class TestDeepLearningForecaster:
    """Test main forecaster class."""
    
    @pytest.fixture
    def sample_training_data(self):
        """Create sample training data."""
        dates = pd.date_range('2024-01-01', periods=1000, freq='H')
        
        # Create synthetic competitive data
        base_price = 100
        price_trend = np.cumsum(np.random.randn(1000) * 0.1)
        seasonal_pattern = 5 * np.sin(2 * np.pi * np.arange(1000) / 24)  # Daily pattern
        
        data = pd.DataFrame({
            'price': base_price + price_trend + seasonal_pattern + np.random.randn(1000) * 0.5,
            'market_share': 0.2 + np.cumsum(np.random.randn(1000) * 0.001),
            'sentiment_score': np.random.randn(1000),
            'competitor_count': np.random.randint(3, 10, 1000),
            'new_product_launches': np.random.poisson(0.1, 1000),
            'target': base_price + price_trend + seasonal_pattern + np.random.randn(1000) * 0.2  # Less noisy target
        }, index=dates)
        
        return data
    
    def test_forecaster_initialization(self):
        """Test forecaster initialization."""
        config = DeepLearningConfig(hidden_size=64, num_layers=1, num_epochs=5)
        
        with patch('src.prediction.deep_learning_forecaster.get_event_bus') as mock_bus:
            mock_bus.return_value = AsyncMock()
            forecaster = DeepLearningForecaster(config)
            
            assert forecaster.config.hidden_size == 64
            assert forecaster.config.num_layers == 1
            assert forecaster.config.num_epochs == 5
            assert not forecaster.is_trained
            assert len(forecaster.models) == 0
            assert isinstance(forecaster.feature_engineer, AdvancedFeatureEngineer)
    
    @pytest.mark.asyncio
    async def test_model_training(self, sample_training_data):
        """Test model training process."""
        config = DeepLearningConfig(
            hidden_size=32,
            num_layers=1,
            num_epochs=5,  # Quick training for tests
            batch_size=16,
            sequence_length=30,
            ensemble_models=[ModelType.LSTM, ModelType.GRU]
        )
        
        with patch('src.prediction.deep_learning_forecaster.get_event_bus') as mock_bus:
            mock_bus.return_value = AsyncMock()
            
            forecaster = DeepLearningForecaster(config)
            
            # Train models
            result = await forecaster.train_models(
                training_data=sample_training_data,
                target_column="target",
                validation_split=0.2
            )
            
            # Check training results
            assert result["status"] == "success"
            assert "metrics" in result
            assert "training_results" in result
            assert forecaster.is_trained
            assert len(forecaster.models) == 2  # LSTM and GRU
            assert forecaster.ensemble is not None
    
    @pytest.mark.asyncio
    async def test_prediction(self, sample_training_data):
        """Test prediction generation."""
        config = DeepLearningConfig(
            hidden_size=32,
            num_layers=1,
            num_epochs=3,  # Very quick training
            batch_size=16,
            sequence_length=30,
            ensemble_models=[ModelType.LSTM]  # Single model for speed
        )
        
        with patch('src.prediction.deep_learning_forecaster.get_event_bus') as mock_bus:
            mock_bus.return_value = AsyncMock()
            
            forecaster = DeepLearningForecaster(config)
            
            # Train first
            await forecaster.train_models(
                training_data=sample_training_data,
                target_column="target",
                validation_split=0.2
            )
            
            # Make prediction
            prediction_data = sample_training_data.drop('target', axis=1)[-100:]  # Last 100 samples
            
            result = await forecaster.predict(
                input_data=prediction_data,
                horizon=PredictionHorizon.MEDIUM_TERM,
                confidence_intervals=True
            )
            
            # Check prediction results
            assert "predictions" in result
            assert "confidence_intervals" in result
            assert "horizon" in result
            assert result["horizon"] == PredictionHorizon.MEDIUM_TERM.value
            
            # Check that predictions are reasonable
            predictions = result["predictions"]
            assert len(predictions) > 0
            
            for pred_value in predictions.values():
                assert isinstance(pred_value, (int, float))
                assert not np.isnan(pred_value)
    
    def test_model_summary(self):
        """Test model summary generation."""
        config = DeepLearningConfig(hidden_size=64)
        
        with patch('src.prediction.deep_learning_forecaster.get_event_bus') as mock_bus:
            mock_bus.return_value = AsyncMock()
            forecaster = DeepLearningForecaster(config)
            
            summary = forecaster.get_model_summary()
            
            assert "is_trained" in summary
            assert "config" in summary
            assert "models_available" in summary
            assert "feature_count" in summary
            assert "device" in summary
            assert summary["is_trained"] is False  # Not trained yet
    
    def test_sequence_creation(self):
        """Test sequence creation for training."""
        config = DeepLearningConfig()
        
        with patch('src.prediction.deep_learning_forecaster.get_event_bus') as mock_bus:
            mock_bus.return_value = AsyncMock()
            forecaster = DeepLearningForecaster(config)
            
            # Create sample data
            features = np.random.randn(100, 10)  # 100 samples, 10 features
            targets = np.random.randn(100)
            sequence_length = 20
            
            X, y = forecaster._create_sequences(features, targets, sequence_length)
            
            expected_samples = 100 - sequence_length
            assert X.shape == (expected_samples, sequence_length, 10)
            assert y.shape == (expected_samples,)
    
    @pytest.mark.asyncio
    async def test_model_save_load(self, sample_training_data, tmp_path):
        """Test model saving and loading."""
        config = DeepLearningConfig(
            hidden_size=32,
            num_layers=1,
            num_epochs=2,
            ensemble_models=[ModelType.LSTM]
        )
        
        with patch('src.prediction.deep_learning_forecaster.get_event_bus') as mock_bus:
            mock_bus.return_value = AsyncMock()
            
            # Train and save model
            forecaster1 = DeepLearningForecaster(config, str(tmp_path))
            
            await forecaster1.train_models(
                training_data=sample_training_data,
                target_column="target",
                validation_split=0.2
            )
            
            assert forecaster1.is_trained
            original_feature_count = len(forecaster1.feature_columns)
            
            # Load model in new instance
            forecaster2 = DeepLearningForecaster(config, str(tmp_path))
            await forecaster2.load_models()
            
            assert forecaster2.is_trained
            assert len(forecaster2.feature_columns) == original_feature_count
            assert len(forecaster2.models) == len(forecaster1.models)


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_forecasting(self):
        """Test complete forecasting pipeline."""
        # Create realistic sample data
        dates = pd.date_range('2024-01-01', periods=500, freq='H')
        
        # Simulate competitive price movements
        base_price = 100
        trend = 0.01
        prices = [base_price]
        
        for i in range(1, 500):
            # Add trend, mean reversion, and noise
            change = trend + 0.1 * (100 - prices[-1]) / 100 + np.random.randn() * 0.5
            new_price = prices[-1] + change
            prices.append(max(50, min(150, new_price)))  # Bound prices
        
        data = pd.DataFrame({
            'price': prices,
            'market_share': 0.2 + np.cumsum(np.random.randn(500) * 0.001),
            'sentiment_score': np.random.randn(500) * 0.5,
            'competitor_count': 5 + np.random.randint(-2, 3, 500),
            'target': prices  # Predict price
        }, index=dates)
        
        config = DeepLearningConfig(
            hidden_size=64,
            num_layers=2,
            num_epochs=10,
            batch_size=32,
            sequence_length=48,  # 48 hours lookback
            ensemble_models=[ModelType.LSTM, ModelType.GRU],
            feature_types=[
                FeatureType.PRICING,
                FeatureType.MARKET_SHARE,
                FeatureType.SENTIMENT,
                FeatureType.TECHNICAL
            ]
        )
        
        with patch('src.prediction.deep_learning_forecaster.get_event_bus') as mock_bus:
            mock_bus.return_value = AsyncMock()
            
            forecaster = DeepLearningForecaster(config)
            
            # Split data
            train_data = data[:400]
            test_data = data[400:].drop('target', axis=1)
            
            # Train
            training_result = await forecaster.train_models(
                training_data=train_data,
                target_column="target",
                validation_split=0.2
            )
            
            assert training_result["status"] == "success"
            
            # Predict
            prediction_result = await forecaster.predict(
                input_data=test_data,
                horizon=PredictionHorizon.MEDIUM_TERM,
                confidence_intervals=True
            )
            
            # Validate predictions
            assert "predictions" in prediction_result
            assert "ensemble" in prediction_result["predictions"]
            
            ensemble_prediction = prediction_result["predictions"]["ensemble"]
            assert 50 <= ensemble_prediction <= 150  # Within reasonable price range
            
            # Check model accuracy
            if "model_metrics" in prediction_result:
                metrics = prediction_result["model_metrics"]
                if "ensemble" in metrics:
                    accuracy = metrics["ensemble"].get("accuracy", 0)
                    # Deep learning should achieve reasonable accuracy
                    assert accuracy > 70  # At least 70% accuracy


if __name__ == "__main__":
    pytest.main([__file__, "-v"])