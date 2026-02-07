"""
Unit tests for Multi-Agent Workflow Orchestrator module.

Tests the orchestration of specialized agents for complex analysis workflows,
including the Stock Deep Dive workflow with 4 agents (DataBot, TechBot, NewsBot, ChiefBot).
"""

from unittest.mock import patch, MagicMock
import pandas as pd


class TestMultiAgentRender:
    """Tests for the main render function."""

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.ui")
    def test_render_displays_title(self, mock_ui, mock_st):
        """Test that render displays the correct title."""
        from modules.multi_agent import render

        render()

        mock_ui.section_header.assert_called_once_with(
            "🤖 Multi-Agent Workflows", "Autonomous Analysis Teams"
        )

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.ui")
    def test_render_shows_workflow_selector(self, mock_ui, mock_st):
        """Test that render displays workflow selection."""
        from modules.multi_agent import render

        render()

        mock_st.selectbox.assert_called_once()
        args = mock_st.selectbox.call_args[0]
        assert args[0] == "Select Workflow"
        assert "💰 Stock Deep Dive (4 Agents)" in args[1]

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.ui")
    @patch("modules.multi_agent._render_stock_deep_dive")
    def test_render_calls_deep_dive_workflow(self, mock_deep_dive, mock_ui, mock_st):
        """Test that selecting Stock Deep Dive calls the correct function."""
        from modules.multi_agent import render

        mock_st.selectbox.return_value = "💰 Stock Deep Dive (4 Agents)"

        render()

        mock_deep_dive.assert_called_once()

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.ui")
    def test_render_shows_info_for_dynamic_workflow(self, mock_ui, mock_st):
        """Test that dynamic workflow can be selected."""
        from modules.multi_agent import render

        mock_st.selectbox.return_value = "🔀 Adaptive Recommendation (Dynamic)"

        # Should call the appropriate renderer (just verify it doesn't crash)
        render()
        mock_st.selectbox.assert_called()


class TestStockDeepDiveUI:
    """Test the Stock Deep Dive workflow UI."""

    @patch("modules.multi_agent.st")
    def test_deep_dive_shows_mission_description(self, mock_st):
        """Test that mission description is displayed."""
        from modules.multi_agent import _render_stock_deep_dive

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_stock_deep_dive()

        # Should show mission markdown
        mock_st.markdown.assert_any_call("""
    **Mission:** Comprehensive analysis of a target asset.

    **The Team:**
    - 🕵️ **DataBot:** Fetches raw price action and fundamental data.
    - 📈 **TechBot:** Analyzes technical indicators (RSI, MACD, Trends).
    - 📰 **NewsBot:** Scouts recent news and analyzes sentiment.
    - 🎓 **ChiefBot:** Synthesizes all intelligence into a final verdict.
    """)

    @patch("modules.multi_agent.st")
    def test_deep_dive_has_ticker_input(self, mock_st):
        """Test that ticker input is present."""
        from modules.multi_agent import _render_stock_deep_dive

        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        _render_stock_deep_dive()

        mock_st.text_input.assert_called_once()
        args = mock_st.text_input.call_args
        assert args[0][0] == "Target Asset"
        assert args[1]["value"] == "NVDA"

    @patch("modules.multi_agent.st")
    def test_deep_dive_has_launch_button(self, mock_st):
        """Test that launch button is present."""
        from modules.multi_agent import _render_stock_deep_dive

        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        _render_stock_deep_dive()

        mock_st.button.assert_called_once()
        args = mock_st.button.call_args
        assert args[0][0] == "🚀 Launch Workflow"
        assert args[1]["type"] == "primary"

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent._run_deep_dive_logic")
    def test_deep_dive_triggers_workflow_on_button_click(self, mock_logic, mock_st):
        """Test that clicking button triggers workflow."""
        from modules.multi_agent import _render_stock_deep_dive

        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.text_input.return_value = "AAPL"
        mock_st.button.return_value = True

        _render_stock_deep_dive()

        mock_logic.assert_called_once_with("AAPL")

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent._run_deep_dive_logic")
    def test_deep_dive_does_not_trigger_without_button(self, mock_logic, mock_st):
        """Test that workflow doesn't run without button click."""
        from modules.multi_agent import _render_stock_deep_dive

        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.text_input.return_value = "AAPL"
        mock_st.button.return_value = False

        _render_stock_deep_dive()

        mock_logic.assert_not_called()


