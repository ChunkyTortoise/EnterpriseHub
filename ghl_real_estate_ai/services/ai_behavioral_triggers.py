#!/usr/bin/env python3
"""
⚡ AI-Powered Behavioral Triggers Service
=========================================

Event-based automation system that detects behavioral patterns
and triggers appropriate actions.

Trigger Types:
1. Engagement Drop Detection
2. High Engagement Spike
3. Price Sensitivity Signals
4. Decision-Making Indicators
5. Abandonment Detection

Author: Mu Team - Behavioral Triggers Builder
Date: 2026-01-05
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class TriggerType(Enum):
    """Types of behavioral triggers"""

    ENGAGEMENT_DROP = "engagement_drop"
    HIGH_ENGAGEMENT = "high_engagement_spike"
    PRICE_SENSITIVITY = "price_sensitivity"
    DECISION_SIGNALS = "decision_signals"
    ABANDONMENT = "abandonment"


class TriggerPriority(Enum):
    """Trigger priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class BehavioralEvent:
    """Behavioral event data"""

    event_type: str
    lead_id: str
    timestamp: datetime
    data: Dict
    source: str


@dataclass
class FiredTrigger:
    """Triggered action"""

    trigger_type: TriggerType
    lead_id: str
    priority: TriggerPriority
    reason: str
    recommended_actions: List[str]
    data: Dict
    fired_at: datetime


