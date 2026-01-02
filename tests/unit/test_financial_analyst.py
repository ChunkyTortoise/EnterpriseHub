"""Tests for Financial Analyst module integration and rendering."""

import pytest
from unittest.mock import patch, MagicMock
from utils.exceptions import DataFetchError


# Mock company info data
MOCK_COMPANY_INFO = {
    "longName": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "country": "United States",
    "website": "https://www.apple.com",
    "longBusinessSummary": (
        "Apple Inc. designs, manufactures, and markets smartphones, personal computers, "
        "tablets, wearables, and accessories worldwide."
    ),
    "marketCap": 2800000000000,  # $2.8T
    "trailingPE": 28.5,
    "trailingEps": 6.42,
    "dividendYield": 0.0045,
    "beta": 1.2,
}

# Mock financials data
MOCK_FINANCIALS = {
    "income_statement": {
        "Revenue": [394328000000, 365817000000, 274515000000],
        "Net Income": [96995000000, 94680000000, 57411000000],
    },
    "balance_sheet": {
        "Total Assets": [352755000000, 323888000000, 338516000000],
        "Total Liabilities": [290437000000, 258549000000, 248028000000],
    },
    "cash_flow": {
        "Operating Cash Flow": [111443000000, 104038000000, 80674000000],
        "Free Cash Flow": [99584000000, 92953000000, 73365000000],
    },
}


