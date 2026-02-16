"""A/B experiment API for prompts."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


class VariantIn(BaseModel):
    name: str
    version_id: int
    traffic_percentage: float


class ExperimentCreate(BaseModel):
    prompt_id: UUID
    name: str
    metric: str = "latency"
    variants: list[VariantIn]
    significance_threshold: float = 0.95
    min_samples: int = 100


class ExperimentOut(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    prompt_id: UUID
    name: str
    status: str = "draft"
    metric: str
    variants: list[VariantIn]


class ExperimentResultOut(BaseModel):
    experiment_id: UUID
    is_significant: bool
    winner: str | None = None
    p_value: float
    confidence: float


_experiments: dict[UUID, ExperimentOut] = {}


@router.post("", response_model=ExperimentOut)
async def create_experiment(exp: ExperimentCreate) -> ExperimentOut:
    total = sum(v.traffic_percentage for v in exp.variants)
    if abs(total - 1.0) > 0.01:
        raise HTTPException(status_code=400, detail="Variant traffic must sum to 1.0")
    out = ExperimentOut(
        prompt_id=exp.prompt_id, name=exp.name,
        metric=exp.metric, variants=exp.variants,
    )
    _experiments[out.id] = out
    return out


@router.get("/{experiment_id}", response_model=ExperimentOut)
async def get_experiment(experiment_id: UUID) -> ExperimentOut:
    if experiment_id not in _experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return _experiments[experiment_id]


@router.get("/{experiment_id}/results", response_model=ExperimentResultOut)
async def get_experiment_results(experiment_id: UUID) -> ExperimentResultOut:
    if experiment_id not in _experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return ExperimentResultOut(
        experiment_id=experiment_id,
        is_significant=False, winner=None, p_value=1.0, confidence=0.0,
    )
