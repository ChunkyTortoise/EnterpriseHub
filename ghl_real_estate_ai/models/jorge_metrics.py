"""Pydantic models for Jorge bot metrics persistence.

Maps to the database schema defined in:
    alembic/versions/2026_02_08_002_add_jorge_metrics_tables.py

Tables: jorge_bot_interactions, jorge_handoff_events,
        jorge_performance_operations, jorge_alert_rules, jorge_alerts.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JorgeBotInteractionDB(BaseModel):
    """Row from the jorge_bot_interactions table."""

    id: Optional[int] = None
    bot_type: str
    duration_ms: float
    success: bool
    cache_hit: bool = False
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class JorgeHandoffEventDB(BaseModel):
    """Row from the jorge_handoff_events table."""

    id: Optional[int] = None
    source_bot: str
    target_bot: str
    success: bool
    duration_ms: float
    timestamp: float
    created_at: Optional[datetime] = None


class JorgePerformanceOperationDB(BaseModel):
    """Row from the jorge_performance_operations table."""

    id: Optional[int] = None
    bot_name: str
    operation: str
    duration_ms: float
    success: bool = True
    cache_hit: bool = False
    metadata: Optional[Dict[str, Any]] = None
    timestamp: float
    created_at: Optional[datetime] = None


class JorgeAlertRuleDB(BaseModel):
    """Row from the jorge_alert_rules table."""

    id: Optional[int] = None
    name: str
    condition_config: Dict[str, Any] = Field(default_factory=dict)
    severity: str = "warning"
    cooldown_seconds: int = 300
    channels: List[str] = Field(default_factory=list)
    description: str = ""
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class JorgeAlertDB(BaseModel):
    """Row from the jorge_alerts table."""

    id: Optional[int] = None
    rule_name: str
    severity: str
    message: str
    triggered_at: float
    performance_stats: Optional[Dict[str, Any]] = None
    channels_sent: Optional[List[str]] = None
    acknowledged: bool = False
    acknowledged_at: Optional[float] = None
    acknowledged_by: Optional[str] = None
    created_at: Optional[datetime] = None


class JorgeMetricsSummary(BaseModel):
    """Aggregated metrics summary returned by the repository."""

    total_interactions: int = 0
    total_handoffs: int = 0
    total_performance_ops: int = 0
    total_alerts: int = 0
    unacknowledged_alerts: int = 0


class JorgeAlertAcknowledgment(BaseModel):
    """Result of acknowledging an alert."""

    alert_id: int
    acknowledged: bool = True
    acknowledged_at: Optional[float] = None
    acknowledged_by: Optional[str] = None
