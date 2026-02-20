"""
Jorge Handoff Router

Performance-based routing layer that prevents handoffs to slow or failing bots.
Integrates with PerformanceTracker to check target bot health before executing handoffs.

When a target bot is underperforming (P95 > 120% SLA or error rate > 10%):
1. Handoff is deferred (not executed)
2. Contact stays with source bot
3. Tag "Handoff-Deferred-{TargetBot}-Performance" is added
4. Retry scheduled after cooldown (30 min)
5. Auto-recover when performance improves

Usage:
    router = HandoffRouter(performance_tracker)
    should_defer, reason = await router.should_defer_handoff("buyer_bot")
    if should_defer:
        logger.warning(f"Deferring handoff to buyer_bot: {reason}")
        # Keep with source bot, schedule retry
    else:
        # Execute handoff normally
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.services.jorge.performance_tracker import (
    SLA_CONFIG,
    PerformanceTracker,
)
from ghl_real_estate_ai.services.jorge.telemetry import trace_operation
from ghl_real_estate_ai.services.service_types import DeferralStats

logger = logging.getLogger(__name__)


@dataclass
class DeferralDecision:
    """Encapsulates a handoff deferral decision."""

    should_defer: bool
    reason: str
    target_bot: str
    p95_actual: float = 0.0
    p95_target: float = 0.0
    p95_percent_of_sla: float = 0.0
    error_rate: float = 0.0
    retry_after_seconds: int = 1800  # 30 minutes


@dataclass
class DeferredHandoff:
    """Tracks a deferred handoff for retry."""

    contact_id: str
    source_bot: str
    target_bot: str
    deferral_reason: str
    deferred_at: float
    retry_after: float
    retry_count: int = 0
    max_retries: int = 3


class HandoffRouter:
    """Performance-based handoff routing with automatic deferral and retry.

    Monitors target bot health and defers handoffs when performance degrades.
    Automatically retries deferred handoffs when performance improves.

    SLA Thresholds:
        - P95 < 100% SLA: Accept handoffs normally
        - P95 100-120% SLA: Warn but accept
        - P95 > 120% SLA: Defer handoff
        - Error rate < 5%: Accept
        - Error rate 5-10%: Warn
        - Error rate > 10%: Defer
    """

    COOLDOWN_SECONDS = 1800  # 30 minutes
    MAX_RETRIES = 3
    ERROR_RATE_WARN_THRESHOLD = 0.05  # 5%
    ERROR_RATE_DEFER_THRESHOLD = 0.10  # 10%
    P95_WARN_THRESHOLD = 1.0  # 100% of SLA target
    P95_DEFER_THRESHOLD = 1.2  # 120% of SLA target

    def __init__(
        self,
        performance_tracker: Optional[PerformanceTracker] = None,
        analytics_service: Optional[Any] = None,
    ):
        """Initialize the handoff router.

        Args:
            performance_tracker: PerformanceTracker instance (creates singleton if None).
            analytics_service: Optional analytics service for deferral tracking.
        """
        self._tracker = performance_tracker or PerformanceTracker()
        self._analytics_service = analytics_service
        self._repository: Any = None

        # Track deferred handoffs for retry
        self._deferred_handoffs: Dict[str, List[DeferredHandoff]] = {}
        self._deferral_stats: DeferralStats = {
            "total_deferrals": 0,
            "deferrals_by_bot": {},
            "auto_recoveries": 0,
            "permanent_deferrals": 0,
        }

        logger.info("HandoffRouter initialized with performance-based routing")

    # ── Persistence Configuration ─────────────────────────────────────

    def set_repository(self, repository: Any) -> None:
        """Attach a repository for deferral event persistence.

        The repository must implement:
            - ``save_deferral_event(contact_id, source_bot, target_bot,
              reason, timestamp, metadata)`` (async)
            - ``load_deferred_handoffs(since_timestamp)``
              (async, returns list of dicts)

        Args:
            repository: A repository instance (or None to disable).
        """
        self._repository = repository
        logger.info(
            "HandoffRouter persistence %s",
            "enabled" if repository else "disabled",
        )

    async def load_from_database(self, since_minutes: int = 60) -> int:
        """Hydrate in-memory deferred handoffs from the database.

        Args:
            since_minutes: How far back to load (default 60 minutes).

        Returns:
            Total number of records loaded from DB.
        """
        if self._repository is None:
            return 0

        cutoff = time.time() - (since_minutes * 60)
        loaded = 0

        try:
            db_deferrals = await self._repository.load_deferred_handoffs(cutoff)

            for row in db_deferrals:
                contact_id = row["contact_id"]
                if contact_id not in self._deferred_handoffs:
                    self._deferred_handoffs[contact_id] = []

                self._deferred_handoffs[contact_id].append(
                    DeferredHandoff(
                        contact_id=contact_id,
                        source_bot=row["source_bot"],
                        target_bot=row["target_bot"],
                        deferral_reason=row["reason"],
                        deferred_at=row["timestamp"],
                        retry_after=row["timestamp"] + self.COOLDOWN_SECONDS,
                        retry_count=row.get("retry_count", 0),
                        max_retries=self.MAX_RETRIES,
                    )
                )
                loaded += 1
        except Exception as exc:
            logger.warning("Failed to load deferred handoffs from DB: %s", exc)

        if loaded:
            logger.info("Loaded %d deferred handoff records from database", loaded)
        return loaded

    @trace_operation("jorge.handoff_router", "should_defer_handoff")
    async def should_defer_handoff(
        self,
        target_bot: str,
        window: str = "1h",
    ) -> DeferralDecision:
        """Check if handoff to target bot should be deferred due to performance.

        Args:
            target_bot: Target bot name (e.g., "buyer_bot", "seller_bot").
            window: Rolling window for performance metrics ("1h", "24h", "7d").

        Returns:
            DeferralDecision with should_defer flag and detailed reason.
        """
        # Normalize bot name to match PerformanceTracker convention
        tracker_bot_name = (
            target_bot
            if target_bot.endswith("_bot") or target_bot == "handoff"
            else f"{target_bot}_bot"
        )
        # Get performance stats for target bot
        stats = await self._tracker.get_bot_stats(tracker_bot_name, window)

        # If no data, allow handoff (assume bot is healthy)
        if stats["count"] == 0:
            return DeferralDecision(
                should_defer=False,
                reason="No performance data available for target bot",
                target_bot=target_bot,
            )

        # Get SLA targets for the target bot's "process" operation
        sla_target = SLA_CONFIG.get(tracker_bot_name, {}).get("process", {}).get("p95_target")
        if not sla_target:
            # Fallback: allow handoff if no SLA configured
            return DeferralDecision(
                should_defer=False,
                reason=f"No SLA target configured for {target_bot}",
                target_bot=target_bot,
            )

        p95_actual = stats["p95"]
        error_rate = 1.0 - stats["success_rate"]
        p95_percent_of_sla = p95_actual / sla_target

        # Check error rate threshold
        if error_rate > self.ERROR_RATE_DEFER_THRESHOLD:
            self._record_deferral(target_bot, "error_rate")
            return DeferralDecision(
                should_defer=True,
                reason=(
                    f"Error rate {error_rate:.2%} exceeds threshold "
                    f"{self.ERROR_RATE_DEFER_THRESHOLD:.2%}"
                ),
                target_bot=target_bot,
                p95_actual=p95_actual,
                p95_target=sla_target,
                p95_percent_of_sla=p95_percent_of_sla,
                error_rate=error_rate,
            )

        # Check P95 latency threshold
        if p95_percent_of_sla > self.P95_DEFER_THRESHOLD:
            self._record_deferral(target_bot, "p95_latency")
            return DeferralDecision(
                should_defer=True,
                reason=(
                    f"P95 latency {p95_actual:.1f}ms exceeds {self.P95_DEFER_THRESHOLD:.0%} "
                    f"of SLA target {sla_target:.0f}ms ({p95_percent_of_sla:.1%} of target)"
                ),
                target_bot=target_bot,
                p95_actual=p95_actual,
                p95_target=sla_target,
                p95_percent_of_sla=p95_percent_of_sla,
                error_rate=error_rate,
            )

        # Warn if approaching thresholds but allow handoff
        if (
            error_rate > self.ERROR_RATE_WARN_THRESHOLD
            or p95_percent_of_sla > self.P95_WARN_THRESHOLD
        ):
            logger.warning(
                f"Target bot {target_bot} approaching performance limits: "
                f"P95={p95_actual:.1f}ms ({p95_percent_of_sla:.1%} of SLA), "
                f"error_rate={error_rate:.2%}"
            )

        return DeferralDecision(
            should_defer=False,
            reason=f"Performance within acceptable limits (P95={p95_percent_of_sla:.1%} of SLA)",
            target_bot=target_bot,
            p95_actual=p95_actual,
            p95_target=sla_target,
            p95_percent_of_sla=p95_percent_of_sla,
            error_rate=error_rate,
        )

    @trace_operation("jorge.handoff_router", "defer_handoff")
    async def defer_handoff(
        self,
        contact_id: str,
        source_bot: str,
        target_bot: str,
        reason: str,
        location_id: str = "",
    ) -> Dict[str, Any]:
        """Record a deferred handoff and schedule retry.

        Args:
            contact_id: Contact ID for the deferred handoff.
            source_bot: Source bot name.
            target_bot: Target bot name.
            reason: Reason for deferral.
            location_id: GHL location ID.

        Returns:
            Dict with deferral details including retry_after timestamp.
        """
        now = time.time()
        retry_after = now + self.COOLDOWN_SECONDS

        # Check if contact already has deferred handoffs
        existing_deferrals = self._deferred_handoffs.get(contact_id, [])
        retry_count = sum(
            1 for d in existing_deferrals
            if d.source_bot == source_bot and d.target_bot == target_bot
        )

        # Check if max retries exceeded
        if retry_count >= self.MAX_RETRIES:
            self._deferral_stats["permanent_deferrals"] += 1
            logger.warning(
                f"Max retries ({self.MAX_RETRIES}) exceeded for handoff "
                f"{source_bot}->{target_bot} contact {contact_id}. "
                f"Deferral is now permanent."
            )
            return {
                "deferred": True,
                "permanent": True,
                "reason": f"Max retries exceeded: {reason}",
                "retry_count": retry_count,
            }

        # Record deferral in statistics
        # Extract reason type from reason string
        reason_type = "other"
        if "error rate" in reason.lower():
            reason_type = "error_rate"
        elif "p95" in reason.lower() or "latency" in reason.lower():
            reason_type = "p95_latency"
        self._record_deferral(target_bot, reason_type)

        # Create deferred handoff record
        deferred = DeferredHandoff(
            contact_id=contact_id,
            source_bot=source_bot,
            target_bot=target_bot,
            deferral_reason=reason,
            deferred_at=now,
            retry_after=retry_after,
            retry_count=retry_count,
        )

        if contact_id not in self._deferred_handoffs:
            self._deferred_handoffs[contact_id] = []
        self._deferred_handoffs[contact_id].append(deferred)

        # Log analytics event
        if self._analytics_service:
            try:
                await self._analytics_service.track_event(
                    event_type="jorge_handoff_deferred",
                    location_id=location_id,
                    contact_id=contact_id,
                    data={
                        "source_bot": source_bot,
                        "target_bot": target_bot,
                        "reason": reason,
                        "retry_after": retry_after,
                        "retry_count": retry_count,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to log deferral analytics for {contact_id}: {e}")

        # Persist to DB
        if self._repository:
            try:
                await self._repository.save_deferral_event(
                    contact_id=contact_id,
                    source_bot=source_bot,
                    target_bot=target_bot,
                    reason=reason,
                    timestamp=now,
                    metadata={"retry_after": retry_after, "retry_count": retry_count},
                )
            except Exception as e:
                logger.debug(f"Failed to persist deferral event: {e}")

        logger.info(
            f"Deferred handoff {source_bot}->{target_bot} for contact {contact_id}. "
            f"Retry scheduled after {self.COOLDOWN_SECONDS}s (attempt {retry_count + 1}/{self.MAX_RETRIES})"
        )

        return {
            "deferred": True,
            "permanent": False,
            "reason": reason,
            "retry_after": retry_after,
            "retry_count": retry_count,
            "max_retries": self.MAX_RETRIES,
        }

    @trace_operation("jorge.handoff_router", "check_deferred_handoffs")
    async def check_deferred_handoffs(self) -> List[Dict[str, Any]]:
        """Check for deferred handoffs ready for retry.

        Scans all deferred handoffs and checks if:
        1. Cooldown period has elapsed
        2. Target bot performance has improved

        Returns:
            List of contacts ready for retry with handoff details.
        """
        now = time.time()
        ready_for_retry: List[Dict[str, Any]] = []

        for contact_id, deferrals in list(self._deferred_handoffs.items()):
            # Filter deferrals ready for retry (cooldown elapsed)
            pending_deferrals = [d for d in deferrals if d.retry_after <= now]

            for deferred in pending_deferrals:
                # Check if target bot performance has improved
                decision = await self.should_defer_handoff(deferred.target_bot)

                if not decision.should_defer:
                    # Performance improved, ready for retry
                    ready_for_retry.append({
                        "contact_id": contact_id,
                        "source_bot": deferred.source_bot,
                        "target_bot": deferred.target_bot,
                        "deferred_at": deferred.deferred_at,
                        "retry_count": deferred.retry_count,
                        "recovery_reason": decision.reason,
                    })
                    self._deferral_stats["auto_recoveries"] += 1

                    # Remove from deferred list
                    self._deferred_handoffs[contact_id].remove(deferred)
                    if not self._deferred_handoffs[contact_id]:
                        del self._deferred_handoffs[contact_id]

                    logger.info(
                        f"Auto-recovery: handoff {deferred.source_bot}->{deferred.target_bot} "
                        f"for contact {contact_id} ready for retry (performance improved)"
                    )

        return ready_for_retry

    def _record_deferral(self, target_bot: str, reason_type: str) -> None:
        """Internal method to update deferral statistics."""
        self._deferral_stats["total_deferrals"] += 1

        if target_bot not in self._deferral_stats["deferrals_by_bot"]:
            self._deferral_stats["deferrals_by_bot"][target_bot] = {
                "total": 0,
                "by_reason": {},
            }

        self._deferral_stats["deferrals_by_bot"][target_bot]["total"] += 1

        reason_stats = self._deferral_stats["deferrals_by_bot"][target_bot]["by_reason"]
        if reason_type not in reason_stats:
            reason_stats[reason_type] = 0
        reason_stats[reason_type] += 1

    def get_deferral_stats(self) -> Dict[str, Any]:
        """Get deferral statistics summary.

        Returns:
            Dict with total_deferrals, deferrals_by_bot, auto_recoveries,
            permanent_deferrals, and current_deferred_count.
        """
        current_deferred = sum(len(d) for d in self._deferred_handoffs.values())

        return {
            **self._deferral_stats,
            "current_deferred_count": current_deferred,
            "current_deferred_contacts": len(self._deferred_handoffs),
        }

    @classmethod
    def reset(cls) -> None:
        """Reset singleton state. For testing only."""
        if hasattr(cls, "_instance") and cls._instance is not None:
            cls._instance._deferred_handoffs.clear()
            cls._instance._deferral_stats = {
                "total_deferrals": 0,
                "deferrals_by_bot": {},
                "auto_recoveries": 0,
                "permanent_deferrals": 0,
            }
