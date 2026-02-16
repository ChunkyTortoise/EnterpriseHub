"""Pipeline job CRUD API."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


class JobCreate(BaseModel):
    name: str
    url_pattern: str
    extraction_schema: dict = Field(default_factory=dict)
    llm_model: str = "gpt-4o-mini"


class JobOut(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    url_pattern: str
    extraction_schema: dict = Field(default_factory=dict)
    status: str = "active"


class JobResultOut(BaseModel):
    job_id: UUID
    records: list[dict] = Field(default_factory=list)
    total: int = 0


_jobs: dict[UUID, JobOut] = {}


@router.post("", response_model=JobOut)
async def create_job(job: JobCreate) -> JobOut:
    out = JobOut(name=job.name, url_pattern=job.url_pattern,
                 extraction_schema=job.extraction_schema)
    _jobs[out.id] = out
    return out


@router.get("", response_model=list[JobOut])
async def list_jobs() -> list[JobOut]:
    return list(_jobs.values())


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: UUID) -> JobOut:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return _jobs[job_id]


@router.get("/{job_id}/results", response_model=JobResultOut)
async def get_job_results(job_id: UUID) -> JobResultOut:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResultOut(job_id=job_id)


@router.delete("/{job_id}")
async def delete_job(job_id: UUID) -> dict:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    del _jobs[job_id]
    return {"deleted": True}