class BehavioralTriggerEngine:
    """
    Behavioral Trigger Detection and Execution Engine

    Monitors user behavior and automatically triggers
    appropriate actions based on detected patterns.
    """

    def __init__(self):
        self.trigger_rules = self._initialize_trigger_rules()
        self.event_history = []

    def _initialize_trigger_rules(self) -> Dict:
        """Initialize trigger detection rules"""
        return {
            TriggerType.ENGAGEMENT_DROP: {
                "condition": "no_interaction_days",
                "threshold": 7,
                "priority": TriggerPriority.HIGH,
                "actions": [
                    "Send re-engagement email campaign",
                    "Trigger SMS follow-up",
                    "Add to high-touch nurture sequence",
                ],
            },
            TriggerType.HIGH_ENGAGEMENT: {
                "condition": "multiple_actions_short_time",
                "threshold": 5,  # 5 actions in 2 hours
                "time_window": 2,  # hours
                "priority": TriggerPriority.CRITICAL,
                "actions": [
                    "Immediate agent notification",
                    "Schedule callback within 1 hour",
                    "Send hot lead alert",
                ],
            },
            TriggerType.PRICE_SENSITIVITY: {
                "condition": "repeated_lower_price_views",
                "threshold": 3,
                "priority": TriggerPriority.MEDIUM,
                "actions": [
                    "Adjust property recommendations downward",
                    "Send financing options info",
                    "Provide budget-friendly alternatives",
                ],
            },
            TriggerType.DECISION_SIGNALS: {
                "condition": "calculator_plus_viewings",
                "priority": TriggerPriority.HIGH,
                "actions": [
                    "Trigger urgency sequence",
                    "Send limited-time offer",
                    "Schedule property tour",
                ],
            },
            TriggerType.ABANDONMENT: {
                "condition": "incomplete_action",
                "time_threshold": 24,  # hours
                "priority": TriggerPriority.MEDIUM,
                "actions": [
                    "Send completion reminder",
                    "Offer assistance",
                    "Provide direct contact link",
                ],
            },
        }

    def detect_triggers(
        self, lead_id: str, recent_events: List[BehavioralEvent]
    ) -> List[FiredTrigger]:
        """
        Detect behavioral triggers from recent events

        Args:
            lead_id: Lead identifier
            recent_events: List of recent behavioral events

        Returns:
            List of fired triggers with recommended actions
        """
        fired_triggers = []

        # Check for engagement drop
        engagement_trigger = self._check_engagement_drop(lead_id, recent_events)
        if engagement_trigger:
            fired_triggers.append(engagement_trigger)

        # Check for high engagement spike
        spike_trigger = self._check_high_engagement_spike(lead_id, recent_events)
        if spike_trigger:
            fired_triggers.append(spike_trigger)

        # Check for price sensitivity
        price_trigger = self._check_price_sensitivity(lead_id, recent_events)
        if price_trigger:
            fired_triggers.append(price_trigger)

        # Check for decision signals
        decision_trigger = self._check_decision_signals(lead_id, recent_events)
        if decision_trigger:
            fired_triggers.append(decision_trigger)

        # Check for abandonment
        abandon_trigger = self._check_abandonment(lead_id, recent_events)
        if abandon_trigger:
            fired_triggers.append(abandon_trigger)

        return fired_triggers

    def _check_engagement_drop(
        self, lead_id: str, events: List[BehavioralEvent]
    ) -> Optional[FiredTrigger]:
        """Check for engagement drop pattern"""
        if not events:
            return None

        # Get last interaction
        last_event = max(events, key=lambda e: e.timestamp)
        days_since_last = (datetime.now() - last_event.timestamp).days

        rule = self.trigger_rules[TriggerType.ENGAGEMENT_DROP]

        if days_since_last >= rule["threshold"]:
            return FiredTrigger(
                trigger_type=TriggerType.ENGAGEMENT_DROP,
                lead_id=lead_id,
                priority=rule["priority"],
                reason=f"No interaction for {days_since_last} days",
                recommended_actions=rule["actions"],
                data={"days_inactive": days_since_last},
                fired_at=datetime.now(),
            )

        return None

    def _check_high_engagement_spike(
        self, lead_id: str, events: List[BehavioralEvent]
    ) -> Optional[FiredTrigger]:
        """Check for high engagement spike"""
        rule = self.trigger_rules[TriggerType.HIGH_ENGAGEMENT]
        time_window = timedelta(hours=rule["time_window"])
        now = datetime.now()

        # Count recent events
        recent_events = [e for e in events if (now - e.timestamp) <= time_window]

        if len(recent_events) >= rule["threshold"]:
            return FiredTrigger(
                trigger_type=TriggerType.HIGH_ENGAGEMENT,
                lead_id=lead_id,
                priority=rule["priority"],
                reason=f"{len(recent_events)} actions in {rule['time_window']} hours",
                recommended_actions=rule["actions"],
                data={
                    "event_count": len(recent_events),
                    "time_window": rule["time_window"],
                    "events": [e.event_type for e in recent_events],
                },
                fired_at=datetime.now(),
            )

        return None

    def _check_price_sensitivity(
        self, lead_id: str, events: List[BehavioralEvent]
    ) -> Optional[FiredTrigger]:
        """Check for price sensitivity signals"""
        rule = self.trigger_rules[TriggerType.PRICE_SENSITIVITY]

        # Get property view events
        property_views = [
            e for e in events if e.event_type == "property_view" and "price" in e.data
        ]

        if len(property_views) < rule["threshold"]:
            return None

        # Check if viewing progressively lower-priced properties
        recent_views = sorted(property_views[-5:], key=lambda e: e.timestamp)
        prices = [e.data["price"] for e in recent_views]

        if len(prices) >= 3:
            # Check for downward trend
            avg_first_half = sum(prices[:2]) / 2
            avg_second_half = sum(prices[-2:]) / 2

            if avg_second_half < avg_first_half * 0.9:  # 10% lower
                return FiredTrigger(
                    trigger_type=TriggerType.PRICE_SENSITIVITY,
                    lead_id=lead_id,
                    priority=rule["priority"],
                    reason="Viewing progressively lower-priced properties",
                    recommended_actions=rule["actions"],
                    data={
                        "price_trend": "downward",
                        "avg_decrease": (avg_first_half - avg_second_half)
                        / avg_first_half
                        * 100,
                        "viewed_prices": prices,
                    },
                    fired_at=datetime.now(),
                )

        return None

    def _check_decision_signals(
        self, lead_id: str, events: List[BehavioralEvent]
    ) -> Optional[FiredTrigger]:
        """Check for decision-making signals"""
        rule = self.trigger_rules[TriggerType.DECISION_SIGNALS]

        recent_24h = [
            e for e in events if (datetime.now() - e.timestamp) <= timedelta(hours=24)
        ]

        # Check for calculator usage
        used_calculator = any(e.event_type == "calculator_use" for e in recent_24h)

        # Check for multiple property views
        property_views = [e for e in recent_24h if e.event_type == "property_view"]

        # Check for saved properties
        saved_properties = any(e.event_type == "property_save" for e in recent_24h)

        # Decision signal: calculator + multiple views OR saves
        if used_calculator and (len(property_views) >= 3 or saved_properties):
            return FiredTrigger(
                trigger_type=TriggerType.DECISION_SIGNALS,
                lead_id=lead_id,
                priority=rule["priority"],
                reason="Strong buying signals detected",
                recommended_actions=rule["actions"],
                data={
                    "calculator_used": used_calculator,
                    "property_views": len(property_views),
                    "properties_saved": saved_properties,
                },
                fired_at=datetime.now(),
            )

        return None

    def _check_abandonment(
        self, lead_id: str, events: List[BehavioralEvent]
    ) -> Optional[FiredTrigger]:
        """Check for abandonment patterns"""
        rule = self.trigger_rules[TriggerType.ABANDONMENT]

        # Look for incomplete actions
        incomplete_events = [
            e
            for e in events
            if e.event_type
            in ["form_started", "tour_request_started", "application_started"]
            and not e.data.get("completed", False)
        ]

        for event in incomplete_events:
            hours_since = (datetime.now() - event.timestamp).total_seconds() / 3600

            if hours_since >= rule["time_threshold"]:
                return FiredTrigger(
                    trigger_type=TriggerType.ABANDONMENT,
                    lead_id=lead_id,
                    priority=rule["priority"],
                    reason=f"Abandoned {event.event_type} {hours_since:.0f}h ago",
                    recommended_actions=rule["actions"],
                    data={
                        "abandoned_action": event.event_type,
                        "hours_since": hours_since,
                        "completion_percentage": event.data.get("progress", 0),
                    },
                    fired_at=datetime.now(),
                )

        return None

    def execute_trigger(self, trigger: FiredTrigger) -> Dict:
        """
        Execute triggered actions

        Args:
            trigger: Fired trigger to execute

        Returns:
            Execution result
        """
        # In production, this would integrate with:
        # - Email service
        # - SMS service
        # - Workflow automation
        # - Agent notification system

        return {
            "trigger_id": f"{trigger.trigger_type.value}_{trigger.lead_id}_{int(trigger.fired_at.timestamp())}",
            "status": "queued",
            "actions_queued": trigger.recommended_actions,
            "priority": trigger.priority.value,
            "estimated_execution": "within 5 minutes",
        }

    def get_trigger_summary(self, triggers: List[FiredTrigger]) -> Dict:
        """Generate summary of fired triggers"""
        return {
            "total_triggers": len(triggers),
            "by_type": {
                trigger_type.value: len(
                    [t for t in triggers if t.trigger_type == trigger_type]
                )
                for trigger_type in TriggerType
            },
            "by_priority": {
                priority.value: len([t for t in triggers if t.priority == priority])
                for priority in TriggerPriority
            },
            "critical_count": len(
                [t for t in triggers if t.priority == TriggerPriority.CRITICAL]
            ),
        }


