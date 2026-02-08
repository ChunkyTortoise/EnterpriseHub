"""
Plotly Optimizer for EnterpriseHub
Provides centralized styling, decimation, and caching for Plotly visualizations.
Targeting 3-5x performance improvement for 463+ identified visualizations.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart


class PlotlyOptimizer:
    """
    Utility to optimize and style Plotly charts with a persistent caching layer.
    """

    @staticmethod
    def generate_chart_key(data: Union[pd.DataFrame, Dict, List], params: Dict) -> str:
        """Generates a stable hash key for caching."""
        if isinstance(data, pd.DataFrame):
            # Use shape and a sample of data for faster hashing
            data_summary = f"{data.shape}-{data.iloc[0:5].to_json()}-{data.iloc[-5:].to_json()}"
        else:
            data_summary = str(data)

        param_summary = json.dumps(params, sort_keys=True)
        combined = f"{data_summary}-{param_summary}"
        return hashlib.md5(combined.encode()).hexdigest()

    @staticmethod
    def decimate_data(df: pd.DataFrame, max_points: int = 1000) -> pd.DataFrame:
        """Reduces the number of points in a dataframe for faster rendering."""
        if len(df) <= max_points:
            return df

        # Simple sampling for decimation
        step = len(df) // max_points
        return df.iloc[::step].copy()

    @staticmethod
    def render_chart(
        fig_func,
        data: Any,
        params: Optional[Dict] = None,
        use_container_width: bool = True,
        key: Optional[str] = None,
        max_points: int = 1000,
    ):
        """
        Renders an optimized and styled chart.

        Args:
            fig_func: Function that takes data and params and returns a Plotly figure
            data: The raw data for the chart
            params: Additional parameters for fig_func
            use_container_width: Streamlit container width flag
            key: Optional override for cache key
            max_points: Maximum points to render before decimation
        """
        params = params or {}

        # 1. Decimate data if it's a DataFrame
        if isinstance(data, pd.DataFrame):
            data = PlotlyOptimizer.decimate_data(data, max_points)

        # 2. Caching layer
        cache_key = key or PlotlyOptimizer.generate_chart_key(data, params)

        if f"chart_{cache_key}" in st.session_state:
            fig = st.session_state[f"chart_{cache_key}"]
        else:
            with st.spinner("🎨 Optimizing visualization..."):
                fig = fig_func(data, **params)
                fig = style_obsidian_chart(fig)
                st.session_state[f"chart_{cache_key}"] = fig

        return st.plotly_chart(fig, use_container_width=use_container_width, key=f"display_{cache_key}")

    @staticmethod
    def create_metric_gauge(value: float, title: str, min_val: float = 0, max_val: float = 100, color: str = "#6366F1"):
        """Optimized gauge chart creator."""
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=value,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": title, "font": {"size": 14, "color": "#8B949E", "family": "Space Grotesk"}},
                gauge={
                    "axis": {"range": [min_val, max_val], "tickwidth": 1, "tickcolor": "#8B949E"},
                    "bar": {"color": color},
                    "bgcolor": "rgba(255,255,255,0.05)",
                    "borderwidth": 1,
                    "bordercolor": "rgba(255,255,255,0.1)",
                    "steps": [
                        {"range": [min_val, (max_val - min_val) * 0.5], "color": "rgba(239, 68, 68, 0.05)"},
                        {"range": [(max_val - min_val) * 0.5, max_val], "color": "rgba(16, 185, 129, 0.05)"},
                    ],
                },
            )
        )
        return style_obsidian_chart(fig)


# Global Instance
plotly_optimizer = PlotlyOptimizer()
