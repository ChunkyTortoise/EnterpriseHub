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


@dataclass
class PiotroskiScore:
    """
    Piotroski F-Score result (0-9 point system).

    Higher scores indicate better financial health.
    Score interpretation:
    - 7-9: Strong financial health
    - 4-6: Moderate financial health
    - 0-3: Weak financial health
    """
    total_score: int  # 0-9
    profitability_score: int  # 0-4 (ROA, OCF, ROA change, Accruals)
    leverage_score: int  # 0-3 (D/E change, Current Ratio change, Shares)
    efficiency_score: int  # 0-2 (Margin change, Turnover change)
    criteria: Dict[str, bool]  # Breakdown of all 9 checks
    interpretation: str  # "Strong", "Moderate", "Weak"


@dataclass
class HistoricalRatios:
    """
    Historical financial ratios over multiple years.

    All Series have years as index and ratio values.
    """
    years: List[str]  # ["2019", "2020", "2021", "2022", "2023"]
    current_ratio: pd.Series  # Current Assets / Current Liabilities
    debt_to_equity: pd.Series  # Total Debt / Equity
    roe: pd.Series  # Return on Equity %
    net_margin: pd.Series  # Net Income / Revenue %
    gross_margin: pd.Series  # Gross Profit / Revenue %


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


# --- Financial Ratio Calculators ---

def calculate_current_ratio(balance_sheet: Optional[pd.DataFrame]) -> Optional[float]:
    """
    Calculate Current Ratio (Current Assets / Current Liabilities).
    Measures short-term liquidity.

    Args:
        balance_sheet: Transposed balance sheet DataFrame (columns are dates)

    Returns:
        Current ratio, or None if data unavailable
    """
    if balance_sheet is None or balance_sheet.empty:
        return None

    # Transpose to get dates as index
    bs_t = balance_sheet.T
    bs_t.index = pd.to_datetime(bs_t.index)
    bs_t = bs_t.sort_index()

    current_assets_col = find_column(bs_t, ["CurrentAssets", "Current Assets", "TotalCurrentAssets"])
    current_liab_col = find_column(bs_t, ["CurrentLiabilities", "Current Liabilities", "TotalCurrentLiabilities"])

    if not current_assets_col or not current_liab_col or len(bs_t) == 0:
        return None

    latest_assets = bs_t[current_assets_col].iloc[-1]
    latest_liab = bs_t[current_liab_col].iloc[-1]

    if pd.isna(latest_liab) or latest_liab == 0:
        return None

    return round(latest_assets / latest_liab, 2)


def calculate_debt_to_equity(balance_sheet: Optional[pd.DataFrame]) -> Optional[float]:
    """
    Calculate Debt-to-Equity Ratio (Total Debt / Total Equity).
    Measures financial leverage.

    Args:
        balance_sheet: Transposed balance sheet DataFrame

    Returns:
        Debt-to-Equity ratio, or None if data unavailable
    """
    if balance_sheet is None or balance_sheet.empty:
        return None

    bs_t = balance_sheet.T
    bs_t.index = pd.to_datetime(bs_t.index)
    bs_t = bs_t.sort_index()

    debt_col = find_column(bs_t, ["TotalDebt", "Total Debt", "LongTermDebt"])
    equity_col = find_column(bs_t, ["TotalStockholderEquity", "Total Stockholder Equity", "StockholdersEquity", "ShareholderEquity"])

    if not debt_col or not equity_col or len(bs_t) == 0:
        return None

    latest_debt = bs_t[debt_col].iloc[-1]
    latest_equity = bs_t[equity_col].iloc[-1]

    if pd.isna(latest_equity) or latest_equity == 0:
        return None

    return round(latest_debt / latest_equity, 2)


def calculate_roe(income_stmt: Optional[pd.DataFrame], balance_sheet: Optional[pd.DataFrame]) -> Optional[float]:
    """
    Calculate Return on Equity (Net Income / Shareholders Equity) * 100.
    Measures profitability relative to equity.

    Args:
        income_stmt: Transposed income statement DataFrame
        balance_sheet: Transposed balance sheet DataFrame

    Returns:
        ROE as percentage, or None if data unavailable
    """
    if income_stmt is None or income_stmt.empty or balance_sheet is None or balance_sheet.empty:
        return None

    # Process income statement
    inc_t = income_stmt.T
    inc_t.index = pd.to_datetime(inc_t.index)
    inc_t = inc_t.sort_index()

    # Process balance sheet
    bs_t = balance_sheet.T
    bs_t.index = pd.to_datetime(bs_t.index)
    bs_t = bs_t.sort_index()

    net_income_col = find_column(inc_t, ["NetIncome", "Net Income", "NetProfit"])
    equity_col = find_column(bs_t, ["TotalStockholderEquity", "Total Stockholder Equity", "StockholdersEquity"])

    if not net_income_col or not equity_col or len(inc_t) == 0 or len(bs_t) == 0:
        return None

    latest_net_income = inc_t[net_income_col].iloc[-1]
    latest_equity = bs_t[equity_col].iloc[-1]

    if pd.isna(latest_equity) or latest_equity == 0:
        return None

    return round((latest_net_income / latest_equity) * 100, 1)


