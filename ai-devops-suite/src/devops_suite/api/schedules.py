"""Cron schedule management API."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/schedules", tags=["schedules"])


class ScheduleCreate(BaseModel):
    job_id: UUID
    cron_expression: str
    is_active: bool = True


class ScheduleOut(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    cron_expression: str
    is_active: bool = True


_schedules: dict[UUID, ScheduleOut] = {}


@router.post("", response_model=ScheduleOut)
async def create_schedule(schedule: ScheduleCreate) -> ScheduleOut:
    out = ScheduleOut(job_id=schedule.job_id, cron_expression=schedule.cron_expression,
                      is_active=schedule.is_active)
    _schedules[out.id] = out
    return out


@router.get("", response_model=list[ScheduleOut])
async def list_schedules() -> list[ScheduleOut]:
    return list(_schedules.values())


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: UUID) -> dict:
    if schedule_id not in _schedules:
        raise HTTPException(status_code=404, detail="Schedule not found")
    del _schedules[schedule_id]
    return {"deleted": True}
