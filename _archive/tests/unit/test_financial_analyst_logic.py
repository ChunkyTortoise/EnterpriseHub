"""Tests for Financial Analyst Core Logic."""

import pytest
import pandas as pd
import numpy as np
from modules.financial_analyst_logic import (
    DCFModel,
    DCFParameters,
    calculate_yoy_growth,
    find_column,
    build_ai_prompt,
    CompanyInfo,
    FinancialsDict
)

class TestDCFModel:
    """Test DCF Calculation Logic."""

    def test_basic_calculation(self):
        """Test a standard DCF calculation."""
        params = DCFParameters(
            growth_years_1_5=10.0,
            growth_years_6_10=5.0,
            terminal_growth=2.5,
            discount_rate=10.0,
            margin_of_safety=20.0
        )
        
        result = DCFModel.calculate(
            latest_fcf=100.0,
            shares_outstanding=10.0,
            current_price=100.0, # Arbitrary
            params=params
        )
        
        # Basic sanity checks
        assert result.fair_value > 0
        assert result.conservative_value < result.fair_value
        assert len(result.projections) == 10
        assert result.enterprise_value > 100.0

    def test_zero_shares(self):
        """Test handling of zero shares outstanding."""
        params = DCFParameters(
            growth_years_1_5=10.0,
            growth_years_6_10=5.0,
            terminal_growth=2.5,
            discount_rate=10.0,
            margin_of_safety=20.0
        )
        
        result = DCFModel.calculate(
            latest_fcf=100.0,
            shares_outstanding=0,
            current_price=100.0,
            params=params
        )
        
        assert result.fair_value == 0.0

    def test_verdict_logic(self):
        """Test the undervalued/overvalued verdict."""
        params = DCFParameters(
            growth_years_1_5=5.0,
            growth_years_6_10=5.0,
            terminal_growth=2.0,
            discount_rate=10.0,
            margin_of_safety=0.0
        )
        
        # Case 1: Undervalued
        # Fair Value will be > 10
        result = DCFModel.calculate(
            latest_fcf=100.0,
            shares_outstanding=1.0, # High per share value
            current_price=10.0,
            params=params
        )
        assert result.verdict == "UNDERVALUED"
        assert result.is_undervalued is True

        # Case 2: Overvalued
        result = DCFModel.calculate(
            latest_fcf=1.0,
            shares_outstanding=1000.0, # Low per share value
            current_price=1000.0,
            params=params
        )
        assert result.verdict == "OVERVALUED"


class TestHelpers:
    """Test helper functions."""

    def test_find_column(self):
        df = pd.DataFrame({"Total Revenue": [1, 2], "Other": [3, 4]})
        
        # Exact match
        assert find_column(df, ["TotalRevenue"]) == "Total Revenue"
        
        # Case insensitive
        assert find_column(df, ["totalrevenue"]) == "Total Revenue"
        
        # Partial match list
        assert find_column(df, ["Revenue", "Sales"]) == "Total Revenue"
        
        # No match
        assert find_column(df, ["Profits"]) is None
        
        # None df
        assert find_column(None, ["Revenue"]) is None

    def test_calculate_yoy_growth(self):
        s = pd.Series([100.0, 110.0])
        assert calculate_yoy_growth(s) == 10.0
        
        s_neg = pd.Series([100.0, 90.0])
        assert calculate_yoy_growth(s_neg) == -10.0
        
        # Not enough data
        s_short = pd.Series([100.0])
        assert calculate_yoy_growth(s_short) is None
        
        # Zero divisor
        s_zero = pd.Series([0.0, 100.0])
        assert calculate_yoy_growth(s_zero) is None