def calculate_ocf_margin(income_stmt: Optional[pd.DataFrame], cashflow: Optional[pd.DataFrame]) -> Optional[float]:
    """
    Calculate Operating Cash Flow Margin (OCF / Revenue) * 100.
    Measures cash generation efficiency.

    Args:
        income_stmt: Transposed income statement DataFrame
        cashflow: Transposed cash flow DataFrame

    Returns:
        OCF margin as percentage, or None if data unavailable
    """
    if income_stmt is None or income_stmt.empty or cashflow is None or cashflow.empty:
        return None

    # Process income statement
    inc_t = income_stmt.T
    inc_t.index = pd.to_datetime(inc_t.index)
    inc_t = inc_t.sort_index()

    # Process cash flow
    cf_t = cashflow.T
    cf_t.index = pd.to_datetime(cf_t.index)
    cf_t = cf_t.sort_index()

    revenue_col = find_column(inc_t, ["TotalRevenue", "Revenue", "OperatingRevenue"])
    ocf_col = find_column(cf_t, ["OperatingCashFlow", "Operating Cash Flow", "TotalCashFromOperatingActivities"])

    if not revenue_col or not ocf_col or len(inc_t) == 0 or len(cf_t) == 0:
        return None

    latest_revenue = inc_t[revenue_col].iloc[-1]
    latest_ocf = cf_t[ocf_col].iloc[-1]

    if pd.isna(latest_revenue) or latest_revenue == 0:
        return None

    return round((latest_ocf / latest_revenue) * 100, 1)


# --- Piotroski F-Score ---

