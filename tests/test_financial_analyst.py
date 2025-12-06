"""Tests for Financial Analyst module."""

import pytest
from unittest.mock import patch, MagicMock, Mock
from utils.exceptions import DataFetchError


# Mock company info data
MOCK_COMPANY_INFO = {
    'longName': 'Apple Inc.',
    'sector': 'Technology',
    'industry': 'Consumer Electronics',
    'country': 'United States',
    'website': 'https://www.apple.com',
    'longBusinessSummary': 'Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.',
    'marketCap': 2800000000000,  # $2.8T
    'trailingPE': 28.5,
    'trailingEps': 6.42,
    'dividendYield': 0.0045,
    'beta': 1.2
}

# Mock financials data
MOCK_FINANCIALS = {
    'income_statement': {
        'Revenue': [394328000000, 365817000000, 274515000000],
        'Net Income': [96995000000, 94680000000, 57411000000]
    },
    'balance_sheet': {
        'Total Assets': [352755000000, 323888000000, 338516000000],
        'Total Liabilities': [290437000000, 258549000000, 248028000000]
    },
    'cash_flow': {
        'Operating Cash Flow': [111443000000, 104038000000, 80674000000],
        'Free Cash Flow': [99584000000, 92953000000, 73365000000]
    }
}


class TestFinancialAnalystRender:
    """Test the main render function."""

    @patch('modules.financial_analyst.st')
    @patch('modules.financial_analyst._fetch_and_display_data')
    def test_render_with_valid_ticker(self, mock_fetch, mock_st):
        """Test successful render with valid ticker."""
        from modules import financial_analyst

        # Mock input
        mock_st.text_input.return_value = "AAPL"
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Call render
        financial_analyst.render()

        # Assertions
        mock_st.title.assert_called_once_with("💼 Financial Analyst")
        mock_st.text_input.assert_called_once()
        mock_fetch.assert_called_once_with("AAPL")

    @patch('modules.financial_analyst.st')
    def test_render_with_empty_ticker(self, mock_st):
        """Test render shows info message when ticker is empty."""
        from modules import financial_analyst

        # Mock empty input
        mock_st.text_input.return_value = ""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Call render
        financial_analyst.render()

        # Should show info and return early
        mock_st.info.assert_called_once_with("Please enter a ticker symbol to begin.")

    @patch('modules.financial_analyst.st')
    @patch('modules.financial_analyst._fetch_and_display_data')
    def test_render_handles_data_fetch_error(self, mock_fetch, mock_st):
        """Test render handles DataFetchError gracefully."""
        from modules import financial_analyst

        # Mock input
        mock_st.text_input.return_value = "INVALID"
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Mock fetch raising error
        mock_fetch.side_effect = DataFetchError("Invalid ticker")

        # Call render
        financial_analyst.render()

        # Should show error message
        mock_st.error.assert_called_once()
        error_call = mock_st.error.call_args[0][0]
        assert "Failed to fetch data" in error_call

    @patch('modules.financial_analyst.st')
    @patch('modules.financial_analyst._fetch_and_display_data')
    def test_render_handles_unexpected_exception(self, mock_fetch, mock_st):
        """Test render handles unexpected exceptions."""
        from modules import financial_analyst

        # Mock input
        mock_st.text_input.return_value = "AAPL"
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Mock fetch raising unexpected error
        mock_fetch.side_effect = ValueError("Unexpected error")

        # Call render
        financial_analyst.render()

        # Should show error message
        mock_st.error.assert_called()
        error_call = mock_st.error.call_args[0][0]
        assert "unexpected error" in error_call.lower()


class TestFetchAndDisplayData:
    """Test the _fetch_and_display_data function."""

    @patch('modules.financial_analyst.get_financials')
    @patch('modules.financial_analyst.get_company_info')
    @patch('modules.financial_analyst._display_financial_tabs')
    @patch('modules.financial_analyst._display_performance_charts')
    @patch('modules.financial_analyst._display_key_metrics')
    @patch('modules.financial_analyst._display_header')
    def test_fetch_and_display_success(
        self, mock_header, mock_metrics, mock_charts, mock_tabs,
        mock_info, mock_financials
    ):
        """Test successful data fetch and display."""
        from modules.financial_analyst import _fetch_and_display_data

        # Mock data
        mock_info.return_value = MOCK_COMPANY_INFO
        mock_financials.return_value = MOCK_FINANCIALS

        # Call function
        _fetch_and_display_data("AAPL")

        # Verify data fetching
        mock_info.assert_called_once_with("AAPL")
        mock_financials.assert_called_once_with("AAPL")

        # Verify display functions called
        mock_header.assert_called_once_with(MOCK_COMPANY_INFO, "AAPL")
        mock_metrics.assert_called_once_with(MOCK_COMPANY_INFO)
        mock_charts.assert_called_once_with(MOCK_FINANCIALS)
        mock_tabs.assert_called_once_with(MOCK_FINANCIALS)

    @patch('modules.financial_analyst.get_financials')
    @patch('modules.financial_analyst.get_company_info')
    def test_fetch_raises_error_on_no_info(self, mock_info, mock_financials):
        """Test raises DataFetchError when no company info returned."""
        from modules.financial_analyst import _fetch_and_display_data

        # Mock no data
        mock_info.return_value = None
        mock_financials.return_value = MOCK_FINANCIALS

        # Should raise error
        with pytest.raises(DataFetchError):
            _fetch_and_display_data("INVALID")

    @patch('modules.financial_analyst.get_financials')
    @patch('modules.financial_analyst.get_company_info')
    def test_fetch_raises_error_on_no_financials(self, mock_info, mock_financials):
        """Test raises DataFetchError when no financials returned."""
        from modules.financial_analyst import _fetch_and_display_data

        # Mock no financials
        mock_info.return_value = MOCK_COMPANY_INFO
        mock_financials.return_value = None

        # Should raise error
        with pytest.raises(DataFetchError):
            _fetch_and_display_data("INVALID")


