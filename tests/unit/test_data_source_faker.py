"""Unit tests for the data_source_faker utility."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.data_source_faker import generate_campaign_data


def test_generate_campaign_data_structure():
    """Test that generated data has expected columns and types."""
    df = generate_campaign_data(platform="Google Ads", days=5)

    expected_columns = [
        "Date",
        "Platform",
        "Impressions",
        "Clicks",
        "Spend",
        "Conversions",
        "Revenue",
        "CPC",
        "CTR",
        "Conversion_Rate",
        "ROAS",
    ]

    assert all(col in df.columns for col in expected_columns)
    assert len(df) == 5
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert df["Platform"].dtype == "object"  # String type
    assert df["Impressions"].dtype == "int64"
    assert df["Clicks"].dtype == "int64"
    assert df["Conversions"].dtype == "int64"
    assert df["Spend"].dtype == "float64"
    assert df["Revenue"].dtype == "float64"
    assert df["CPC"].dtype == "float64"
    assert df["CTR"].dtype == "float64"
    assert df["Conversion_Rate"].dtype == "float64"
    assert df["ROAS"].dtype == "float64"


def test_generate_campaign_data_platforms():
    """Test data generation for different platforms."""
    df_google = generate_campaign_data(platform="Google Ads", days=1)
    df_meta = generate_campaign_data(platform="Meta Ads", days=1)

    assert df_google["Platform"].iloc[0] == "Google Ads"
    assert df_meta["Platform"].iloc[0] == "Meta Ads"


def test_generate_campaign_data_date_range():
    """Test that dates are within the expected range."""
    start = "2024-03-15"
    days = 10
    df = generate_campaign_data(platform="Google Ads", start_date=start, days=days)

    assert df["Date"].min().strftime("%Y-%m-%d") == start
    assert df["Date"].max().strftime("%Y-%m-%d") == (
        datetime.strptime(start, "%Y-%m-%d") + timedelta(days=days - 1)
    ).strftime("%Y-%m-%d")


def test_generate_campaign_data_values_plausibility():
    """Test that generated values are within a plausible range."""
    df = generate_campaign_data(
        platform="Google Ads",
        days=10,
        base_impressions=10000,
        base_cpc=1.0,
        base_ctr=0.02,
        base_conversion_rate=0.05,
        conversion_value=10.0,
    )

    assert (df["Impressions"] >= 0).all()
    assert (df["Clicks"] >= 0).all()
    assert (df["Spend"] >= 0).all()
    assert (df["Conversions"] >= 0).all()
    assert (df["Revenue"] >= 0).all()
    assert (df["CPC"] > 0).all()  # CPC must be > 0
    assert (df["CTR"] >= 0).all()
    assert (df["Conversion_Rate"] >= 0).all()
    assert (df["ROAS"] >= 0).all()

    # Basic relationship checks
    assert (df["Clicks"] <= df["Impressions"]).all()
    assert (df["Conversions"] <= df["Clicks"]).all()
    # Spend = Clicks * CPC, allowing for some floating point
    assert np.allclose(df["Spend"], df["Clicks"] * df["CPC"], rtol=0.1)
    # Revenue = Conversions * Conversion_Value (approx)
    assert np.allclose(
        df["Revenue"], df["Conversions"] * 10.0, rtol=0.2
    )  # rtol higher due to noise


def test_generate_campaign_data_output_length():
    """Test that the number of rows matches the 'days' parameter."""
    df = generate_campaign_data(platform="Meta Ads", days=15)
    assert len(df) == 15

    df = generate_campaign_data(platform="Google Ads", days=1)
    assert len(df) == 1


def test_generate_campaign_data_no_negative_values():
    """Ensure no generated metric falls below zero."""
    for _ in range(10):  # Run multiple times due to randomness
        df = generate_campaign_data(
            platform="Google Ads",
            days=100,
            base_impressions=100,
            base_cpc=0.1,
            base_ctr=0.001,
            base_conversion_rate=0.001,
        )
        assert (df["Impressions"] >= 0).all()
        assert (df["Clicks"] >= 0).all()
        assert (df["Spend"] >= 0).all()
        assert (df["Conversions"] >= 0).all()
        assert (df["Revenue"] >= 0).all()
        assert (df["CPC"] > 0).all()
        assert (df["CTR"] >= 0).all()
        assert (df["Conversion_Rate"] >= 0).all()
        assert (df["ROAS"] >= 0).all()
