"""Tier enforcement: per-tier limits for events, prompts, jobs, etc."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from devops_suite.config import TIER_LIMITS, Tier


@dataclass
class UsageCounter:
    events_today: int = 0
    prompts_total: int = 0
    pipelines_total: int = 0
    pipeline_runs_today: int = 0
    prompt_renders_today: int = 0
    last_reset: datetime = field(default_factory=datetime.utcnow)


class TierLimitExceeded(Exception):
    def __init__(self, resource: str, limit: int | None, current: int, tier: str):
        self.resource = resource
        self.limit = limit
        self.current = current
        self.tier = tier
        super().__init__(f"Tier '{tier}' limit exceeded for {resource}: {current}/{limit}")


class TierManager:
    """Enforces per-tier resource limits."""

    def __init__(self) -> None:
        self._tenants: dict[str, Tier] = {}
        self._usage: dict[str, UsageCounter] = {}

    def register_tenant(self, tenant_id: str, tier: Tier) -> None:
        self._tenants[tenant_id] = tier
        if tenant_id not in self._usage:
            self._usage[tenant_id] = UsageCounter()

    def get_tier(self, tenant_id: str) -> Tier | None:
        return self._tenants.get(tenant_id)

    def get_limits(self, tenant_id: str) -> dict | None:
        tier = self._tenants.get(tenant_id)
        if not tier:
            return None
        return TIER_LIMITS.get(tier)

    def get_usage(self, tenant_id: str) -> UsageCounter | None:
        return self._usage.get(tenant_id)

    def check_and_increment(self, tenant_id: str, resource: str, amount: int = 1) -> bool:
        tier = self._tenants.get(tenant_id)
        if not tier:
            raise ValueError(f"Unknown tenant: {tenant_id}")

        limits = TIER_LIMITS[tier]
        usage = self._usage.setdefault(tenant_id, UsageCounter())
        self._maybe_reset_daily(usage)

        limit_val = limits.get(resource)
        if limit_val is None:
            # Unlimited
            self._increment(usage, resource, amount)
            return True

        current = self._get_current(usage, resource)
        if current + amount > limit_val:
            raise TierLimitExceeded(resource, limit_val, current, tier.value)

        self._increment(usage, resource, amount)
        return True

    def _get_current(self, usage: UsageCounter, resource: str) -> int:
        mapping = {
            "events_per_day": usage.events_today,
            "prompts": usage.prompts_total,
            "pipelines": usage.pipelines_total,
            "pipeline_runs_per_day": usage.pipeline_runs_today,
            "prompt_renders_per_day": usage.prompt_renders_today,
        }
        return mapping.get(resource, 0)

    def _increment(self, usage: UsageCounter, resource: str, amount: int) -> None:
        if resource == "events_per_day":
            usage.events_today += amount
        elif resource == "prompts":
            usage.prompts_total += amount
        elif resource == "pipelines":
            usage.pipelines_total += amount
        elif resource == "pipeline_runs_per_day":
            usage.pipeline_runs_today += amount
        elif resource == "prompt_renders_per_day":
            usage.prompt_renders_today += amount

    def _maybe_reset_daily(self, usage: UsageCounter) -> None:
        now = datetime.utcnow()
        if now.date() > usage.last_reset.date():
            usage.events_today = 0
            usage.pipeline_runs_today = 0
            usage.prompt_renders_today = 0
            usage.last_reset = now

    def upgrade_tier(self, tenant_id: str, new_tier: Tier) -> None:
        self._tenants[tenant_id] = new_tier