class TestDisplayHeader:
    """Test the _display_header function."""

    @patch('modules.financial_analyst.st')
    def test_display_header_with_full_info(self, mock_st):
        """Test header display with complete company info."""
        from modules.financial_analyst import _display_header

        # Mock columns
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_st.columns.return_value = [mock_col1, mock_col2]

        # Call function
        _display_header(MOCK_COMPANY_INFO, "AAPL")

        # Verify header call
        mock_col1.header.assert_called_once()
        header_text = mock_col1.header.call_args[0][0]
        assert "Apple Inc." in header_text
        assert "AAPL" in header_text

        # Verify caption
        mock_col1.caption.assert_called_once()
        caption_text = mock_col1.caption.call_args[0][0]
        assert "Technology" in caption_text
        assert "Consumer Electronics" in caption_text

        # Verify website link
        mock_col2.markdown.assert_called_once()
        website_link = mock_col2.markdown.call_args[0][0]
        assert "apple.com" in website_link

    @patch('modules.financial_analyst.st')
    def test_display_header_without_summary(self, mock_st):
        """Test header display when business summary is missing."""
        from modules.financial_analyst import _display_header

        # Mock columns
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_st.columns.return_value = [mock_col1, mock_col2]

        # Create info without summary
        info_no_summary = MOCK_COMPANY_INFO.copy()
        del info_no_summary['longBusinessSummary']

        # Call function
        _display_header(info_no_summary, "AAPL")

        # Verify "No summary available" was shown
        calls = [call[0][0] for call in mock_col1.markdown.call_args_list]
        assert any("No summary available" in str(call) for call in calls)


class TestDisplayKeyMetrics:
    """Test the _display_key_metrics function."""

    @patch('modules.financial_analyst.st')
    def test_display_key_metrics_with_valid_data(self, mock_st):
        """Test key metrics display with valid data."""
        from modules.financial_analyst import _display_key_metrics

        # Mock columns
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols

        # Call function
        _display_key_metrics(MOCK_COMPANY_INFO)

        # Verify metrics were called
        mock_cols[0].metric.assert_called_once()  # Market Cap
        mock_cols[1].metric.assert_called_once()  # P/E Ratio
        mock_cols[2].metric.assert_called_once()  # EPS
        mock_cols[3].metric.assert_called_once()  # Dividend or Beta

    @patch('modules.financial_analyst.st')
    def test_display_key_metrics_with_missing_data(self, mock_st):
        """Test key metrics display handles missing data."""
        from modules.financial_analyst import _display_key_metrics

        # Mock columns
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols

        # Info with missing values
        incomplete_info = {
            'marketCap': None,
            'trailingPE': None,
            'trailingEps': None
        }

        # Call function - should not crash
        _display_key_metrics(incomplete_info)

        # Verify metrics were still called (with "N/A" values)
        assert mock_cols[0].metric.called
        assert mock_cols[1].metric.called
        assert mock_cols[2].metric.called


class TestFinancialAnalystEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch('modules.financial_analyst.st')
    @patch('modules.financial_analyst._fetch_and_display_data')
    def test_lowercase_ticker_converted_to_uppercase(self, mock_fetch, mock_st):
        """Test that lowercase ticker is converted to uppercase."""
        from modules import financial_analyst

        # Mock input with lowercase
        mock_st.text_input.return_value = "aapl"
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Call render
        financial_analyst.render()

        # Should be called with uppercase
        mock_fetch.assert_called_once_with("AAPL")

    def test_market_cap_formatting(self):
        """Test market cap is formatted correctly in billions."""
        market_cap = 2800000000000  # $2.8T
        formatted = f"${market_cap/1e9:.2f}B"
        assert formatted == "$2800.00B"

    def test_eps_formatting(self):
        """Test EPS is formatted with 2 decimal places."""
        eps = 6.42
        formatted = f"${eps:.2f}"
        assert formatted == "$6.42"

    def test_pe_ratio_formatting(self):
        """Test P/E ratio is formatted with 2 decimal places."""
        pe = 28.5
        formatted = f"{pe:.2f}"
        assert formatted == "28.50"
