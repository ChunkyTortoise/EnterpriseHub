"""
Unit tests for Market Pulse module.
"""

import pandas as pd
import pytest
from unittest.mock import MagicMock, patch
from modules import market_pulse
from utils.exceptions import InvalidTickerError, DataFetchError, DataProcessingError


def create_mock_stock_data(days=10):
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start="2023-01-01", periods=days)
    data = {
        "Open": [100.0] * days,
        "High": [105.0] * days,
        "Low": [95.0] * days,
        "Close": [102.0] * days,
        "Volume": [1000] * days,
        "RSI": [50.0] * days,
        "MACD": [0.0] * days,
        "Signal": [0.0] * days,
    }
    return pd.DataFrame(data, index=dates)


class TestMarketPulseRender:
    """Test the render function of Market Pulse."""

    @patch("modules.market_pulse.ui.section_header")
    @patch("modules.market_pulse.st")
    @patch("modules.market_pulse.get_stock_data")
    @patch("modules.market_pulse.calculate_indicators")
    @patch("modules.market_pulse._create_technical_chart")
    @patch("modules.market_pulse._display_metrics")
    def test_render_success_with_valid_ticker(
        self,
        mock_display_metrics,
        mock_create_chart,
        mock_calc_indicators,
        mock_get_stock,
        mock_st,
        mock_section,
    ):
        """Test successful render with valid ticker."""
        from modules import market_pulse

        # Mock user inputs
        mock_st.checkbox.return_value = False # Disable demo mode
        mock_st.text_input.side_effect = ["SPY", ""]  # Ticker, then empty comparison
        mock_st.selectbox.side_effect = ["1y", "1d"]
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Mock data
        mock_df = create_mock_stock_data()
        mock_get_stock.return_value = mock_df
        mock_calc_indicators.return_value = mock_df
        mock_create_chart.return_value = MagicMock()

        # Call render
        market_pulse.render()

        # Assertions
        mock_section.assert_called_once_with(
            "Market Pulse", "Real-Time Technical Analysis Dashboard"
        )
        # Verify get_stock_data call includes use_demo from checkbox mock
        mock_get_stock.assert_called_once()
        args, kwargs = mock_get_stock.call_args
        assert args[0] == "SPY"
        assert kwargs["period"] == "1y"
        assert kwargs["interval"] == "1d"
        assert kwargs["use_demo"] == False

    @patch("modules.market_pulse.st")
    def test_render_warning_on_empty_ticker(self, mock_st):
        """Test render shows warning when ticker is empty."""
        from modules import market_pulse

        # Mock empty ticker
        mock_st.checkbox.return_value = False
        mock_st.text_input.return_value = ""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Call render
        market_pulse.render()

        # Should show warning and return early
        mock_st.warning.assert_called_once_with("⚠️ Please enter a ticker symbol")

    @patch("modules.market_pulse.st")
    @patch("modules.market_pulse.get_stock_data")
    def test_render_error_on_no_data(self, mock_get_stock, mock_st):
        """Test render shows error when no data is returned."""
        from modules import market_pulse

        # Mock inputs
        mock_st.checkbox.return_value = False
        mock_st.text_input.return_value = "INVALID"
        mock_st.selectbox.side_effect = ["1y", "1d"]
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Mock no data
        mock_get_stock.return_value = None

        # Call render
        market_pulse.render()

        # Should show error
        mock_st.error.assert_called_once()
        error_msg = mock_st.error.call_args[0][0]
        assert "No data found" in error_msg


class TestDisplayMetrics:
    """Test the _display_metrics helper function."""

    @patch("modules.market_pulse.ui.animated_metric")
    @patch("modules.market_pulse.st")
    def test_display_metrics_calculates_delta(self, mock_st, mock_animated):
        """Test metrics display calculates price delta correctly."""
        from modules.market_pulse import _display_metrics

        # Create test data
        df = create_mock_stock_data(days=5)
        df.iloc[-1, df.columns.get_loc("Close")] = 105.0
        df.iloc[-2, df.columns.get_loc("Close")] = 100.0

        # Call function
        _display_metrics(df, "SPY")

        # Verify animated_metric was called
        mock_animated.assert_called_once()
        kwargs = mock_animated.call_args[1]
        assert "105.00" in kwargs["value"]
        assert "+5.00" in kwargs["delta"]
        assert "5.00%" in kwargs["delta"]
        assert kwargs["color"] == "success"


class TestPredictiveIndicators:
    """Test predictive indicator logic and display."""

    def test_predict_trend_bullish(self):
        """Test bullish trend prediction."""
        rsi = 25.0  # RSI < 30 is Oversold (Bullish signal)
        macd = 0.5
        signal = 0.2  # Bullish crossover

        trend, conf, reason = market_pulse._predict_trend(rsi, macd, signal)
        assert trend == "Bullish"
        assert conf > 0.5

    def test_predict_trend_bearish(self):
        """Test bearish trend prediction."""
        rsi = 75.0  # Overbought
        macd = -0.5
        signal = -0.2  # Bearish crossover

        trend, conf, reason = market_pulse._predict_trend(rsi, macd, signal)
        assert trend == "Bearish"
        assert conf > 0.5

    @patch("modules.market_pulse.ui.animated_metric")
    @patch("modules.market_pulse.st")
    def test_display_predictive_indicators(self, mock_st, mock_animated):
        """Test predictive indicators display."""
        from modules.market_pulse import _display_predictive_indicators

        # Create test data with known values
        df = create_mock_stock_data()
        df.iloc[-1, df.columns.get_loc("RSI")] = 65.0
        df.iloc[-1, df.columns.get_loc("MACD")] = 1.5
        df.iloc[-1, df.columns.get_loc("Signal")] = 1.0

        # Mock columns
        mock_cols = [MagicMock() for _ in range(3)]
        mock_st.columns.return_value = mock_cols

        # Call function
        _display_predictive_indicators(df, "SPY")

        # Verify markdown was called
        assert mock_st.markdown.called
        # Verify metrics were called (at least one)
        assert mock_animated.called