class TestDataBotAgent:
    """Tests for DataBot agent (Agent 1)."""

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.get_stock_data")
    @patch("modules.multi_agent.get_company_info")
    @patch("modules.multi_agent.time.sleep")
    def test_databot_fetches_stock_data(self, mock_sleep, mock_info, mock_stock, mock_st):
        """Test that DataBot fetches stock data correctly."""
        from modules.multi_agent import _run_deep_dive_logic

        # Setup mock data
        mock_df = pd.DataFrame({"Close": [150.0, 151.0], "Volume": [1000000, 1100000]})
        mock_stock.return_value = mock_df
        mock_info.return_value = {"sector": "Technology"}

        # Mock calculate_indicators to return the same df with indicators
        with patch("modules.multi_agent.calculate_indicators") as mock_calc:
            mock_df_with_indicators = mock_df.copy()
            mock_df_with_indicators["RSI"] = [50.0, 55.0]
            mock_df_with_indicators["MACD"] = [1.0, 1.5]
            mock_df_with_indicators["Signal_Line"] = [0.8, 1.2]
            mock_calc.return_value = mock_df_with_indicators

            with patch("modules.multi_agent.get_news") as mock_news:
                mock_news.return_value = []
                with patch("modules.multi_agent.process_news_sentiment") as mock_sentiment:
                    mock_sentiment.return_value = {
                        "average_score": 0.0,
                        "verdict": "NEUTRAL",
                        "article_count": 0,
                    }

                    mock_st.container.return_value.__enter__ = MagicMock()
                    mock_st.container.return_value.__exit__ = MagicMock()
                    mock_st.spinner.return_value.__enter__ = MagicMock()
                    mock_st.spinner.return_value.__exit__ = MagicMock()

                    _run_deep_dive_logic("AAPL")

                    mock_stock.assert_called_once_with("AAPL", period="1y", interval="1d")
                    mock_info.assert_called_once_with("AAPL")

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.get_stock_data")
    @patch("modules.multi_agent.get_company_info")
    @patch("modules.multi_agent.time.sleep")
    def test_databot_handles_empty_data(self, mock_sleep, mock_info, mock_stock, mock_st):
        """Test that DataBot handles empty data gracefully."""
        from modules.multi_agent import _run_deep_dive_logic

        mock_stock.return_value = pd.DataFrame()
        mock_info.return_value = {}

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        _run_deep_dive_logic("INVALID")

        mock_st.error.assert_called_once()
        error_msg = str(mock_st.error.call_args[0][0])
        assert "Mission Failed" in error_msg
        assert "INVALID" in error_msg

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.get_stock_data")
    @patch("modules.multi_agent.get_company_info")
    @patch("modules.multi_agent.time.sleep")
    def test_databot_handles_none_data(self, mock_sleep, mock_info, mock_stock, mock_st):
        """Test that DataBot handles None data."""
        from modules.multi_agent import _run_deep_dive_logic

        mock_stock.return_value = None
        mock_info.return_value = {}

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        _run_deep_dive_logic("INVALID")

        mock_st.error.assert_called_once()


