"""Unit tests for Smart Forecast Engine."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from modules import smart_forecast

@pytest.fixture
def sample_stock_data():
    """Create sample stock dataframe."""
    dates = pd.date_range(start='2023-01-01', periods=100)
    data = {
        'Close': np.linspace(100, 200, 100) + np.random.normal(0, 5, 100),
        'Volume': np.random.randint(1000, 5000, 100),
        'RSI': np.random.uniform(30, 70, 100),
        'MACD': np.random.uniform(-2, 2, 100),
        'Signal_Line': np.random.uniform(-2, 2, 100),
        'SMA_20': np.linspace(100, 200, 100),
        'SMA_50': np.linspace(100, 200, 100)
    }
    return pd.DataFrame(data, index=dates)

def test_prepare_features(sample_stock_data):
    """Test feature engineering logic."""
    df = smart_forecast._prepare_features(sample_stock_data)
    
    # Check if Lag columns were created
    assert 'Close_Lag_1' in df.columns
    assert 'Close_Lag_5' in df.columns
    
    # Check if rows with NaNs (due to lags) were dropped
    # Lag 5 introduces 5 NaNs, so length should be 100 - 5 = 95
    assert len(df) == 95

@patch('modules.smart_forecast.RandomForestRegressor')
def test_train_and_predict(mock_rf, sample_stock_data):
    """Test model training and prediction flow."""
    # Setup mock
    mock_model = MagicMock()
    # Dynamic side_effect to match input shape
    def predict_side_effect(X):
        return np.array([150.0] * len(X))
    mock_model.predict.side_effect = predict_side_effect
    
    mock_rf.return_value = mock_model
    
    # Run function
    df = smart_forecast._prepare_features(sample_stock_data)
    model, metrics, pred_df = smart_forecast._train_and_predict(df, future_days=10)
    
    # Assertions
    assert 'MAE' in metrics
    assert 'R2' in metrics
    assert len(pred_df) == 10
    assert 'Predicted_Close' in pred_df.columns
    
    # Verify model was trained
    mock_model.fit.assert_called_once()

@patch('modules.smart_forecast.st')
@patch('modules.smart_forecast.get_stock_data')
@patch('modules.smart_forecast.calculate_indicators')
def test_render_flow(mock_calc, mock_get, mock_st):
    """Test the main render function execution path."""
    # Setup mocks
    mock_st.text_input.return_value = "TEST"
    mock_st.slider.return_value = 30
    mock_st.button.return_value = True
    # Fix st.columns unpacking
    mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
    
    # Mock data
    dates = pd.date_range(start='2023-01-01', periods=50)
    mock_df = pd.DataFrame({
        'Close': [100.0] * 50,
        'Volume': [1000] * 50,
        'RSI': [50.0] * 50,
        'MACD': [0.0] * 50,
        'Signal_Line': [0.0] * 50,
        'SMA_20': [100.0] * 50,
        'SMA_50': [100.0] * 50
    }, index=dates)
    
    mock_get.return_value = mock_df
    mock_calc.return_value = mock_df # Return same df
    
    # Run render
    smart_forecast.render()
    
    # Check that success components were called
    mock_st.plotly_chart.assert_called()
    mock_st.error.assert_not_called()