def calculate_piotroski_score(financials: FinancialsDict) -> Optional[PiotroskiScore]:
    """
    Calculate Piotroski F-Score (0-9 point financial health score).

    The score evaluates 9 criteria across profitability, leverage, and efficiency.
    Higher scores indicate stronger financial health.

    Args:
        financials: Dictionary with income_stmt, balance_sheet, cashflow DataFrames

    Returns:
        PiotroskiScore object with score breakdown, or None if insufficient data
    """
    income_stmt = financials.get("income_stmt")
    balance_sheet = financials.get("balance_sheet")
    cashflow = financials.get("cashflow")

    # Require at least 2 years of data
    if (income_stmt is None or income_stmt.empty or
        balance_sheet is None or balance_sheet.empty or
        cashflow is None or cashflow.empty):
        return None

    # Transpose and sort by date
    inc_t = income_stmt.T
    inc_t.index = pd.to_datetime(inc_t.index)
    inc_t = inc_t.sort_index()

    bs_t = balance_sheet.T
    bs_t.index = pd.to_datetime(bs_t.index)
    bs_t = bs_t.sort_index()

    cf_t = cashflow.T
    cf_t.index = pd.to_datetime(cf_t.index)
    cf_t = cf_t.sort_index()

    if len(inc_t) < 2 or len(bs_t) < 2 or len(cf_t) < 2:
        return None

    # Initialize criteria tracking
    criteria = {}
    prof_score = 0
    lev_score = 0
    eff_score = 0

    # Find required columns
    net_income_col = find_column(inc_t, ["NetIncome", "Net Income"])
    revenue_col = find_column(inc_t, ["TotalRevenue", "Revenue"])
    gross_profit_col = find_column(inc_t, ["GrossProfit", "Gross Profit"])
    total_assets_col = find_column(bs_t, ["TotalAssets", "Total Assets"])
    equity_col = find_column(bs_t, ["TotalStockholderEquity", "Total Stockholder Equity", "StockholdersEquity"])
    current_assets_col = find_column(bs_t, ["CurrentAssets", "Current Assets"])
    current_liab_col = find_column(bs_t, ["CurrentLiabilities", "Current Liabilities"])
    debt_col = find_column(bs_t, ["TotalDebt", "Total Debt", "LongTermDebt"])
    shares_col = find_column(bs_t, ["CommonStockSharesOutstanding", "Common Stock Shares Outstanding", "SharesOutstanding"])
    ocf_col = find_column(cf_t, ["OperatingCashFlow", "Operating Cash Flow", "TotalCashFromOperatingActivities"])

    # --- PROFITABILITY CRITERIA (4 points) ---

    # 1. Positive ROA (Net Income / Total Assets > 0)
    if net_income_col and total_assets_col:
        latest_ni = inc_t[net_income_col].iloc[-1]
        latest_assets = bs_t[total_assets_col].iloc[-1]
        if not pd.isna(latest_ni) and not pd.isna(latest_assets) and latest_assets > 0:
            roa = latest_ni / latest_assets
            criteria["positive_roa"] = roa > 0
            if roa > 0:
                prof_score += 1
        else:
            criteria["positive_roa"] = False
    else:
        criteria["positive_roa"] = False

    # 2. Positive Operating Cash Flow
    if ocf_col:
        latest_ocf = cf_t[ocf_col].iloc[-1]
        if not pd.isna(latest_ocf):
            criteria["positive_ocf"] = latest_ocf > 0
            if latest_ocf > 0:
                prof_score += 1
        else:
            criteria["positive_ocf"] = False
    else:
        criteria["positive_ocf"] = False

    # 3. ROA increasing (compare last 2 years)
    if net_income_col and total_assets_col and len(inc_t) >= 2 and len(bs_t) >= 2:
        prev_ni = inc_t[net_income_col].iloc[-2]
        prev_assets = bs_t[total_assets_col].iloc[-2]
        latest_ni = inc_t[net_income_col].iloc[-1]
        latest_assets = bs_t[total_assets_col].iloc[-1]

        if all(not pd.isna(x) and x > 0 for x in [prev_assets, latest_assets]):
            prev_roa = prev_ni / prev_assets
            latest_roa = latest_ni / latest_assets
            criteria["roa_improving"] = latest_roa > prev_roa
            if latest_roa > prev_roa:
                prof_score += 1
        else:
            criteria["roa_improving"] = False
    else:
        criteria["roa_improving"] = False

    # 4. Quality of Earnings (OCF > Net Income, i.e., low accruals)
    if ocf_col and net_income_col:
        latest_ocf = cf_t[ocf_col].iloc[-1]
        latest_ni = inc_t[net_income_col].iloc[-1]
        if not pd.isna(latest_ocf) and not pd.isna(latest_ni):
            criteria["quality_earnings"] = latest_ocf > latest_ni
            if latest_ocf > latest_ni:
                prof_score += 1
        else:
            criteria["quality_earnings"] = False
    else:
        criteria["quality_earnings"] = False

    # --- LEVERAGE/LIQUIDITY CRITERIA (3 points) ---

    # 5. Decreasing leverage (D/E ratio improving)
    if debt_col and equity_col and len(bs_t) >= 2:
        prev_debt = bs_t[debt_col].iloc[-2]
        prev_equity = bs_t[equity_col].iloc[-2]
        latest_debt = bs_t[debt_col].iloc[-1]
        latest_equity = bs_t[equity_col].iloc[-1]

        if all(not pd.isna(x) and x > 0 for x in [prev_equity, latest_equity]):
            prev_de = prev_debt / prev_equity
            latest_de = latest_debt / latest_equity
            criteria["leverage_decreasing"] = latest_de < prev_de
            if latest_de < prev_de:
                lev_score += 1
        else:
            criteria["leverage_decreasing"] = False
    else:
        criteria["leverage_decreasing"] = False

    # 6. Increasing liquidity (Current Ratio improving)
    if current_assets_col and current_liab_col and len(bs_t) >= 2:
        prev_ca = bs_t[current_assets_col].iloc[-2]
        prev_cl = bs_t[current_liab_col].iloc[-2]
        latest_ca = bs_t[current_assets_col].iloc[-1]
        latest_cl = bs_t[current_liab_col].iloc[-1]

        if all(not pd.isna(x) and x > 0 for x in [prev_cl, latest_cl]):
            prev_cr = prev_ca / prev_cl
            latest_cr = latest_ca / latest_cl
            criteria["liquidity_improving"] = latest_cr > prev_cr
            if latest_cr > prev_cr:
                lev_score += 1
        else:
            criteria["liquidity_improving"] = False
    else:
        criteria["liquidity_improving"] = False

    # 7. No new shares issued (shares outstanding not increasing)
    if shares_col and len(bs_t) >= 2:
        prev_shares = bs_t[shares_col].iloc[-2]
        latest_shares = bs_t[shares_col].iloc[-1]
        if not pd.isna(prev_shares) and not pd.isna(latest_shares):
            criteria["no_dilution"] = latest_shares <= prev_shares
            if latest_shares <= prev_shares:
                lev_score += 1
        else:
            criteria["no_dilution"] = False
    else:
        criteria["no_dilution"] = False

    # --- OPERATING EFFICIENCY CRITERIA (2 points) ---

    # 8. Increasing gross margin
    if gross_profit_col and revenue_col and len(inc_t) >= 2:
        prev_gp = inc_t[gross_profit_col].iloc[-2]
        prev_rev = inc_t[revenue_col].iloc[-2]
        latest_gp = inc_t[gross_profit_col].iloc[-1]
        latest_rev = inc_t[revenue_col].iloc[-1]

        if all(not pd.isna(x) and x > 0 for x in [prev_rev, latest_rev]):
            prev_margin = prev_gp / prev_rev
            latest_margin = latest_gp / latest_rev
            criteria["margin_improving"] = latest_margin > prev_margin
            if latest_margin > prev_margin:
                eff_score += 1
        else:
            criteria["margin_improving"] = False
    else:
        criteria["margin_improving"] = False

    # 9. Increasing asset turnover (Revenue / Total Assets improving)
    if revenue_col and total_assets_col and len(inc_t) >= 2 and len(bs_t) >= 2:
        prev_rev = inc_t[revenue_col].iloc[-2]
        prev_assets = bs_t[total_assets_col].iloc[-2]
        latest_rev = inc_t[revenue_col].iloc[-1]
        latest_assets = bs_t[total_assets_col].iloc[-1]

        if all(not pd.isna(x) and x > 0 for x in [prev_assets, latest_assets]):
            prev_turnover = prev_rev / prev_assets
            latest_turnover = latest_rev / latest_assets
            criteria["turnover_improving"] = latest_turnover > prev_turnover
            if latest_turnover > prev_turnover:
                eff_score += 1
        else:
            criteria["turnover_improving"] = False
    else:
        criteria["turnover_improving"] = False

    # Calculate total score
    total = prof_score + lev_score + eff_score

    # Determine interpretation
    if total >= 7:
        interpretation = "Strong"
    elif total >= 4:
        interpretation = "Moderate"
    else:
        interpretation = "Weak"

    return PiotroskiScore(
        total_score=total,
        profitability_score=prof_score,
        leverage_score=lev_score,
        efficiency_score=eff_score,
        criteria=criteria,
        interpretation=interpretation
    )


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

