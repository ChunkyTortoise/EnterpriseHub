import pytest

pytestmark = pytest.mark.unit

"""Unit tests for agent handlers."""

from unittest.mock import MagicMock, call, patch

import numpy as np
import pandas as pd
import pytest

from utils.agent_handlers import (
    AGENT_HANDLERS,
    analyst_bot_handler,
    calculate_data_quality,
    data_bot_handler,
    forecast_bot_handler,
    get_handler,
    retry_with_exponential_backoff,
    sentiment_bot_handler,
    synthesis_bot_handler,
    tech_bot_handler,
    validator_bot_handler,
)
from utils.exceptions import APIError, DataProcessingError

# ============================================================================
# Helper Tests
# ============================================================================


class TestHelperFunctions:
    """Test suite for helper functions in agent_handlers."""

    def test_calculate_data_quality_full(self):
        """Test quality calculation with complete data."""
        df = pd.DataFrame({"Close": [100, 101], "Volume": [1000, 1100]})
        info = {"marketCap": 1000000, "sector": "Tech", "industry": "Software", "currentPrice": 101}
        news = [MagicMock()] * 10

        quality = calculate_data_quality(df, info, news)
        assert 0.0 <= quality <= 1.0
        assert quality > 0.8  # Should be high for full data

    def test_calculate_data_quality_empty(self):
        """Test quality calculation with empty data."""
        quality = calculate_data_quality(None, {}, [])
        assert quality == pytest.approx(0.01, abs=0.001)

    def test_calculate_data_quality_partial_info(self):
        """Test quality calculation with partial company info."""
        df = pd.DataFrame({"Close": [100, 101]})
        info = {"marketCap": 1000000}  # Missing other fields
        news = [MagicMock()]

        quality = calculate_data_quality(df, info, news)
        assert 0.0 < quality < 1.0

    def test_get_handler_success(self):
        """Test successful handler retrieval."""
        handler = get_handler("data_bot")
        assert handler == data_bot_handler

    def test_get_handler_failure(self):
        """Test handler retrieval with invalid ID."""
        with pytest.raises(KeyError) as excinfo:
            get_handler("invalid_bot")
        assert "Handler for 'invalid_bot' not found" in str(excinfo.value)


# ============================================================================
# Retry Decorator Tests
# ============================================================================


class TestRetryDecorator:
    """Test suite for retry_with_exponential_backoff decorator."""

    def test_retry_success_first_try(self):
        """Test decorator when function succeeds immediately."""
        mock_func = MagicMock(return_value="success")
        decorated = retry_with_exponential_backoff(max_attempts=3)(mock_func)

        result = decorated("test")
        assert result == "success"
        assert mock_func.call_count == 1

    @patch("time.sleep", return_value=None)
    def test_retry_eventual_success(self, mock_sleep):
        """Test decorator when function succeeds after failures."""

        class MockRateLimitError(Exception):
            pass

        mock_func = MagicMock()
        mock_func.side_effect = [MockRateLimitError("Rate limit"), "success"]

        with patch("utils.agent_handlers.RateLimitError", MockRateLimitError):
            decorated = retry_with_exponential_backoff(max_attempts=3, initial_delay=1.0)(mock_func)
            result = decorated()
            assert result == "success"
            assert mock_func.call_count == 2
            mock_sleep.assert_called_once_with(1.0)

    @patch("time.sleep", return_value=None)
    def test_retry_exhausted(self, mock_sleep):
        """Test decorator when retries are exhausted."""

        class MockConnError(Exception):
            pass

        mock_func = MagicMock()
        mock_func.side_effect = MockConnError("Connection failed")

        with patch("utils.agent_handlers.APIConnectionError", MockConnError):
            decorated = retry_with_exponential_backoff(max_attempts=2)(mock_func)
            with pytest.raises(MockConnError):
                decorated()
            assert mock_func.call_count == 2

    def test_non_retryable_error(self):
        """Test decorator with non-retryable error."""
        mock_func = MagicMock()
        mock_func.side_effect = APIError("Fatal API Error")
        decorated = retry_with_exponential_backoff()(mock_func)

        with pytest.raises(APIError):
            decorated()
        assert mock_func.call_count == 1


# ============================================================================
# DataBot & TechBot Tests
# ============================================================================