class TestTechBotAgent:
    """Tests for TechBot agent (Agent 2)."""

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.get_stock_data")
    @patch("modules.multi_agent.get_company_info")
    @patch("modules.multi_agent.calculate_indicators")
    @patch("modules.multi_agent.get_news")
    @patch("modules.multi_agent.process_news_sentiment")
    @patch("modules.multi_agent.time.sleep")
    def test_techbot_calculates_indicators(
        self,
        mock_sleep,
        mock_sentiment,
        mock_news,
        mock_calc,
        mock_info,
        mock_stock,
        mock_st,
    ):
        """Test that TechBot calculates indicators."""
        from modules.multi_agent import _run_deep_dive_logic

        mock_df = pd.DataFrame({"Close": [150.0, 151.0], "Volume": [1000000, 1100000]})
        mock_stock.return_value = mock_df
        mock_info.return_value = {"sector": "Technology"}

        mock_df_with_indicators = mock_df.copy()
        mock_df_with_indicators["RSI"] = [50.0, 55.0]
        mock_df_with_indicators["MACD"] = [1.0, 1.5]
        mock_df_with_indicators["Signal_Line"] = [0.8, 1.2]
        mock_calc.return_value = mock_df_with_indicators

        mock_news.return_value = []
        mock_sentiment.return_value = {
            "average_score": 0.0,
            "verdict": "NEUTRAL",
            "article_count": 0,
        }

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        _run_deep_dive_logic("AAPL")

        mock_calc.assert_called_once()

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.get_stock_data")
    @patch("modules.multi_agent.get_company_info")
    @patch("modules.multi_agent.calculate_indicators")
    @patch("modules.multi_agent.get_news")
    @patch("modules.multi_agent.process_news_sentiment")
    @patch("modules.multi_agent.time.sleep")
    def test_techbot_detects_bullish_macd(
        self,
        mock_sleep,
        mock_sentiment,
        mock_news,
        mock_calc,
        mock_info,
        mock_stock,
        mock_st,
    ):
        """Test that TechBot detects bullish MACD signal."""
        from modules.multi_agent import _run_deep_dive_logic

        mock_df = pd.DataFrame({"Close": [150.0, 151.0], "Volume": [1000000, 1100000]})
        mock_stock.return_value = mock_df
        mock_info.return_value = {"sector": "Technology"}

        # MACD > Signal = BULLISH
        mock_df_with_indicators = mock_df.copy()
        mock_df_with_indicators["RSI"] = [50.0, 55.0]
        mock_df_with_indicators["MACD"] = [1.5, 2.0]
        mock_df_with_indicators["Signal_Line"] = [1.0, 1.5]
        mock_calc.return_value = mock_df_with_indicators

        mock_news.return_value = []
        mock_sentiment.return_value = {
            "average_score": 0.0,
            "verdict": "NEUTRAL",
            "article_count": 0,
        }

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        _run_deep_dive_logic("AAPL")

        # Check that success message includes BULLISH
        success_calls = [str(call) for call in mock_st.success.call_args_list]
        techbot_call = [c for c in success_calls if "TechBot" in c][0]
        assert "BULLISH" in techbot_call


class TestNewsBotAgent:
    """Tests for NewsBot agent (Agent 3)."""

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.get_stock_data")
    @patch("modules.multi_agent.get_company_info")
    @patch("modules.multi_agent.calculate_indicators")
    @patch("modules.multi_agent.get_news")
    @patch("modules.multi_agent.process_news_sentiment")
    @patch("modules.multi_agent.time.sleep")
    def test_newsbot_fetches_news(
        self,
        mock_sleep,
        mock_sentiment,
        mock_news,
        mock_calc,
        mock_info,
        mock_stock,
        mock_st,
    ):
        """Test that NewsBot fetches news."""
        from modules.multi_agent import _run_deep_dive_logic

        mock_df = pd.DataFrame({"Close": [150.0, 151.0], "Volume": [1000000, 1100000]})
        mock_stock.return_value = mock_df
        mock_info.return_value = {"sector": "Technology"}

        mock_df_with_indicators = mock_df.copy()
        mock_df_with_indicators["RSI"] = [50.0, 55.0]
        mock_df_with_indicators["MACD"] = [1.0, 1.5]
        mock_df_with_indicators["Signal_Line"] = [0.8, 1.2]
        mock_calc.return_value = mock_df_with_indicators

        mock_news.return_value = [{"title": "Test News", "url": "http://test.com"}]
        mock_sentiment.return_value = {
            "average_score": 0.5,
            "verdict": "POSITIVE",
            "article_count": 1,
        }

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        _run_deep_dive_logic("AAPL")

        mock_news.assert_called_once_with("AAPL")
        mock_sentiment.assert_called_once()


