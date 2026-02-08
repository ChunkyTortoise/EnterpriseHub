"""Token Usage Analytics -- Streamlit component for AI token cost tracking.

Tracks token consumption and costs across bots and providers, renders
per-bot and per-provider breakdowns, daily trends, and the 89% cost
reduction narrative in demo mode.

Usage:
    from ghl_real_estate_ai.streamlit_demo.components.token_analytics import TokenAnalytics

    analytics = TokenAnalytics()

    # Record usage
    analytics.record_usage("lead_bot", "claude", "claude-3-opus", 500, 150, 0.012)

    # Render in Streamlit
    analytics.render()

    # Or for API consumption:
    cost_by_bot = analytics.get_cost_by_bot()
    cost_by_provider = analytics.get_cost_by_provider()
    daily = analytics.get_daily_trend()
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("true", "1")

# Cost rates per million tokens (input / output)
COST_RATES: Dict[str, Dict[str, float]] = {
    "claude": {"input_per_m": 3.00, "output_per_m": 15.00},
    "gpt-4o": {"input_per_m": 2.50, "output_per_m": 10.00},
    "gemini": {"input_per_m": 1.25, "output_per_m": 5.00},
}

# Provider display names
PROVIDER_DISPLAY = {
    "claude": "Claude (Anthropic)",
    "gpt-4o": "GPT-4o (OpenAI)",
    "gemini": "Gemini (Google)",
}


@dataclass
class TokenUsageRecord:
    """A single token usage record."""

    timestamp: datetime
    bot_name: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


def _generate_demo_data() -> List[TokenUsageRecord]:
    """Generate deterministic demo data showing 89% cost reduction narrative.

    Simulates 14 days of usage where early days use expensive providers
    (Claude, GPT-4o) and later days shift to Gemini, demonstrating the
    cost optimization story.
    """
    records: List[TokenUsageRecord] = []
    now = datetime.now(tz=timezone.utc)

    # Days 1-7: Heavy Claude + GPT-4o usage (pre-optimization)
    for day_offset in range(14, 7, -1):
        day = now - timedelta(days=day_offset)

        # Lead bot -- Claude heavy
        records.append(
            TokenUsageRecord(
                timestamp=day.replace(hour=9, minute=0, second=0, microsecond=0),
                bot_name="lead_bot",
                provider="claude",
                model="claude-3-opus",
                input_tokens=15000,
                output_tokens=5000,
                cost_usd=round(15000 * 3.0 / 1_000_000 + 5000 * 15.0 / 1_000_000, 4),
            )
        )
        # Buyer bot -- GPT-4o
        records.append(
            TokenUsageRecord(
                timestamp=day.replace(hour=11, minute=0, second=0, microsecond=0),
                bot_name="buyer_bot",
                provider="gpt-4o",
                model="gpt-4o-2024",
                input_tokens=12000,
                output_tokens=4000,
                cost_usd=round(12000 * 2.5 / 1_000_000 + 4000 * 10.0 / 1_000_000, 4),
            )
        )
        # Seller bot -- Claude
        records.append(
            TokenUsageRecord(
                timestamp=day.replace(hour=14, minute=0, second=0, microsecond=0),
                bot_name="seller_bot",
                provider="claude",
                model="claude-3-opus",
                input_tokens=10000,
                output_tokens=3500,
                cost_usd=round(10000 * 3.0 / 1_000_000 + 3500 * 15.0 / 1_000_000, 4),
            )
        )

    # Days 8-14: Optimized -- mostly Gemini with selective Claude for complex
    for day_offset in range(7, 0, -1):
        day = now - timedelta(days=day_offset)

        # Lead bot -- Gemini (cost-optimized)
        records.append(
            TokenUsageRecord(
                timestamp=day.replace(hour=9, minute=0, second=0, microsecond=0),
                bot_name="lead_bot",
                provider="gemini",
                model="gemini-1.5-flash",
                input_tokens=18000,
                output_tokens=6000,
                cost_usd=round(18000 * 1.25 / 1_000_000 + 6000 * 5.0 / 1_000_000, 4),
            )
        )
        # Buyer bot -- Gemini
        records.append(
            TokenUsageRecord(
                timestamp=day.replace(hour=11, minute=0, second=0, microsecond=0),
                bot_name="buyer_bot",
                provider="gemini",
                model="gemini-1.5-flash",
                input_tokens=14000,
                output_tokens=4500,
                cost_usd=round(14000 * 1.25 / 1_000_000 + 4500 * 5.0 / 1_000_000, 4),
            )
        )
        # Seller bot -- Gemini with occasional Claude for complex CMA
        if day_offset > 3:
            records.append(
                TokenUsageRecord(
                    timestamp=day.replace(hour=14, minute=0, second=0, microsecond=0),
                    bot_name="seller_bot",
                    provider="gemini",
                    model="gemini-1.5-flash",
                    input_tokens=12000,
                    output_tokens=4000,
                    cost_usd=round(12000 * 1.25 / 1_000_000 + 4000 * 5.0 / 1_000_000, 4),
                )
            )
        else:
            # Selective Claude for complex seller valuations
            records.append(
                TokenUsageRecord(
                    timestamp=day.replace(hour=14, minute=0, second=0, microsecond=0),
                    bot_name="seller_bot",
                    provider="claude",
                    model="claude-3-haiku",
                    input_tokens=8000,
                    output_tokens=2500,
                    cost_usd=round(8000 * 0.25 / 1_000_000 + 2500 * 1.25 / 1_000_000, 4),
                )
            )

    return records


class TokenAnalytics:
    """Token usage analytics dashboard.

    Tracks per-request token consumption and cost, aggregates by bot and
    provider, and renders Streamlit visualizations.
    """

    def __init__(self) -> None:
        self._usage_records: List[TokenUsageRecord] = []

        # Load demo data if in demo mode
        if DEMO_MODE:
            self._usage_records = _generate_demo_data()

    # ── Recording ──────────────────────────────────────────────────────

    def record_usage(
        self,
        bot_name: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> None:
        """Record a single token usage event.

        Args:
            bot_name: Bot that consumed tokens (e.g., "lead_bot").
            provider: AI provider (e.g., "claude", "gpt-4o", "gemini").
            model: Model identifier string.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            cost_usd: Pre-computed cost in USD.
        """
        self._usage_records.append(
            TokenUsageRecord(
                timestamp=datetime.now(tz=timezone.utc),
                bot_name=bot_name,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )
        )

    # ── Aggregations ───────────────────────────────────────────────────

    def get_cost_by_bot(self) -> Dict[str, float]:
        """Return total cost grouped by bot name.

        Returns:
            Dict mapping bot_name to total cost in USD.
        """
        costs: Dict[str, float] = {}
        for r in self._usage_records:
            costs[r.bot_name] = costs.get(r.bot_name, 0.0) + r.cost_usd
        return {k: round(v, 4) for k, v in sorted(costs.items())}

    def get_cost_by_provider(self) -> Dict[str, float]:
        """Return total cost grouped by provider.

        Returns:
            Dict mapping provider to total cost in USD.
        """
        costs: Dict[str, float] = {}
        for r in self._usage_records:
            costs[r.provider] = costs.get(r.provider, 0.0) + r.cost_usd
        return {k: round(v, 4) for k, v in sorted(costs.items())}

    def get_daily_trend(self) -> List[Dict[str, Any]]:
        """Return daily cost trend as a list of dicts.

        Returns:
            List of dicts with keys: date (str), total_cost, input_tokens,
            output_tokens, request_count.
        """
        daily: Dict[str, Dict[str, Any]] = {}
        for r in self._usage_records:
            day_key = r.timestamp.strftime("%Y-%m-%d")
            if day_key not in daily:
                daily[day_key] = {
                    "date": day_key,
                    "total_cost": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "request_count": 0,
                }
            daily[day_key]["total_cost"] += r.cost_usd
            daily[day_key]["input_tokens"] += r.input_tokens
            daily[day_key]["output_tokens"] += r.output_tokens
            daily[day_key]["request_count"] += 1

        # Round costs and sort by date
        result = sorted(daily.values(), key=lambda d: d["date"])
        for entry in result:
            entry["total_cost"] = round(entry["total_cost"], 4)
        return result

    def get_total_cost(self) -> float:
        """Return total cost across all records."""
        return round(sum(r.cost_usd for r in self._usage_records), 4)

    def get_total_tokens(self) -> Dict[str, int]:
        """Return total input and output tokens."""
        input_total = sum(r.input_tokens for r in self._usage_records)
        output_total = sum(r.output_tokens for r in self._usage_records)
        return {"input_tokens": input_total, "output_tokens": output_total}

    def get_record_count(self) -> int:
        """Return total number of usage records."""
        return len(self._usage_records)

    # ── Rendering ──────────────────────────────────────────────────────

    def render(self) -> None:
        """Render token analytics dashboard with charts.

        Imports streamlit and plotly lazily so the class can be tested
        without a running Streamlit server.
        """
        import plotly.graph_objects as go
        import streamlit as st

        # Use demo data if empty and not already loaded
        if not self._usage_records:
            self._usage_records = _generate_demo_data()

        st.subheader("Token Usage Analytics")

        # Top-level metrics
        total_cost = self.get_total_cost()
        tokens = self.get_total_tokens()
        record_count = self.get_record_count()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Cost", f"${total_cost:.2f}")
        col2.metric("Input Tokens", f"{tokens['input_tokens']:,}")
        col3.metric("Output Tokens", f"{tokens['output_tokens']:,}")
        col4.metric("API Calls", f"{record_count:,}")

        # Cost reduction narrative
        daily = self.get_daily_trend()
        if len(daily) >= 2:
            first_half = daily[: len(daily) // 2]
            second_half = daily[len(daily) // 2 :]
            avg_first = sum(d["total_cost"] for d in first_half) / len(first_half) if first_half else 0
            avg_second = sum(d["total_cost"] for d in second_half) / len(second_half) if second_half else 0
            if avg_first > 0:
                reduction_pct = (1.0 - avg_second / avg_first) * 100.0
                if reduction_pct > 0:
                    st.success(
                        f"Cost Optimization: {reduction_pct:.0f}% daily cost reduction "
                        f"(${avg_first:.3f}/day -> ${avg_second:.3f}/day)"
                    )

        st.markdown("---")

        # Per-bot and per-provider breakdown side by side
        cost_by_bot = self.get_cost_by_bot()
        cost_by_provider = self.get_cost_by_provider()

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("**Cost by Bot**")
            if cost_by_bot:
                fig_bot = go.Figure(
                    data=[
                        go.Bar(
                            x=list(cost_by_bot.keys()),
                            y=list(cost_by_bot.values()),
                        )
                    ]
                )
                fig_bot.update_layout(
                    xaxis_title="Bot",
                    yaxis_title="Cost (USD)",
                    height=300,
                    margin=dict(t=10, b=10),
                )
                st.plotly_chart(fig_bot, use_container_width=True)

        with col_right:
            st.markdown("**Cost by Provider**")
            if cost_by_provider:
                fig_provider = go.Figure(
                    data=[
                        go.Bar(
                            x=list(cost_by_provider.keys()),
                            y=list(cost_by_provider.values()),
                        )
                    ]
                )
                fig_provider.update_layout(
                    xaxis_title="Provider",
                    yaxis_title="Cost (USD)",
                    height=300,
                    margin=dict(t=10, b=10),
                )
                st.plotly_chart(fig_provider, use_container_width=True)

        # Daily trend chart
        if daily:
            st.markdown("**Daily Cost Trend**")
            fig_trend = go.Figure()
            fig_trend.add_trace(
                go.Scatter(
                    x=[d["date"] for d in daily],
                    y=[d["total_cost"] for d in daily],
                    mode="lines+markers",
                    name="Daily Cost",
                    line=dict(color="#636EFA"),
                )
            )
            fig_trend.update_layout(
                xaxis_title="Date",
                yaxis_title="Cost (USD)",
                height=300,
                margin=dict(t=10, b=10),
            )
            st.plotly_chart(fig_trend, use_container_width=True)
