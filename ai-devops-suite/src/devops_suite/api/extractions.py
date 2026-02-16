"""LLM extraction configuration endpoints."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/extractions", tags=["extractions"])


class ExtractionConfigOut(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    fields: dict[str, str] = Field(default_factory=dict)
    model: str = "gpt-4o-mini"


@router.get("", response_model=list[ExtractionConfigOut])
async def list_extractions() -> list[ExtractionConfigOut]:
    return []
