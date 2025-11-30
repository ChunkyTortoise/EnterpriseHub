"""
Data loading and processing utilities for market data.

This module handles fetching stock data from Yahoo Finance and
calculating technical indicators for analysis.
"""

from typing import Optional

import pandas as pd
import streamlit as st
import ta
import yfinance as yf

from utils.exceptions import DataFetchError, DataProcessingError, InvalidTickerError
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_data(
    ticker: str,
    period: str = "1y",
    interval: str = "1d"
) -> Optional[pd.DataFrame]:
    """
    Fetch stock data from Yahoo Finance with caching.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'SPY')
        period: Time period for data (e.g., '1mo', '6mo', '1y', '5y')
        interval: Data interval (e.g., '1d', '1wk', '1mo')
    
    Returns:
        DataFrame containing OHLCV data, or None if fetch fails
    
    Raises:
        InvalidTickerError: If ticker symbol is invalid
        DataFetchError: If data fetching fails
    
    Example:
        >>> df = get_stock_data("AAPL", period="1y", interval="1d")
        >>> if df is not None:
        ...     print(df.head())
    """
    # Validate ticker
    if not ticker or not ticker.strip():
        logger.error("Empty ticker symbol provided")
        raise InvalidTickerError(ticker or "", "Ticker symbol cannot be empty")
    
    ticker = ticker.strip().upper()
    logger.info(f"Fetching data for {ticker} (period={period}, interval={interval})")
    
    try:
        # Fetch data from Yahoo Finance
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            progress=False,
            show_errors=False
        )
        
        # Check if data was returned
        if df.empty:
            logger.warning(f"No data returned for ticker: {ticker}")
            raise InvalidTickerError(
                ticker,
                f"No data available for '{ticker}'. Please check ticker symbol."
            )
        
        logger.info(f"Successfully fetched {len(df)} rows for {ticker}")
        return df
        
    except InvalidTickerError:
        # Re-raise ticker errors as-is
        raise
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        raise DataFetchError(
            f"Failed to fetch data for '{ticker}': {str(e)}"
        ) from e


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators for stock data.
    
    Adds the following indicators to the DataFrame:
    - MA20: 20-period Simple Moving Average
    - RSI: Relative Strength Index (14-period)
    - MACD: Moving Average Convergence Divergence
    - Signal: MACD Signal Line
    
    Args:
        df: DataFrame with OHLCV data (Open, High, Low, Close, Volume)
    
    Returns:
        DataFrame with added technical indicators
    
    Raises:
        DataProcessingError: If indicator calculation fails
    
    Example:
        >>> df = get_stock_data("AAPL")
        >>> df_with_indicators = calculate_indicators(df)
        >>> print(df_with_indicators[['Close', 'MA20', 'RSI']].tail())
    """
    if df is None or df.empty:
        logger.warning("Empty DataFrame provided to calculate_indicators")
        return df
    
    logger.info(f"Calculating indicators for {len(df)} rows")
    
    try:
        # Handle MultiIndex columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Validate required columns
        required_columns = ['Close', 'Open', 'High', 'Low', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise DataProcessingError(
                f"Missing required columns: {missing_columns}"
            )
        
        # Calculate Moving Average (20-period)
        df['MA20'] = ta.trend.sma_indicator(df['Close'], window=20)
        logger.debug("Calculated MA20")
        
        # Calculate RSI (14-period)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        logger.debug("Calculated RSI")
        
        # Calculate MACD
        df['MACD'] = ta.trend.macd(df['Close'])
        df['Signal'] = ta.trend.macd_signal(df['Close'])
        logger.debug("Calculated MACD and Signal")
        
        logger.info("Successfully calculated all indicators")
        return df
        
    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        raise DataProcessingError(
            f"Failed to calculate technical indicators: {str(e)}"
        ) from e

