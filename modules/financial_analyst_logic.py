"""
Core logic for the Financial Analyst module.

This module contains:
- Type definitions for financial data.
- Pure functions for financial calculations (DCF, Ratios).
- Helper functions for data parsing and prompt generation.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict, Union, Any
import pandas as pd
import numpy as np

# --- Type Definitions ---

class CompanyInfo(TypedDict, total=False):
    """Type definition for company information from yfinance."""
    longName: str
    sector: str
    industry: str
    country: str
    website: str
    longBusinessSummary: str
    marketCap: Optional[float]
    trailingPE: Optional[float]
    trailingEps: Optional[float]
    dividendYield: Optional[float]
    currentPrice: Optional[float]
    regularMarketPrice: Optional[float]
    sharesOutstanding: Optional[float]
    beta: Optional[float]


class FinancialsDict(TypedDict):
    """Type definition for financial statements."""
    balance_sheet: Optional[pd.DataFrame]
    income_stmt: Optional[pd.DataFrame]
    cashflow: Optional[pd.DataFrame]


@dataclass
class DCFParameters:
    """Parameters for DCF Valuation Model."""
    growth_years_1_5: float
    growth_years_6_10: float
    terminal_growth: float
    discount_rate: float
    margin_of_safety: float


@dataclass
class DCFResult:
    """Result of DCF Valuation."""
    fair_value: float
    conservative_value: float
    upside_percent: float
    enterprise_value: float
    projections: List[Dict[str, float]]
    is_undervalued: bool
    verdict: str  # "UNDERVALUED", "OVERVALUED", "FAIRLY VALUED"


# --- Helper Functions ---

def find_column(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
    """
    Find a column in a DataFrame that matches one of the keywords.
    Case-insensitive and ignores spaces.
    
    Args:
        df: The DataFrame to search.
        keywords: List of keywords to match (e.g., ["TotalRevenue", "Revenue"])
        
    Returns:
        The matching column name, or None if not found.
    """
    if df is None or df.empty:
        return None
        
    for col in df.columns:
        col_clean = str(col).replace(" ", "").lower()
        for kw in keywords:
            if kw.lower() in col_clean:
                return col
    return None


def calculate_yoy_growth(series: pd.Series) -> Optional[float]:
    """
    Calculate Year-over-Year growth rate from the last two data points.
    Assumes series is sorted chronologically. 
    
    Returns:
        Growth rate as a percentage (e.g., 15.5 for 15.5%), or None if invalid.
    """
    try:
        clean_series = series.dropna()
        if len(clean_series) < 2:
            return None
            
        latest = clean_series.iloc[-1]
        previous = clean_series.iloc[-2]
        
        if previous == 0:
            return None
            
        return ((latest - previous) / previous) * 100
    except Exception:
        return None


# --- Core Logic ---

class DCFModel:
    """Discounted Cash Flow Valuation Model."""
    
    @staticmethod
    def calculate(
        latest_fcf: float,
        shares_outstanding: float,
        current_price: float,
        params: DCFParameters
    ) -> DCFResult:
        """
        Perform DCF calculation.
        
        Args:
            latest_fcf: Most recent Free Cash Flow value.
            shares_outstanding: Number of shares.
            current_price: Current stock price.
            params: DCF parameters (growth rates, discount rate, etc.)
            
        Returns:
            DCFResult object containing valuation details.
        """
        projected_fcf = []
        current_val = latest_fcf
        
        # Years 1-5
        for year in range(1, 6):
            current_val *= (1 + params.growth_years_1_5 / 100)
            pv = current_val / ((1 + params.discount_rate / 100) ** year)
            projected_fcf.append({"Year": year, "FCF": current_val, "PV": pv})
            
        # Years 6-10
        for year in range(6, 11):
            current_val *= (1 + params.growth_years_6_10 / 100)
            pv = current_val / ((1 + params.discount_rate / 100) ** year)
            projected_fcf.append({"Year": year, "FCF": current_val, "PV": pv})
            
        # Terminal Value
        terminal_fcf = current_val * (1 + params.terminal_growth / 100)
        # Gordon Growth Model: TV = FCF * (1+g) / (r - g)
        # Ensure denominator is not zero or negative
        denom = max(0.001, (params.discount_rate / 100) - (params.terminal_growth / 100))
        terminal_val = terminal_fcf / denom
        terminal_pv = terminal_val / ((1 + params.discount_rate / 100) ** 10)
        
        # Enterprise Value
        sum_pv = sum(p["PV"] for p in projected_fcf)
        enterprise_value = sum_pv + terminal_pv
        
        # Fair Value per Share
        if shares_outstanding <= 0:
            fair_value = 0.0
        else:
            fair_value = enterprise_value / shares_outstanding
            
        conservative_value = fair_value * (1 - params.margin_of_safety / 100)
        
        upside = 0.0
        if current_price > 0:
            upside = ((fair_value - current_price) / current_price) * 100
            
        # Verdict
        if fair_value > current_price * 1.2:
            verdict = "UNDERVALUED"
        elif fair_value < current_price * 0.8:
            verdict = "OVERVALUED"
        else:
            verdict = "FAIRLY VALUED"
            
        return DCFResult(
            fair_value=fair_value,
            conservative_value=conservative_value,
            upside_percent=upside,
            enterprise_value=enterprise_value,
            projections=projected_fcf,
            is_undervalued=(verdict == "UNDERVALUED"),
            verdict=verdict
        )

# --- AI Integration ---

def build_ai_prompt(info: CompanyInfo, financials: FinancialsDict) -> str:
    """Constructs the prompt for the AI analyst."""
    
    summary_parts = []
    
    # Basics
    summary_parts.append(f"Company: {info.get('longName', 'N/A')}")
    summary_parts.append(f"Sector: {info.get('sector', 'N/A')}")
    summary_parts.append(f"Industry: {info.get('industry', 'N/A')}")
    
    if info.get("marketCap"):
        summary_parts.append(f"Market Cap: ${info['marketCap'] / 1e9:.2f}B")
    
    # Financials (Last Year vs Previous)
    inc = financials.get("income_stmt")
    if inc is not None and not inc.empty:
        # Transpose to get dates as index
        inc_t = inc.T
        inc_t.index = pd.to_datetime(inc_t.index)
        inc_t = inc_t.sort_index()
        
        rev_col = find_column(inc_t, ["TotalRevenue", "Revenue"])
        net_col = find_column(inc_t, ["NetIncome", "NetProfit"])
        
        if rev_col and len(inc_t) >= 2:
            latest_rev = inc_t[rev_col].iloc[-1]
            rev_growth = calculate_yoy_growth(inc_t[rev_col])
            
            summary_parts.append(f"Latest Revenue: ${latest_rev / 1e9:.2f}B")
            if rev_growth is not None:
                summary_parts.append(f"Revenue Growth (YoY): {rev_growth:.1f}%")
                
        if net_col and len(inc_t) >= 1:
             latest_net = inc_t[net_col].iloc[-1]
             summary_parts.append(f"Latest Net Income: ${latest_net / 1e9:.2f}B")

    financial_summary = "\n".join(summary_parts)
    
    return f"""Analyze the following financial data for {info.get('longName', 'the company')}:

{financial_summary}

Provide a concise financial analysis in the following format:

**Financial Health Assessment:**
[3-5 bullet points assessing overall financial health, profitability, liquidity, and growth]

**Key Risks:**
[2-3 bullet points identifying potential risks or concerns]

**Key Opportunities:**
[2-3 bullet points highlighting strengths and opportunities]

Keep each bullet point to 1-2 sentences. Be specific and data-driven. Focus on actionable insights."""
