"""Tests for the Agent Logic module."""

from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

# Mock data for testing
MOCK_NEWS_ITEMS = [
    {
        'uuid': '1', 
        'title': 'Big Gains for AAPL', 
        'publisher': 'BizNews', 
        'link': 'http://example.com/1',
        'providerPublishTime': 1672531200 # 2023-01-01
    }
]

MOCK_ANALYSIS = {
    'average_score': 0.75,
    'verdict': 'Positive',
    'article_count': 1,
    'processed_news': [
        {
            'title': 'Big Gains for AAPL',
            'sentiment_label': 'POSITIVE',
            'sentiment_score': 0.75,
            'publisher': 'BizNews',
            'link': 'http://example.com/1',
            'providerPublishTime': 1672531200
        }
    ]
}

# Import the module to be tested
from modules import agent_logic

@patch('modules.agent_logic.st')
@patch('modules.agent_logic.get_news')
@patch('modules.agent_logic.process_news_sentiment')
@patch('modules.agent_logic.go')
def test_render_successful_analysis(mock_go, mock_process, mock_get_news, mock_st):
    """Test the successful rendering path of the Agent Logic module."""
    # --- Arrange ---
    # Mock streamlit inputs
    mock_st.text_input.return_value = "AAPL"
    
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
    mock_st.title.assert_called_with("🤖 Agent Logic: Sentiment Scout")
    mock_st.text_input.assert_called_with("Analyze Ticker", value="AAPL", max_chars=5)
    
    # Check if backend functions are called correctly
    mock_get_news.assert_called_once_with("AAPL")
    mock_process.assert_called_once_with(MOCK_NEWS_ITEMS)
    
    # Check if results are displayed
    mock_st.plotly_chart.assert_called_once_with(mock_figure, use_container_width=True)
    # Check that one of the key verdict components was called
    mock_st.markdown.assert_any_call("## Positive")
    mock_st.expander.assert_called_once() # Check that the news feed is rendered
    
    # Ensure no error/warning messages are shown
    mock_st.warning.assert_not_called()
    mock_st.error.assert_not_called()


@patch('modules.agent_logic.st')
@patch('modules.agent_logic.get_news')
@patch('modules.agent_logic.process_news_sentiment')
def test_render_no_news_found(mock_process, mock_get_news, mock_st):
    """Test the case where no news is found for a ticker."""
    # --- Arrange ---
    mock_st.text_input.return_value = "FAILTICKER"
    mock_get_news.return_value = [] # No news

    # --- Act ---
    agent_logic.render()

    # --- Assert ---
    mock_get_news.assert_called_once_with("FAILTICKER")
    mock_st.warning.assert_called_once_with("No recent news found for FAILTICKER.")
    
    # Ensure analysis and plotting are not performed
    mock_process.assert_not_called()
    mock_st.plotly_chart.assert_not_called()
    mock_st.expander.assert_not_called()

@patch('modules.agent_logic.st')
@patch('modules.agent_logic.get_news')
def test_render_no_ticker_entered(mock_get_news, mock_st):
    """Test the case where no ticker is entered."""
    # --- Arrange ---
    mock_st.text_input.return_value = "" # Empty input

    # --- Act ---
    agent_logic.render()

    # --- Assert ---
    mock_st.info.assert_called_once_with("Enter a ticker to scout sentiment.")
    
    # Ensure no backend calls are made
    mock_get_news.assert_not_called()


@patch('modules.agent_logic.st')
@patch('modules.agent_logic.get_news')
def test_render_handles_exception(mock_get_news, mock_st):
    """Test that errors during data fetching are handled gracefully."""
    # --- Arrange ---
    mock_st.text_input.return_value = "AAPL"
    mock_get_news.side_effect = Exception("Network Error")

    # --- Act ---
    agent_logic.render()

    # --- Assert ---
    mock_get_news.assert_called_once_with("AAPL")
    mock_st.error.assert_called_once_with("An error occurred while scouting AAPL.")
    
    # Ensure no results are displayed
    mock_st.plotly_chart.assert_not_called()
    mock_st.expander.assert_not_called()
