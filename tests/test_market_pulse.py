"""Tests for market_pulse module."""

import pytest
from unittest.mock import MagicMock, patch, Mock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.exceptions import InvalidTickerError, DataFetchError, DataProcessingError


# Mock stock data for testing
def create_mock_stock_data(days=30):
    """Create mock stock data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    data = {
        'Open': np.random.uniform(100, 110, days),
        'High': np.random.uniform(110, 120, days),
        'Low': np.random.uniform(90, 100, days),
        'Close': np.random.uniform(100, 110, days),
        'Volume': np.random.randint(1000000, 10000000, days),
        'MA20': np.random.uniform(100, 110, days),
        'RSI': np.random.uniform(30, 70, days),
        'MACD': np.random.uniform(-2, 2, days),
        'Signal': np.random.uniform(-2, 2, days)
    }
    return pd.DataFrame(data, index=dates)


def test_import_market_pulse():
    """Test that market_pulse module can be imported."""
    from modules import market_pulse
    assert hasattr(market_pulse, 'render')


class TestMarketPulseRender:
    """Test the main render function."""

    @patch('modules.market_pulse.st')
    @patch('modules.market_pulse.get_stock_data')
    @patch('modules.market_pulse.calculate_indicators')
    @patch('modules.market_pulse._create_technical_chart')
    @patch('modules.market_pulse._display_metrics')
    def test_render_success_with_valid_ticker(
        self, mock_display_metrics, mock_create_chart, mock_calc_indicators,
        mock_get_stock, mock_st
    ):
        """Test successful render with valid ticker."""
        from modules import market_pulse

        # Mock user inputs
        mock_st.text_input.return_value = "SPY"
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
        mock_st.title.assert_called_once_with("📊 Market Pulse")
        mock_get_stock.assert_called_once_with("SPY", period="1y", interval="1d")
        mock_calc_indicators.assert_called_once_with(mock_df)
        mock_display_metrics.assert_called_once_with(mock_df, "SPY")
        mock_create_chart.assert_called_once_with(mock_df, "SPY")
        mock_st.plotly_chart.assert_called_once()

    @patch('modules.market_pulse.st')
    def test_render_warning_on_empty_ticker(self, mock_st):
        """Test render shows warning when ticker is empty."""
        from modules import market_pulse

        # Mock empty ticker
        mock_st.text_input.return_value = ""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Call render
        market_pulse.render()

        # Should show warning and return early
        mock_st.warning.assert_called_once_with("⚠️ Please enter a ticker symbol")

    @patch('modules.market_pulse.st')
    @patch('modules.market_pulse.get_stock_data')
    def test_render_error_on_no_data(self, mock_get_stock, mock_st):
        """Test render shows error when no data is returned."""
        from modules import market_pulse

        # Mock inputs
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

    @patch('modules.market_pulse.st')
    @patch('modules.market_pulse.get_stock_data')
    def test_render_handles_invalid_ticker_error(self, mock_get_stock, mock_st):
        """Test render handles InvalidTickerError."""
        from modules import market_pulse

        # Mock inputs
        mock_st.text_input.return_value = "BADTICKER"
        mock_st.selectbox.side_effect = ["1y", "1d"]
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Mock error
        mock_get_stock.side_effect = InvalidTickerError("Invalid ticker: BADTICKER")

        # Call render
        market_pulse.render()

        # Should show error and info
        assert mock_st.error.called
        assert mock_st.info.called

    @patch('modules.market_pulse.st')
    @patch('modules.market_pulse.get_stock_data')
    def test_render_handles_data_fetch_error(self, mock_get_stock, mock_st):
        """Test render handles DataFetchError."""
        from modules import market_pulse

        # Mock inputs
        mock_st.text_input.return_value = "SPY"
        mock_st.selectbox.side_effect = ["1y", "1d"]
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Mock error
        mock_get_stock.side_effect = DataFetchError("Network error")

        # Call render
        market_pulse.render()

        # Should show error
        assert mock_st.error.called
        error_msg = mock_st.error.call_args[0][0]
        assert "Failed to fetch data" in error_msg


class TestDisplayMetrics:
    """Test the _display_metrics function."""

    @patch('modules.market_pulse.st')
    def test_display_metrics_calculates_delta(self, mock_st):
        """Test metrics display calculates price delta correctly."""
        from modules.market_pulse import _display_metrics

        # Create test data
        df = create_mock_stock_data(days=5)
        df.iloc[-1, df.columns.get_loc('Close')] = 105.0
        df.iloc[-2, df.columns.get_loc('Close')] = 100.0

        # Call function
        _display_metrics(df, "SPY")

        # Verify metric was called
        mock_st.metric.assert_called_once()
        call_args = mock_st.metric.call_args[1]

        # Check label and value
        assert "SPY" in call_args['label']
        assert "$105.00" in call_args['value']
        assert "5.00" in call_args['delta']  # Delta of 5.0


class TestCreateTechnicalChart:
    """Test the _create_technical_chart function."""

    def test_create_chart_returns_figure(self):
        """Test chart creation returns a Plotly Figure."""
        from modules.market_pulse import _create_technical_chart
        import plotly.graph_objects as go

        # Create test data
        df = create_mock_stock_data()

        # Call function
        fig = _create_technical_chart(df, "SPY")

        # Assertions
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0  # Has traces

    def test_chart_has_four_panels(self):
        """Test chart has 4 subplots (Price, RSI, MACD, Volume)."""
        from modules.market_pulse import _create_technical_chart

        # Create test data
        df = create_mock_stock_data()

        # Call function
        fig = _create_technical_chart(df, "SPY")

        # Check subplot structure
        assert fig.layout.xaxis is not None
        assert fig.layout.xaxis2 is not None  # RSI subplot
        assert fig.layout.xaxis3 is not None  # MACD subplot
        assert fig.layout.xaxis4 is not None  # Volume subplot

    def test_chart_includes_candlestick_trace(self):
        """Test chart includes candlestick price data."""
        from modules.market_pulse import _create_technical_chart
        import plotly.graph_objects as go

        # Create test data
        df = create_mock_stock_data()

        # Call function
        fig = _create_technical_chart(df, "SPY")

        # Find candlestick trace
        candlestick_traces = [t for t in fig.data if isinstance(t, go.Candlestick)]
        assert len(candlestick_traces) > 0

    def test_chart_includes_volume_bars(self):
        """Test chart includes volume bar chart."""
        from modules.market_pulse import _create_technical_chart
        import plotly.graph_objects as go

        # Create test data
        df = create_mock_stock_data()

        # Call function
        fig = _create_technical_chart(df, "SPY")

        # Find bar trace (volume)
        bar_traces = [t for t in fig.data if isinstance(t, go.Bar)]
        assert len(bar_traces) > 0