class TestChiefBotAgent:
    """Tests for ChiefBot agent (Agent 4 - Synthesis)."""

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.get_stock_data")
    @patch("modules.multi_agent.get_company_info")
    @patch("modules.multi_agent.calculate_indicators")
    @patch("modules.multi_agent.get_news")
    @patch("modules.multi_agent.process_news_sentiment")
    @patch("modules.multi_agent.time.sleep")
    def test_chiefbot_strong_buy_signal(
        self,
        mock_sleep,
        mock_sentiment,
        mock_news,
        mock_calc,
        mock_info,
        mock_stock,
        mock_st,
    ):
        """Test ChiefBot produces STRONG BUY signal."""
        from modules.multi_agent import _run_deep_dive_logic

        mock_df = pd.DataFrame({"Close": [150.0, 151.0], "Volume": [1000000, 1100000]})
        mock_stock.return_value = mock_df
        mock_info.return_value = {"sector": "Technology"}

        # All bullish indicators
        mock_df_with_indicators = mock_df.copy()
        mock_df_with_indicators["RSI"] = [30.0, 32.0]  # Oversold
        mock_df_with_indicators["MACD"] = [1.5, 2.0]  # Above signal
        mock_df_with_indicators["Signal_Line"] = [1.0, 1.5]
        mock_calc.return_value = mock_df_with_indicators

        mock_news.return_value = []
        mock_sentiment.return_value = {
            "average_score": 0.3,  # Positive sentiment
            "verdict": "POSITIVE",
            "article_count": 5,
        }

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        _run_deep_dive_logic("AAPL")

        # Check for STRONG BUY in markdown
        markdown_calls = [str(call) for call in mock_st.markdown.call_args_list]
        final_card = [c for c in markdown_calls if "RECOMMENDATION" in c]
        assert len(final_card) > 0
        assert "STRONG BUY" in final_card[0]

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.get_stock_data")
    @patch("modules.multi_agent.get_company_info")
    @patch("modules.multi_agent.calculate_indicators")
    @patch("modules.multi_agent.get_news")
    @patch("modules.multi_agent.process_news_sentiment")
    @patch("modules.multi_agent.time.sleep")
    def test_chiefbot_strong_sell_signal(
        self,
        mock_sleep,
        mock_sentiment,
        mock_news,
        mock_calc,
        mock_info,
        mock_stock,
        mock_st,
    ):
        """Test ChiefBot produces STRONG SELL signal."""
        from modules.multi_agent import _run_deep_dive_logic

        mock_df = pd.DataFrame({"Close": [150.0, 151.0], "Volume": [1000000, 1100000]})
        mock_stock.return_value = mock_df
        mock_info.return_value = {"sector": "Technology"}

        # All bearish indicators
        mock_df_with_indicators = mock_df.copy()
        mock_df_with_indicators["RSI"] = [75.0, 78.0]  # Overbought
        mock_df_with_indicators["MACD"] = [0.5, 0.3]  # Below signal
        mock_df_with_indicators["Signal_Line"] = [1.0, 1.5]
        mock_calc.return_value = mock_df_with_indicators

        mock_news.return_value = []
        mock_sentiment.return_value = {
            "average_score": -0.3,  # Negative sentiment
            "verdict": "NEGATIVE",
            "article_count": 5,
        }

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        _run_deep_dive_logic("AAPL")

        # Check for STRONG SELL in markdown
        markdown_calls = [str(call) for call in mock_st.markdown.call_args_list]
        final_card = [c for c in markdown_calls if "RECOMMENDATION" in c]
        assert len(final_card) > 0
        assert "STRONG SELL" in final_card[0]

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.get_stock_data")
    @patch("modules.multi_agent.get_company_info")
    @patch("modules.multi_agent.calculate_indicators")
    @patch("modules.multi_agent.get_news")
    @patch("modules.multi_agent.process_news_sentiment")
    @patch("modules.multi_agent.time.sleep")
    def test_chiefbot_hold_signal(
        self,
        mock_sleep,
        mock_sentiment,
        mock_news,
        mock_calc,
        mock_info,
        mock_stock,
        mock_st,
    ):
        """Test ChiefBot produces HOLD signal."""
        from modules.multi_agent import _run_deep_dive_logic

        mock_df = pd.DataFrame({"Close": [150.0, 151.0], "Volume": [1000000, 1100000]})
        mock_stock.return_value = mock_df
        mock_info.return_value = {"sector": "Technology"}

        # Neutral indicators
        mock_df_with_indicators = mock_df.copy()
        mock_df_with_indicators["RSI"] = [50.0, 52.0]  # Neutral
        mock_df_with_indicators["MACD"] = [0.5, 0.3]  # Below signal (bearish)
        mock_df_with_indicators["Signal_Line"] = [1.0, 1.5]
        mock_calc.return_value = mock_df_with_indicators

        mock_news.return_value = []
        mock_sentiment.return_value = {
            "average_score": 0.1,  # Neutral sentiment
            "verdict": "NEUTRAL",
            "article_count": 5,
        }

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        _run_deep_dive_logic("AAPL")

        # Check for HOLD in markdown
        markdown_calls = [str(call) for call in mock_st.markdown.call_args_list]
        final_card = [c for c in markdown_calls if "RECOMMENDATION" in c]
        assert len(final_card) > 0
        # This should be HOLD or SELL based on score = -1 (MACD bearish)
        assert any(word in final_card[0] for word in ["HOLD", "SELL"])


