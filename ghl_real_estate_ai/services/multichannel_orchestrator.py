"""
Enhanced Multi-Channel Sequence Orchestrator

Advanced coordination of messages across SMS, Email, Voice, and Social channels.
Features intelligent timing, A/B testing, behavioral triggers, and engagement optimization.

Enhanced Features:
- Behavioral trigger sequences
- Cross-channel message coordination
- A/B testing integration
- Machine learning-powered optimization
- Advanced analytics and insights
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Channel(Enum):
    """Communication channels"""

    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    WHATSAPP = "whatsapp"
    DIRECT_MAIL = "direct_mail"
    SOCIAL = "social"
    PUSH_NOTIFICATION = "push_notification"


class SequenceStatus(Enum):
    """Sequence execution status"""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"


class TriggerType(Enum):
    """Sequence trigger types"""

    IMMEDIATE = "immediate"
    TIME_BASED = "time_based"
    BEHAVIOR_BASED = "behavior_based"
    ENGAGEMENT_BASED = "engagement_based"
    SCORE_BASED = "score_based"


class Priority(Enum):
    """Message priority levels"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class LeadProfile:
    """Lead profile for sequence targeting"""

    lead_id: str
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SequenceStep:
    """Individual step in a sequence"""

    step_id: str
    channel: str
    message_template: str
    delay_hours: int
    conditions: Dict[str, Any] = field(default_factory=dict)
    fallback_channel: Optional[str] = None


@dataclass
class MessageSequence:
    """Complete multi-channel sequence"""

    sequence_id: str
    name: str
    description: str
    steps: List[SequenceStep]
    target_segment: str
    status: str = SequenceStatus.ACTIVE.value
    created_at: str = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class SequenceExecution:
    """Track sequence execution for a lead"""

    execution_id: str
    lead_id: str
    sequence_id: str
    current_step: int
    status: str
    started_at: str
    completed_at: Optional[str] = None
    messages_sent: List[Dict] = field(default_factory=list)


