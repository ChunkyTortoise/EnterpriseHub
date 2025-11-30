"""Tests for data_loader module."""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from utils.data_loader import get_stock_data, calculate_indicators
from utils.exceptions import InvalidTickerError, DataFetchError, DataProcessingError


class TestGetStockData:
    """Test suite for get_stock_data function."""
    
    def test_get_stock_data_validates_empty_ticker(self):
        """Test that empty ticker raises  InvalidTickerError."""
        with pytest.raises(InvalidTickerError):
            get_stock_data("")
    
    def test_get_stock_data_strips_whitespace(self, sample_stock_data):
        """Test that ticker whitespace is stripped."""
        with patch('utils.data_loader.yf.download') as mock_download:
            mock_download.return_value = sample_stock_data
            
            # Should work with whitespace
            result = get_stock_data("  AAPL  ")
            assert result is not None
            
            # Verify it was called with uppercase stripped version
            mock_download.assert_called_once()
            args = mock_download.call_args
            assert "AAPL" in str(args)
    
    def test_get_stock_data_raises_on_empty_dataframe(self):
        """Test that empty DataFrame raises InvalidTickerError."""
        with patch('utils.data_loader.yf.download') as mock_download:
            mock_download.return_value = pd.DataFrame()
            
            with pytest.raises(InvalidTickerError):
                get_stock_data("INVALID")
    
    def test_get_stock_data_handles_api_error(self):
        """Test that API errors are caught and wrapped."""
        with patch('utils.data_loader.yf.download') as mock_download:
            mock_download.side_effect = Exception("API Error")
            
            with pytest.raises(DataFetchError):
                get_stock_data("AAPL")
    
    def test_get_stock_data_success(self, sample_stock_data):
        """Test successful data fetch."""
        with patch('utils.data_loader.yf.download') as mock_download:
            mock_download.return_value = sample_stock_data
            
            result = get_stock_data("AAPL")
            assert result is not None
            assert len(result) == 30
            assert 'Close' in result.columns


class TestCalculateIndicators:
    """Test suite for calculate_indicators function."""
    
    def test_calculate_indicators_handles_none(self):
        """Test that None input returns None."""
        result = calculate_indicators(None)
        assert result is None
    
    def test_calculate_indicators_handles_empty_df(self):
        """Test that empty DataFrame is returned as-is."""
        df = pd.DataFrame()
        result = calculate_indicators(df)
        assert result.empty
    
    def test_calculate_indicators_adds_ma20(self, sample_stock_data):
        """Test that MA20 is calculated."""
        result = calculate_indicators(sample_stock_data.copy())
        assert 'MA20' in result.columns
        assert not result['MA20'].isna().all()
    
    def test_calculate_indicators_adds_rsi(self, sample_stock_data):
        """Test that RSI is calculated."""
        result = calculate_indicators(sample_stock_data.copy())
        assert 'RSI' in result.columns
        assert not result['RSI'].isna().all()
    
    def test_calculate_indicators_adds_macd(self, sample_stock_data):
        """Test that MACD and Signal are calculated."""
        result = calculate_indicators(sample_stock_data.copy())
        assert 'MACD' in result.columns
        assert 'Signal' in result.columns
    
    def test_calculate_indicators_handles_multiindex(self):
        """Test that MultiIndex columns are flattened."""
        # Create MultiIndex DataFrame (like yfinance returns)
        dates = pd.date_range('2023-01-01', periods=30)
        columns = pd.MultiIndex.from_product([['AAPL'], ['Open', 'High', 'Low', 'Close', 'Volume']])
        data = {
            ('AAPL', 'Open'): [100] * 30,
            ('AAPL', 'High'): [105] * 30,
            ('AAPL', 'Low'): [95] * 30,
            ('AAPL', 'Close'): [102] * 30,
            ('AAPL', 'Volume'): [1000000] * 30,
        }
        df = pd.DataFrame(data, index=dates)
        
        result = calculate_indicators(df)
        assert isinstance(result.columns, pd.Index)
        assert 'MA20' in result.columns
    
    def test_calculate_indicators_raises_on_missing_columns(self):
        """Test that missing required columns raise error."""
        # DataFrame with missing 'Close' column
        df = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
        })
        
        with pytest.raises(DataProcessingError):
            calculate_indicators(df)
