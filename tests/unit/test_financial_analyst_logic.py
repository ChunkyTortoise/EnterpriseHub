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


class TestAIIntegration:
    """Test AI Prompt Builder."""
    
    def test_build_prompt(self):
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
