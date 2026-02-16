"""
WS-6 reporting helpers for API/dashboard surfaces.

Provides a stable payload that combines:
- bot metric event schema + snapshots
- performance tracker event schema + KPI deltas
- A/B experiment guardrail states
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker


async def build_ws6_observability_payload(
    *,
    window: str = "1h",
    include_recent_events: bool = False,
    event_limit: int = 20,
    baseline: Optional[Dict[str, Dict[str, float]]] = None,
) -> Dict[str, Any]:
    """
    Build a unified WS-6 observability payload for API and dashboard consumers.

    Args:
        window: Rolling window for performance deltas ("1h", "24h", "7d")
        include_recent_events: Include recent event samples from both collectors.
        event_limit: Max number of events per collector when include_recent_events=True.
        baseline: Optional baseline map for performance deltas.
    """
    collector = BotMetricsCollector()
    tracker = PerformanceTracker()
    ab_testing = ABTestingService()

    active_experiments = ab_testing.list_experiments()
    guardrail_states = []
    for experiment in active_experiments:
        experiment_id = experiment.get("experiment_id")
        if not experiment_id:
            continue
        try:
            guardrail_states.append(ab_testing.get_guardrail_status(experiment_id))
        except Exception:
            # Keep payload generation resilient even if one experiment cannot be read.
            continue

    payload: Dict[str, Any] = {
        "available": True,
        "version": "ws6.v1",
        "window": window,
        "generated_at": datetime.utcnow().isoformat(),
        "dashboard": {
            "definitions": collector.get_dashboard_definitions(),
            "snapshot": collector.get_dashboard_kpi_snapshot(),
        },
        "event_schemas": {
            "bot_metrics": collector.get_required_event_schema(),
            "performance": tracker.get_required_event_schema(),
        },
        "performance_deltas": await tracker.get_kpi_deltas_vs_baseline(
            baseline=baseline or {},
            window=window,
        ),
        "experiments": {
            "active": active_experiments,
            "guardrails": guardrail_states,
        },
    }

    if include_recent_events:
        payload["recent_events"] = {
            "bot_metrics": collector.get_recent_events(limit=event_limit),
            "performance": tracker.get_recent_events(limit=event_limit),
        }

    return payload
