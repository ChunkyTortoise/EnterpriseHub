"""Technical indicator calculations for market data.

Provides functions for calculating RSI, MACD, Moving Averages,
and other technical indicators with proper error handling.
"""

import pandas as pd
import numpy as np
from utils.config import INDICATORS


def calculate_rsi(prices: pd.Series, period: int = None) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).

    Args:
        prices: Series of closing prices
        period: RSI period (default from config)

    Returns:
        Series of RSI values (0-100)

    Raises:
        ValueError: If period is greater than available data
    """
    if period is None:
        period = INDICATORS["RSI_PERIOD"]

    if len(prices) < period:
        raise ValueError(f"Need at least {period} data points for RSI calculation")

    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    # Prevent division by zero
    loss = loss.replace(0, 1e-10)
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Fill NaN values with neutral RSI
    rsi = rsi.fillna(50)

    return rsi


def calculate_macd(
    prices: pd.Series, fast: int = None, slow: int = None, signal: int = None
) -> tuple:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Args:
        prices: Series of closing prices
        fast: Fast EMA period (default from config)
        slow: Slow EMA period (default from config)
        signal: Signal line period (default from config)

    Returns:
        Tuple of (macd_line, signal_line)
    """
    if fast is None:
        fast = INDICATORS["MACD_FAST"]
    if slow is None:
        slow = INDICATORS["MACD_SLOW"]
    if signal is None:
        signal = INDICATORS["MACD_SIGNAL"]

    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()

    return macd, signal_line


def calculate_moving_averages(
    prices: pd.Series, short_period: int = None, long_period: int = None
) -> tuple:
    """
    Calculate short and long-term moving averages.

    Args:
        prices: Series of closing prices
        short_period: Short MA period (default from config)
        long_period: Long MA period (default from config)

    Returns:
        Tuple of (short_ma, long_ma)
    """
    if short_period is None:
        short_period = INDICATORS["MA_SHORT"]
    if long_period is None:
        long_period = INDICATORS["MA_LONG"]

    ma_short = prices.rolling(window=short_period).mean()
    ma_long = prices.rolling(window=long_period).mean()

    return ma_short, ma_long


def calculate_volatility(returns: pd.Series, window: int = 7) -> pd.Series:
    """
    Calculate annualized volatility from returns.

    Args:
        returns: Series of percentage returns
        window: Rolling window for volatility calculation

    Returns:
        Series of annualized volatility percentages
    """
    volatility = returns.rolling(window=window).std() * np.sqrt(365) * 100
    return volatility


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical indicators to a dataframe.

    Args:
        df: DataFrame with at least 'Close' and 'Returns' columns

    Returns:
        DataFrame with added indicator columns

    Raises:
        ValueError: If required columns are missing
    """
    required_cols = ["Close"]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame must contain {required_cols} columns")

    # Calculate indicators
    df["RSI"] = calculate_rsi(df["Close"])
    df["MACD"], df["Signal"] = calculate_macd(df["Close"])
    df["MA7"], df["MA30"] = calculate_moving_averages(df["Close"])

    # Calculate returns if not present
    if "Returns" not in df.columns:
        df["Returns"] = df["Close"].pct_change()

    df["Volatility"] = calculate_volatility(df["Returns"])

    return df
