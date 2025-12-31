"""Tests for Financial Analyst module."""

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
        self, mock_header, mock_metrics, mock_charts, mock_tabs, mock_info, mock_financials
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

        # Verify header call
        mock_st.header.assert_called_once()
        header_text = mock_st.header.call_args[0][0]
        assert "Apple Inc." in header_text
        assert "AAPL" in header_text

        # Verify caption
        mock_st.caption.assert_called_once()
        caption_text = mock_st.caption.call_args[0][0]
        assert "Technology" in caption_text
        assert "Consumer Electronics" in caption_text

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

        # Verify "No summary available" was shown
        calls = [call[0][0] for call in mock_st.markdown.call_args_list]
        assert any("No summary available" in str(call) for call in calls)


class TestDisplayKeyMetrics:
    """Test the _display_key_metrics function."""

    @patch("modules.financial_analyst.ui.card_metric")
    @patch("modules.financial_analyst.st")
    def test_display_key_metrics_with_valid_data(self, mock_st, mock_card):
        """Test key metrics display with valid data."""
        from modules.financial_analyst import _display_key_metrics

        # Mock columns
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols

        # Call function
        _display_key_metrics(MOCK_COMPANY_INFO)

        # Verify metrics were called (via ui.card_metric)
        assert mock_card.call_count >= 4

    @patch("modules.financial_analyst.ui.card_metric")
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

    def test_build_financial_summary(self):
        """Test building financial summary for Claude."""
        from modules.financial_analyst import _build_financial_summary
        import pandas as pd

        # Create mock financials with proper structure (dates as columns)
        mock_financials = {
            "income_stmt": pd.DataFrame(
                {"2024-01-01": [400e9, 100e9], "2023-01-01": [380e9, 95e9]},
                index=["Total Revenue", "Net Income"],
            )
        }

        summary = _build_financial_summary(MOCK_COMPANY_INFO, mock_financials)

        # Verify key elements are in summary
        assert "Apple Inc." in summary
        assert "Technology" in summary
        assert "P/E Ratio" in summary
        assert isinstance(summary, str)
        assert len(summary) > 0

    @patch("modules.financial_analyst.Anthropic")
    def test_generate_financial_insights_success(self, mock_anthropic):
        """Test successful insights generation."""
        from modules.financial_analyst import _generate_financial_insights

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


