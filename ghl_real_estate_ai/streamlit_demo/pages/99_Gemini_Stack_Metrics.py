import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Gemini Stack Metrics", layout="wide")

st.title("📊 Gemini Stack Metrics & Observability")
st.markdown("Monitor LLM usage, costs, and response quality across the platform.")

METRICS_FILE = "gemini_metrics.csv"


def load_data():
    if not os.path.exists(METRICS_FILE):
        return None
    try:
        df = pd.read_csv(METRICS_FILE)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        # Handle 'N/A' in accuracy_score
        df["accuracy_score"] = pd.to_numeric(df["accuracy_score"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Error loading metrics: {e}")
        return None


df = load_data()

if df is None or df.empty:
    st.info("No metrics data available yet. Start using the AI features to generate logs.")
else:
    # --- Top Level Metrics ---
    total_cost = df["cost_usd"].sum()
    total_tokens = df["total_tokens"].sum()
    avg_accuracy = df["accuracy_score"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cost", f"${total_cost:.4f}")
    col2.metric("Total Tokens", f"{total_tokens:,}")
    col3.metric("Avg Accuracy", f"{avg_accuracy:.2%}" if not pd.isna(avg_accuracy) else "N/A")
    col4.metric("Total Calls", len(df))

    # --- Charts ---
    st.divider()

    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("Cost by Task Type")
        cost_by_task = df.groupby("task_type")["cost_usd"].sum().reset_index()
        fig_cost = px.pie(
            cost_by_task,
            values="cost_usd",
            names="task_type",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Emerald,
        )
        st.plotly_chart(fig_cost, use_container_width=True)

    with row1_col2:
        st.subheader("Calls by Model")
        calls_by_model = df["model"].value_counts().reset_index()
        calls_by_model.columns = ["model", "count"]
        fig_models = px.bar(calls_by_model, x="model", y="count", color="count", color_continuous_scale="Viridis")
        st.plotly_chart(fig_models, use_container_width=True)

    st.divider()

    st.subheader("Daily Usage & Cost")
    df["date"] = df["timestamp"].dt.date
    daily_metrics = (
        df.groupby("date").agg({"cost_usd": "sum", "total_tokens": "sum", "accuracy_score": "mean"}).reset_index()
    )

    fig_daily = px.line(
        daily_metrics, x="date", y="cost_usd", markers=True, title="Daily Spend (USD)", labels={"cost_usd": "Cost ($)"}
    )
    fig_daily.update_traces(line_color="#10B981")
    st.plotly_chart(fig_daily, use_container_width=True)

    # --- Data Table ---
    st.divider()
    st.subheader("Recent Activity Log")
    st.dataframe(df.sort_values("timestamp", ascending=False).head(100), use_container_width=True)

    # --- Recommendations ---
    st.sidebar.header("Optimization Tips")

    if total_cost > 10:
        st.sidebar.warning("Daily cost is climbing. Consider enabling Context Caching for your most frequent tasks.")

    flash_usage = len(df[df["model"].str.contains("flash", case=False)])
    pro_usage = len(df[df["model"].str.contains("pro", case=False)])

    if pro_usage > flash_usage:
        st.sidebar.info(
            "High Pro model usage detected. Can any of these tasks be handled by Flash with a better prompt?"
        )

    if df["accuracy_score"].min() < 0.7:
        st.sidebar.error("Low accuracy detected in some calls. Check the activity log to identify failing prompts.")
