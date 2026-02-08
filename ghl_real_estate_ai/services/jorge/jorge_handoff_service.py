"""
Jorge Cross-Bot Handoff Service

Tag-driven handoff between lead, buyer, and seller bots.
When Bot A determines the contact should be handled by Bot B, it:
1. Removes Bot A's activation tag
2. Adds Bot B's activation tag
3. Adds a handoff tracking tag (e.g., Handoff-Lead-to-Buyer)
4. Logs the handoff event via analytics_service

The next inbound message routes to Bot B via existing tag-based routing.
"""

import logging
import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.services.jorge.telemetry import trace_operation

logger = logging.getLogger(__name__)


@dataclass
class HandoffDecision:
    """Encapsulates a bot-to-bot handoff decision."""

    source_bot: str  # "lead", "buyer", "seller"
    target_bot: str  # "lead", "buyer", "seller"
    reason: str  # "buyer_intent_detected", "seller_intent_detected", etc.
    confidence: float  # 0.0-1.0
    context: Dict[str, Any] = field(default_factory=dict)


class JorgeHandoffService:
    """Evaluates and executes cross-bot handoffs based on intent signals."""

    TAG_MAP = {
        "lead": "Needs Qualifying",
        "buyer": "Buyer-Lead",
        "seller": "Needs Qualifying",
    }

    # Confidence thresholds per handoff direction
    THRESHOLDS = {
        ("lead", "buyer"): 0.7,
        ("lead", "seller"): 0.7,
        ("buyer", "seller"): 0.8,
        ("seller", "buyer"): 0.6,
    }

    CIRCULAR_WINDOW_SECONDS = 30 * 60
    HOURLY_HANDOFF_LIMIT = 3
    DAILY_HANDOFF_LIMIT = 10
    HOUR_SECONDS = 3600
    DAY_SECONDS = 86400
    HANDOFF_LOCK_TIMEOUT = 30  # seconds before a handoff lock expires

    _handoff_history: Dict[str, List[Dict[str, Any]]] = {}
    _handoff_outcomes: Dict[str, List[Dict[str, Any]]] = {}
    _active_handoffs: Dict[str, float] = {}
    _analytics: Dict[str, Any] = {
        "total_handoffs": 0,
        "successful_handoffs": 0,
        "failed_handoffs": 0,
        "processing_times_ms": [],
        "handoffs_by_route": {},
        "handoffs_by_hour": {h: 0 for h in range(24)},
        "blocked_by_rate_limit": 0,
        "blocked_by_circular": 0,
    }

    # Minimum data points required before learned adjustments apply
    MIN_LEARNING_SAMPLES = 10

    # Intent phrase patterns for signal boosting
    BUYER_INTENT_PATTERNS = [
        r"\bi\s+want\s+to\s+buy\b",
        r"\blooking\s+to\s+buy\b",
        r"\bbudget\b.*\$",
        r"\bpre[- ]?approv",
        r"\bpre[- ]?qualif",
        r"\bdown\s+payment\b",
        r"\bfha\b|\bva\s+loan\b|\bconventional\b",
        r"\bfind\s+(a|my)\s+(new\s+)?(home|house|place|property)\b",
    ]

    SELLER_INTENT_PATTERNS = [
        r"\bsell\s+my\s+(home|house|property)\b",
        r"\bwhat'?s\s+my\s+home\s+worth\b",
        r"\bhome\s+valu",
        r"\bcma\b",
        r"\blist(ing)?\s+my\s+(home|house|property)\b",
        r"\bneed\s+to\s+sell\b",
        r"\bsell\s+before\s+buy",
        r"\bsell\s+first\b",
    ]

    def __init__(self, analytics_service=None):
        self.analytics_service = analytics_service
        self._repository: Any = None

    # ── Persistence Configuration ─────────────────────────────────────

    def set_repository(self, repository: Any) -> None:
        """Attach a repository for handoff outcome persistence.

        The repository must implement:
            - ``save_handoff_outcome(contact_id, source_bot, target_bot,
              outcome, timestamp, metadata)`` (async)
            - ``load_handoff_outcomes(since_timestamp, source_bot, target_bot)``
              (async, returns list of dicts)

        Args:
            repository: A repository instance (or None to disable).
        """
        self._repository = repository
        logger.info(
            "JorgeHandoffService persistence %s",
            "enabled" if repository else "disabled",
        )

    async def load_from_database(self, since_minutes: int = 10080) -> int:
        """Hydrate in-memory handoff outcomes from the database.

        Loads outcomes recorded within the last ``since_minutes`` (default
        7 days) and merges them into ``_handoff_outcomes``, deduplicating
        by contact_id + timestamp.

        Args:
            since_minutes: How far back to load (default 10080 = 7 days).

        Returns:
            Total number of records loaded from DB.
        """
        if self._repository is None:
            return 0

        cutoff = time.time() - (since_minutes * 60)
        loaded = 0

        try:
            db_outcomes = await self._repository.load_handoff_outcomes(cutoff)

            # Build set of existing keys for dedup
            existing_keys: set = set()
            for route, outcomes in self._handoff_outcomes.items():
                for o in outcomes:
                    existing_keys.add((o.get("contact_id", ""), o.get("timestamp", 0)))

            for row in db_outcomes:
                key = (row["contact_id"], row["timestamp"])
                if key in existing_keys:
                    continue

                pair_key = f"{row['source_bot']}->{row['target_bot']}"
                if pair_key not in self._handoff_outcomes:
                    self._handoff_outcomes[pair_key] = []

                self._handoff_outcomes[pair_key].append({
                    "contact_id": row["contact_id"],
                    "outcome": row["outcome"],
                    "timestamp": row["timestamp"],
                    "metadata": row.get("metadata") or {},
                })
                loaded += 1
        except Exception as exc:
            logger.warning("Failed to load handoff outcomes from DB: %s", exc)

        if loaded:
            logger.info("Loaded %d handoff outcome records from database", loaded)
        return loaded

    @classmethod
    def _cleanup_old_entries(cls, max_age: float = 86400) -> None:
        now = time.time()
        cutoff = now - max_age
        contacts_to_remove = []
        for contact_id, entries in cls._handoff_history.items():
            cls._handoff_history[contact_id] = [e for e in entries if e["timestamp"] > cutoff]
            if not cls._handoff_history[contact_id]:
                contacts_to_remove.append(contact_id)
        for contact_id in contacts_to_remove:
            del cls._handoff_history[contact_id]

    @classmethod
    def _check_circular_handoff(cls, contact_id: str, source_bot: str, target_bot: str) -> Optional[str]:
        """Check for direct circular handoff (same source->target within 30 min)."""
        now = time.time()
        cutoff = now - cls.CIRCULAR_WINDOW_SECONDS
        for entry in cls._handoff_history.get(contact_id, []):
            if entry["from"] == source_bot and entry["to"] == target_bot and entry["timestamp"] > cutoff:
                return (
                    f"Circular handoff blocked: {source_bot}->{target_bot} "
                    f"for contact {contact_id} occurred within last 30 minutes"
                )
        return None

    @classmethod
    def _check_circular_prevention(cls, contact_id: str, source_bot: str, target_bot: str) -> Tuple[bool, str]:
        """Check if handoff would create a cycle.

        Performs two checks:
        1. Same source->target handoff within 30-minute window
        2. Full handoff chain detection for circular patterns (e.g., Lead->Buyer->Lead)

        Returns:
            Tuple of (is_blocked: bool, reason: str)
        """
        now = time.time()
        cutoff = now - cls.CIRCULAR_WINDOW_SECONDS
        history = cls._handoff_history.get(contact_id, [])

        # Check 1: Same source->target within 30-minute window
        for entry in history:
            if entry["from"] == source_bot and entry["to"] == target_bot and entry["timestamp"] > cutoff:
                return (
                    True,
                    f"Circular prevention: {source_bot}->{target_bot} blocked "
                    f"within 30-min window for contact {contact_id}",
                )

        # Check 2: Detect circular patterns in handoff chain
        # Build the chain of bot transitions
        chain: List[str] = []
        for entry in reversed(history):
            if entry["timestamp"] > cutoff:
                chain.append(entry["to"])
                chain.append(entry["from"])

        # If chain is empty, no circular pattern possible
        if not chain:
            return (False, "")

        # Check if proposed handoff creates a cycle
        # A cycle exists if the target_bot appears earlier in the chain
        # and the path from that occurrence back to target_bot completes a loop
        chain = list(dict.fromkeys(chain))  # Remove duplicates while preserving order

        # Check if target_bot is already in the chain (would create a loop)
        if target_bot in chain:
            chain_str = " -> ".join(chain[-6:]) if len(chain) > 6 else " -> ".join(chain)
            return (
                True,
                f"Circular prevention: handoff chain detected for contact {contact_id}. "
                f"Current chain: {chain_str} -> {target_bot} (would create cycle)",
            )

        return (False, "")

    @classmethod
    def _check_rate_limit(cls, contact_id: str) -> Optional[str]:
        now = time.time()
        entries = cls._handoff_history.get(contact_id, [])
        hourly_count = sum(1 for e in entries if e["timestamp"] > now - cls.HOUR_SECONDS)
        if hourly_count >= cls.HOURLY_HANDOFF_LIMIT:
            return (
                f"Rate limit exceeded: {hourly_count} handoffs in the last hour "
                f"for contact {contact_id} (max {cls.HOURLY_HANDOFF_LIMIT}/hour)"
            )
        daily_count = sum(1 for e in entries if e["timestamp"] > now - cls.DAY_SECONDS)
        if daily_count >= cls.DAILY_HANDOFF_LIMIT:
            return (
                f"Rate limit exceeded: {daily_count} handoffs in the last 24 hours "
                f"for contact {contact_id} (max {cls.DAILY_HANDOFF_LIMIT}/day)"
            )
        return None

    @classmethod
    def _record_handoff(cls, contact_id: str, source_bot: str, target_bot: str) -> None:
        if contact_id not in cls._handoff_history:
            cls._handoff_history[contact_id] = []
        cls._handoff_history[contact_id].append(
            {
                "from": source_bot,
                "to": target_bot,
                "timestamp": time.time(),
            }
        )

    @classmethod
    def _acquire_handoff_lock(cls, contact_id: str) -> bool:
        """Acquire a handoff lock for the given contact.

        Returns False if the contact already has an active handoff
        (within HANDOFF_LOCK_TIMEOUT seconds). Otherwise sets the lock
        timestamp and returns True.
        """
        now = time.time()
        if contact_id in cls._active_handoffs:
            lock_time = cls._active_handoffs[contact_id]
            if now - lock_time < cls.HANDOFF_LOCK_TIMEOUT:
                return False
        cls._active_handoffs[contact_id] = now
        return True

    @classmethod
    def _release_handoff_lock(cls, contact_id: str) -> None:
        """Remove the handoff lock for the given contact."""
        cls._active_handoffs.pop(contact_id, None)

    @classmethod
    def _record_analytics(
        cls,
        route: str,
        start_time: float,
        success: bool,
        blocked_by: Optional[str] = None,
    ) -> None:
        """Record a handoff event into the analytics ledger."""
        elapsed_ms = (time.time() - start_time) * 1000
        cls._analytics["total_handoffs"] += 1
        if success:
            cls._analytics["successful_handoffs"] += 1
        else:
            cls._analytics["failed_handoffs"] += 1
        cls._analytics["processing_times_ms"].append(elapsed_ms)

        # Route counter
        if route not in cls._analytics["handoffs_by_route"]:
            cls._analytics["handoffs_by_route"][route] = 0
        cls._analytics["handoffs_by_route"][route] += 1

        # Hour distribution
        hour = time.localtime().tm_hour
        cls._analytics["handoffs_by_hour"][hour] += 1

        # Blocked counters
        if blocked_by == "rate_limit":
            cls._analytics["blocked_by_rate_limit"] += 1
        elif blocked_by == "circular":
            cls._analytics["blocked_by_circular"] += 1

    @classmethod
    def get_analytics_summary(cls) -> Dict[str, Any]:
        """Return an aggregate summary of handoff analytics.

        Returns:
            Dict with total_handoffs, successful_handoffs, failed_handoffs,
            success_rate, avg_processing_time_ms, handoffs_by_route,
            handoffs_by_hour, peak_hour, blocked_by_rate_limit,
            blocked_by_circular.
        """
        total = cls._analytics["total_handoffs"]
        successful = cls._analytics["successful_handoffs"]
        failed = cls._analytics["failed_handoffs"]
        times = cls._analytics["processing_times_ms"]
        avg_time = sum(times) / len(times) if times else 0.0
        by_hour = cls._analytics["handoffs_by_hour"]
        peak_hour = max(by_hour, key=by_hour.get) if total > 0 else 0

        return {
            "total_handoffs": total,
            "successful_handoffs": successful,
            "failed_handoffs": failed,
            "success_rate": round(successful / total, 4) if total > 0 else 0.0,
            "avg_processing_time_ms": round(avg_time, 2),
            "handoffs_by_route": dict(cls._analytics["handoffs_by_route"]),
            "handoffs_by_hour": dict(by_hour),
            "peak_hour": peak_hour,
            "blocked_by_rate_limit": cls._analytics["blocked_by_rate_limit"],
            "blocked_by_circular": cls._analytics["blocked_by_circular"],
        }

    @classmethod
    def reset_analytics(cls) -> None:
        """Clear all analytics and outcome data (useful for testing)."""
        cls._analytics = {
            "total_handoffs": 0,
            "successful_handoffs": 0,
            "failed_handoffs": 0,
            "processing_times_ms": [],
            "handoffs_by_route": {},
            "handoffs_by_hour": {h: 0 for h in range(24)},
            "blocked_by_rate_limit": 0,
            "blocked_by_circular": 0,
        }
        cls._active_handoffs = {}
        cls._handoff_outcomes = {}
        cls._handoff_history = {}

    @classmethod
    def seed_historical_data(
        cls,
        num_samples: int = 20,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Seed handoff outcome history with realistic sample data.

        Populates ``_handoff_outcomes`` with enough data points for each
        route so that ``get_learned_adjustments`` can compute meaningful
        threshold adjustments (requires >= MIN_LEARNING_SAMPLES).

        The generated data reflects realistic Rancho Cucamonga market
        patterns:
        - lead->buyer: ~80% success rate (most common, well-qualified)
        - lead->seller: ~70% success rate (moderate qualification)
        - buyer->seller: ~60% success rate (cross-intent, harder)
        - seller->buyer: ~75% success rate (sell-first-then-buy)

        Args:
            num_samples: Number of outcome records per route
                         (default 20, must be >= MIN_LEARNING_SAMPLES).
            seed: Optional random seed for reproducible data generation.

        Returns:
            Dict summarizing what was seeded:
                routes_seeded, samples_per_route, total_records,
                per_route_success_rates.

        Raises:
            ValueError: If num_samples < MIN_LEARNING_SAMPLES.
        """
        if num_samples < cls.MIN_LEARNING_SAMPLES:
            raise ValueError(f"num_samples must be >= {cls.MIN_LEARNING_SAMPLES}, got {num_samples}")

        rng = random.Random(seed)
        now = time.time()

        # Route configurations: (source, target, success_probability)
        route_configs = [
            ("lead", "buyer", 0.80),
            ("lead", "seller", 0.70),
            ("buyer", "seller", 0.60),
            ("seller", "buyer", 0.75),
        ]

        per_route_rates: Dict[str, float] = {}
        total_records = 0

        for source, target, success_prob in route_configs:
            pair_key = f"{source}->{target}"
            if pair_key not in cls._handoff_outcomes:
                cls._handoff_outcomes[pair_key] = []

            successes = 0
            for i in range(num_samples):
                is_success = rng.random() < success_prob
                if is_success:
                    outcome = "successful"
                    successes += 1
                else:
                    # Distribute failures across failure types
                    outcome = rng.choice(["failed", "reverted", "timeout"])

                # Spread timestamps over the last 7 days
                hours_ago = rng.uniform(0, 168)  # 7 days in hours
                ts = now - (hours_ago * 3600)

                cls._handoff_outcomes[pair_key].append(
                    {
                        "contact_id": f"seed_{source}_{target}_{i:03d}",
                        "outcome": outcome,
                        "timestamp": ts,
                        "metadata": {"seeded": True, "batch": "historical_seed"},
                    }
                )
                total_records += 1

            per_route_rates[pair_key] = round(successes / num_samples, 4)

        logger.info(
            "Seeded %d handoff outcome records across %d routes (per_route=%d)",
            total_records,
            len(route_configs),
            num_samples,
        )

        return {
            "routes_seeded": [f"{s}->{t}" for s, t, _ in route_configs],
            "samples_per_route": num_samples,
            "total_records": total_records,
            "per_route_success_rates": per_route_rates,
        }

    @classmethod
    def export_seed_data(cls) -> List[Dict[str, Any]]:
        """Export current handoff outcome history as a JSON-serializable list.

        Returns:
            List of dicts, each containing route, contact_id, outcome,
            timestamp, and metadata for one handoff outcome record.
        """
        records: List[Dict[str, Any]] = []
        for route, outcomes in cls._handoff_outcomes.items():
            for outcome in outcomes:
                records.append({
                    "route": route,
                    "contact_id": outcome.get("contact_id", ""),
                    "outcome": outcome["outcome"],
                    "timestamp": outcome["timestamp"],
                    "metadata": outcome.get("metadata", {}),
                })
        logger.info("Exported %d handoff outcome records", len(records))
        return records

    @classmethod
    def import_seed_data(cls, records: List[Dict[str, Any]]) -> int:
        """Import handoff outcome records from a list of dicts.

        Args:
            records: List of dicts with route, contact_id, outcome,
                     timestamp, and optional metadata.

        Returns:
            Number of records imported.
        """
        imported = 0
        for record in records:
            route = record["route"]
            if route not in cls._handoff_outcomes:
                cls._handoff_outcomes[route] = []
            cls._handoff_outcomes[route].append({
                "contact_id": record.get("contact_id", ""),
                "outcome": record["outcome"],
                "timestamp": record["timestamp"],
                "metadata": record.get("metadata", {}),
            })
            imported += 1
        logger.info("Imported %d handoff outcome records", imported)
        return imported

    async def persist_seed_data(self) -> int:
        """Persist current in-memory handoff outcomes to the database.

        Requires a repository to be set via ``set_repository()``.
        Iterates over all ``_handoff_outcomes`` and writes each record.

        Returns:
            Number of records persisted.
        """
        if self._repository is None:
            return 0

        persisted = 0
        for route, outcomes in self._handoff_outcomes.items():
            parts = route.split("->")
            if len(parts) != 2:
                continue
            source_bot, target_bot = parts

            for record in outcomes:
                try:
                    await self._repository.save_handoff_outcome(
                        contact_id=record.get("contact_id", ""),
                        source_bot=source_bot,
                        target_bot=target_bot,
                        outcome=record["outcome"],
                        timestamp=record["timestamp"],
                        metadata=record.get("metadata"),
                    )
                    persisted += 1
                except Exception as exc:
                    logger.debug("Failed to persist seed outcome: %s", exc)

        logger.info("Persisted %d handoff outcome records to database", persisted)
        return persisted

    @trace_operation("jorge.handoff", "evaluate_handoff")
    async def evaluate_handoff(
        self,
        current_bot: str,
        contact_id: str,
        conversation_history: List[Dict],
        intent_signals: Dict[str, Any],
    ) -> Optional[HandoffDecision]:
        """Evaluate whether a handoff is needed based on intent signals.

        Incorporates learned threshold adjustments from historical handoff
        outcomes and intent signals extracted from conversation history.
        Performs circular handoff prevention checks before returning a decision.
        """
        buyer_score = intent_signals.get("buyer_intent_score", 0.0)
        seller_score = intent_signals.get("seller_intent_score", 0.0)
        detected_phrases = intent_signals.get("detected_intent_phrases", [])

        # Boost scores with signals extracted from conversation history
        history_signals: Dict[str, float] = {}
        if conversation_history:
            history_signals = self.extract_intent_signals_from_history(conversation_history)
            # Blend history signals: add half of history confidence to current
            if "buyer_intent" in history_signals:
                buyer_score = min(1.0, buyer_score + history_signals["buyer_intent"] * 0.5)
            if "seller_intent" in history_signals:
                seller_score = min(1.0, seller_score + history_signals["seller_intent"] * 0.5)

        # Determine candidate target and score
        if current_bot in ("lead", "seller") and buyer_score > seller_score:
            target = "buyer"
            score = buyer_score
        elif current_bot in ("lead", "buyer") and seller_score > buyer_score:
            target = "seller"
            score = seller_score
        else:
            return None

        # No self-handoff
        if target == current_bot:
            return None

        threshold = self.THRESHOLDS.get((current_bot, target))
        if threshold is None:
            return None

        # Apply learned adjustment from historical handoff outcomes
        learned = self.get_learned_adjustments(current_bot, target)
        adjusted_threshold = max(0.0, min(1.0, threshold + learned["adjustment"]))

        if score < adjusted_threshold:
            return None

        # Check circular prevention before returning decision
        self._cleanup_old_entries()
        is_blocked, block_reason = self._check_circular_prevention(contact_id, current_bot, target)
        if is_blocked:
            logger.info(f"Handoff blocked by circular prevention: {block_reason}")
            return None

        reason = f"{target}_intent_detected"
        return HandoffDecision(
            source_bot=current_bot,
            target_bot=target,
            reason=reason,
            confidence=score,
            context={
                "contact_id": contact_id,
                "detected_phrases": detected_phrases,
                "conversation_turns": len(conversation_history),
                "learned_adjustment": learned["adjustment"],
                "learned_success_rate": learned["success_rate"],
                "learned_sample_size": learned["sample_size"],
                "history_signals": history_signals,
            },
        )

    @trace_operation("jorge.handoff", "execute_handoff")
    async def execute_handoff(
        self,
        decision: HandoffDecision,
        contact_id: str,
        location_id: str = "",
    ) -> List[Dict[str, Any]]:
        """Generate GHL action dicts to execute the handoff."""
        start_time = time.time()
        route = f"{decision.source_bot}->{decision.target_bot}"

        # Conflict resolution: prevent concurrent handoffs for the same contact
        if not self._acquire_handoff_lock(contact_id):
            return [
                {
                    "handoff_executed": False,
                    "reason": "Concurrent handoff in progress for this contact",
                }
            ]

        try:
            self._cleanup_old_entries()

            circular_reason = self._check_circular_handoff(contact_id, decision.source_bot, decision.target_bot)
            if circular_reason:
                logger.warning(circular_reason)
                self._record_analytics(route, start_time, success=False, blocked_by="circular")
                return [{"handoff_executed": False, "reason": circular_reason}]

            rate_reason = self._check_rate_limit(contact_id)
            if rate_reason:
                logger.warning(rate_reason)
                self._record_analytics(route, start_time, success=False, blocked_by="rate_limit")
                return [{"handoff_executed": False, "reason": rate_reason}]

            actions: List[Dict[str, Any]] = []

            source_tag = self.TAG_MAP.get(decision.source_bot)
            target_tag = self.TAG_MAP.get(decision.target_bot)

            # Remove source bot's activation tag
            if source_tag:
                actions.append({"type": "remove_tag", "tag": source_tag})

            # Add target bot's activation tag
            if target_tag:
                actions.append({"type": "add_tag", "tag": target_tag})

            # Add tracking tag
            tracking_tag = f"Handoff-{decision.source_bot.capitalize()}-to-{decision.target_bot.capitalize()}"
            actions.append({"type": "add_tag", "tag": tracking_tag})

            # Log analytics event
            if self.analytics_service:
                try:
                    await self.analytics_service.track_event(
                        event_type="jorge_handoff",
                        location_id=location_id,
                        contact_id=contact_id,
                        data={
                            "source_bot": decision.source_bot,
                            "target_bot": decision.target_bot,
                            "reason": decision.reason,
                            "confidence": decision.confidence,
                            "detected_phrases": decision.context.get("detected_phrases", []),
                        },
                    )
                except Exception as e:
                    logger.warning(f"Failed to log handoff analytics for {contact_id}: {e}")

            logger.info(
                f"Handoff: {decision.source_bot} -> {decision.target_bot} "
                f"for contact {contact_id} (confidence={decision.confidence:.2f}, "
                f"reason={decision.reason})"
            )

            self._record_handoff(contact_id, decision.source_bot, decision.target_bot)
            self._record_analytics(route, start_time, success=True)

            return actions
        finally:
            self._release_handoff_lock(contact_id)

    @classmethod
    def extract_intent_signals(cls, message: str) -> Dict[str, Any]:
        """Extract intent signals from a user message for handoff evaluation."""
        buyer_matches = []
        for pattern in cls.BUYER_INTENT_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                buyer_matches.append(pattern)

        seller_matches = []
        for pattern in cls.SELLER_INTENT_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                seller_matches.append(pattern)

        # Score: each pattern match adds ~0.3, capped at 1.0
        buyer_score = min(1.0, len(buyer_matches) * 0.3) if buyer_matches else 0.0
        seller_score = min(1.0, len(seller_matches) * 0.3) if seller_matches else 0.0

        # Collect human-readable phrases
        detected = []
        if buyer_matches:
            detected.append("buyer intent detected")
        if seller_matches:
            detected.append("seller intent detected")

        return {
            "buyer_intent_score": buyer_score,
            "seller_intent_score": seller_score,
            "detected_intent_phrases": detected,
        }

    @classmethod
    def record_handoff_outcome(
        cls,
        contact_id: str,
        source_bot: str,
        target_bot: str,
        outcome: str,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        _repository: Any = None,
    ) -> None:
        """Record the outcome of a handoff for pattern learning.

        If a repository is attached (via ``_repository`` kwarg or
        instance-level ``_repository``), the outcome is also persisted
        to PostgreSQL (fire-and-forget; DB errors are logged, not raised).

        Args:
            contact_id: The contact that was handed off.
            source_bot: Bot that initiated the handoff.
            target_bot: Bot that received the handoff.
            outcome: One of "successful", "failed", "reverted", "timeout".
            metadata: Optional extra context about the outcome.
            _repository: Optional repository for DB write-through.
        """
        valid_outcomes = {"successful", "failed", "reverted", "timeout"}
        if outcome not in valid_outcomes:
            logger.warning(
                f"Invalid handoff outcome '{outcome}' for contact {contact_id}. Expected one of {valid_outcomes}"
            )
            return

        pair_key = f"{source_bot}->{target_bot}"
        if pair_key not in cls._handoff_outcomes:
            cls._handoff_outcomes[pair_key] = []

        ts = time.time()
        record = {
            "contact_id": contact_id,
            "outcome": outcome,
            "timestamp": ts,
            "metadata": metadata or {},
        }
        cls._handoff_outcomes[pair_key].append(record)

        # Write-through to DB if repository provided
        repo = _repository
        if repo is not None:
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(
                        repo.save_handoff_outcome(
                            contact_id=contact_id,
                            source_bot=source_bot,
                            target_bot=target_bot,
                            outcome=outcome,
                            timestamp=ts,
                            metadata=metadata,
                        )
                    )
                else:
                    loop.run_until_complete(
                        repo.save_handoff_outcome(
                            contact_id=contact_id,
                            source_bot=source_bot,
                            target_bot=target_bot,
                            outcome=outcome,
                            timestamp=ts,
                            metadata=metadata,
                        )
                    )
            except RuntimeError:
                logger.debug("No event loop for handoff outcome DB write-through")

        logger.info(f"Recorded handoff outcome: {pair_key} for contact {contact_id} -> {outcome}")

    @classmethod
    def get_learned_adjustments(cls, source_bot: str, target_bot: str) -> Dict[str, Any]:
        """Calculate confidence threshold adjustments from historical outcomes.

        Returns a dict with:
            adjustment: float threshold delta (negative = easier handoff)
            success_rate: float between 0.0-1.0
            sample_size: int number of data points
        """
        pair_key = f"{source_bot}->{target_bot}"
        outcomes = cls._handoff_outcomes.get(pair_key, [])
        sample_size = len(outcomes)

        if sample_size < cls.MIN_LEARNING_SAMPLES:
            return {
                "adjustment": 0.0,
                "success_rate": 0.0,
                "sample_size": sample_size,
            }

        successful_count = sum(1 for o in outcomes if o["outcome"] == "successful")
        success_rate = successful_count / sample_size

        # High success rate -> lower threshold (easier handoffs)
        # Low success rate -> raise threshold (harder handoffs)
        if success_rate > 0.8:
            adjustment = -0.05
        elif success_rate < 0.5:
            adjustment = 0.1
        else:
            adjustment = 0.0

        return {
            "adjustment": adjustment,
            "success_rate": round(success_rate, 4),
            "sample_size": sample_size,
        }

    @classmethod
    def extract_intent_signals_from_history(cls, conversation_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Scan recent conversation history for intent patterns.

        Examines up to the last 5 messages and aggregates buyer/seller
        intent signals with confidence scores.

        Args:
            conversation_history: List of message dicts, each expected to
                have a "message" or "content" key with the text.

        Returns:
            Dict mapping signal names to confidence scores, e.g.:
            {"buyer_intent": 0.6, "seller_intent": 0.3}
        """
        recent = conversation_history[-5:] if conversation_history else []
        buyer_total = 0
        seller_total = 0

        for msg in recent:
            text = msg.get("message") or msg.get("content") or ""
            if not isinstance(text, str) or not text.strip():
                continue

            for pattern in cls.BUYER_INTENT_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    buyer_total += 1

            for pattern in cls.SELLER_INTENT_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    seller_total += 1

        # Each pattern match adds 0.2 confidence, capped at 1.0
        signals: Dict[str, float] = {}
        if buyer_total > 0:
            signals["buyer_intent"] = min(1.0, round(buyer_total * 0.2, 2))
        if seller_total > 0:
            signals["seller_intent"] = min(1.0, round(seller_total * 0.2, 2))

        return signals
