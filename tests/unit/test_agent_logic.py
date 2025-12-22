"""Tests for the Agent Logic module."""

from unittest.mock import patch, MagicMock
import json
from modules import agent_logic

# Mock data for testing
MOCK_NEWS_ITEMS = [
    {
        "uuid": "1",
        "title": "Big Gains for AAPL",
        "publisher": "BizNews",
        "link": "http://example.com/1",
        "providerPublishTime": 1672531200,  # 2023-01-01
    }
]

MOCK_ANALYSIS = {
    "average_score": 0.75,
    "verdict": "Positive",
    "article_count": 1,
    "processed_news": [
        {
            "title": "Big Gains for AAPL",
            "sentiment_label": "POSITIVE",
            "sentiment_score": 0.75,
            "publisher": "BizNews",
            "link": "http://example.com/1",
            "providerPublishTime": 1672531200,
        }
    ],
}


@patch("modules.agent_logic.ui.section_header")
@patch("modules.agent_logic.st")
@patch("modules.agent_logic.get_news")
@patch("modules.agent_logic.process_news_sentiment")
@patch("modules.agent_logic.go")
def test_render_successful_analysis(mock_go, mock_process, mock_get_news, mock_st, mock_section):
    """Test the successful rendering path of the Agent Logic module."""
    # --- Arrange ---
    # Mock streamlit inputs
    mock_st.text_input.return_value = "AAPL"
    mock_st.toggle.return_value = False  # Use basic sentiment, not AI

    # Mock columns to prevent unpacking errors (2 calls: input layout and dashboard layout)
    mock_st.columns.side_effect = [
        [MagicMock(), MagicMock()],  # Input layout (2 columns)
        [MagicMock(), MagicMock()],  # Dashboard layout (2 columns)
    ]

    # Mock backend functions
    mock_get_news.return_value = MOCK_NEWS_ITEMS
    mock_process.return_value = MOCK_ANALYSIS

    # Mock the Figure object
    mock_figure = MagicMock()
    mock_go.Figure.return_value = mock_figure

    # --- Act ---
    agent_logic.render()

    # --- Assert ---
    # Check if UI components are called
    mock_section.assert_called_once_with(
        "Agent Logic: Sentiment Scout", "AI-Powered Market Sentiment Analysis"
    )
    mock_st.text_input.assert_called_with("Analyze Ticker", value="AAPL", max_chars=5)

    # Check if backend functions are called correctly
    mock_get_news.assert_called_once_with("AAPL")
    mock_process.assert_called_once_with(MOCK_NEWS_ITEMS)

    # Check if results are displayed
    mock_st.plotly_chart.assert_called_once_with(mock_figure, use_container_width=True)
    # Check that one of the key verdict components was called
    mock_st.markdown.assert_any_call("## Positive")
    mock_st.expander.assert_called()  # Check that news feed expanders are called

    # Ensure no error/warning messages are shown
    mock_st.warning.assert_not_called()
    mock_st.error.assert_not_called()


@patch("modules.agent_logic.ui.section_header")
@patch("modules.agent_logic.st")
@patch("modules.agent_logic.get_news")
@patch("modules.agent_logic.process_news_sentiment")
def test_render_no_news_found(mock_process, mock_get_news, mock_st, mock_section):
    """Test the case where no news is found for a ticker."""
    # --- Arrange ---
    mock_st.text_input.return_value = "FAILTICKER"

    # Mock columns for input layout
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    mock_get_news.return_value = []  # No news

    # --- Act ---
    agent_logic.render()

    # --- Assert ---
    mock_get_news.assert_called_once_with("FAILTICKER")
    mock_st.warning.assert_called_once_with("No recent news found for FAILTICKER.")

    # Ensure analysis and plotting are not performed
    mock_process.assert_not_called()
    mock_st.plotly_chart.assert_not_called()
    mock_st.expander.assert_not_called()


@patch("modules.agent_logic.ui.section_header")
@patch("modules.agent_logic.st")
@patch("modules.agent_logic.get_news")
def test_render_no_ticker_entered(mock_get_news, mock_st, mock_section):
    """Test the case where no ticker is entered."""
    # --- Arrange ---
    mock_st.text_input.return_value = ""  # Empty input

    # Mock columns for input layout
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    # --- Act ---
    agent_logic.render()

    # --- Assert ---
    mock_st.info.assert_called_once_with("Enter a ticker to scout sentiment.")

    # Ensure no backend calls are made
    mock_get_news.assert_not_called()


