"""Job scheduler using APScheduler-style cron expressions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class ScheduledJob:
    job_id: str
    name: str
    cron_expression: str
    callback: Callable[..., Any] | None = None
    is_active: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    metadata: dict = field(default_factory=dict)


class JobScheduler:
    """Manages cron-scheduled jobs (in-memory for simplicity; backs to APScheduler in production)."""

    def __init__(self) -> None:
        self._jobs: dict[str, ScheduledJob] = {}

    def add_job(
        self,
        job_id: str,
        name: str,
        cron_expression: str,
        callback: Callable[..., Any] | None = None,
        metadata: dict | None = None,
    ) -> ScheduledJob:
        if not _validate_cron(cron_expression):
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        job = ScheduledJob(
            job_id=job_id, name=name, cron_expression=cron_expression,
            callback=callback, metadata=metadata or {},
        )
        self._jobs[job_id] = job
        return job

    def remove_job(self, job_id: str) -> bool:
        return self._jobs.pop(job_id, None) is not None

    def pause_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.is_active = False
        return True

    def resume_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.is_active = True
        return True

    def get_job(self, job_id: str) -> ScheduledJob | None:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[ScheduledJob]:
        return list(self._jobs.values())

    def list_active_jobs(self) -> list[ScheduledJob]:
        return [j for j in self._jobs.values() if j.is_active]

    def trigger_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or not job.callback:
            return False
        job.callback()
        job.last_run = datetime.utcnow()
        job.run_count += 1
        return True

    def update_cron(self, job_id: str, cron_expression: str) -> bool:
        if not _validate_cron(cron_expression):
            raise ValueError(f"Invalid cron expression: {cron_expression}")
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.cron_expression = cron_expression
        return True


def _validate_cron(expr: str) -> bool:
    """Basic cron expression validation (5 or 6 fields)."""
    parts = expr.strip().split()
    return len(parts) in (5, 6)
