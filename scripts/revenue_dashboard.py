"""
revenue_dashboard.py — Revenue Intelligence Dashboard

Streamlit app showing:
  - Monthly revenue by channel
  - YTD total
  - Transaction log
  - Weekly trend

Reads from ~/.claude/reference/freelance/revenue-tracker.md

Usage:
    streamlit run scripts/revenue_dashboard.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Revenue Intelligence Dashboard",
    page_icon="$",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Check dependencies
# ---------------------------------------------------------------------------

try:
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError as e:
    st.error(f"Missing dependency: {e}. Run: pip install pandas plotly")
    st.stop()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TRACKER_PATH = Path.home() / ".claude" / "reference" / "freelance" / "revenue-tracker.md"

CHANNELS = ["Upwork", "Fiverr", "Gumroad", "Stripe", "GitHub Sponsors", "Cold Outreach", "Other"]

CHANNEL_COLORS = {
    "Upwork": "#14a800",
    "Fiverr": "#1dbf73",
    "Gumroad": "#ff90e8",
    "Stripe": "#6772e5",
    "GitHub Sponsors": "#f778ba",
    "Cold Outreach": "#ff6b35",
    "Other": "#8b9dc3",
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def load_tracker(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_monthly_summary(content: str) -> pd.DataFrame:
    """Parse the Monthly Summary table from revenue-tracker.md."""
    # Find Monthly Summary section
    match = re.search(r"## Monthly Summary\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if not match:
        return pd.DataFrame()

    table_text = match.group(1).strip()
    rows = []
    for line in table_text.split("\n"):
        if not line.startswith("|") or "---" in line or "Month" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 7:
            continue
        try:
            month = cells[0].strip("*")
            row = {
                "Month": month,
                "Upwork": _parse_dollar(cells[1]),
                "Fiverr": _parse_dollar(cells[2]),
                "Gumroad": _parse_dollar(cells[3]),
                "GitHub Sponsors": _parse_dollar(cells[4]),
                "Cold Outreach": _parse_dollar(cells[5]),
                "Other": _parse_dollar(cells[6]),
            }
            # Calculate total
            row["Total"] = sum(row[c] for c in CHANNELS if c in row)
            rows.append(row)
        except (IndexError, ValueError):
            continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # Sort by month (attempt chronological)
    df["_sort_key"] = df["Month"].apply(_month_sort_key)
    df = df.sort_values("_sort_key").drop(columns=["_sort_key"]).reset_index(drop=True)
    return df


def parse_transaction_log(content: str) -> pd.DataFrame:
    """Parse the Transaction Log table from revenue-tracker.md."""
    match = re.search(r"## Transaction Log\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if not match:
        return pd.DataFrame()

    table_text = match.group(1).strip()
    rows = []
    for line in table_text.split("\n"):
        if not line.startswith("|") or "---" in line or "Date" in line or "No transactions" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 6:
            continue
        try:
            # Handle both old format (no ID column) and new format (with ID)
            if len(cells) >= 7 and cells[0].startswith(("stripe_", "gumroad_", "upwork_", "manual_")):
                row = {
                    "ID": cells[0],
                    "Date": cells[1],
                    "Channel": cells[2],
                    "Client": cells[3],
                    "Description": cells[4],
                    "Amount": _parse_dollar(cells[5]),
                    "Status": cells[6] if len(cells) > 6 else "completed",
                }
            else:
                row = {
                    "ID": "manual_" + cells[0],
                    "Date": cells[0],
                    "Channel": cells[1],
                    "Client": cells[2],
                    "Description": cells[3],
                    "Amount": _parse_dollar(cells[4]),
                    "Status": cells[5] if len(cells) > 5 else "completed",
                }
            rows.append(row)
        except (IndexError, ValueError):
            continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df


def parse_ytd_total(content: str) -> float:
    match = re.search(r"## YTD Total: \$([0-9,]+(?:\.[0-9]{2})?)", content)
    if not match:
        return 0.0
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return 0.0


def parse_last_updated(content: str) -> str:
    match = re.search(r"\*\*Last Updated\*\*:\s*(.+)", content)
    if match:
        return match.group(1).strip()
    return "Unknown"


def _parse_dollar(s: str) -> float:
    s = s.strip().replace("$", "").replace(",", "").replace("**", "")
    if not s or s == "0":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _month_sort_key(month_str: str) -> int:
    """Convert 'Feb 2026' to sortable int like 202602."""
    try:
        dt = datetime.strptime(month_str.strip(), "%b %Y")
        return dt.year * 100 + dt.month
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Weekly trend calculation
# ---------------------------------------------------------------------------

def build_weekly_trend(tx_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate transactions into weekly buckets for trend chart."""
    if tx_df.empty:
        return pd.DataFrame(columns=["Week", "Revenue"])

    df = tx_df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df["Week"] = df["Date"].dt.to_period("W").apply(lambda p: p.start_time)
    weekly = df.groupby("Week")["Amount"].sum().reset_index()
    weekly.columns = ["Week", "Revenue"]
    weekly = weekly.sort_values("Week")
    return weekly


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