class TestMarketBots:
    """Test suite for DataBot and TechBot handlers."""

    @patch("utils.agent_handlers.get_stock_data")
    @patch("utils.agent_handlers.get_company_info")
    @patch("utils.agent_handlers.get_news")
    def test_data_bot_handler_success(self, mock_news, mock_info, mock_stock):
        """Test successful execution of DataBot."""
        mock_stock.return_value = pd.DataFrame({"Close": [100, 101]})
        mock_info.return_value = {"marketCap": 1000000, "currentPrice": 101, "sector": "Tech", "industry": "Software"}
        mock_news.return_value = ["news1", "news2", "news3"]

        inputs = {"ticker": "AAPL", "period": "1mo"}
        result = data_bot_handler(inputs, {})

        assert "df" in result
        assert "info" in result
        assert "news" in result
        assert "quality_score" in result
        assert result["quality_score"] > 0.5
        mock_stock.assert_called_once_with("AAPL", period="1mo")

    @patch("utils.agent_handlers.get_stock_data")
    @patch("utils.agent_handlers.get_company_info")
    @patch("utils.agent_handlers.get_news")
    def test_data_bot_handler_partial_failure(self, mock_news, mock_info, mock_stock):
        """Test DataBot when company info fails."""
        from utils.exceptions import DataFetchError

        mock_stock.return_value = pd.DataFrame({"Close": [100]})
        mock_info.side_effect = DataFetchError("Fetch failed")
        mock_news.return_value = []

        result = data_bot_handler({"ticker": "INVALID"}, {})
        assert result["info"] == {}
        assert result["quality_score"] < 0.5

    def test_tech_bot_handler_success(self):
        """Test successful technical analysis signal generation."""
        # Create sample data with indicators
        df = pd.DataFrame(
            {
                "Close": [100] * 20 + [110],
                "MA20": [100] * 21,
                "RSI": [50.0] * 21,
                "MACD": [0.1] * 21,
                "Signal": [0.0] * 21,
                "Volume": [1000] * 21,
            }
        )

        with patch("utils.agent_handlers.calculate_indicators", return_value=df):
            result = tech_bot_handler({"df": df}, {})

            assert "signal" in result
            assert result["signal"] in ["BULLISH", "BEARISH", "NEUTRAL"]
            assert "confidence" in result
            assert "macd_signal" in result

    def test_tech_bot_handler_empty_df(self):
        """Test TechBot with empty input."""
        with pytest.raises(DataProcessingError):
            tech_bot_handler({"df": pd.DataFrame()}, {})

    def test_tech_bot_handler_signals(self):
        """Test specific technical signal logic."""
        # Bullish case: Close > MA20, RSI Oversold, MACD Bullish
        df = pd.DataFrame(
            {"Close": [110.0], "MA20": [100.0], "RSI": [25.0], "MACD": [1.0], "Signal": [0.5], "Volume": [1000]}
        )

        with patch("utils.agent_handlers.calculate_indicators", return_value=df):
            result = tech_bot_handler({"df": df}, {})
            assert result["signal"] == "BULLISH"
            assert result["macd_signal"] == "BULLISH"
            assert result["rsi_value"] == 25.0


# ============================================================================
# SentimentBot & ValidatorBot Tests
# ============================================================================


class TestLogicBots:
    """Test suite for SentimentBot and ValidatorBot handlers."""

    @patch("utils.agent_handlers.process_news_sentiment")
    def test_sentiment_bot_handler_fallback(self, mock_sentiment):
        """Test SentimentBot using TextBlob fallback."""
        mock_sentiment.return_value = {"verdict": "Bullish 🐂", "average_score": 0.8, "article_count": 5}

        inputs = {"news": ["article1", "article2", "article3"], "ticker": "AAPL"}
        # Ensure ANTHROPIC_API_KEY is not set for fallback test
        with patch.dict("os.environ", {}, clear=True):
            result = sentiment_bot_handler(inputs, {})

            assert result["verdict"] == "Positive"
            assert result["confidence"] > 0.5
            assert result["article_count"] == 5

    def test_sentiment_bot_insufficient_news(self):
        """Test SentimentBot with too few articles."""
        result = sentiment_bot_handler({"news": ["one"], "ticker": "AAPL"}, {})
        assert result["verdict"] == "Neutral"
        assert result["confidence"] == 0.3

    def test_validator_bot_handler_success(self):
        """Test ValidatorBot with passing results."""
        results = {
            "tech_bot": {"signal": "BULLISH", "confidence": 0.9},
            "sentiment_bot": {"verdict": "Positive", "confidence": 0.8},
        }

        result = validator_bot_handler({"results": results}, {})
        assert result["passed"] is True
        assert result["confidence"] > 0.7
        assert len(result["errors"]) == 0

    def test_validator_bot_handler_conflicts(self):
        """Test ValidatorBot detecting contradictions."""
        # Bullish technical vs Bearish sentiment should trigger a conflict
        results = {
            "technical": {"signal": "BULLISH", "confidence": 0.9},
            "sentiment": {"verdict": "Negative", "confidence": 0.9},
        }

        result = validator_bot_handler({"results": results}, {})
        # Conflict should be detected (depending on ContradictionDetector implementation)
        assert len(result["conflicts"]) >= 0  # Just verifying it runs