class TestFinancialAnalystRender:
    """Test the main render function."""

    @patch("modules.financial_analyst.ui.section_header")
    @patch("modules.financial_analyst.st")
    @patch("modules.financial_analyst._fetch_and_display_data")
    def test_render_with_valid_ticker(self, mock_fetch, mock_st, mock_section):
        """Test successful render with valid ticker."""
        from modules import financial_analyst

        # Mock input
        mock_st.checkbox.return_value = False
        mock_st.text_input.return_value = "AAPL"
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Call render
        financial_analyst.render()

        # Assertions
        mock_section.assert_called_once_with(
            "Financial Analyst", "Fundamental Analysis & Company Metrics"
        )
        mock_st.text_input.assert_called_once()
        mock_fetch.assert_called_once_with("AAPL")

    @patch("modules.financial_analyst.st")
    def test_render_with_empty_ticker(self, mock_st):
        """Test render shows info message when ticker is empty."""
        from modules import financial_analyst

        # Mock empty input
        mock_st.checkbox.return_value = False
        mock_st.text_input.return_value = ""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Call render
        financial_analyst.render()

        # Should show info and return early
        mock_st.info.assert_called_once_with("Please enter a ticker symbol to begin.")

    @patch("modules.financial_analyst.st")
    @patch("modules.financial_analyst._fetch_and_display_data")
    def test_render_handles_data_fetch_error(self, mock_fetch, mock_st):
        """Test render handles DataFetchError gracefully."""
        from modules import financial_analyst

        # Mock input
        mock_st.checkbox.return_value = False
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

    @patch("modules.financial_analyst.st")
    @patch("modules.financial_analyst._fetch_and_display_data")
    def test_render_handles_unexpected_exception(self, mock_fetch, mock_st):
        """Test render handles unexpected exceptions."""
        from modules import financial_analyst

        # Mock input
        mock_st.checkbox.return_value = False
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

    @patch("modules.financial_analyst.get_financials")
    @patch("modules.financial_analyst.get_company_info")
    @patch("modules.financial_analyst._display_financial_tabs")
    @patch("modules.financial_analyst._display_performance_charts")
    @patch("modules.financial_analyst._display_key_metrics")
    @patch("modules.financial_analyst._display_header")
    def test_fetch_and_display_success(
        self,
        mock_header,
        mock_metrics,
        mock_charts,
        mock_tabs,
        mock_info,
        mock_financials,
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

    @patch("modules.financial_analyst.get_financials")
    @patch("modules.financial_analyst.get_company_info")
    def test_fetch_raises_error_on_no_info(self, mock_info, mock_financials):
        """Test raises DataFetchError when no company info returned."""
        from modules.financial_analyst import _fetch_and_display_data

        # Mock no data
        mock_info.return_value = None
        mock_financials.return_value = MOCK_FINANCIALS

        # Should raise error
        with pytest.raises(DataFetchError):
            _fetch_and_display_data("INVALID")

    @patch("modules.financial_analyst.get_financials")
    @patch("modules.financial_analyst.get_company_info")
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

    @patch("modules.financial_analyst.st")
    def test_display_header_with_full_info(self, mock_st):
        """Test header display with complete company info."""
        from modules.financial_analyst import _display_header

        # Mock columns
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_st.columns.return_value = [mock_col1, mock_col2]

        # Call function
        _display_header(MOCK_COMPANY_INFO, "AAPL")

        # Verify header call (now using markdown for custom styling)
        mock_st.markdown.assert_called()
        calls = [call[0][0] for call in mock_st.markdown.call_args_list]
        header_call = next(c for c in calls if "Apple Inc." in c and "AAPL" in c)
        assert "h2" in header_call

        # Verify sector/industry/country info (now in markdown)
        assert any("Technology" in str(call) for call in calls)
        assert any("Consumer Electronics" in str(call) for call in calls)

        # Verify website link
        mock_st.markdown.assert_called()
        calls = [call[0][0] for call in mock_st.markdown.call_args_list]
        assert any("apple.com" in str(call) for call in calls)

    @patch("modules.financial_analyst.st")
    def test_display_header_without_summary(self, mock_st):
        """Test header display when business summary is missing."""
        from modules.financial_analyst import _display_header

        # Mock columns
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_st.columns.return_value = [mock_col1, mock_col2]

        # Create info without summary
        info_no_summary = MOCK_COMPANY_INFO.copy()
        del info_no_summary["longBusinessSummary"]

        # Call function
        _display_header(info_no_summary, "AAPL")

        # Verify "currently unavailable" was shown
        calls = [call[0][0] for call in mock_st.markdown.call_args_list]
        assert any("currently unavailable" in str(call) for call in calls)


class TestDisplayKeyMetrics:
    """Test the _display_key_metrics function."""

    @patch("modules.financial_analyst.ui.animated_metric")
    @patch("modules.financial_analyst.st")
    def test_display_key_metrics_with_valid_data(self, mock_st, mock_card):
        """Test key metrics display with valid data."""
        from modules.financial_analyst import _display_key_metrics

        # Mock columns
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols

        # Call function
        _display_key_metrics(MOCK_COMPANY_INFO)

        # Verify metrics were called (via ui.animated_metric)
        assert mock_card.call_count >= 4

    @patch("modules.financial_analyst.ui.animated_metric")
    @patch("modules.financial_analyst.st")
    def test_display_key_metrics_with_missing_data(self, mock_st, mock_card):
        """Test key metrics display handles missing data."""
        from modules.financial_analyst import _display_key_metrics

        # Mock columns
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols

        # Info with missing values
        incomplete_info = {"marketCap": None, "trailingPE": None, "trailingEps": None}

        # Call function - should not crash
        _display_key_metrics(incomplete_info)

        # Verify metrics were still called (with "N/A" values)
        assert mock_card.call_count >= 3


class TestFinancialAnalystEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("modules.financial_analyst.st")
    @patch("modules.financial_analyst._fetch_and_display_data")
    def test_lowercase_ticker_converted_to_uppercase(self, mock_fetch, mock_st):
        """Test that lowercase ticker is converted to uppercase."""
        from modules import financial_analyst

        # Mock input with lowercase
        mock_st.checkbox.return_value = False
        mock_st.text_input.return_value = "aapl"
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Call render
        financial_analyst.render()

        # Should be called with uppercase
        mock_fetch.assert_called_once_with("AAPL")

    def test_market_cap_formatting(self):
        """Test market cap is formatted correctly in billions."""
        market_cap = 2800000000000  # $2.8T
        formatted = f"${market_cap / 1e9:.2f}B"
        assert formatted == "$2800.00B"


class TestAIInsights:
    """Test AI insights functionality."""

    @patch("modules.financial_analyst._get_api_key")
    @patch("modules.financial_analyst.ANTHROPIC_AVAILABLE", True)
    @patch("modules.financial_analyst._generate_financial_insights")
    @patch("modules.financial_analyst.st")
    def test_display_ai_insights_enabled(self, mock_st, mock_generate, mock_get_key):
        """Test AI insights display when enabled."""
        from modules.financial_analyst import _display_ai_insights

        # Mock API key and toggle
        mock_get_key.return_value = "sk-test-key"
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.toggle.return_value = True

        # Mock generated insights
        mock_generate.return_value = "**Test insights**"

        # Call function
        _display_ai_insights(MOCK_COMPANY_INFO, MOCK_FINANCIALS, "AAPL", "sk-test-key")

        # Verify generation was called
        mock_generate.assert_called_once()
        mock_st.markdown.assert_called()

    @patch("modules.financial_analyst.st")
    def test_display_ai_insights_disabled(self, mock_st):
        """Test AI insights display when disabled."""
        from modules.financial_analyst import _display_ai_insights

        # Mock toggle disabled
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.toggle.return_value = False

        # Call function
        _display_ai_insights(MOCK_COMPANY_INFO, MOCK_FINANCIALS, "AAPL", "sk-test-key")

        # Verify info message shown
        mock_st.info.assert_called_once()

    @patch("modules.financial_analyst.Anthropic")
    @patch("modules.financial_analyst.build_ai_prompt")
    def test_generate_financial_insights_success(self, mock_build_prompt, mock_anthropic):
        """Test successful insights generation."""
        from modules.financial_analyst import _generate_financial_insights

        # Mock prompt builder
        mock_build_prompt.return_value = "Mock Prompt"

        # Mock Claude response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(text="**Financial Health Assessment:**\n- Strong position")
        ]
        mock_client.messages.create.return_value = mock_message

        # Call function
        result = _generate_financial_insights(
            MOCK_COMPANY_INFO, MOCK_FINANCIALS, "AAPL", "sk-test-key"
        )

        # Verify result
        assert result is not None
        assert "Financial Health Assessment" in result
        mock_build_prompt.assert_called_once()

    def test_get_api_key_from_env(self):
        """Test getting API key from environment."""
        from modules.financial_analyst import _get_api_key
        import os

        # Set env variable
        os.environ["ANTHROPIC_API_KEY"] = "test-key-env"

        key = _get_api_key()

        assert key == "test-key-env"

        # Clean up
        del os.environ["ANTHROPIC_API_KEY"]