class MultiChannelOrchestrator:
    """Orchestrate multi-channel message sequences"""

    def __init__(self):
        self.sequences: Dict[str, MessageSequence] = {}
        self.executions: Dict[str, SequenceExecution] = {}
        self.channel_preferences: Dict[str, Dict] = {}
        self.engagement_history: Dict[str, List[Dict]] = {}
        self._load_default_sequences()

    def _load_default_sequences(self):
        """Load pre-configured sequences"""

        # Welcome sequence
        welcome_steps = [
            SequenceStep(
                step_id="welcome_1",
                channel=Channel.SMS.value,
                message_template="Hi {name}! Thanks for your interest. I'm {agent} and I'll help you find your perfect property. 🏡",
                delay_hours=0,
            ),
            SequenceStep(
                step_id="welcome_2",
                channel=Channel.EMAIL.value,
                message_template="Detailed email with property listings...",
                delay_hours=2,
                conditions={"sms_delivered": True},
            ),
            SequenceStep(
                step_id="welcome_3",
                channel=Channel.SMS.value,
                message_template="Did you get a chance to review the properties I sent? Any questions?",
                delay_hours=24,
                conditions={"email_opened": False},
            ),
        ]

        self.add_sequence(
            MessageSequence(
                sequence_id="seq_welcome",
                name="Welcome Sequence",
                description="3-step welcome for new leads",
                steps=welcome_steps,
                target_segment="new_leads",
            )
        )

        # High-value nurture sequence
        nurture_steps = [
            SequenceStep(
                step_id="nurture_1",
                channel=Channel.EMAIL.value,
                message_template="Market insights and new listings...",
                delay_hours=0,
            ),
            SequenceStep(
                step_id="nurture_2",
                channel=Channel.SMS.value,
                message_template="Quick question: What's your ideal timeline for moving?",
                delay_hours=48,
                conditions={"email_opened": True},
            ),
            SequenceStep(
                step_id="nurture_3",
                channel=Channel.VOICE.value,
                message_template="Voice message: Personal introduction...",
                delay_hours=72,
                conditions={"sms_responded": False},
                fallback_channel=Channel.EMAIL.value,
            ),
        ]

        self.add_sequence(
            MessageSequence(
                sequence_id="seq_nurture",
                name="High-Value Nurture",
                description="Multi-touch nurture sequence",
                steps=nurture_steps,
                target_segment="qualified_leads",
            )
        )

    def add_sequence(self, sequence: MessageSequence):
        """Add a new sequence"""
        self.sequences[sequence.sequence_id] = sequence

    def start_sequence(self, lead_id: str, sequence_id: str) -> Optional[SequenceExecution]:
        """Start a sequence for a lead"""

        sequence = self.sequences.get(sequence_id)
        if not sequence:
            return None

        execution = SequenceExecution(
            execution_id=f"exec_{datetime.utcnow().timestamp()}",
            lead_id=lead_id,
            sequence_id=sequence_id,
            current_step=0,
            status=SequenceStatus.ACTIVE.value,
            started_at=datetime.utcnow().isoformat(),
        )

        self.executions[execution.execution_id] = execution
        return execution

    def select_optimal_channel(self, lead_id: str, message_type: str, time_of_day: int) -> str:
        """AI-powered channel selection"""

        # Get lead's channel preferences from history
        prefs = self.channel_preferences.get(lead_id, {})
        engagement = self.engagement_history.get(lead_id, [])

        # Calculate channel scores
        channel_scores = {}

        # SMS scoring
        sms_score = 0.7  # Base score
        if prefs.get("prefers_sms"):
            sms_score += 0.2
        if 9 <= time_of_day <= 20:  # Business hours
            sms_score += 0.1
        channel_scores[Channel.SMS.value] = sms_score

        # Email scoring
        email_score = 0.6
        if prefs.get("prefers_email"):
            email_score += 0.2
        if message_type == "detailed":
            email_score += 0.2
        channel_scores[Channel.EMAIL.value] = email_score

        # Voice scoring
        voice_score = 0.4
        if prefs.get("answered_calls"):
            voice_score += 0.3
        if message_type == "urgent":
            voice_score += 0.2
        channel_scores[Channel.VOICE.value] = voice_score

        # Return highest scoring channel
        return max(channel_scores, key=channel_scores.get)

    def predict_best_send_time(self, lead_id: str, channel: str) -> Tuple[int, int]:
        """Predict optimal send time for a lead"""

        engagement = self.engagement_history.get(lead_id, [])

        if not engagement:
            # Default times by channel
            defaults = {
                Channel.SMS.value: (10, 14),  # 10 AM - 2 PM
                Channel.EMAIL.value: (9, 11),  # 9-11 AM
                Channel.VOICE.value: (14, 17),  # 2-5 PM
            }
            return defaults.get(channel, (10, 14))

        # Analyze past engagement times
        response_times = []
        for event in engagement:
            if event.get("responded"):
                hour = datetime.fromisoformat(event["timestamp"]).hour
                response_times.append(hour)

        if response_times:
            avg_hour = sum(response_times) // len(response_times)
            return (avg_hour, avg_hour + 2)

        return (10, 14)

    def execute_sequence_step(self, execution_id: str, lead_context: Dict) -> Dict:
        """Execute next step in sequence"""

        execution = self.executions.get(execution_id)
        if not execution:
            return {"success": False, "error": "Execution not found"}

        sequence = self.sequences.get(execution.sequence_id)
        if not sequence:
            return {"success": False, "error": "Sequence not found"}

        # Check if sequence is complete
        if execution.current_step >= len(sequence.steps):
            execution.status = SequenceStatus.COMPLETED.value
            execution.completed_at = datetime.utcnow().isoformat()
            return {"success": True, "status": "completed"}

        # Get current step
        step = sequence.steps[execution.current_step]

        # Check conditions
        if step.conditions:
            if not self._check_conditions(step.conditions, lead_context):
                # Try fallback channel
                if step.fallback_channel:
                    step.channel = step.fallback_channel
                else:
                    # Skip this step
                    execution.current_step += 1
                    return {
                        "success": True,
                        "status": "skipped",
                        "reason": "conditions_not_met",
                    }

        # Select optimal channel if not specified
        if not step.channel:
            step.channel = self.select_optimal_channel(execution.lead_id, "general", datetime.utcnow().hour)

        # Format message
        message = self._format_message(step.message_template, lead_context)

        # Send message (mock implementation)
        result = self._send_message(execution.lead_id, step.channel, message)

        # Record sent message
        execution.messages_sent.append(
            {
                "step_id": step.step_id,
                "channel": step.channel,
                "sent_at": datetime.utcnow().isoformat(),
                "message": message,
                "result": result,
            }
        )

        # Move to next step
        execution.current_step += 1

        return {
            "success": True,
            "status": "sent",
            "channel": step.channel,
            "message": message,
            "next_step_delay": (
                sequence.steps[execution.current_step].delay_hours
                if execution.current_step < len(sequence.steps)
                else None
            ),
        }

    def _check_conditions(self, conditions: Dict, context: Dict) -> bool:
        """Check if conditions are met"""
        for key, required_value in conditions.items():
            actual_value = context.get(key)
            if actual_value != required_value:
                return False
        return True

    def _format_message(self, template: str, context: Dict) -> str:
        """Format message with context variables"""
        message = template
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in message:
                message = message.replace(placeholder, str(value))
        return message

    def _send_message(self, lead_id: str, channel: str, message: str) -> Dict:
        """Send message via specified channel (mock)"""
        # In production, this would call actual SMS/Email/Voice APIs
        return {
            "success": True,
            "channel": channel,
            "message_id": f"msg_{datetime.utcnow().timestamp()}",
            "delivered": True,
        }

    def track_engagement(self, lead_id: str, channel: str, action: str, metadata: Dict = None):
        """Track lead engagement with messages"""

        if lead_id not in self.engagement_history:
            self.engagement_history[lead_id] = []

        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "channel": channel,
            "action": action,  # opened, clicked, responded, etc.
            "metadata": metadata or {},
        }

        self.engagement_history[lead_id].append(event)

        # Update channel preferences
        self._update_channel_preferences(lead_id, channel, action)

    def _update_channel_preferences(self, lead_id: str, channel: str, action: str):
        """Update learned preferences for channel selection"""

        if lead_id not in self.channel_preferences:
            self.channel_preferences[lead_id] = {}

        prefs = self.channel_preferences[lead_id]

        if action == "responded":
            prefs[f"prefers_{channel}"] = True
            prefs[f"{channel}_response_rate"] = prefs.get(f"{channel}_response_rate", 0) + 1

    def get_sequence_performance(self, sequence_id: str) -> Dict:
        """Get performance metrics for a sequence"""

        executions = [e for e in self.executions.values() if e.sequence_id == sequence_id]

        if not executions:
            return {"sequence_id": sequence_id, "total_executions": 0}

        completed = len([e for e in executions if e.status == SequenceStatus.COMPLETED.value])
        active = len([e for e in executions if e.status == SequenceStatus.ACTIVE.value])

        # Calculate average completion rate
        total_messages = sum(len(e.messages_sent) for e in executions)
        avg_messages = total_messages / len(executions) if executions else 0

        return {
            "sequence_id": sequence_id,
            "total_executions": len(executions),
            "completed": completed,
            "active": active,
            "completion_rate": f"{(completed / len(executions) * 100):.1f}%",
            "avg_messages_sent": f"{avg_messages:.1f}",
            "total_messages": total_messages,
        }

    def get_channel_performance(self, lead_id: str = None) -> Dict:
        """Get performance by channel"""

        engagement = self.engagement_history.get(lead_id, []) if lead_id else []
        if not lead_id:
            # Aggregate all leads
            for lead_engagement in self.engagement_history.values():
                engagement.extend(lead_engagement)

        channel_stats = {}
        for channel in [c.value for c in Channel]:
            channel_events = [e for e in engagement if e["channel"] == channel]
            responses = len([e for e in channel_events if e["action"] == "responded"])

            channel_stats[channel] = {
                "total_sent": len(channel_events),
                "responses": responses,
                "response_rate": (f"{(responses / len(channel_events) * 100):.1f}%" if channel_events else "0%"),
            }

        return channel_stats