class TestFinancialRatios:
    """Test financial ratio calculation functions."""

    def test_calculate_current_ratio(self):
        """Test Current Ratio calculation (Current Assets / Current Liabilities)."""
        from modules.financial_analyst_logic import calculate_current_ratio

        # Mock balance sheet
        df = pd.DataFrame({
            "Current Assets": [100e9, 120e9],
            "Current Liabilities": [50e9, 60e9]
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01"]))

        balance_sheet = df.T
        ratio = calculate_current_ratio(balance_sheet)

        assert ratio == 2.0  # 120/60

    def test_calculate_current_ratio_missing_data(self):
        """Test Current Ratio with missing columns."""
        from modules.financial_analyst_logic import calculate_current_ratio

        df = pd.DataFrame({
            "Other Column": [100e9, 120e9]
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01"]))

        balance_sheet = df.T
        ratio = calculate_current_ratio(balance_sheet)

        assert ratio is None

    def test_calculate_debt_to_equity(self):
        """Test Debt-to-Equity ratio (Total Debt / Total Equity)."""
        from modules.financial_analyst_logic import calculate_debt_to_equity

        df = pd.DataFrame({
            "Total Debt": [50e9, 60e9],
            "Total Stockholder Equity": [100e9, 120e9]
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01"]))

        balance_sheet = df.T
        ratio = calculate_debt_to_equity(balance_sheet)

        assert ratio == 0.5  # 60/120

    def test_calculate_roe(self):
        """Test Return on Equity (Net Income / Shareholders Equity)."""
        from modules.financial_analyst_logic import calculate_roe

        income_df = pd.DataFrame({
            "Net Income": [10e9, 15e9]
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01"]))

        balance_df = pd.DataFrame({
            "Total Stockholder Equity": [100e9, 120e9]
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01"]))

        income_stmt = income_df.T
        balance_sheet = balance_df.T

        roe = calculate_roe(income_stmt, balance_sheet)

        # (15/120) * 100 = 12.5%
        assert roe == 12.5

    def test_calculate_ocf_margin(self):
        """Test Operating Cash Flow Margin (OCF / Revenue)."""
        from modules.financial_analyst_logic import calculate_ocf_margin

        income_df = pd.DataFrame({
            "Total Revenue": [100e9, 120e9]
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01"]))

        cashflow_df = pd.DataFrame({
            "Operating Cash Flow": [30e9, 40e9]
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01"]))

        income_stmt = income_df.T
        cashflow = cashflow_df.T

        margin = calculate_ocf_margin(income_stmt, cashflow)

        # (40/120) * 100 = 33.33%, but function rounds to 1 decimal = 33.3%
        assert margin == 33.3


class TestPiotroskiScore:
    """Test Piotroski F-Score calculation."""

    def test_perfect_score(self):
        """Test company with perfect financial health (score 9)."""
        from modules.financial_analyst_logic import calculate_piotroski_score

        # Mock ideal financials - all criteria pass
        # Year 1 (older) and Year 2 (latest)
        balance_df = pd.DataFrame({
            "Total Assets": [1000e9, 1150e9],  # Assets grow slower than revenue (efficiency!)
            "Total Stockholder Equity": [500e9, 600e9],
            "Current Assets": [400e9, 500e9],
            "Current Liabilities": [200e9, 220e9],  # Current ratio improving (500/220 > 400/200)
            "Total Debt": [300e9, 250e9],  # Debt decreasing
            "Common Stock Shares Outstanding": [10e9, 10e9]  # No dilution
        }, index=pd.to_datetime(["2022-01-01", "2023-01-01"]))

        income_df = pd.DataFrame({
            "Total Revenue": [1000e9, 1200e9],  # Revenue grows faster than assets
            "Net Income": [100e9, 140e9],  # ROA improving (140/1150 > 100/1000)
            "Gross Profit": [400e9, 520e9],  # Margin improving (520/1200 > 400/1000)
        }, index=pd.to_datetime(["2022-01-01", "2023-01-01"]))

        cashflow_df = pd.DataFrame({
            "Operating Cash Flow": [120e9, 160e9]  # Positive and > Net Income
        }, index=pd.to_datetime(["2022-01-01", "2023-01-01"]))

        financials = {
            "income_stmt": income_df.T,
            "balance_sheet": balance_df.T,
            "cashflow": cashflow_df.T
        }

        result = calculate_piotroski_score(financials)

        assert result.total_score == 9
        assert result.profitability_score == 4
        assert result.leverage_score == 3
        assert result.efficiency_score == 2
        assert result.interpretation == "Strong"

    def test_poor_score(self):
        """Test company with poor financial health (low score)."""
        from modules.financial_analyst_logic import calculate_piotroski_score

        # Mock poor financials - most criteria fail
        balance_df = pd.DataFrame({
            "Total Assets": [1000e9, 1000e9],
            "Total Stockholder Equity": [500e9, 450e9],  # Equity declining
            "Current Assets": [400e9, 350e9],  # Liquidity worsening
            "Current Liabilities": [200e9, 220e9],
            "Total Debt": [300e9, 400e9],  # Debt increasing
            "Common Stock Shares Outstanding": [10e9, 11e9]  # Dilution
        }, index=pd.to_datetime(["2022-01-01", "2023-01-01"]))

        income_df = pd.DataFrame({
            "Total Revenue": [1000e9, 950e9],  # Revenue declining
            "Net Income": [-50e9, -80e9],  # Losses
            "Gross Profit": [400e9, 350e9],  # Margin declining
        }, index=pd.to_datetime(["2022-01-01", "2023-01-01"]))

        cashflow_df = pd.DataFrame({
            "Operating Cash Flow": [-30e9, -60e9]  # Negative OCF
        }, index=pd.to_datetime(["2022-01-01", "2023-01-01"]))

        financials = {
            "income_stmt": income_df.T,
            "balance_sheet": balance_df.T,
            "cashflow": cashflow_df.T
        }

        result = calculate_piotroski_score(financials)

        assert result.total_score <= 3  # Should be weak
        assert result.interpretation == "Weak"

    def test_missing_data(self):
        """Test handling of incomplete financial data."""
        from modules.financial_analyst_logic import calculate_piotroski_score

        # Empty financials
        financials = {
            "income_stmt": None,
            "balance_sheet": None,
            "cashflow": None
        }

        result = calculate_piotroski_score(financials)

        # Should return score of 0 or None with appropriate handling
        assert result is None or result.total_score == 0


class TestHistoricalRatios:
    """Test historical ratio trend calculations."""

    def test_calculate_historical_ratios(self):
        """Test calculation of 5-year ratio trends."""
        from modules.financial_analyst_logic import calculate_historical_ratios

        # Mock 3 years of data
        balance_df = pd.DataFrame({
            "Total Assets": [1000e9, 1100e9, 1200e9],
            "Total Stockholder Equity": [500e9, 550e9, 600e9],
            "Current Assets": [400e9, 450e9, 500e9],
            "Current Liabilities": [200e9, 225e9, 250e9],
            "Total Debt": [300e9, 275e9, 250e9],
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01", "2023-01-01"]))

        income_df = pd.DataFrame({
            "Total Revenue": [1000e9, 1100e9, 1200e9],
            "Net Income": [100e9, 120e9, 140e9],
            "Gross Profit": [400e9, 450e9, 520e9],
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01", "2023-01-01"]))

        financials = {
            "income_stmt": income_df.T,
            "balance_sheet": balance_df.T,
            "cashflow": None
        }

        result = calculate_historical_ratios(financials)

        # Verify structure
        assert result is not None
        assert len(result.years) == 3
        assert result.years == ["2021", "2022", "2023"]

        # Verify current ratio trend (should be 2.0, 2.0, 2.0)
        assert len(result.current_ratio) == 3
        assert result.current_ratio.iloc[0] == 2.0  # 400/200

        # Verify D/E ratio trend (should be decreasing: 0.6, 0.5, 0.42)
        assert len(result.debt_to_equity) == 3
        assert result.debt_to_equity.iloc[0] == 0.6  # 300/500
        assert result.debt_to_equity.iloc[-1] < result.debt_to_equity.iloc[0]  # Improving

        # Verify ROE trend (should be improving)
        assert len(result.roe) == 3
        assert result.roe.iloc[-1] > result.roe.iloc[0]  # ROE improving

    def test_calculate_historical_ratios_insufficient_data(self):
        """Test handling of insufficient historical data."""
        from modules.financial_analyst_logic import calculate_historical_ratios

        # Only 1 year of data
        financials = {
            "income_stmt": None,
            "balance_sheet": None,
            "cashflow": None
        }

        result = calculate_historical_ratios(financials)
        assert result is None


class TestAIIntegration:
    """Test AI Prompt Builder."""

    def test_build_prompt_basic(self):
        """Test basic prompt building with income statement only."""
        info: CompanyInfo = {"longName": "Test Corp", "sector": "Tech", "marketCap": 1e9}

        # Mock simple financials
        df = pd.DataFrame({
            "Total Revenue": [100e9, 120e9],
            "Net Income": [10e9, 15e9]
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01"]))

        financials: FinancialsDict = {
            "income_stmt": df.T, # Transposed as expected by logic
            "balance_sheet": None,
            "cashflow": None
        }

        prompt = build_ai_prompt(info, financials)

        assert "Test Corp" in prompt
        assert "Tech" in prompt
        assert "Revenue Growth (YoY): 20.0%" in prompt
        assert "Latest Net Income: $15.00B" in prompt

    def test_build_prompt_with_ratios(self):
        """Test enhanced prompt with balance sheet and cash flow ratios."""
        info: CompanyInfo = {
            "longName": "Test Corp",
            "sector": "Tech",
            "marketCap": 1e9
        }

        # Mock comprehensive financials
        income_df = pd.DataFrame({
            "Total Revenue": [100e9, 120e9],
            "Net Income": [10e9, 15e9]
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01"]))

        balance_df = pd.DataFrame({
            "Current Assets": [80e9, 100e9],
            "Current Liabilities": [40e9, 50e9],
            "Total Debt": [30e9, 40e9],
            "Total Stockholder Equity": [100e9, 120e9]
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01"]))

        cashflow_df = pd.DataFrame({
            "Operating Cash Flow": [30e9, 40e9]
        }, index=pd.to_datetime(["2021-01-01", "2022-01-01"]))

        financials: FinancialsDict = {
            "income_stmt": income_df.T,
            "balance_sheet": balance_df.T,
            "cashflow": cashflow_df.T
        }

        prompt = build_ai_prompt(info, financials)

        # Verify enhanced metrics are present
        assert "Current Ratio: 2.00" in prompt  # 100/50
        assert "Debt-to-Equity: 0.33" in prompt  # 40/120
        assert "ROE: 12.5%" in prompt  # (15/120)*100
        assert "Operating Cash Flow Margin: 33.3%" in prompt  # (40/120)*100