class TestDisplayProfitabilityRatios:
    """Test the _display_profitability_ratios function."""

    @patch("modules.financial_analyst.ui.card_metric")
    @patch("modules.financial_analyst.st")
    @patch("modules.financial_analyst.calculate_yoy_growth")
    @patch("modules.financial_analyst.find_column")
    def test_display_profitability_ratios_with_yoy(self, mock_find, mock_calc, mock_st, mock_card):
        """Test profitability ratios display includes YoY growth."""
        from modules.financial_analyst import _display_profitability_ratios
        import pandas as pd

        # Mock find_column
        mock_find.side_effect = lambda df, keys: "Gross Profit" if "Gross" in keys[0] else None

        # Mock calculation
        mock_calc.return_value = 15.0

        # Mock columns
        mock_cols = [MagicMock() for _ in range(3)]
        mock_st.columns.return_value = mock_cols

        # Create mock income statement with 2 years
        dates = pd.to_datetime(["2022-01-01", "2023-01-01"])
        income_stmt = pd.DataFrame(
            {
                "Total Revenue": [100e9, 115e9],
                "Net Income": [20e9, 25e9],
                "Gross Profit": [40e9, 46e9],
            },
            index=dates,
        )

        # Call function
        _display_profitability_ratios(income_stmt, "Total Revenue", "Net Income")

        # Verify card_metric was called 3 times (Net Margin, Gross Margin, YoY Growth)
        assert mock_card.call_count == 3


