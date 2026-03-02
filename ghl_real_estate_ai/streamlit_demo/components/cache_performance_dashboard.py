"""
Cache Performance Dashboard -- L1/L2/L3 tier hit-rate visualization.

Displays:
- st.metric() cards for hit rates per cache tier
- Stacked area chart of cache performance over time
- Summary table with latency and throughput stats

Uses realistic demo data consistent with README canonical metrics:
  L1 59.1% | L2 20.5% | L3 8.5% | Total 88.1%
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

import plotly.graph_objects as go
import streamlit as st


def _generate_demo_cache_data(
    days: int = 14, seed: int = 20260301
) -> Dict[str, Any]:
    """Generate deterministic demo cache metrics."""
    rng = random.Random(seed)

    # Canonical hit-rate targets (from README / METRICS_CANONICAL.md)
    l1_base = 59.1
    l2_base = 20.5
    l3_base = 8.5

    timestamps: List[datetime] = []
    l1_rates: List[float] = []
    l2_rates: List[float] = []
    l3_rates: List[float] = []
    miss_rates: List[float] = []
    request_counts: List[int] = []

    now = datetime.now()
    for i in range(days * 24):
        ts = now - timedelta(hours=(days * 24 - 1 - i))
        timestamps.append(ts)

        # Add realistic variance around canonical values
        l1 = max(0, min(100, l1_base + rng.gauss(0, 2.5)))
        l2 = max(0, min(100 - l1, l2_base + rng.gauss(0, 1.8)))
        l3 = max(0, min(100 - l1 - l2, l3_base + rng.gauss(0, 1.2)))
        miss = max(0, 100 - l1 - l2 - l3)

        l1_rates.append(round(l1, 2))
        l2_rates.append(round(l2, 2))
        l3_rates.append(round(l3, 2))
        miss_rates.append(round(miss, 2))

        # Request volume: higher during business hours
        hour = ts.hour
        base_reqs = 800 if 9 <= hour <= 17 else 200
        request_counts.append(int(base_reqs + rng.gauss(0, 80)))

    total_reqs = sum(request_counts)
    avg_l1 = sum(l1_rates) / len(l1_rates)
    avg_l2 = sum(l2_rates) / len(l2_rates)
    avg_l3 = sum(l3_rates) / len(l3_rates)
    avg_total = avg_l1 + avg_l2 + avg_l3

    return {
        "timestamps": timestamps,
        "l1_rates": l1_rates,
        "l2_rates": l2_rates,
        "l3_rates": l3_rates,
        "miss_rates": miss_rates,
        "request_counts": request_counts,
        "summary": {
            "total_requests": total_reqs,
            "l1_hit_rate": round(avg_l1, 1),
            "l2_hit_rate": round(avg_l2, 1),
            "l3_hit_rate": round(avg_l3, 1),
            "total_hit_rate": round(avg_total, 1),
            "l1_avg_latency_ms": 0.8,
            "l2_avg_latency_ms": 4.2,
            "l3_avg_latency_ms": 12.5,
            "miss_avg_latency_ms": 185.0,
            "l1_size_current": 8_742,
            "l1_size_max": 10_000,
            "l2_promotions": int(total_reqs * avg_l2 / 100 * 0.35),
            "l1_evictions": int(total_reqs * 0.04),
            "tokens_saved": int(total_reqs * avg_total / 100 * 12),
            "cost_saved_dollars": round(total_reqs * avg_total / 100 * 12 * 0.000003, 2),
        },
    }


def render_cache_performance_dashboard() -> None:
    """Render the L1/L2/L3 cache performance dashboard."""
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

    data = _generate_demo_cache_data()
    summary = data["summary"]

    # -- Tier Hit Rate Metrics --
    st.markdown("### Hit Rates by Cache Tier")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="L1 Memory (<1ms)",
            value=f"{summary['l1_hit_rate']}%",
            delta="+2.1% vs last week",
        )
    with col2:
        st.metric(
            label="L2 Redis (<5ms)",
            value=f"{summary['l2_hit_rate']}%",
            delta="+0.8% vs last week",
        )
    with col3:
        st.metric(
            label="L3 PostgreSQL (<15ms)",
            value=f"{summary['l3_hit_rate']}%",
            delta="+0.3% vs last week",
        )
    with col4:
        st.metric(
            label="Total Hit Rate",
            value=f"{summary['total_hit_rate']}%",
            delta="+3.2% vs last week",
        )

    st.markdown("---")

    # -- Stacked Area Chart: Cache Performance Over Time --
    st.markdown("### Cache Performance Over Time")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["timestamps"],
            y=data["l1_rates"],
            name="L1 Memory",
            stackgroup="cache",
            fillcolor="rgba(99, 102, 241, 0.6)",
            line=dict(color="#6366F1", width=0),
            hovertemplate="L1: %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["timestamps"],
            y=data["l2_rates"],
            name="L2 Redis",
            stackgroup="cache",
            fillcolor="rgba(16, 185, 129, 0.6)",
            line=dict(color="#10B981", width=0),
            hovertemplate="L2: %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["timestamps"],
            y=data["l3_rates"],
            name="L3 PostgreSQL",
            stackgroup="cache",
            fillcolor="rgba(245, 158, 11, 0.6)",
            line=dict(color="#F59E0B", width=0),
            hovertemplate="L3: %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["timestamps"],
            y=data["miss_rates"],
            name="Cache Miss",
            stackgroup="cache",
            fillcolor="rgba(239, 68, 68, 0.3)",
            line=dict(color="#EF4444", width=0),
            hovertemplate="Miss: %{y:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        yaxis=dict(
            title="Hit Rate (%)",
            range=[0, 100],
            dtick=20,
        ),
        xaxis=dict(title="Time"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        height=400,
        margin=dict(l=40, r=20, t=40, b=40),
    )

    st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

    # -- Request Volume Sparkline --
    st.markdown("### Request Volume")
    vol_fig = go.Figure()
    vol_fig.add_trace(
        go.Bar(
            x=data["timestamps"],
            y=data["request_counts"],
            marker_color="rgba(99, 102, 241, 0.5)",
            hovertemplate="Requests: %{y:,}<extra></extra>",
        )
    )
    vol_fig.update_layout(
        yaxis=dict(title="Requests / hour"),
        xaxis=dict(title="Time"),
        height=200,
        margin=dict(l=40, r=20, t=10, b=40),
        showlegend=False,
    )
    st.plotly_chart(style_obsidian_chart(vol_fig), use_container_width=True)

    st.markdown("---")

    # -- Summary Table --
    st.markdown("### Performance Summary")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**Latency by Tier**")
        st.table(
            {
                "Tier": ["L1 Memory", "L2 Redis", "L3 PostgreSQL", "Cache Miss"],
                "Avg Latency": [
                    f"{summary['l1_avg_latency_ms']} ms",
                    f"{summary['l2_avg_latency_ms']} ms",
                    f"{summary['l3_avg_latency_ms']} ms",
                    f"{summary['miss_avg_latency_ms']} ms",
                ],
                "Hit Rate": [
                    f"{summary['l1_hit_rate']}%",
                    f"{summary['l2_hit_rate']}%",
                    f"{summary['l3_hit_rate']}%",
                    f"{round(100 - summary['total_hit_rate'], 1)}%",
                ],
            }
        )

    with col_right:
        st.markdown("**Operational Stats**")
        st.table(
            {
                "Metric": [
                    "Total Requests (14d)",
                    "L1 Utilization",
                    "L2 -> L1 Promotions",
                    "L1 Evictions",
                    "Tokens Saved",
                    "Cost Savings (est.)",
                ],
                "Value": [
                    f"{summary['total_requests']:,}",
                    f"{summary['l1_size_current']:,} / {summary['l1_size_max']:,}",
                    f"{summary['l2_promotions']:,}",
                    f"{summary['l1_evictions']:,}",
                    f"{summary['tokens_saved']:,}",
                    f"${summary['cost_saved_dollars']:,.2f}",
                ],
            }
        )
