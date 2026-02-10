"""Interactive data workspace for Smart Analyst."""
from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

try:
    from st_aggrid import AgGrid, GridOptionsBuilder
    AGGRID_AVAILABLE = True
except Exception:
    AgGrid = None
    GridOptionsBuilder = None
    AGGRID_AVAILABLE = False


def render_data_workspace(df: pd.DataFrame, title: str = "Data Workspace") -> pd.DataFrame:
    """Render an interactive data grid and return possibly edited data.

    Falls back to st.dataframe when st-aggrid is not available.
    """
    st.subheader(title)

    if df.empty:
        st.info("No data loaded yet.")
        return df

    if AGGRID_AVAILABLE:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination()
        gb.configure_default_column(editable=True, sortable=True, filter=True, resizable=True)
        grid_options = gb.build()
        grid_response = AgGrid(df, gridOptions=grid_options, height=400, fit_columns_on_grid_load=True)
        if grid_response and "data" in grid_response:
            return pd.DataFrame(grid_response["data"])

    st.dataframe(df, use_container_width=True)
    return df
