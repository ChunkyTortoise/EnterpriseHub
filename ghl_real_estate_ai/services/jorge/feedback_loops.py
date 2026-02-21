"""
Jorge Phase 3 Feedback Loops

Implements 5 closed-loop feedback mechanisms that continuously improve
bot performance based on observed outcomes:

1. Handoff outcome -> threshold adjustment (delegates to JorgeHandoffService.get_learned_adjustments)
2. Abandonment detection -> recovery trigger
3. A/B test result -> strategy selection (auto-promote winning variants)
4. Alert firing -> escalation action (delegates to AlertingService.check_escalations)
5. Performance metric -> routing weight adjustment
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Abandonment thresholds
ABANDONMENT_SILENCE_SECONDS = 600  # 10 minutes of silence after handoff
ABANDONMENT_CHECK_WINDOW = 3600  # Look back 1 hour for recent handoffs
RECOVERY_MAX_ATTEMPTS = 2

# Routing weight bounds
MIN_ROUTING_WEIGHT = 0.3
MAX_ROUTING_WEIGHT = 1.0
WEIGHT_DECAY_FACTOR = 0.1  # How much to penalize per SLA breach
WEIGHT_RECOVERY_FACTOR = 0.05  # How much to recover per check cycle


@dataclass
class AbandonmentRecord:
    """Tracks a contact that went silent after handoff."""

    contact_id: str
    source_bot: str
    target_bot: str
    handoff_time: float
    last_activity_time: float
    recovery_attempts: int = 0
    recovered: bool = False


@dataclass
class RoutingWeights:
    """Dynamic routing weights per bot, adjusted by performance."""

    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "lead_bot": 1.0,
            "buyer_bot": 1.0,
            "seller_bot": 1.0,
        }
    )
    last_updated: float = 0.0


class FeedbackLoopManager:
    """Orchestrates all 5 feedback loops for Jorge bots.

    Usage:
        manager = FeedbackLoopManager(
            handoff_service=handoff_svc,
            ab_testing_service=ab_svc,
            alerting_service=alert_svc,
            performance_tracker=perf_tracker,
            handoff_router=router,
        )

        # Run all loops in a periodic task
        results = await manager.run_all_loops()
    """

    def __init__(
        self,
        handoff_service=None,
        ab_testing_service=None,
        alerting_service=None,
        performance_tracker=None,
        handoff_router=None,
    ):
        self._handoff_service = handoff_service
        self._ab_testing = ab_testing_service
        self._alerting = alerting_service
        self._perf_tracker = performance_tracker
        self._handoff_router = handoff_router

        self._abandonment_records: Dict[str, AbandonmentRecord] = {}
        self._routing_weights = RoutingWeights()
        self._loop_stats: Dict[str, Dict[str, Any]] = {
            "threshold_adjustment": {"runs": 0, "last_run": 0.0},
            "abandonment_recovery": {"runs": 0, "last_run": 0.0, "recoveries": 0},
            "ab_test_promotion": {"runs": 0, "last_run": 0.0, "promotions": 0},
            "alert_escalation": {"runs": 0, "last_run": 0.0, "escalations": 0},
            "routing_weight_adjustment": {"runs": 0, "last_run": 0.0, "adjustments": 0},
        }

    # ── Loop 1: Handoff Outcome -> Threshold Adjustment ──────────────

    async def run_threshold_adjustment_loop(self) -> Dict[str, Any]:
        """Loop 1: Check handoff outcomes and report current threshold adjustments.

        This loop is already implemented in JorgeHandoffService.get_learned_adjustments().
        This method provides a unified interface and logging.

        Returns:
            Dict with per-route adjustment details.
        """
        if self._handoff_service is None:
            return {"status": "skipped", "reason": "handoff_service not configured"}

        routes = [
            ("lead", "buyer"),
            ("lead", "seller"),
            ("buyer", "seller"),
            ("seller", "buyer"),
        ]

        adjustments = {}
        for source, target in routes:
            learned = self._handoff_service.get_learned_adjustments(source, target)
            route_key = f"{source}->{target}"
            adjustments[route_key] = {
                "adjustment": learned["adjustment"],
                "success_rate": learned["success_rate"],
                "sample_size": learned["sample_size"],
                "effective": learned["sample_size"] >= self._handoff_service.MIN_LEARNING_SAMPLES,
            }

        self._loop_stats["threshold_adjustment"]["runs"] += 1
        self._loop_stats["threshold_adjustment"]["last_run"] = time.time()

        active_count = sum(1 for a in adjustments.values() if a["effective"])
        logger.info(
            "Loop 1 (threshold adjustment): %d/%d routes have active learned adjustments",
            active_count,
            len(routes),
        )

        return {"status": "ok", "adjustments": adjustments}

    # ── Loop 2: Abandonment Detection -> Recovery Trigger ────────────

    def report_handoff_activity(
        self,
        contact_id: str,
        source_bot: str,
        target_bot: str,
        handoff_time: float,
    ) -> None:
        """Register a handoff event for abandonment monitoring.

        Call this after each successful handoff execution.
        """
        self._abandonment_records[contact_id] = AbandonmentRecord(
            contact_id=contact_id,
            source_bot=source_bot,
            target_bot=target_bot,
            handoff_time=handoff_time,
            last_activity_time=handoff_time,
        )

    def report_contact_activity(self, contact_id: str) -> None:
        """Update last activity time for a contact (message received)."""
        if contact_id in self._abandonment_records:
            self._abandonment_records[contact_id].last_activity_time = time.time()

    async def run_abandonment_recovery_loop(self) -> Dict[str, Any]:
        """Loop 2: Detect contacts that went silent after handoff and trigger recovery.

        Scans recent handoffs. If a contact hasn't responded within
        ABANDONMENT_SILENCE_SECONDS, generates a recovery action
        (re-engage message or revert to source bot).

        Returns:
            Dict with detected abandonments and recovery actions.
        """
        now = time.time()
        cutoff = now - ABANDONMENT_CHECK_WINDOW
        recoveries: List[Dict[str, Any]] = []

        for contact_id, record in list(self._abandonment_records.items()):
            # Skip old records outside the check window
            if record.handoff_time < cutoff:
                del self._abandonment_records[contact_id]
                continue

            # Skip already recovered
            if record.recovered:
                continue

            # Check for silence
            silence_duration = now - record.last_activity_time
            if silence_duration < ABANDONMENT_SILENCE_SECONDS:
                continue

            # Max recovery attempts reached
            if record.recovery_attempts >= RECOVERY_MAX_ATTEMPTS:
                continue

            # Trigger recovery
            record.recovery_attempts += 1
            action = self._determine_recovery_action(record)
            recoveries.append(action)

            logger.info(
                "Loop 2 (abandonment): Contact %s silent for %.0fs after %s->%s handoff. "
                "Recovery action: %s (attempt %d/%d)",
                contact_id,
                silence_duration,
                record.source_bot,
                record.target_bot,
                action["action"],
                record.recovery_attempts,
                RECOVERY_MAX_ATTEMPTS,
            )

        self._loop_stats["abandonment_recovery"]["runs"] += 1
        self._loop_stats["abandonment_recovery"]["last_run"] = now
        self._loop_stats["abandonment_recovery"]["recoveries"] += len(recoveries)

        return {
            "status": "ok",
            "detected": len(recoveries),
            "recoveries": recoveries,
            "monitored_contacts": len(self._abandonment_records),
        }

    def _determine_recovery_action(self, record: AbandonmentRecord) -> Dict[str, Any]:
        """Decide what recovery action to take for an abandoned contact.

        First attempt: Send a re-engagement nudge from the target bot.
        Second attempt: Revert to source bot.
        """
        if record.recovery_attempts <= 1:
            return {
                "contact_id": record.contact_id,
                "action": "nudge",
                "target_bot": record.target_bot,
                "message_template": "re_engagement_followup",
                "context": {
                    "source_bot": record.source_bot,
                    "handoff_time": record.handoff_time,
                    "silence_seconds": time.time() - record.last_activity_time,
                },
            }
        else:
            record.recovered = True
            return {
                "contact_id": record.contact_id,
                "action": "revert",
                "target_bot": record.source_bot,
                "reason": "No response after nudge, reverting to original bot",
                "context": {
                    "original_target": record.target_bot,
                    "handoff_time": record.handoff_time,
                    "total_silence_seconds": time.time() - record.handoff_time,
                },
            }

    # ── Loop 3: A/B Test Result -> Strategy Selection ────────────────

    async def run_ab_test_promotion_loop(
        self,
        min_p_value: float = 0.05,
        min_lift_percent: float = 10.0,
        min_sample_size: int = 100,
        min_runtime_days: float = 3.0,
        auto_deactivate: bool = True,
    ) -> Dict[str, Any]:
        """Loop 3: Auto-promote winning A/B test variants.

        Checks all active experiments for statistically significant winners.
        When found, deactivates the experiment and records the winning strategy.

        Args:
            min_p_value: Significance threshold (default 0.05).
            min_lift_percent: Minimum improvement over control (default 10%).
            min_sample_size: Minimum impressions (default 100).
            min_runtime_days: Minimum experiment duration (default 3 days).
            auto_deactivate: Whether to auto-close winning experiments.

        Returns:
            Dict with promotion candidates and actions taken.
        """
        if self._ab_testing is None:
            return {"status": "skipped", "reason": "ab_testing_service not configured"}

        candidates = self._ab_testing.get_promotion_candidates(
            min_p_value=min_p_value,
            min_lift_percent=min_lift_percent,
            min_sample_size=min_sample_size,
            min_runtime_days=min_runtime_days,
        )

        promoted = []
        for candidate in candidates:
            exp_id = candidate["experiment_id"]

            if auto_deactivate:
                self._ab_testing.deactivate_experiment(exp_id)

            promoted.append(
                {
                    "experiment_id": exp_id,
                    "winning_variant": candidate["winning_variant"],
                    "lift_percent": candidate["lift_percent"],
                    "p_value": candidate["p_value"],
                    "sample_size": candidate["sample_size"],
                    "auto_deactivated": auto_deactivate,
                }
            )

            logger.info(
                "Loop 3 (A/B promotion): Experiment '%s' winner='%s' lift=%.1f%% p=%.4f samples=%d",
                exp_id,
                candidate["winning_variant"],
                candidate["lift_percent"],
                candidate["p_value"],
                candidate["sample_size"],
            )

        self._loop_stats["ab_test_promotion"]["runs"] += 1
        self._loop_stats["ab_test_promotion"]["last_run"] = time.time()
        self._loop_stats["ab_test_promotion"]["promotions"] += len(promoted)

        return {
            "status": "ok",
            "candidates_found": len(candidates),
            "promoted": promoted,
        }

    # ── Loop 4: Alert Firing -> Escalation Action ────────────────────

    async def run_alert_escalation_loop(self) -> Dict[str, Any]:
        """Loop 4: Check for unacknowledged critical alerts needing escalation.

        Delegates to AlertingService.check_escalations() which implements
        the 3-level escalation policy.

        Returns:
            Dict with escalation details.
        """
        if self._alerting is None:
            return {"status": "skipped", "reason": "alerting_service not configured"}

        escalations = await self._alerting.check_escalations()

        escalation_details = []
        for alert, level in escalations:
            escalation_details.append(
                {
                    "alert_id": alert.id,
                    "rule_name": alert.rule_name,
                    "severity": alert.severity,
                    "escalation_level": level.level,
                    "channels": level.channels,
                    "description": level.description,
                    "age_seconds": round(time.time() - alert.triggered_at, 1),
                }
            )

            # Send to escalation channels
            for channel in level.channels:
                if channel == "pagerduty":
                    await self._alerting._send_pagerduty_alert(alert)
                elif channel == "opsgenie":
                    await self._alerting._send_opsgenie_alert(alert)
                elif channel in ("email", "slack", "webhook"):
                    await self._alerting.send_alert(alert)

        self._loop_stats["alert_escalation"]["runs"] += 1
        self._loop_stats["alert_escalation"]["last_run"] = time.time()
        self._loop_stats["alert_escalation"]["escalations"] += len(escalation_details)

        if escalation_details:
            logger.warning(
                "Loop 4 (escalation): %d unacknowledged critical alerts escalated",
                len(escalation_details),
            )

        return {
            "status": "ok",
            "escalations": escalation_details,
            "total_escalated": len(escalation_details),
        }

    # ── Loop 5: Performance Metric -> Routing Weight Adjustment ──────

    async def run_routing_weight_loop(self) -> Dict[str, Any]:
        """Loop 5: Adjust routing weights based on bot performance metrics.

        Checks each bot's SLA compliance and adjusts routing weights:
        - SLA breach: Reduce weight by WEIGHT_DECAY_FACTOR
        - SLA compliant: Recover weight by WEIGHT_RECOVERY_FACTOR
        - Weight clamped to [MIN_ROUTING_WEIGHT, MAX_ROUTING_WEIGHT]

        Weights are used by HandoffRouter to prefer healthier bots.

        Returns:
            Dict with updated weights and adjustment details.
        """
        if self._perf_tracker is None:
            return {"status": "skipped", "reason": "performance_tracker not configured"}

        adjustments = []
        for bot_name in ["lead_bot", "buyer_bot", "seller_bot"]:
            stats = await self._perf_tracker.get_bot_stats(bot_name, "1h")

            if stats["count"] == 0:
                continue

            old_weight = self._routing_weights.weights.get(bot_name, 1.0)
            new_weight = old_weight

            # Check SLA compliance
            sla_breached = False
            from ghl_real_estate_ai.services.jorge.performance_tracker import SLA_CONFIG

            sla = SLA_CONFIG.get(bot_name, {}).get("process", {})
            p95_target = sla.get("p95_target", 2000)

            if stats["p95"] > p95_target:
                # SLA breach: reduce weight
                new_weight = max(MIN_ROUTING_WEIGHT, old_weight - WEIGHT_DECAY_FACTOR)
                sla_breached = True
            elif stats["success_rate"] < 0.90:
                # Low success rate: reduce weight
                new_weight = max(MIN_ROUTING_WEIGHT, old_weight - WEIGHT_DECAY_FACTOR)
                sla_breached = True
            else:
                # Healthy: recover weight
                new_weight = min(MAX_ROUTING_WEIGHT, old_weight + WEIGHT_RECOVERY_FACTOR)

            if new_weight != old_weight:
                self._routing_weights.weights[bot_name] = round(new_weight, 2)
                adjustments.append(
                    {
                        "bot_name": bot_name,
                        "old_weight": old_weight,
                        "new_weight": round(new_weight, 2),
                        "reason": "sla_breach" if sla_breached else "recovery",
                        "p95": stats["p95"],
                        "p95_target": p95_target,
                        "success_rate": stats["success_rate"],
                    }
                )

        self._routing_weights.last_updated = time.time()
        self._loop_stats["routing_weight_adjustment"]["runs"] += 1
        self._loop_stats["routing_weight_adjustment"]["last_run"] = time.time()
        self._loop_stats["routing_weight_adjustment"]["adjustments"] += len(adjustments)

        if adjustments:
            logger.info(
                "Loop 5 (routing weights): %d adjustments made: %s",
                len(adjustments),
                {a["bot_name"]: a["new_weight"] for a in adjustments},
            )

        return {
            "status": "ok",
            "weights": dict(self._routing_weights.weights),
            "adjustments": adjustments,
        }

    def get_routing_weight(self, bot_name: str) -> float:
        """Get the current routing weight for a bot.

        Args:
            bot_name: Bot name (e.g., "buyer_bot").

        Returns:
            Weight between MIN_ROUTING_WEIGHT and MAX_ROUTING_WEIGHT.
        """
        return self._routing_weights.weights.get(bot_name, 1.0)

    # ── Run All Loops ────────────────────────────────────────────────

    async def run_all_loops(self) -> Dict[str, Any]:
        """Execute all 5 feedback loops and return combined results.

        Returns:
            Dict with results from each loop.
        """
        results = {}

        results["loop_1_threshold_adjustment"] = await self.run_threshold_adjustment_loop()
        results["loop_2_abandonment_recovery"] = await self.run_abandonment_recovery_loop()
        results["loop_3_ab_test_promotion"] = await self.run_ab_test_promotion_loop()
        results["loop_4_alert_escalation"] = await self.run_alert_escalation_loop()
        results["loop_5_routing_weights"] = await self.run_routing_weight_loop()

        logger.info("All 5 feedback loops completed")
        return results

    def get_loop_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get execution statistics for all feedback loops."""
        return dict(self._loop_stats)
