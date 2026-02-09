"""
Tests for PlotlyOptimizer utility.
"""

import pandas as pd
import plotly.graph_objects as go
import pytest

from ghl_real_estate_ai.streamlit_demo.plotly_optimizer import PlotlyOptimizer

@pytest.mark.unit


def test_decimate_data():
    """Test that data decimation works correctly."""
    optimizer = PlotlyOptimizer()
    df = pd.DataFrame({"x": range(2000), "y": range(2000)})

    decimated = optimizer.decimate_data(df, max_points=1000)

    assert len(decimated) <= 1000
    assert len(decimated) > 0


def test_generate_chart_key():
    """Test that chart key generation is stable."""
    optimizer = PlotlyOptimizer()
    data = {"val": 10}
    params = {"title": "test"}

    key1 = optimizer.generate_chart_key(data, params)
    key2 = optimizer.generate_chart_key(data, params)

    assert key1 == key2

    # Different data should produce different key
    key3 = optimizer.generate_chart_key({"val": 11}, params)
    assert key1 != key3


def test_create_metric_gauge():
    """Test that gauge creation returns a valid plotly figure."""
    optimizer = PlotlyOptimizer()
    fig = optimizer.create_metric_gauge(75, "Test Gauge")

    assert isinstance(fig, go.Figure)
    assert fig.data[0].type == "indicator"
    assert fig.data[0].mode == "gauge+number"