def render_header(ytd: float, last_updated: str) -> None:
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("Revenue Intelligence Dashboard")
        st.caption(f"Last updated: {last_updated}")
    with col2:
        st.metric("YTD Total", f"${ytd:,.2f}", delta=None)
    with col3:
        if st.button("Refresh Data", type="secondary"):
            st.cache_data.clear()
            st.rerun()


def render_monthly_chart(monthly_df: pd.DataFrame) -> None:
    st.subheader("Monthly Revenue by Channel")

    if monthly_df.empty:
        st.info("No monthly revenue data yet. Run `python scripts/revenue_auto_update.py` to populate.")
        return

    channel_cols = [c for c in CHANNELS if c in monthly_df.columns]
    fig = go.Figure()

    for channel in channel_cols:
        if monthly_df[channel].sum() == 0:
            continue
        fig.add_trace(
            go.Bar(
                name=channel,
                x=monthly_df["Month"],
                y=monthly_df[channel],
                marker_color=CHANNEL_COLORS.get(channel, "#8b9dc3"),
            )
        )

    fig.update_layout(
        barmode="stack",
        xaxis_title="Month",
        yaxis_title="Revenue (USD)",
        legend_title="Channel",
        height=400,
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(tickprefix="$", gridcolor="rgba(128,128,128,0.2)")

    st.plotly_chart(fig, use_container_width=True)


def render_channel_breakdown(monthly_df: pd.DataFrame) -> None:
    st.subheader("Channel Breakdown (All Time)")

    if monthly_df.empty:
        st.info("No data yet.")
        return

    channel_cols = [c for c in CHANNELS if c in monthly_df.columns]
    totals = {ch: monthly_df[ch].sum() for ch in channel_cols if monthly_df[ch].sum() > 0}

    if not totals:
        st.info("All channels at $0.")
        return

    fig = px.pie(
        values=list(totals.values()),
        names=list(totals.keys()),
        color=list(totals.keys()),
        color_discrete_map=CHANNEL_COLORS,
        hole=0.4,
    )
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")

    st.plotly_chart(fig, use_container_width=True)


def render_weekly_trend(tx_df: pd.DataFrame) -> None:
    st.subheader("Weekly Revenue Trend")

    if tx_df.empty:
        st.info("No transaction data yet.")
        return

    weekly = build_weekly_trend(tx_df)

    if weekly.empty:
        st.info("No transactions with parseable dates.")
        return

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=weekly["Week"],
            y=weekly["Revenue"],
            mode="lines+markers",
            name="Weekly Revenue",
            line=dict(color="#1dbf73", width=2),
            marker=dict(size=6),
            fill="tozeroy",
            fillcolor="rgba(29,191,115,0.1)",
        )
    )
    fig.update_layout(
        xaxis_title="Week",
        yaxis_title="Revenue (USD)",
        height=300,
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(tickprefix="$", gridcolor="rgba(128,128,128,0.2)")

    st.plotly_chart(fig, use_container_width=True)


def render_transaction_log(tx_df: pd.DataFrame) -> None:
    st.subheader("Transaction Log")

    if tx_df.empty:
        st.info("No transactions yet. Transactions will appear here after the first MCP sync.")
        return

    # Display options
    col1, col2 = st.columns([2, 1])
    with col1:
        channel_filter = st.multiselect(
            "Filter by channel",
            options=sorted(tx_df["Channel"].unique().tolist()),
            default=[],
            label_visibility="collapsed",
        )
    with col2:
        sort_order = st.selectbox(
            "Sort",
            ["Newest first", "Oldest first", "Highest amount"],
            label_visibility="collapsed",
        )

    display_df = tx_df.copy()
    if channel_filter:
        display_df = display_df[display_df["Channel"].isin(channel_filter)]

    if sort_order == "Newest first":
        display_df = display_df.sort_values("Date", ascending=False)
    elif sort_order == "Oldest first":
        display_df = display_df.sort_values("Date", ascending=True)
    elif sort_order == "Highest amount":
        display_df = display_df.sort_values("Amount", ascending=False)

    # Format for display
    display_cols = ["Date", "Channel", "Client", "Description", "Amount", "Status"]
    available_cols = [c for c in display_cols if c in display_df.columns]
    show_df = display_df[available_cols].copy()
    if "Amount" in show_df.columns:
        show_df["Amount"] = show_df["Amount"].apply(lambda x: f"${x:,.2f}")

    st.dataframe(
        show_df,
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"{len(display_df)} transactions displayed")


def render_revenue_targets(monthly_df: pd.DataFrame) -> None:
    """Show progress toward monthly revenue targets."""
    st.subheader("Monthly Targets")

    current_month = datetime.now().strftime("%b %Y")

    targets = {
        "Conservative": 4495,
        "Moderate": 10000,
        "Optimistic": 17000,
    }

    current_total = 0.0
    if not monthly_df.empty:
        month_row = monthly_df[monthly_df["Month"] == current_month]
        if not month_row.empty:
            current_total = float(month_row["Total"].iloc[0])

    cols = st.columns(len(targets))
    for col, (scenario, target) in zip(cols, targets.items()):
        with col:
            progress = min(current_total / target, 1.0) if target > 0 else 0.0
            st.metric(
                label=scenario,
                value=f"${current_total:,.0f} / ${target:,}",
                delta=f"{progress:.0%} of goal",
                delta_color="normal",
            )


def render_no_data_state() -> None:
    st.warning(f"Revenue tracker not found at: `{TRACKER_PATH}`")
    st.markdown("""
**To get started:**

1. Ensure the file exists:
   ```
   ~/.claude/reference/freelance/revenue-tracker.md
   ```

2. Run the auto-update script to pull from MCP sources:
   ```bash
   python scripts/revenue_auto_update.py
   ```

3. Or create the file manually with this structure:
   ```markdown
   # Revenue Tracker
   **Last Updated**: 2026-02-19
   ## YTD Total: $0
   ## Monthly Summary
   | Month | Upwork | Fiverr | Gumroad | GitHub Sponsors | Cold Outreach | Other | Total |
   |-------|--------|--------|---------|-----------------|---------------|-------|-------|
   | Feb 2026 | $0 | $0 | $0 | $0 | $0 | $0 | **$0** |
   ## Transaction Log
   | Date | Channel | Client | Description | Amount | Status |
   |------|---------|--------|-------------|--------|--------|
   | _No transactions yet_ | — | — | — | — | — |
   ```
""")


def render_run_update_button() -> None:
    """Sidebar button to trigger revenue_auto_update.py."""
    with st.sidebar:
        st.header("Data Sources")
        st.markdown("Pull latest data from MCP sources:")
        if st.button("Run Auto-Update", type="primary"):
            with st.spinner("Running revenue_auto_update.py..."):
                result = subprocess.run(
                    [sys.executable, "scripts/revenue_auto_update.py"],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent,
                )
            if result.returncode == 0:
                st.success("Update complete!")
                st.text(result.stdout[-500:] if result.stdout else "No output")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Update failed")
                st.text(result.stderr[-500:] if result.stderr else "No error output")

        st.divider()
        st.markdown("**Tracker file:**")
        st.code(str(TRACKER_PATH), language=None)
        st.markdown("**Run update manually:**")
        st.code("python scripts/revenue_auto_update.py", language="bash")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    render_run_update_button()

    content = load_tracker(TRACKER_PATH)
    if not content:
        render_no_data_state()
        return

    ytd = parse_ytd_total(content)
    last_updated = parse_last_updated(content)
    monthly_df = parse_monthly_summary(content)
    tx_df = parse_transaction_log(content)

    render_header(ytd, last_updated)

    st.divider()

    # Row 1: Monthly chart + channel breakdown
    col1, col2 = st.columns([3, 1])
    with col1:
        render_monthly_chart(monthly_df)
    with col2:
        render_channel_breakdown(monthly_df)

    st.divider()

    # Row 2: Weekly trend + targets
    col1, col2 = st.columns([2, 1])
    with col1:
        render_weekly_trend(tx_df)
    with col2:
        render_revenue_targets(monthly_df)

    st.divider()

    # Row 3: Full transaction log
    render_transaction_log(tx_df)


if __name__ == "__main__":
    main()