# --- Historical Ratio Trends ---

def calculate_historical_ratios(financials: FinancialsDict) -> Optional[HistoricalRatios]:
    """
    Calculate historical financial ratios over all available years.

    Args:
        financials: Dictionary with income_stmt, balance_sheet, cashflow DataFrames

    Returns:
        HistoricalRatios object with trends, or None if insufficient data
    """
    income_stmt = financials.get("income_stmt")
    balance_sheet = financials.get("balance_sheet")

    if (income_stmt is None or income_stmt.empty or
        balance_sheet is None or balance_sheet.empty):
        return None

    # Transpose and sort by date
    inc_t = income_stmt.T
    inc_t.index = pd.to_datetime(inc_t.index)
    inc_t = inc_t.sort_index()

    bs_t = balance_sheet.T
    bs_t.index = pd.to_datetime(bs_t.index)
    bs_t = bs_t.sort_index()

    if len(inc_t) < 2 or len(bs_t) < 2:
        return None

    # Find columns
    revenue_col = find_column(inc_t, ["TotalRevenue", "Revenue"])
    net_income_col = find_column(inc_t, ["NetIncome", "Net Income"])
    gross_profit_col = find_column(inc_t, ["GrossProfit", "Gross Profit"])
    total_assets_col = find_column(bs_t, ["TotalAssets", "Total Assets"])
    equity_col = find_column(bs_t, ["TotalStockholderEquity", "Total Stockholder Equity", "StockholdersEquity"])
    current_assets_col = find_column(bs_t, ["CurrentAssets", "Current Assets"])
    current_liab_col = find_column(bs_t, ["CurrentLiabilities", "Current Liabilities"])
    debt_col = find_column(bs_t, ["TotalDebt", "Total Debt", "LongTermDebt"])

    # Extract years
    years = [str(dt.year) for dt in inc_t.index]

    # Calculate ratio series
    current_ratio_series = pd.Series(dtype=float)
    debt_to_equity_series = pd.Series(dtype=float)
    roe_series = pd.Series(dtype=float)
    net_margin_series = pd.Series(dtype=float)
    gross_margin_series = pd.Series(dtype=float)

    for idx in inc_t.index:
        year = str(idx.year)

        # Current Ratio
        if current_assets_col and current_liab_col:
            ca = bs_t.loc[idx, current_assets_col] if idx in bs_t.index else None
            cl = bs_t.loc[idx, current_liab_col] if idx in bs_t.index else None
            if ca is not None and cl is not None and cl > 0:
                current_ratio_series[year] = round(ca / cl, 2)

        # Debt-to-Equity
        if debt_col and equity_col:
            debt = bs_t.loc[idx, debt_col] if idx in bs_t.index else None
            equity = bs_t.loc[idx, equity_col] if idx in bs_t.index else None
            if debt is not None and equity is not None and equity > 0:
                debt_to_equity_series[year] = round(debt / equity, 2)

        # ROE
        if net_income_col and equity_col:
            ni = inc_t.loc[idx, net_income_col]
            equity = bs_t.loc[idx, equity_col] if idx in bs_t.index else None
            if ni is not None and equity is not None and equity > 0:
                roe_series[year] = round((ni / equity) * 100, 1)

        # Net Margin
        if net_income_col and revenue_col:
            ni = inc_t.loc[idx, net_income_col]
            rev = inc_t.loc[idx, revenue_col]
            if ni is not None and rev is not None and rev > 0:
                net_margin_series[year] = round((ni / rev) * 100, 1)

        # Gross Margin
        if gross_profit_col and revenue_col:
            gp = inc_t.loc[idx, gross_profit_col]
            rev = inc_t.loc[idx, revenue_col]
            if gp is not None and rev is not None and rev > 0:
                gross_margin_series[year] = round((gp / rev) * 100, 1)

    return HistoricalRatios(
        years=years,
        current_ratio=current_ratio_series,
        debt_to_equity=debt_to_equity_series,
        roe=roe_series,
        net_margin=net_margin_series,
        gross_margin=gross_margin_series
    )