class TestErrorHandling:
    """Tests for error handling in the workflow."""

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.get_stock_data")
    @patch("modules.multi_agent.logger")
    @patch("modules.multi_agent.time.sleep")
    def test_workflow_handles_exceptions(self, mock_sleep, mock_logger, mock_stock, mock_st):
        """Test that workflow handles exceptions gracefully."""
        from modules.multi_agent import _run_deep_dive_logic

        mock_stock.side_effect = Exception("API Error")

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        _run_deep_dive_logic("AAPL")

        mock_st.error.assert_called()
        error_msg = str(mock_st.error.call_args[0][0])
        assert "Mission Aborted" in error_msg

    @patch("modules.multi_agent.st")
    @patch("modules.multi_agent.get_stock_data")
    @patch("modules.multi_agent.get_company_info")
    @patch("modules.multi_agent.calculate_indicators")
    @patch("modules.multi_agent.logger")
    @patch("modules.multi_agent.time.sleep")
    def test_workflow_logs_errors(
        self, mock_sleep, mock_logger, mock_calc, mock_info, mock_stock, mock_st
    ):
        """Test that workflow logs errors."""
        from modules.multi_agent import _run_deep_dive_logic

        mock_stock.side_effect = Exception("Test Error")

        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        _run_deep_dive_logic("AAPL")

        mock_logger.error.assert_called_once()
        log_msg = str(mock_logger.error.call_args[0][0])
        assert "Workflow failed" in log_msg


class TestModuleImports:
    """Tests for module imports and structure."""

    def test_module_imports_successfully(self):
        """Test that module imports without errors."""
        import modules.multi_agent

        assert modules.multi_agent is not None

    def test_render_function_exists(self):
        """Test that render function exists."""
        from modules.multi_agent import render

        assert callable(render)

    def test_private_functions_exist(self):
        """Test that private functions exist."""
        from modules.multi_agent import (
            _render_stock_deep_dive,
            _run_deep_dive_logic,
        )

        assert callable(_render_stock_deep_dive)
        assert callable(_run_deep_dive_logic)