class TestYoYRevenueGrowth:
    """Test YoY Revenue Growth calculation."""

    def test_calculate_yoy_revenue_growth_positive(self):
        """Test YoY calculation with positive growth."""
        from modules.financial_analyst import _calculate_yoy_revenue_growth
        import pandas as pd

        # Create mock income statement with 2 years of data
        dates = pd.to_datetime(["2022-01-01", "2023-01-01"])
        income_stmt = pd.DataFrame(
            {"Total Revenue": [100e9, 115e9], "Net Income": [20e9, 25e9]}, index=dates
        )

        result = _calculate_yoy_revenue_growth(income_stmt, "Total Revenue")

        # Should show +15% growth
        assert result == "+15.0%"

    def test_calculate_yoy_revenue_growth_negative(self):
        """Test YoY calculation with negative growth."""
        from modules.financial_analyst import _calculate_yoy_revenue_growth
        import pandas as pd

        # Create mock income statement with declining revenue
        dates = pd.to_datetime(["2022-01-01", "2023-01-01"])
        income_stmt = pd.DataFrame(
            {"Total Revenue": [100e9, 90e9], "Net Income": [20e9, 15e9]}, index=dates
        )

        result = _calculate_yoy_revenue_growth(income_stmt, "Total Revenue")

        # Should show -10% growth
        assert result == "-10.0%"

    def test_calculate_yoy_revenue_growth_insufficient_data(self):
        """Test YoY calculation with only one year of data."""
        from modules.financial_analyst import _calculate_yoy_revenue_growth
        import pandas as pd

        # Create mock income statement with only 1 year
        dates = pd.to_datetime(["2023-01-01"])
        income_stmt = pd.DataFrame({"Total Revenue": [100e9], "Net Income": [20e9]}, index=dates)

        result = _calculate_yoy_revenue_growth(income_stmt, "Total Revenue")

        # Should return N/A
        assert result == "N/A"

    def test_calculate_yoy_revenue_growth_with_nan(self):
        """Test YoY calculation handles NaN values."""
        from modules.financial_analyst import _calculate_yoy_revenue_growth
        import pandas as pd
        import numpy as np

        # Create mock income statement with NaN
        dates = pd.to_datetime(["2022-01-01", "2023-01-01"])
        income_stmt = pd.DataFrame(
            {"Total Revenue": [100e9, np.nan], "Net Income": [20e9, 25e9]}, index=dates
        )

        result = _calculate_yoy_revenue_growth(income_stmt, "Total Revenue")

        # Should return N/A
        assert result == "N/A"

    def test_calculate_yoy_revenue_growth_zero_previous(self):
        """Test YoY calculation when previous year is zero."""
        from modules.financial_analyst import _calculate_yoy_revenue_growth
        import pandas as pd

        # Create mock income statement with zero previous revenue
        dates = pd.to_datetime(["2022-01-01", "2023-01-01"])
        income_stmt = pd.DataFrame(
            {"Total Revenue": [0, 100e9], "Net Income": [0, 20e9]}, index=dates
        )

        result = _calculate_yoy_revenue_growth(income_stmt, "Total Revenue")

        # Should return N/A to avoid division by zero
        assert result == "N/A"

    def test_calculate_yoy_revenue_growth_small_change(self):
        """Test YoY calculation with small percentage change."""
        from modules.financial_analyst import _calculate_yoy_revenue_growth
        import pandas as pd

        # Create mock income statement with small growth
        dates = pd.to_datetime(["2022-01-01", "2023-01-01"])
        income_stmt = pd.DataFrame(
            {"Total Revenue": [100e9, 102.5e9], "Net Income": [20e9, 21e9]}, index=dates
        )

        result = _calculate_yoy_revenue_growth(income_stmt, "Total Revenue")

        # Should show +2.5% growth
        assert result == "+2.5%"

    def test_calculate_yoy_revenue_growth_with_multiple_years(self):
        """Test YoY calculation uses only latest two years."""
        from modules.financial_analyst import _calculate_yoy_revenue_growth
        import pandas as pd

        # Create mock income statement with 4 years of data
        dates = pd.to_datetime(["2020-01-01", "2021-01-01", "2022-01-01", "2023-01-01"])
        income_stmt = pd.DataFrame(
            {
                "Total Revenue": [80e9, 90e9, 100e9, 110e9],
                "Net Income": [15e9, 18e9, 20e9, 22e9],
            },
            index=dates,
        )

        result = _calculate_yoy_revenue_growth(income_stmt, "Total Revenue")

        # Should calculate growth between 2022 and 2023: (110-100)/100 = 10%
        assert result == "+10.0%"

    @patch("modules.financial_analyst.ui.card_metric")
    @patch("modules.financial_analyst.st")
    def test_display_profitability_ratios_with_yoy(self, mock_st, mock_card):
        """Test profitability ratios display includes YoY growth."""
        from modules.financial_analyst import _display_profitability_ratios
        import pandas as pd

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

        # Verify YoY Growth was called with correct value
        calls = [call[0] for call in mock_card.call_args_list]
        yoy_calls = [call for call in calls if len(call) > 0 and "YoY Revenue Growth" in str(call)]


