"""
Behavioral Trigger Engine
Watches lead behavior and triggers actions automatically based on patterns

Feature 11: Behavioral Trigger Engine
Real-time behavior monitoring with AI-powered pattern detection.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List


class BehaviorType(Enum):
    """Types of trackable behaviors"""

    PROPERTY_VIEW = "property_view"
    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    SMS_RESPONSE = "sms_response"
    WEBSITE_VISIT = "website_visit"
    FORM_SUBMIT = "form_submit"
    CALL_MADE = "call_made"
    DOCUMENT_DOWNLOAD = "document_download"


class TriggerAction(Enum):
    """Actions that can be triggered"""

    SEND_MESSAGE = "send_message"
    NOTIFY_AGENT = "notify_agent"
    UPDATE_SCORE = "update_score"
    ADD_TAG = "add_tag"
    ASSIGN_AGENT = "assign_agent"
    CREATE_TASK = "create_task"
    START_WORKFLOW = "start_workflow"


@dataclass
class BehaviorEvent:
    """Single behavior event"""

    event_id: str
    lead_id: str
    behavior_type: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TriggerRule:
    """Behavioral trigger rule"""

    rule_id: str
    name: str
    description: str
    pattern: Dict[str, Any]  # Pattern to match
    action: str  # Action to take
    action_config: Dict[str, Any]
    enabled: bool = True
    priority: int = 5  # 1-10, higher = more important


class BehavioralTriggerEngine:
    """Engine for detecting behavioral patterns and triggering actions"""

    def __init__(self):
        self.behavior_history: Dict[str, List[BehaviorEvent]] = {}
        self.trigger_rules: List[TriggerRule] = []
        self.triggered_actions: List[Dict] = []
        self._load_default_rules()

    def _load_default_rules(self):
        """Load pre-configured trigger rules"""

        # High-intent pattern: Views property 3+ times in 24h
        self.add_trigger_rule(
            TriggerRule(
                rule_id="high_intent_viewing",
                name="High Intent - Multiple Views",
                description="Lead viewed same property 3+ times in 24 hours",
                pattern={
                    "behavior": BehaviorType.PROPERTY_VIEW.value,
                    "count": 3,
                    "timeframe_hours": 24,
                    "same_property": True,
                },
                action=TriggerAction.SEND_MESSAGE.value,
                action_config={
                    "message_type": "sms",
                    "template": "high_intent_video",
                    "priority": "high",
                },
                priority=9,
            )
        )

        # Email engagement pattern
        self.add_trigger_rule(
            TriggerRule(
                rule_id="email_engaged",
                name="Email Engaged But No Reply",
                description="Opened email but didn't respond",
                pattern={
                    "behavior": BehaviorType.EMAIL_OPEN.value,
                    "count": 1,
                    "no_response_hours": 24,
                },
                action=TriggerAction.SEND_MESSAGE.value,
                action_config={"message_type": "sms", "template": "follow_up_nudge"},
                priority=6,
            )
        )

        # Price sensitivity pattern
        self.add_trigger_rule(
            TriggerRule(
                rule_id="price_sensitivity",
                name="Price Sensitivity Detected",
                description="Clicked price but closed page",
                pattern={
                    "sequence": [
                        BehaviorType.EMAIL_CLICK.value,
                        BehaviorType.WEBSITE_VISIT.value,
                    ],
                    "metadata_contains": {"clicked": "price"},
                    "timeframe_minutes": 5,
                    "no_further_action": True,
                },
                action=TriggerAction.SEND_MESSAGE.value,
                action_config={
                    "message_type": "email",
                    "template": "financing_options",
                },
                priority=8,
            )
        )

        # Night owl pattern
        self.add_trigger_rule(
            TriggerRule(
                rule_id="night_owl",
                name="Night Owl - Motivated Buyer",
                description="Visits website late at night on weekend",
                pattern={
                    "behavior": BehaviorType.WEBSITE_VISIT.value,
                    "time_of_day": "late_night",  # 10 PM - 2 AM
                    "day_of_week": "weekend",
                    "count": 1,
                },
                action=TriggerAction.NOTIFY_AGENT.value,
                action_config={
                    "priority": "high",
                    "message": "Motivated buyer - viewing late night on weekend",
                    "schedule_follow_up": "next_morning",
                },
                priority=7,
            )
        )

        # Comparison shopping pattern
        self.add_trigger_rule(
            TriggerRule(
                rule_id="comparison_shopping",
                name="Comparison Shopping",
                description="Viewing multiple similar properties",
                pattern={
                    "behavior": BehaviorType.PROPERTY_VIEW.value,
                    "count": 3,
                    "timeframe_hours": 2,
                    "different_properties": True,
                    "similar_features": True,
                },
                action=TriggerAction.SEND_MESSAGE.value,
                action_config={"message_type": "email", "template": "comparison_guide"},
                priority=7,
            )
        )

        # Churn risk pattern
        self.add_trigger_rule(
            TriggerRule(
                rule_id="churn_risk",
                name="Churn Risk - Cooling Down",
                description="Previously active, now no activity for 7 days",
                pattern={
                    "previous_activity": "high",
                    "no_activity_days": 7,
                    "declining_engagement": True,
                },
                action=TriggerAction.START_WORKFLOW.value,
                action_config={"workflow_id": "reengagement_sequence"},
                priority=8,
            )
        )

        # Hot lead pattern
        self.add_trigger_rule(
            TriggerRule(
                rule_id="hot_lead_signals",
                name="Hot Lead - Multiple Signals",
                description="Multiple high-intent behaviors in short time",
                pattern={
                    "behaviors": [
                        BehaviorType.PROPERTY_VIEW.value,
                        BehaviorType.EMAIL_OPEN.value,
                        BehaviorType.DOCUMENT_DOWNLOAD.value,
                    ],
                    "timeframe_hours": 4,
                    "minimum_actions": 3,
                },
                action=TriggerAction.NOTIFY_AGENT.value,
                action_config={
                    "priority": "urgent",
                    "assign_to": "senior_agent",
                    "message": "HOT LEAD: Multiple high-intent signals",
                },
                priority=10,
            )
        )

    def track_behavior(self, lead_id: str, behavior_type: str, metadata: Dict = None) -> List[Dict]:
        """Track a behavior and check for triggered patterns"""

        # Create behavior event
        event = BehaviorEvent(
            event_id=f"evt_{datetime.utcnow().timestamp()}",
            lead_id=lead_id,
            behavior_type=behavior_type,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )

        # Store in history
        if lead_id not in self.behavior_history:
            self.behavior_history[lead_id] = []
        self.behavior_history[lead_id].append(event)

        # Check for pattern matches
        triggered = self._check_patterns(lead_id)

        return triggered

    def _check_patterns(self, lead_id: str) -> List[Dict]:
        """Check if any trigger patterns are matched"""

        triggered_actions = []
        lead_history = self.behavior_history.get(lead_id, [])

        if not lead_history:
            return triggered_actions

        # Sort rules by priority
        sorted_rules = sorted(self.trigger_rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            if not rule.enabled:
                continue

            if self._pattern_matches(rule.pattern, lead_history):
                action = self._execute_trigger(lead_id, rule)
                triggered_actions.append(action)

        return triggered_actions

    def _pattern_matches(self, pattern: Dict, history: List[BehaviorEvent]) -> bool:
        """Check if behavior pattern matches"""

        behavior_type = pattern.get("behavior")
        count_required = pattern.get("count", 1)
        timeframe_hours = pattern.get("timeframe_hours")

        if not behavior_type:
            return False

        # Filter events by behavior type
        matching_events = [e for e in history if e.behavior_type == behavior_type]

        # Apply timeframe filter
        if timeframe_hours:
            cutoff = datetime.utcnow() - timedelta(hours=timeframe_hours)
            matching_events = [e for e in matching_events if datetime.fromisoformat(e.timestamp) > cutoff]

        # Check count
        if len(matching_events) < count_required:
            return False

        # Check for same property
        if pattern.get("same_property"):
            property_ids = [e.metadata.get("property_id") for e in matching_events]
            if len(set(property_ids)) > 1:
                return False

        # Check for different properties
        if pattern.get("different_properties"):
            property_ids = [e.metadata.get("property_id") for e in matching_events]
            if len(set(property_ids)) < count_required:
                return False

        return True

    def _execute_trigger(self, lead_id: str, rule: TriggerRule) -> Dict:
        """Execute triggered action"""

        action_result = {
            "triggered_at": datetime.utcnow().isoformat(),
            "lead_id": lead_id,
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "action": rule.action,
            "config": rule.action_config,
            "status": "executed",
        }

        self.triggered_actions.append(action_result)
        return action_result

    def add_trigger_rule(self, rule: TriggerRule):
        """Add a new trigger rule"""
        self.trigger_rules.append(rule)

    def get_lead_behavior_summary(self, lead_id: str) -> Dict:
        """Get behavior summary for a lead"""

        history = self.behavior_history.get(lead_id, [])

        if not history:
            return {"lead_id": lead_id, "total_events": 0}

        # Count by behavior type
        behavior_counts = {}
        for event in history:
            behavior_counts[event.behavior_type] = behavior_counts.get(event.behavior_type, 0) + 1

        # Calculate engagement score
        engagement_score = min(len(history) * 5, 100)

        return {
            "lead_id": lead_id,
            "total_events": len(history),
            "behavior_counts": behavior_counts,
            "engagement_score": engagement_score,
            "first_activity": history[0].timestamp,
            "last_activity": history[-1].timestamp,
        }

    def get_triggered_actions(self, lead_id: str = None) -> List[Dict]:
        """Get triggered actions, optionally filtered by lead"""

        if lead_id:
            return [a for a in self.triggered_actions if a["lead_id"] == lead_id]
        return self.triggered_actions

    def get_all_rules(self) -> List[TriggerRule]:
        """Get all trigger rules"""
        return self.trigger_rules


def demo_behavioral_triggers():
    """Demonstrate behavioral trigger engine"""
    engine = BehavioralTriggerEngine()

    print("🎯 Behavioral Trigger Engine Demo\n")

    lead_id = "lead_456"

    # Simulate behavior sequence
    print("📊 Simulating lead behavior...\n")

    # Day 1: Initial interest
    triggered = engine.track_behavior(lead_id, BehaviorType.PROPERTY_VIEW.value, {"property_id": "prop_123"})
    print(f"✓ Tracked: Property view")

    # Same day: Views again
    triggered = engine.track_behavior(lead_id, BehaviorType.PROPERTY_VIEW.value, {"property_id": "prop_123"})
    print(f"✓ Tracked: Second property view")

    # Third view - should trigger!
    triggered = engine.track_behavior(lead_id, BehaviorType.PROPERTY_VIEW.value, {"property_id": "prop_123"})
    print(f"✓ Tracked: Third property view")

    if triggered:
        print(f"\n🚨 TRIGGERED: {len(triggered)} action(s)!")
        for action in triggered:
            print(f"   • {action['rule_name']}")
            print(f"     Action: {action['action']}")
            print(f"     Config: {action['config']}")

    # Email engagement
    print(f"\n✓ Tracked: Email open")
    engine.track_behavior(lead_id, BehaviorType.EMAIL_OPEN.value)

    # Get summary
    summary = engine.get_lead_behavior_summary(lead_id)
    print(f"\n📈 Lead Behavior Summary:")
    print(f"   Total events: {summary['total_events']}")
    print(f"   Engagement score: {summary['engagement_score']}/100")
    print(f"   Behaviors: {summary['behavior_counts']}")

    # Show all rules
    print(f"\n📋 Active Trigger Rules: {len(engine.get_all_rules())}")
    for rule in engine.get_all_rules()[:5]:
        print(f"   • {rule.name} (Priority: {rule.priority})")


if __name__ == "__main__":
    demo_behavioral_triggers()