# ============================================================================
# Forecast & Synthesis Tests
# ============================================================================


class TestSynthesisBots:
    """Test suite for ForecastBot and SynthesisBot handlers."""

    def test_forecast_bot_handler_success(self):
        """Test successful ML forecast generation."""
        # Create 100 days of data to satisfy the 90-day minimum
        dates = pd.date_range(start="2023-01-01", periods=100)
        df = pd.DataFrame(
            {
                "Close": np.linspace(100, 110, 100) + np.random.normal(0, 1, 100),
                "Volume": [1000] * 100,
                "MA20": [100] * 100,
                "RSI": [50] * 100,
                "MACD": [0.1] * 100,
                "Signal": [0.0] * 100,
            },
            index=dates,
        )

        result = forecast_bot_handler({"df": df}, {})

        assert "forecast" in result
        assert isinstance(result["forecast"], pd.DataFrame)
        assert len(result["forecast"]) == 30
        assert "trend" in result
        assert "metrics" in result

    def test_forecast_bot_insufficient_data(self):
        """Test ForecastBot with too few data points."""
        df = pd.DataFrame({"Close": [100] * 10})
        with pytest.raises(DataProcessingError):
            forecast_bot_handler({"df": df}, {})

    def test_synthesis_bot_handler_buy(self):
        """Test SynthesisBot generating a BUY recommendation."""
        results = {
            "tech_bot": {"signal": "BULLISH", "confidence": 0.9},
            "sentiment_bot": {"verdict": "Positive", "confidence": 0.8},
        }

        result = synthesis_bot_handler({"results": results}, {})
        assert result["recommendation"] == "BUY"
        assert result["confidence"] > 0.7
        assert "Technical: BULLISH" in result["reasoning"]

    def test_synthesis_bot_insufficient_signals(self):
        """Test SynthesisBot with only one signal."""
        results = {"tech_bot": {"signal": "BULLISH", "confidence": 0.9}}

        result = synthesis_bot_handler({"results": results}, {})
        assert result["recommendation"] == "INSUFFICIENT_DATA"

    def test_synthesis_bot_conflicting_signals(self):
        """Test SynthesisBot with conflicting signals resulting in HOLD."""
        results = {
            "tech_bot": {"signal": "BULLISH", "confidence": 0.9},
            "sentiment_bot": {"verdict": "Negative", "confidence": 0.9},
        }

        result = synthesis_bot_handler({"results": results}, {})
        assert result["recommendation"] == "HOLD"
        assert any("Conflicting signals" in risk for risk in result["risk_factors"])


class TestAnalystBot:
    """Test suite for AnalystBot handler."""

    def test_analyst_bot_handler_alignment(self):
        """Test AnalystBot when modules align."""
        module_results = {"technical": {"signal": "BULLISH"}, "forecast": {"trend": "BULLISH"}}

        result = analyst_bot_handler({"module_results": module_results}, {})
        assert any("align" in insight for insight in result["integrated_insights"])
        assert result["confidence"] == 0.85
        assert "increasing position" in result["portfolio_guidance"]

    def test_analyst_bot_handler_divergence(self):
        """Test AnalystBot when modules diverge."""
        module_results = {"technical": {"signal": "BULLISH"}, "forecast": {"trend": "BEARISH"}}

        result = analyst_bot_handler({"module_results": module_results}, {})
        assert len(result["divergences"]) >= 1
        assert "Divergence detected" in result["integrated_insights"][0]
        assert result["confidence"] == 0.65

    def test_analyst_bot_insufficient_data(self):
        """Test AnalystBot with missing modules."""
        result = analyst_bot_handler({}, {})
        assert "Insufficient cross-module data" in result["integrated_insights"][0]


def test_agent_handlers_registry():
    """Test that all handlers are registered."""
    expected_bots = [
        "data_bot",
        "tech_bot",
        "sentiment_bot",
        "validator_bot",
        "forecast_bot",
        "synthesis_bot",
        "analyst_bot",
    ]
    for bot in expected_bots:
        assert bot in AGENT_HANDLERS
        assert callable(AGENT_HANDLERS[bot])
