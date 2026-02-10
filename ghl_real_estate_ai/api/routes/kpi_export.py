"""
KPI Export API
Provides KPI snapshots with provenance for enterprise proof packs.
"""

from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

from ghl_real_estate_ai.services.performance_monitoring_service import performance_monitor

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/kpi-export")
async def export_kpi_snapshot() -> Dict[str, Any]:
    snapshot = performance_monitor.get_kpi_snapshot()
    demo_mode = any(
        isinstance(value, dict) and value.get("tags", {}).get("source") == "synthetic"
        for value in snapshot.values()
    )

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "data_provenance": {
            "source": "telemetry_snapshot",
            "timestamp": datetime.utcnow().isoformat(),
            "demo_mode": demo_mode,
            "note": "Snapshot captured from KPI telemetry"
        },
        "kpis": snapshot
    }