@patch("modules.agent_logic.ui.section_header")
@patch("modules.agent_logic.st")
@patch("modules.agent_logic.get_news")
def test_render_handles_exception(mock_get_news, mock_st, mock_section):
    """Test that errors during data fetching are handled gracefully."""
    # --- Arrange ---
    mock_st.text_input.return_value = "AAPL"

    # Mock columns for input layout
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    mock_get_news.side_effect = Exception("Network Error")

    # --- Act ---
    agent_logic.render()

    # --- Assert ---
    mock_get_news.assert_called_once_with("AAPL")
    mock_st.error.assert_called_once_with("An error occurred while scouting AAPL.")

    # Ensure no results are displayed
    mock_st.plotly_chart.assert_not_called()
    mock_st.expander.assert_not_called()


class TestClaudeSentiment:
    """Test Claude AI sentiment analysis functionality."""

    @patch("modules.agent_logic._get_api_key")
    @patch("modules.agent_logic.ANTHROPIC_AVAILABLE", True)
    @patch("modules.agent_logic.st")
    def test_get_api_key_toggle_shown(self, mock_st, mock_get_key):
        """Test that AI sentiment toggle is shown when API key available."""
        from modules import agent_logic

        mock_get_key.return_value = "sk-test-key"
        mock_st.text_input.return_value = "AAPL"
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Call render (it will return early due to no symbol)
        agent_logic.render()

        # Verify toggle was created
        mock_st.toggle.assert_called_once()

    @patch("modules.agent_logic._get_api_key")
    @patch("modules.agent_logic.st")
    def test_no_api_key_caption_shown(self, mock_st, mock_get_key):
        """Test that caption is shown when no API key available."""
        from modules import agent_logic

        mock_get_key.return_value = None
        mock_st.text_input.return_value = "AAPL"
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Call render
        agent_logic.render()

        # Verify caption was shown
        mock_st.caption.assert_called_once()

    def test_get_api_key_from_env(self):
        """Test getting API key from environment."""
        from modules.agent_logic import _get_api_key
        import os

        # Set env variable
        os.environ["ANTHROPIC_API_KEY"] = "test-key-env"

        key = _get_api_key()

        assert key == "test-key-env"

        # Clean up
        del os.environ["ANTHROPIC_API_KEY"]


class TestSentimentAnalyzerClaude:
    """Test Claude sentiment analysis in utils."""

    @patch("utils.sentiment_analyzer.Anthropic")
    def test_analyze_sentiment_with_claude_success(self, mock_anthropic):
        """Test successful Claude sentiment analysis."""
        from utils.sentiment_analyzer import analyze_sentiment_with_claude

        # Mock Claude response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = {
            "overall_sentiment": "bullish",
            "confidence": 80,
            "reasoning": "Strong earnings report",
            "article_sentiments": [{"title": "Big Gains", "sentiment": "positive", "score": 0.8}],
        }

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps(mock_response))]
        mock_client.messages.create.return_value = mock_message

        # Call function
        result = analyze_sentiment_with_claude(MOCK_NEWS_ITEMS, "AAPL", "sk-test-key")

        # Verify result
        assert result is not None
        assert "average_score" in result
        assert "verdict" in result
        assert "reasoning" in result
        assert result["reasoning"] == "Strong earnings report"
        assert result["article_count"] == 1

    @patch("utils.sentiment_analyzer.Anthropic")
    def test_analyze_sentiment_with_claude_fallback(self, mock_anthropic):
        """Test fallback to TextBlob when Claude fails."""
        from utils.sentiment_analyzer import analyze_sentiment_with_claude

        # Mock Claude error
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        # Call function
        result = analyze_sentiment_with_claude(MOCK_NEWS_ITEMS, "AAPL", "sk-test-key")

        # Should fall back to TextBlob and return result
        assert result is not None
        assert "average_score" in result
        assert "verdict" in result

    def test_analyze_sentiment_with_claude_no_news(self):
        """Test Claude sentiment with no news items."""
        from utils.sentiment_analyzer import analyze_sentiment_with_claude

        result = analyze_sentiment_with_claude([], "AAPL", "sk-test-key")

        assert result["average_score"] == 0.0
        assert result["verdict"] == "Neutral"
        assert result["article_count"] == 0
        assert "reasoning" in result

    @patch("utils.sentiment_analyzer.ANTHROPIC_AVAILABLE", False)
    def test_analyze_sentiment_with_claude_not_available(self):
        """Test when Anthropic library not available."""
        from utils.sentiment_analyzer import analyze_sentiment_with_claude

        # Should fall back to TextBlob
        result = analyze_sentiment_with_claude(MOCK_NEWS_ITEMS, "AAPL", "sk-test-key")

        assert result is not None
        assert "average_score" in result
