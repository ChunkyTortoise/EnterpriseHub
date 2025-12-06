"""Test configuration and fixtures for pytest."""

import pytest

# Conditional imports for optional dependencies
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@pytest.fixture
def sample_stock_data():
    """Create sample OHLCV data for testing."""
    if not PANDAS_AVAILABLE:
        pytest.skip("pandas and numpy not available")

    dates = pd.date_range(start='2023-01-01', periods=30, freq='D')

    data = {
        'Open': np.random.uniform(100, 150, 30),
        'High': np.random.uniform(105, 155, 30),
        'Low': np.random.uniform(95, 145, 30),
        'Close': np.random.uniform(100, 150, 30),
        'Volume': np.random.randint(1000000, 10000000, 30)
    }

    df = pd.DataFrame(data, index=dates)
    return df


@pytest.fixture
def valid_ticker():
    """Return a valid ticker symbol for testing."""
    return "AAPL"


@pytest.fixture
def invalid_ticker():
    """Return an invalid ticker symbol for testing."""
    return "INVALID_TICKER_XYZ123"
