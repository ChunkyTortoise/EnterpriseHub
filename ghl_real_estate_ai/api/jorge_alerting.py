"""
Jorge Bot Alerting API

FastAPI router exposing the AlertingService for alert management,
acknowledgment, and rule configuration. Used by the Streamlit alert
center and any external monitoring integrations.

Endpoints:
    GET  /jorge/alerts                       - List alerts (active or all)
    POST /jorge/alerts/{alert_id}/acknowledge - Acknowledge an alert
    GET  /jorge/alerts/{alert_id}/status      - Get alert ack status
    GET  /jorge/alert-rules                   - List all alert rules
    PATCH /jorge/alert-rules/{rule_name}      - Enable/disable a rule
"""

import logging
from typing import Any, Dict, List, Optional, TypedDict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jorge", tags=["jorge-alerting"])


# ── TypedDict Definitions ─────────────────────────────────────────────────


class AlertDict(TypedDict):
    """Type definition for serialized alert data."""

    id: str
    rule_name: str
    severity: str
    message: str
    triggered_at: float
    acknowledged: bool
    acknowledged_at: Optional[float]
    acknowledged_by: Optional[str]
    channels_sent: List[str]


class AlertRuleDict(TypedDict):
    """Type definition for serialized alert rule data."""

    name: str
    severity: str
    cooldown_seconds: int
    channels: List[str]
    description: str
    active: bool


# ── Request / Response Models ────────────────────────────────────────


class AcknowledgeRequest(BaseModel):
    """Request body for acknowledging an alert."""

    acknowledged_by: Optional[str] = None


class RuleUpdateRequest(BaseModel):
    """Request body for enabling/disabling an alert rule."""

    active: bool


class AlertResponse(BaseModel):
    """Serialized representation of a triggered alert."""

    id: str
    rule_name: str
    severity: str
    message: str
    triggered_at: float
    acknowledged: bool
    acknowledged_at: Optional[float] = None
    acknowledged_by: Optional[str] = None
    channels_sent: List[str] = Field(default_factory=list)


class AlertRuleResponse(BaseModel):
    """Serialized representation of an alert rule."""

    name: str
    severity: str
    cooldown_seconds: int
    channels: List[str]
    description: str
    active: bool


# ── Helpers ───────────────────────────────────────────────────────────


def _alert_to_dict(alert) -> AlertDict:
    """Convert an Alert dataclass to a serializable dict."""
    return AlertDict(
        id=alert.id,
        rule_name=alert.rule_name,
        severity=alert.severity,
        message=alert.message,
        triggered_at=alert.triggered_at,
        acknowledged=alert.acknowledged,
        acknowledged_at=alert.acknowledged_at,
        acknowledged_by=alert.acknowledged_by,
        channels_sent=alert.channels_sent,
    )


def _rule_to_dict(rule, active: bool) -> AlertRuleDict:
    """Convert an AlertRule dataclass to a serializable dict."""
    return AlertRuleDict(
        name=rule.name,
        severity=rule.severity,
        cooldown_seconds=rule.cooldown_seconds,
        channels=rule.channels,
        description=rule.description,
        active=active,
    )


# ── Endpoints ─────────────────────────────────────────────────────────


@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(active_only: bool = False, limit: int = 50):
    """List alerts with optional filtering.

    Args:
        active_only: If True, only return unacknowledged alerts.
        limit: Maximum number of alerts to return (default 50).

    Returns:
        List of alert dicts, most recent first.
    """
    service = AlertingService()
    if active_only:
        alerts = await service.get_active_alerts()
    else:
        alerts = await service.get_alert_history(limit=limit)
    return [_alert_to_dict(a) for a in alerts]


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, body: AcknowledgeRequest):
    """Acknowledge an alert by its ID.

    Args:
        alert_id: The short hex ID of the alert.
        body: Optional acknowledged_by identifier.

    Returns:
        Acknowledgment result with timing details.

    Raises:
        HTTPException 404: If the alert ID is not found.
    """
    service = AlertingService()
    try:
        result = await service.acknowledge_alert(
            alert_id=alert_id,
            acknowledged_by=body.acknowledged_by,
        )
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")


@router.get("/alerts/{alert_id}/status")
async def get_alert_status(alert_id: str):
    """Get the acknowledgment status of a specific alert.

    Args:
        alert_id: The short hex ID of the alert.

    Returns:
        Status dict with acknowledgment details.

    Raises:
        HTTPException 404: If the alert ID is not found.
    """
    service = AlertingService()
    try:
        result = await service.get_acknowledgment_status(alert_id)
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")


@router.get("/alert-rules", response_model=List[AlertRuleResponse])
async def list_alert_rules():
    """List all registered alert rules with their active status.

    Returns:
        List of alert rule dicts including name, severity, channels, and active flag.
    """
    service = AlertingService()
    rules = await service.list_rules()
    return [_rule_to_dict(r, service.is_rule_active(r.name)) for r in rules]


@router.patch("/alert-rules/{rule_name}")
async def update_alert_rule(rule_name: str, body: RuleUpdateRequest):
    """Enable or disable an alert rule.

    Args:
        rule_name: The rule name to update.
        body: Contains ``active`` boolean.

    Returns:
        Updated rule info dict.

    Raises:
        HTTPException 404: If the rule name is not found.
    """
    service = AlertingService()
    try:
        if body.active:
            await service.enable_rule(rule_name)
        else:
            await service.disable_rule(rule_name)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Alert rule '{rule_name}' not found",
        )

    # Return updated rule info
    rules = await service.list_rules()
    for rule in rules:
        if rule.name == rule_name:
            return _rule_to_dict(rule, service.is_rule_active(rule.name))

    # Should not reach here if enable/disable succeeded
    raise HTTPException(status_code=404, detail=f"Alert rule '{rule_name}' not found")