# Example usage
if __name__ == "__main__":
    engine = BehavioralTriggerEngine()

    # Simulate events
    now = datetime.now()
    events = [
        BehavioralEvent(
            "property_view",
            "lead_456",
            now - timedelta(hours=1),
            {"price": 500000},
            "web",
        ),
        BehavioralEvent(
            "property_view",
            "lead_456",
            now - timedelta(minutes=45),
            {"price": 450000},
            "web",
        ),
        BehavioralEvent(
            "calculator_use",
            "lead_456",
            now - timedelta(minutes=30),
            {"type": "mortgage"},
            "web",
        ),
        BehavioralEvent(
            "property_view",
            "lead_456",
            now - timedelta(minutes=15),
            {"price": 420000},
            "web",
        ),
        BehavioralEvent(
            "property_save",
            "lead_456",
            now - timedelta(minutes=5),
            {"property_id": "prop_123"},
            "web",
        ),
    ]

    # Detect triggers
    triggers = engine.detect_triggers("lead_456", events)

    print(f"\n⚡ Behavioral Triggers Detected: {len(triggers)}")
    for trigger in triggers:
        print(f"\n🎯 {trigger.trigger_type.value.upper()}")
        print(f"   Priority: {trigger.priority.value}")
        print(f"   Reason: {trigger.reason}")
        print(f"   Actions:")
        for action in trigger.recommended_actions:
            print(f"   • {action}")