# --- AI Integration ---

def build_ai_prompt(info: CompanyInfo, financials: FinancialsDict) -> str:
    """
    Constructs an enhanced prompt for the AI analyst with comprehensive financial ratios.

    Args:
        info: Company information dictionary
        financials: Financial statements (income, balance sheet, cash flow)

    Returns:
        Formatted prompt string for Claude API
    """
    summary_parts = []

    # Basics
    summary_parts.append(f"Company: {info.get('longName', 'N/A')}")
    summary_parts.append(f"Sector: {info.get('sector', 'N/A')}")
    summary_parts.append(f"Industry: {info.get('industry', 'N/A')}")

    if info.get("marketCap"):
        summary_parts.append(f"Market Cap: ${info['marketCap'] / 1e9:.2f}B")

    # Income Statement Metrics
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

    # Balance Sheet Ratios
    balance_sheet = financials.get("balance_sheet")
    if balance_sheet is not None and not balance_sheet.empty:
        summary_parts.append("\n--- Liquidity & Leverage Metrics ---")

        # Current Ratio
        current_ratio = calculate_current_ratio(balance_sheet)
        if current_ratio is not None:
            summary_parts.append(f"Current Ratio: {current_ratio:.2f}")

        # Debt-to-Equity
        debt_to_equity = calculate_debt_to_equity(balance_sheet)
        if debt_to_equity is not None:
            summary_parts.append(f"Debt-to-Equity: {debt_to_equity:.2f}")

    # Profitability Ratios (require both income statement and balance sheet)
    if inc is not None and not inc.empty and balance_sheet is not None and not balance_sheet.empty:
        # Return on Equity
        roe = calculate_roe(inc, balance_sheet)
        if roe is not None:
            summary_parts.append(f"ROE: {roe:.1f}%")

    # Cash Flow Metrics
    cashflow = financials.get("cashflow")
    if inc is not None and not inc.empty and cashflow is not None and not cashflow.empty:
        summary_parts.append("\n--- Cash Flow Metrics ---")

        # Operating Cash Flow Margin
        ocf_margin = calculate_ocf_margin(inc, cashflow)
        if ocf_margin is not None:
            summary_parts.append(f"Operating Cash Flow Margin: {ocf_margin:.1f}%")

    financial_summary = "\n".join(summary_parts)

    return f"""Analyze the following financial data for {info.get('longName', 'the company')}:

{financial_summary}

Provide a concise financial analysis in the following format:

**Financial Health Assessment:**
[3-5 bullet points assessing overall financial health, profitability, liquidity, and growth. Reference the specific ratios provided above.]

**Key Risks:**
[2-3 bullet points identifying potential risks or concerns based on the financial metrics]

**Key Opportunities:**
[2-3 bullet points highlighting strengths and opportunities based on the data]

Keep each bullet point to 1-2 sentences. Be specific and data-driven. Focus on actionable insights."""
