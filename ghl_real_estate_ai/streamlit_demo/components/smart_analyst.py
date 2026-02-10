"""Smart Analyst Streamlit component."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
from ghl_real_estate_ai.services.smart_analyst.code_executor import SelfHealingExecutor
from ghl_real_estate_ai.services.smart_analyst.data_workspace import render_data_workspace
from ghl_real_estate_ai.services.smart_analyst.nl2sql import NL2SQLGenerator
from ghl_real_estate_ai.services.smart_analyst.report_generator import ReportGenerator


def _load_sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "lead": ["Alex Rivera", "Jamie Lee", "Morgan Patel", "Riley Chen"],
            "stage": ["New", "Contacted", "Qualified", "Negotiation"],
            "deal_value": [1200000, 845000, 1500000, 975000],
            "response_time_min": [12, 28, 8, 15],
        }
    )


def render_smart_analyst() -> None:
    st.header("📊 Smart Analyst")
    st.caption("Self-healing analysis workspace with NL2SQL, interactive grid, and PDF reporting.")

    if "smart_analyst_df" not in st.session_state:
        st.session_state.smart_analyst_df = _load_sample_data()

    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None:
        st.session_state.smart_analyst_df = pd.read_csv(uploaded)

    df = st.session_state.smart_analyst_df
    df = render_data_workspace(df, title="Interactive Data Grid")
    st.session_state.smart_analyst_df = df

    st.markdown("---")
    st.subheader("Ask Your Data (NL2SQL)")
    question = st.text_input("Ask a question", placeholder="e.g., What is the average deal value by stage?")
    if st.button("Generate SQL", key="smart_analyst_generate_sql"):
        generator = NL2SQLGenerator()
        try:
            sql = run_async(generator.generate_sql(question)) if question else ""
            st.code(sql, language="sql")
        except Exception as exc:
            st.error(f"Failed to generate SQL: {exc}")

    st.markdown("---")
    st.subheader("Self-Healing Code Runner")
    code = st.text_area(
        "Run Python against your dataset (use df variable)",
        value="print(df.head())",
        height=160,
    )
    if st.button("Execute Code", key="smart_analyst_execute_code"):
        executor = SelfHealingExecutor()
        result = run_async(executor.execute(code, globals_dict={"df": df, "pd": pd}))
        if result.success:
            st.success(f"Execution succeeded in {result.attempts} attempt(s)")
            if result.output:
                st.code(result.output)
        else:
            st.error(f"Execution failed after {result.attempts} attempts: {result.error}")

    st.markdown("---")
    st.subheader("Generate PDF Report")
    summary = st.text_area("Executive Summary", value="Key trends indicate strong momentum in qualified leads.")
    trends_input = st.text_area(
        "Key Trends (one per line)",
        value="High-value deals cluster in qualified stage\nAverage response time under 20 minutes",
    )
    if st.button("Create Report", key="smart_analyst_report"):
        trends = [line.strip() for line in trends_input.splitlines() if line.strip()]
        output_dir = Path(os.getenv("SMART_ANALYST_REPORT_DIR", "/tmp"))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "smart_analyst_report.pdf"
        generator = ReportGenerator()
        generator.generate_report(
            output_path=str(output_path),
            title="Smart Analyst Report",
            summary=summary,
            trends=trends,
        )
        with open(output_path, "rb") as handle:
            st.download_button(
                "Download Report",
                data=handle,
                file_name=output_path.name,
                mime="application/pdf",
            )
