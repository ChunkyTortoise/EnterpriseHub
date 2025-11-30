"""Market data generation with validation and error handling.

Provides functions for generating realistic OHLCV market data
with proper validation and reproducible random seeds.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Optional

from utils.config import BASE_PRICES, VOLATILITY, VOLUME_RANGE
from utils.indicators import add_all_indicators


def generate_market_data(symbol: str, 
                        days: int = 30,
                        seed: Optional[int] = 42) -> pd.DataFrame:
    """
    Generate realistic market data with OHLCV format.
    
    Args:
        symbol: Asset symbol (BTC, ETH, AAPL, TSLA)
        days: Number of days of data to generate
        seed: Random seed for reproducibility (None for random)
    
    Returns:
        DataFrame with OHLCV data and technical indicators
    
    Raises:
        ValueError: If symbol is invalid or days < 30
    """
    # Validation
    if symbol not in BASE_PRICES:
        raise ValueError(f"Invalid symbol: {symbol}. Must be one of {list(BASE_PRICES.keys())}")
    
    if days < 30:
        raise ValueError(f"Need at least 30 days for proper indicator calculation. Got {days}")
    
    # Set random seed for reproducibility
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    
    # Generate date range
    dates = [datetime.now() - timedelta(days=x) for x in range(days)]
    dates.reverse()
    
    # Get asset-specific parameters
    base_price = BASE_PRICES[symbol]
    volatility = VOLATILITY[symbol]
    
    # Generate price data
    data = []
    current_price = base_price
    
    for i in range(days):
        open_price = current_price
        
        # Daily price movement
        daily_change = random.uniform(-volatility, volatility)
        close_price = open_price * (1 + daily_change)
        
        # High/Low with realistic spread
        high_price = max(open_price, close_price) * random.uniform(1.0, 1.02)
        low_price = min(open_price, close_price) * random.uniform(0.98, 1.0)
        
        # Volume
        volume = random.uniform(VOLUME_RANGE["MIN"], VOLUME_RANGE["MAX"])
        
        data.append({
            'Date': dates[i],
            'Open': round(open_price, 2),
            'High': round(high_price, 2),
            'Low': round(low_price, 2),
            'Close': round(close_price, 2),
            'Volume': int(volume)
        })
        
        current_price = close_price
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Calculate returns
    df['Returns'] = df['Close'].pct_change()
    
    # Add all technical indicators
    df = add_all_indicators(df)
    
    return df


def validate_market_data(df: pd.DataFrame) -> bool:
    """
    Validate market data integrity.
    
    Args:
        df: Market data DataFrame
    
    Returns:
        True if data is valid
    
    Raises:
        ValueError: If data fails validation
    """
    required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    
    # Check required columns
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Missing required columns: {missing}")
    
    # Check OHLC relationships
    invalid_high = (df['High'] < df['Low']) | (df['High'] < df['Open']) | (df['High'] < df['Close'])
    if invalid_high.any():
        raise ValueError("High price must be >= all other prices")
    
    invalid_low = (df['Low'] > df['High']) | (df['Low'] > df['Open']) | (df['Low'] > df['Close'])
    if invalid_low.any():
        raise ValueError("Low price must be <= all other prices")
    
    # Check for negative prices
    price_cols = ['Open', 'High', 'Low', 'Close']
    if (df[price_cols] <= 0).any().any():
        raise ValueError("Prices must be positive")
    
    # Check for negative volume
    if (df['Volume'] < 0).any():
        raise ValueError("Volume must be non-negative")
    
    return True
