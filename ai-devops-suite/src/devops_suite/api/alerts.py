"""Alert rules CRUD API."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


class AlertRuleIn(BaseModel):
    name: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "anomaly"
    threshold: float | None = None
    cooldown_seconds: int = 300
    notification_channels: list[str] = Field(default_factory=lambda: ["webhook"])


class AlertRuleOut(AlertRuleIn):
    id: UUID = Field(default_factory=uuid4)
    is_active: bool = True


class AlertHistoryOut(BaseModel):
    rule_id: UUID
    metric_name: str
    metric_value: float
    severity: str
    message: str
    triggered_at: str


_rules: dict[UUID, AlertRuleOut] = {}


@router.post("", response_model=AlertRuleOut)
async def create_alert_rule(rule: AlertRuleIn) -> AlertRuleOut:
    out = AlertRuleOut(**rule.model_dump())
    _rules[out.id] = out
    return out


@router.get("", response_model=list[AlertRuleOut])
async def list_alert_rules() -> list[AlertRuleOut]:
    return list(_rules.values())


@router.get("/active", response_model=list[AlertRuleOut])
async def list_active_alerts() -> list[AlertRuleOut]:
    return [r for r in _rules.values() if r.is_active]


@router.get("/{rule_id}", response_model=AlertRuleOut)
async def get_alert_rule(rule_id: UUID) -> AlertRuleOut:
    if rule_id not in _rules:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return _rules[rule_id]


@router.delete("/{rule_id}")
async def delete_alert_rule(rule_id: UUID) -> dict:
    if rule_id not in _rules:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    del _rules[rule_id]
    return {"deleted": True}