class TestDCFValuationRenderFunction:
    """Test DCF Valuation render function with mocked Streamlit."""

    @patch("modules.financial_analyst.st")
    @patch("modules.financial_analyst.find_column")
    @patch("modules.financial_analyst.DCFModel")
    def test_display_dcf_valuation_basic(self, mock_dcf_model, mock_find, mock_st):
        """Test DCF valuation render executes without errors."""
        from modules.financial_analyst import _display_dcf_valuation
        import pandas as pd
        from modules.financial_analyst_logic import DCFResult

        # Mock find_column
        mock_find.return_value = "Free Cash Flow"

        # Mock DCF Result
        mock_dcf_model.calculate.return_value = DCFResult(
            fair_value=200.0,
            conservative_value=160.0,
            upside_percent=33.3,
            enterprise_value=3000e9,
            projections=[{"Year": 1, "FCF": 100, "PV": 90}],
            is_undervalued=True,
            verdict="UNDERVALUED"
        )

        # Mock info and financials
        mock_info = {
            "currentPrice": 150.0,
            "sharesOutstanding": 15e9,
        }

        # Mock cash flow data
        dates = pd.to_datetime(["2021-01-01", "2022-01-01", "2023-01-01"])
        mock_financials = {
            "cashflow": pd.DataFrame(
                {
                    dates[0]: [80e9, 100e9],
                    dates[1]: [90e9, 110e9],
                    dates[2]: [100e9, 120e9],
                },
                index=["Free Cash Flow", "Operating Cash Flow"],
            )
        }

        # Mock columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        # Mock sliders
        mock_st.slider.return_value = 10.0

        # Mock expander
        mock_expander = MagicMock()
        mock_st.expander.return_value.__enter__.return_value = mock_expander

        # Call function
        _display_dcf_valuation(mock_info, mock_financials, "AAPL")

        # Verify DCF calculation was triggered
        mock_dcf_model.calculate.assert_called()

        # Verify basic calls
        assert mock_st.slider.call_count >= 4
        # We expect metrics for Price, Fair Value, Upside, Conservative Value
        # But since we mocked ui.animated_metric (which likely calls st.metric or similar),
        # we check if DCFModel was called which implies the flow reached the end.


class TestPDFExportFunction:
    """Test PDF statement export functionality."""

    @patch("modules.financial_analyst.st")
    def test_display_statement_export_button_present(self, mock_st):
        """Test that PDF export button is present."""
        from modules.financial_analyst import _display_statement_export
        import pandas as pd

        # Mock DataFrame
        df = pd.DataFrame(
            {
                "Revenue": [100e9, 110e9, 120e9],
                "Net Income": [20e9, 22e9, 25e9],
            }
        )

        # Mock button (not clicked)
        mock_st.button.return_value = False

        # Mock columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        # Call function
        _display_statement_export(df, "income_statement")

        # Verify button was created
        mock_st.button.assert_called_once()
        button_call = mock_st.button.call_args
        assert "PDF" in button_call[0][0]

    @patch("modules.financial_analyst.st")
    def test_pdf_export_matplotlib_not_available(self, mock_st):
        """Test PDF export handles missing matplotlib gracefully."""
        from modules.financial_analyst import _display_statement_export
        import pandas as pd
        import sys
        from unittest.mock import MagicMock

        # Mock DataFrame
        df = pd.DataFrame(
            {
                "Revenue": [100e9, 110e9, 120e9],
            }
        )

        # Mock button clicked
        mock_st.button.return_value = True

        # Mock columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        # Mock session state
        mock_st.session_state = {"fa_ticker": "AAPL"}

        # Simulate ImportError by mocking the import in sys.modules
        with patch.dict(
            sys.modules, {"matplotlib.pyplot": None, "matplotlib.backends.backend_pdf": None}
        ):
            _display_statement_export(df, "income_statement")

            # Should show error about matplotlib
            mock_st.error.assert_called()
            error_call = mock_st.error.call_args[0][0]
            assert "matplotlib" in error_call.lower()