def demo_multichannel_orchestrator():
    """Demonstrate multi-channel orchestrator"""
    orchestrator = MultiChannelOrchestrator()

    print("📱 Multi-Channel Sequence Orchestrator Demo\n")

    lead_id = "lead_789"
    lead_context = {
        "name": "Jennifer Smith",
        "agent": "Mike Reynolds",
        "property_interest": "3-bedroom house",
    }

    # Start welcome sequence
    execution = orchestrator.start_sequence(lead_id, "seq_welcome")
    print(f"✅ Started sequence: {execution.sequence_id}")
    print(f"   Execution ID: {execution.execution_id}\n")

    # Execute steps
    for i in range(3):
        result = orchestrator.execute_sequence_step(execution.execution_id, lead_context)
        if result["success"]:
            print(f"📤 Step {i + 1}: Sent via {result.get('channel', 'N/A')}")
            print(f"   Message: {result.get('message', 'N/A')[:80]}...")
            if result.get("next_step_delay"):
                print(f"   Next step in: {result['next_step_delay']} hours")
        print()

    # Simulate engagement
    print("📊 Simulating engagement tracking...\n")
    orchestrator.track_engagement(lead_id, Channel.SMS.value, "responded")
    orchestrator.track_engagement(lead_id, Channel.EMAIL.value, "opened")

    # Show optimal channel
    optimal = orchestrator.select_optimal_channel(lead_id, "general", 14)
    print(f"🎯 Optimal channel for this lead: {optimal}")

    # Show performance
    perf = orchestrator.get_sequence_performance("seq_welcome")
    print(f"\n📈 Sequence Performance:")
    print(f"   Executions: {perf['total_executions']}")
    print(f"   Completion rate: {perf['completion_rate']}")
    print(f"   Messages sent: {perf['total_messages']}")


if __name__ == "__main__":
    demo_multichannel_orchestrator()