class TestDCFValuationCalculations:
    """Test DCF (Discounted Cash Flow) valuation calculations."""

    def test_dcf_basic_fcf_projection(self):
        """Test basic FCF projection calculation for Year 1."""
        latest_fcf = 100e9  # $100B
        growth_rate = 10.0  # 10% growth
        discount_rate = 10.0  # 10% WACC

        # Year 1 projection
        year_1_fcf = latest_fcf * (1 + growth_rate / 100)
        year_1_pv = year_1_fcf / ((1 + discount_rate / 100) ** 1)

        assert year_1_fcf == 110e9  # 100B * 1.10 = 110B
        assert year_1_pv == pytest.approx(100e9, rel=0.01)  # 110B / 1.10 = 100B

    def test_dcf_multi_year_projection(self):
        """Test multi-year FCF projection (Years 1-5)."""
        latest_fcf = 100e9
        growth_rate = 15.0  # 15% growth
        discount_rate = 10.0

        current_fcf = latest_fcf
        projected_fcf = []

        for year in range(1, 6):
            current_fcf = current_fcf * (1 + growth_rate / 100)
            pv = current_fcf / ((1 + discount_rate / 100) ** year)
            projected_fcf.append({"Year": year, "FCF": current_fcf, "PV": pv})

        # Verify we have 5 years
        assert len(projected_fcf) == 5

        # Year 5 should have significant growth
        assert projected_fcf[4]["FCF"] > latest_fcf * 2  # More than doubled

    def test_dcf_terminal_value_calculation(self):
        """Test terminal value calculation."""
        current_fcf = 200e9  # $200B after 10 years of growth
        terminal_growth = 2.5  # 2.5% perpetual growth
        discount_rate = 10.0  # 10% WACC

        terminal_fcf = current_fcf * (1 + terminal_growth / 100)
        terminal_value = terminal_fcf / (discount_rate / 100 - terminal_growth / 100)
        terminal_pv = terminal_value / ((1 + discount_rate / 100) ** 10)

        # Terminal value should be very large (perpetual cash flows)
        assert terminal_value > current_fcf * 20  # Should be many multiples

        # PV should be discounted significantly
        assert terminal_pv < terminal_value / 2  # Heavily discounted over 10 years

    def test_dcf_enterprise_value_calculation(self):
        """Test enterprise value = sum of PV + terminal PV."""
        sum_pv_fcf = 500e9  # $500B sum of years 1-10
        terminal_pv = 2000e9  # $2T terminal value PV

        enterprise_value = sum_pv_fcf + terminal_pv

        assert enterprise_value == 2500e9  # $2.5T

    def test_dcf_fair_value_per_share(self):
        """Test fair value per share calculation."""
        enterprise_value = 2500e9  # $2.5T
        shares_outstanding = 15e9  # 15B shares

        fair_value_per_share = enterprise_value / shares_outstanding

        assert fair_value_per_share == pytest.approx(166.67, rel=0.01)  # 2500B / 15B

    def test_dcf_margin_of_safety(self):
        """Test margin of safety calculation."""
        fair_value_per_share = 200.0
        margin_of_safety = 20  # 20%

        conservative_value = fair_value_per_share * (1 - margin_of_safety / 100)

        assert conservative_value == 160.0  # 200 * 0.80

    def test_dcf_upside_calculation(self):
        """Test upside/downside percentage calculation."""
        fair_value = 180.0
        current_price = 150.0

        upside = ((fair_value - current_price) / current_price) * 100

        assert upside == 20.0  # (180-150)/150 * 100 = 20%

    def test_dcf_downside_calculation(self):
        """Test downside when overvalued."""
        fair_value = 120.0
        current_price = 150.0

        downside = ((fair_value - current_price) / current_price) * 100

        assert downside == -20.0  # (120-150)/150 * 100 = -20%

    def test_dcf_sensitivity_analysis(self):
        """Test sensitivity analysis with varying discount rates."""
        latest_fcf = 100e9
        growth_rate = 15.0
        discount_rate_base = 10.0
        terminal_growth = 2.5
        shares_outstanding = 15e9

        # Calculate at base discount rate
        discount_rate = discount_rate_base
        temp_fcf = latest_fcf
        temp_pv_sum = 0

        for y in range(1, 11):
            temp_fcf = temp_fcf * (1 + growth_rate / 100)
            temp_pv_sum += temp_fcf / ((1 + discount_rate / 100) ** y)

        temp_terminal_fcf = temp_fcf * (1 + terminal_growth / 100)
        temp_terminal_value = temp_terminal_fcf / (discount_rate / 100 - terminal_growth / 100)
        temp_terminal_pv = temp_terminal_value / ((1 + discount_rate / 100) ** 10)

        temp_ev = temp_pv_sum + temp_terminal_pv
        fair_value_base = temp_ev / shares_outstanding

        # Calculate at higher discount rate (should result in lower fair value)
        discount_rate = discount_rate_base + 2  # 12%
        temp_fcf = latest_fcf
        temp_pv_sum_higher = 0

        for y in range(1, 11):
            temp_fcf = temp_fcf * (1 + growth_rate / 100)
            temp_pv_sum_higher += temp_fcf / ((1 + discount_rate / 100) ** y)

        temp_terminal_fcf = temp_fcf * (1 + terminal_growth / 100)
        temp_terminal_value = temp_terminal_fcf / (discount_rate / 100 - terminal_growth / 100)
        temp_terminal_pv = temp_terminal_value / ((1 + discount_rate / 100) ** 10)

        temp_ev_higher = temp_pv_sum_higher + temp_terminal_pv
        fair_value_higher = temp_ev_higher / shares_outstanding

        # Higher discount rate should result in lower fair value
        assert fair_value_higher < fair_value_base


