"""Cost governance service for LLM spend tracking and alerting.

Records per-request costs, aggregates by agent/model, and exposes
summary data for the admin cost dashboard.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Pricing per million tokens (USD)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-3-5-haiku-20251022": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
}

# From agent_mesh_coordinator.py
EMERGENCY_SHUTDOWN_THRESHOLD = 100.0  # USD per hour


@dataclass
class CostRecord:
    id: str
    request_id: str
    agent_name: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    prompt_version: str | None
    created_at: datetime


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate USD cost for a single LLM call."""
    pricing = MODEL_PRICING.get(model)
    if pricing is None:
        # Fall back to sonnet pricing for unknown models
        pricing = MODEL_PRICING["claude-sonnet-4-6"]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


_PERIOD_MAP = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


class CostTracker:
    """DB-backed LLM cost tracker."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def record(
        self,
        request_id: str,
        agent_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        prompt_version: str | None = None,
    ) -> CostRecord:
        """Calculate cost and store record."""
        cost_usd = calculate_cost(model, input_tokens, output_tokens)
        record_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        async with self._session_factory() as session:
            await session.execute(
                text(
                    "INSERT INTO cost_records "
                    "(id, request_id, agent_name, model, input_tokens, output_tokens, cost_usd, prompt_version, created_at) "
                    "VALUES (:id, :request_id, :agent_name, :model, :input_tokens, :output_tokens, :cost_usd, :prompt_version, :created_at)"
                ),
                {
                    "id": record_id,
                    "request_id": request_id,
                    "agent_name": agent_name,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": cost_usd,
                    "prompt_version": prompt_version,
                    "created_at": now,
                },
            )
            await session.commit()

        return CostRecord(
            id=record_id,
            request_id=request_id,
            agent_name=agent_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            prompt_version=prompt_version,
            created_at=now,
        )

    async def get_summary(self, period: str = "24h") -> dict[str, Any]:
        """Aggregate cost data for a time period.

        Returns: total_cost, by_agent, by_model, per_lead_avg,
                 cost_trend, emergency_status
        """
        delta = _PERIOD_MAP.get(period, timedelta(hours=24))
        cutoff = datetime.now(UTC) - delta

        async with self._session_factory() as session:
            # Total cost
            total_result = await session.execute(
                text("SELECT COALESCE(SUM(cost_usd), 0) AS total FROM cost_records WHERE created_at >= :cutoff"),
                {"cutoff": cutoff},
            )
            total_cost = float(total_result.scalar_one())

            # By agent
            agent_result = await session.execute(
                text(
                    "SELECT agent_name, SUM(cost_usd) AS cost, COUNT(*) AS requests "
                    "FROM cost_records WHERE created_at >= :cutoff "
                    "GROUP BY agent_name ORDER BY cost DESC"
                ),
                {"cutoff": cutoff},
            )
            by_agent = {row["agent_name"]: {"cost": float(row["cost"]), "requests": row["requests"]} for row in agent_result.mappings()}

            # By model
            model_result = await session.execute(
                text(
                    "SELECT model, SUM(cost_usd) AS cost, SUM(input_tokens) AS input_tok, SUM(output_tokens) AS output_tok "
                    "FROM cost_records WHERE created_at >= :cutoff "
                    "GROUP BY model ORDER BY cost DESC"
                ),
                {"cutoff": cutoff},
            )
            by_model = {
                row["model"]: {
                    "cost": float(row["cost"]),
                    "input_tokens": int(row["input_tok"]),
                    "output_tokens": int(row["output_tok"]),
                }
                for row in model_result.mappings()
            }

            # Per-lead average (unique request_ids as proxy for leads)
            lead_result = await session.execute(
                text(
                    "SELECT COUNT(DISTINCT request_id) AS leads FROM cost_records WHERE created_at >= :cutoff"
                ),
                {"cutoff": cutoff},
            )
            unique_leads = lead_result.scalar_one() or 0
            per_lead_avg = round(total_cost / unique_leads, 4) if unique_leads > 0 else 0.0

            # Cost trend: compare current period to previous period
            prev_cutoff = cutoff - delta
            prev_result = await session.execute(
                text(
                    "SELECT COALESCE(SUM(cost_usd), 0) AS total FROM cost_records "
                    "WHERE created_at >= :prev_cutoff AND created_at < :cutoff"
                ),
                {"prev_cutoff": prev_cutoff, "cutoff": cutoff},
            )
            prev_cost = float(prev_result.scalar_one())
            if prev_cost > 0:
                cost_trend = round((total_cost - prev_cost) / prev_cost * 100, 1)
            else:
                cost_trend = 0.0 if total_cost == 0 else 100.0

            # Emergency status: hourly rate check
            one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
            hourly_result = await session.execute(
                text(
                    "SELECT COALESCE(SUM(cost_usd), 0) AS hourly FROM cost_records WHERE created_at >= :cutoff"
                ),
                {"cutoff": one_hour_ago},
            )
            hourly_cost = float(hourly_result.scalar_one())
            emergency_status = "critical" if hourly_cost >= EMERGENCY_SHUTDOWN_THRESHOLD else "normal"

        return {
            "period": period,
            "total_cost": round(total_cost, 4),
            "by_agent": by_agent,
            "by_model": by_model,
            "per_lead_avg": per_lead_avg,
            "cost_trend_pct": cost_trend,
            "hourly_cost": round(hourly_cost, 4),
            "emergency_status": emergency_status,
        }