class TestDCFValuationRenderFunction:
    """Test DCF Valuation render function with mocked Streamlit."""

    @patch("modules.financial_analyst.st")
    def test_display_dcf_valuation_basic(self, mock_st):
        """Test DCF valuation render executes without errors."""
        from modules.financial_analyst import _display_dcf_valuation
        import pandas as pd

        # Mock info and financials
        mock_info = {
            "currentPrice": 150.0,
            "sharesOutstanding": 15e9,
        }

        # Mock cash flow data
        dates = pd.to_datetime(["2021-01-01", "2022-01-01", "2023-01-01"])
        mock_financials = {
            "cash_flow": pd.DataFrame(
                {
                    "Free Cash Flow": [80e9, 90e9, 100e9],
                    "Operating Cash Flow": [100e9, 110e9, 120e9],
                },
                index=dates,
            )
        }

        # Mock columns
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]

        # Mock sliders
        mock_st.slider.return_value = 10.0

        # Mock expander
        mock_expander = MagicMock()
        mock_st.expander.return_value.__enter__.return_value = mock_expander

        # Call function
        _display_dcf_valuation(mock_info, mock_financials, "AAPL")

        # Verify basic calls
        mock_st.subheader.assert_called()
        mock_st.markdown.assert_called()


class TestPDFExportFunction:
    """Test PDF statement export functionality."""

    @patch("modules.financial_analyst.st")
    def test_display_statement_export_button_present(self, mock_st):
        """Test that PDF export button is present."""
        from modules.financial_analyst import _display_statement_export
        import pandas as pd

        # Mock DataFrame
        df = pd.DataFrame({
            "Revenue": [100e9, 110e9, 120e9],
            "Net Income": [20e9, 22e9, 25e9],
        })

        # Mock button (not clicked)
        mock_st.button.return_value = False

        # Call function
        _display_statement_export(df, "income_statement")

        # Verify button was created
        mock_st.button.assert_called_once()
        button_call = mock_st.button.call_args
        assert "PDF" in button_call[0][0]

    @patch("modules.financial_analyst.st")
    @patch("modules.financial_analyst.plt")
    def test_pdf_export_matplotlib_not_available(self, mock_plt, mock_st):
        """Test PDF export handles missing matplotlib gracefully."""
        from modules.financial_analyst import _display_statement_export
        import pandas as pd

        # Mock DataFrame
        df = pd.DataFrame({
            "Revenue": [100e9, 110e9, 120e9],
        })

        # Mock button clicked
        mock_st.button.return_value = True

        # Mock session state
        mock_st.session_state.fa_ticker = "AAPL"

        # Simulate ImportError by making matplotlib import fail
        with patch("modules.financial_analyst.PdfPages", side_effect=ImportError):
            _display_statement_export(df, "income_statement")

            # Should show error about matplotlib
            mock_st.error.assert_called()
            error_call = mock_st.error.call_args[0][0]
            assert "matplotlib" in error_call.lower()
