"""
Behavioral Trigger Service

Intelligent behavior monitoring and trigger evaluation for GHL workflow automation.
Tracks lead engagement patterns and triggers workflow actions based on behavioral intelligence.

Features:
- Real-time engagement tracking (email opens, property views, website activity)
- Behavioral pattern detection (engagement spikes, qualification improvements, inactivity risks)
- Dynamic trigger evaluation with cooldown management
- Machine learning-based engagement scoring
- Integration with Advanced Workflow Engine

Performance Targets:
- Behavior tracking: <25ms
- Trigger evaluation: <100ms
- Engagement score calculation: <50ms
- Pattern detection: <75ms
"""

import asyncio
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class BehaviorType(Enum):
    """Types of behavioral events."""
    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    SMS_REPLY = "sms_reply"
    PROPERTY_VIEW = "property_view"
    WEBSITE_VISIT = "website_visit"
    FORM_SUBMISSION = "form_submission"
    CALL_ANSWERED = "call_answered"
    MEETING_SCHEDULED = "meeting_scheduled"
    DOCUMENT_DOWNLOAD = "document_download"


class TriggerType(Enum):
    """Types of behavioral triggers."""
    ENGAGEMENT_SPIKE = "engagement_spike"
    QUALIFICATION_IMPROVEMENT = "qualification_improvement"
    INACTIVITY_RISK = "inactivity_risk"
    OBJECTION_DETECTION = "objection_detection"
    BUYING_SIGNAL = "buying_signal"
    HIGH_INTENT = "high_intent"


@dataclass
class BehaviorEvent:
    """Individual behavioral event."""
    event_id: str
    contact_id: str
    behavior_type: BehaviorType
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Scoring impact
    engagement_value: float = 1.0
    qualification_impact: float = 0.0


@dataclass
class EngagementSpike:
    """Detected engagement spike."""
    contact_id: str
    spike_type: str
    confidence: float
    events_count: int
    time_window_hours: int
    detected_at: datetime
    trigger_actions: List[str] = field(default_factory=list)


@dataclass
class InactivityRisk:
    """Detected inactivity risk."""
    contact_id: str
    days_inactive: int
    last_engagement_type: str
    risk_level: str  # low, medium, high, critical
    engagement_score: float
    detected_at: datetime


@dataclass
class TriggeredAction:
    """Action triggered by behavioral pattern."""
    trigger_id: str
    action_type: str
    contact_id: str
    trigger_type: TriggerType
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    cooldown_until: Optional[datetime] = None


class BehavioralTriggerService:
    """
    Behavioral Trigger Service

    Monitors lead behavior and triggers intelligent workflow actions
    based on engagement patterns and behavioral signals.
    """

    def __init__(self, cache_manager=None, workflow_engine=None):
        """
        Initialize behavioral trigger service.

        Args:
            cache_manager: Integration cache manager for pattern caching
            workflow_engine: Advanced workflow engine for action triggering
        """
        self.cache_manager = cache_manager
        self.workflow_engine = workflow_engine

        # Behavior tracking
        self._behavior_history: Dict[str, List[BehaviorEvent]] = defaultdict(list)
        self._engagement_scores: Dict[str, float] = {}
        self._qualification_scores: Dict[str, float] = {}

        # Pattern detection state
        self._pattern_cache: Dict[str, Any] = {}
        self._last_spike_detection: Dict[str, datetime] = {}
        self._trigger_cooldowns: Dict[str, datetime] = {}

        # Configuration
        self.engagement_config = {
            'spike_threshold_events': 3,
            'spike_time_window_hours': 24,
            'inactivity_threshold_days': 7,
            'qualification_improvement_threshold': 0.15,
            'engagement_decay_hours': 168  # 1 week
        }

        # Trigger configuration
        self.trigger_config = {
            'engagement_spike': {
                'cooldown_hours': 24,
                'min_confidence': 0.7
            },
            'qualification_improvement': {
                'cooldown_hours': 48,
                'min_confidence': 0.6
            },
            'inactivity_risk': {
                'cooldown_hours': 72,
                'min_confidence': 0.8
            },
            'buying_signal': {
                'cooldown_hours': 12,
                'min_confidence': 0.9
            }
        }

        # Performance tracking
        self._performance_metrics = {
            'events_tracked': 0,
            'triggers_evaluated': 0,
            'triggers_fired': 0,
            'avg_evaluation_time_ms': 0.0
        }

        logger.info("Behavioral Trigger Service initialized")

    async def track_behavior(
        self,
        contact_id: str,
        behavior_event: BehaviorEvent
    ) -> None:
        """
        Track a behavioral event for a contact.

        Args:
            contact_id: Contact identifier
            behavior_event: Behavior event to track
        """
        start_time = time.time()

        try:
            # Add event to history
            self._behavior_history[contact_id].append(behavior_event)

            # Limit history size (keep last 100 events per contact)
            if len(self._behavior_history[contact_id]) > 100:
                self._behavior_history[contact_id] = self._behavior_history[contact_id][-100:]

            # Update engagement score
            await self._update_engagement_score(contact_id, behavior_event)

            # Update qualification score if applicable
            if behavior_event.qualification_impact != 0:
                await self._update_qualification_score(contact_id, behavior_event)

            # Cache behavioral patterns
            if self.cache_manager:
                await self._cache_behavioral_patterns(contact_id)

            # Track performance
            self._performance_metrics['events_tracked'] += 1

            logger.debug(f"Tracked {behavior_event.behavior_type.value} for contact {contact_id}")

        except Exception as e:
            logger.error(f"Error tracking behavior for {contact_id}: {e}")

        finally:
            processing_time = (time.time() - start_time) * 1000
            # Update average processing time if needed

    async def evaluate_triggers(self, contact_id: str) -> List[TriggeredAction]:
        """
        Evaluate all trigger types for a contact.

        Args:
            contact_id: Contact to evaluate triggers for

        Returns:
            List of triggered actions
        """
        start_time = time.time()
        triggered_actions = []

        try:
            # Check engagement spike
            spike = await self.detect_engagement_spike(contact_id)
            if spike:
                actions = await self._evaluate_engagement_spike_triggers(spike)
                triggered_actions.extend(actions)

            # Check qualification improvement
            improvement = await self._detect_qualification_improvement(contact_id)
            if improvement:
                actions = await self._evaluate_qualification_triggers(contact_id, improvement)
                triggered_actions.extend(actions)

            # Check inactivity risk
            inactivity = await self.detect_inactivity_risk(contact_id)
            if inactivity:
                actions = await self._evaluate_inactivity_triggers(inactivity)
                triggered_actions.extend(actions)

            # Check buying signals
            buying_signals = await self._detect_buying_signals(contact_id)
            if buying_signals:
                actions = await self._evaluate_buying_signal_triggers(contact_id, buying_signals)
                triggered_actions.extend(actions)

            # Filter by cooldowns and confidence
            filtered_actions = await self._filter_triggered_actions(triggered_actions)

            # Track performance
            self._performance_metrics['triggers_evaluated'] += 1
            self._performance_metrics['triggers_fired'] += len(filtered_actions)

            processing_time_ms = (time.time() - start_time) * 1000
            self._update_avg_evaluation_time(processing_time_ms)

            return filtered_actions

        except Exception as e:
            logger.error(f"Error evaluating triggers for {contact_id}: {e}")
            return []

    async def calculate_engagement_score(
        self,
        contact_id: str,
        time_window_hours: int = 24
    ) -> float:
        """
        Calculate engagement score for a contact within time window.

        Args:
            contact_id: Contact identifier
            time_window_hours: Time window for scoring

        Returns:
            Engagement score (0.0 to 1.0)
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
            events = self._behavior_history.get(contact_id, [])

            # Filter events within time window
            recent_events = [e for e in events if e.timestamp > cutoff_time]

            if not recent_events:
                return 0.0

            # Calculate weighted score
            total_score = 0.0
            max_possible_score = 0.0

            for event in recent_events:
                # Apply time decay
                hours_ago = (datetime.now() - event.timestamp).total_seconds() / 3600
                decay_factor = max(0.1, 1.0 - (hours_ago / time_window_hours))

                # Weight by behavior type
                weight = self._get_behavior_weight(event.behavior_type)

                event_score = event.engagement_value * weight * decay_factor
                total_score += event_score
                max_possible_score += weight

            # Normalize score
            if max_possible_score > 0:
                score = min(1.0, total_score / max_possible_score)
            else:
                score = 0.0

            # Cache the score
            self._engagement_scores[contact_id] = score

            return score

        except Exception as e:
            logger.error(f"Error calculating engagement score for {contact_id}: {e}")
            return 0.0

    async def detect_engagement_spike(self, contact_id: str) -> Optional[EngagementSpike]:
        """
        Detect engagement spikes for a contact.

        Args:
            contact_id: Contact identifier

        Returns:
            EngagementSpike if detected, None otherwise
        """
        try:
            spike_window = self.engagement_config['spike_time_window_hours']
            cutoff_time = datetime.now() - timedelta(hours=spike_window)

            events = self._behavior_history.get(contact_id, [])
            recent_events = [e for e in events if e.timestamp > cutoff_time]

            # Check for different spike patterns
            spikes = []

            # Property view spike
            property_views = [e for e in recent_events if e.behavior_type == BehaviorType.PROPERTY_VIEW]
            if len(property_views) >= 3:
                spikes.append({
                    'type': 'property_view_spike',
                    'count': len(property_views),
                    'confidence': min(1.0, len(property_views) / 5)
                })

            # Email engagement spike
            email_events = [e for e in recent_events if e.behavior_type in [BehaviorType.EMAIL_OPEN, BehaviorType.EMAIL_CLICK]]
            if len(email_events) >= 2:
                spikes.append({
                    'type': 'email_engagement_spike',
                    'count': len(email_events),
                    'confidence': min(1.0, len(email_events) / 3)
                })

            # Overall activity spike
            if len(recent_events) >= self.engagement_config['spike_threshold_events']:
                spikes.append({
                    'type': 'general_activity_spike',
                    'count': len(recent_events),
                    'confidence': min(1.0, len(recent_events) / 6)
                })

            if spikes:
                # Return highest confidence spike
                best_spike = max(spikes, key=lambda s: s['confidence'])

                return EngagementSpike(
                    contact_id=contact_id,
                    spike_type=best_spike['type'],
                    confidence=best_spike['confidence'],
                    events_count=best_spike['count'],
                    time_window_hours=spike_window,
                    detected_at=datetime.now(),
                    trigger_actions=['immediate_follow_up', 'priority_routing']
                )

            return None

        except Exception as e:
            logger.error(f"Error detecting engagement spike for {contact_id}: {e}")
            return None

    async def detect_inactivity_risk(self, contact_id: str) -> Optional[InactivityRisk]:
        """
        Detect inactivity risk for a contact.

        Args:
            contact_id: Contact identifier

        Returns:
            InactivityRisk if detected, None otherwise
        """
        try:
            events = self._behavior_history.get(contact_id, [])
            if not events:
                return None

            last_event = max(events, key=lambda e: e.timestamp)
            days_since_last = (datetime.now() - last_event.timestamp).days

            threshold_days = self.engagement_config['inactivity_threshold_days']

            if days_since_last >= threshold_days:
                # Determine risk level
                if days_since_last >= threshold_days * 2:
                    risk_level = "critical"
                elif days_since_last >= threshold_days * 1.5:
                    risk_level = "high"
                elif days_since_last >= threshold_days:
                    risk_level = "medium"
                else:
                    risk_level = "low"

                current_engagement = await self.calculate_engagement_score(contact_id, 168)  # 1 week window

                return InactivityRisk(
                    contact_id=contact_id,
                    days_inactive=days_since_last,
                    last_engagement_type=last_event.behavior_type.value,
                    risk_level=risk_level,
                    engagement_score=current_engagement,
                    detected_at=datetime.now()
                )

            return None

        except Exception as e:
            logger.error(f"Error detecting inactivity risk for {contact_id}: {e}")
            return None

    async def _update_engagement_score(
        self,
        contact_id: str,
        behavior_event: BehaviorEvent
    ) -> None:
        """Update engagement score for contact."""
        try:
            current_score = self._engagement_scores.get(contact_id, 0.0)

            # Calculate behavior impact
            weight = self._get_behavior_weight(behavior_event.behavior_type)
            impact = behavior_event.engagement_value * weight * 0.1  # Moderate impact per event

            # Update score with decay
            new_score = min(1.0, current_score + impact)
            self._engagement_scores[contact_id] = new_score

        except Exception as e:
            logger.error(f"Error updating engagement score for {contact_id}: {e}")

    async def _update_qualification_score(
        self,
        contact_id: str,
        behavior_event: BehaviorEvent
    ) -> None:
        """Update qualification score for contact."""
        try:
            current_score = self._qualification_scores.get(contact_id, 0.5)

            # Apply qualification impact
            new_score = max(0.0, min(1.0, current_score + behavior_event.qualification_impact))
            self._qualification_scores[contact_id] = new_score

        except Exception as e:
            logger.error(f"Error updating qualification score for {contact_id}: {e}")

    def _get_behavior_weight(self, behavior_type: BehaviorType) -> float:
        """Get weight for behavior type."""
        weights = {
            BehaviorType.EMAIL_OPEN: 0.3,
            BehaviorType.EMAIL_CLICK: 0.6,
            BehaviorType.SMS_REPLY: 0.8,
            BehaviorType.PROPERTY_VIEW: 0.7,
            BehaviorType.WEBSITE_VISIT: 0.4,
            BehaviorType.FORM_SUBMISSION: 0.9,
            BehaviorType.CALL_ANSWERED: 1.0,
            BehaviorType.MEETING_SCHEDULED: 1.0,
            BehaviorType.DOCUMENT_DOWNLOAD: 0.5
        }
        return weights.get(behavior_type, 0.5)

    async def _detect_qualification_improvement(self, contact_id: str) -> Optional[float]:
        """Detect qualification score improvement."""
        try:
            current_score = self._qualification_scores.get(contact_id, 0.5)

            # Check for recent qualification-impacting events
            cutoff_time = datetime.now() - timedelta(hours=24)
            events = self._behavior_history.get(contact_id, [])
            recent_qual_events = [
                e for e in events
                if e.timestamp > cutoff_time and e.qualification_impact > 0
            ]

            if recent_qual_events:
                total_improvement = sum(e.qualification_impact for e in recent_qual_events)
                if total_improvement >= self.engagement_config['qualification_improvement_threshold']:
                    return total_improvement

            return None

        except Exception as e:
            logger.error(f"Error detecting qualification improvement for {contact_id}: {e}")
            return None

    async def _detect_buying_signals(self, contact_id: str) -> List[str]:
        """Detect buying signals from behavior patterns."""
        try:
            signals = []
            cutoff_time = datetime.now() - timedelta(hours=48)
            events = self._behavior_history.get(contact_id, [])
            recent_events = [e for e in events if e.timestamp > cutoff_time]

            # Multiple property views in short time
            property_views = [e for e in recent_events if e.behavior_type == BehaviorType.PROPERTY_VIEW]
            if len(property_views) >= 5:
                signals.append("multiple_property_views")

            # Form submissions indicate high intent
            form_submissions = [e for e in recent_events if e.behavior_type == BehaviorType.FORM_SUBMISSION]
            if form_submissions:
                signals.append("form_submission")

            # Meeting scheduled is strong buying signal
            meetings = [e for e in recent_events if e.behavior_type == BehaviorType.MEETING_SCHEDULED]
            if meetings:
                signals.append("meeting_scheduled")

            # Document downloads (financing, contracts, etc.)
            downloads = [e for e in recent_events if e.behavior_type == BehaviorType.DOCUMENT_DOWNLOAD]
            if downloads:
                signals.append("document_download")

            return signals

        except Exception as e:
            logger.error(f"Error detecting buying signals for {contact_id}: {e}")
            return []

    async def _evaluate_engagement_spike_triggers(self, spike: EngagementSpike) -> List[TriggeredAction]:
        """Evaluate triggers for engagement spike."""
        actions = []

        if spike.confidence >= self.trigger_config['engagement_spike']['min_confidence']:
            # Check cooldown
            cooldown_key = f"{spike.contact_id}:engagement_spike"
            if not self._is_in_cooldown(cooldown_key):
                actions.append(TriggeredAction(
                    trigger_id=f"engagement_spike_{spike.contact_id}_{int(time.time())}",
                    action_type="immediate_follow_up",
                    contact_id=spike.contact_id,
                    trigger_type=TriggerType.ENGAGEMENT_SPIKE,
                    confidence=spike.confidence,
                    metadata={
                        "spike_type": spike.spike_type,
                        "events_count": spike.events_count
                    },
                    cooldown_until=datetime.now() + timedelta(hours=self.trigger_config['engagement_spike']['cooldown_hours'])
                ))

                # Set cooldown
                self._trigger_cooldowns[cooldown_key] = datetime.now() + timedelta(
                    hours=self.trigger_config['engagement_spike']['cooldown_hours']
                )

        return actions

    async def _evaluate_qualification_triggers(self, contact_id: str, improvement: float) -> List[TriggeredAction]:
        """Evaluate triggers for qualification improvement."""
        actions = []

        confidence = min(1.0, improvement / self.engagement_config['qualification_improvement_threshold'])

        if confidence >= self.trigger_config['qualification_improvement']['min_confidence']:
            cooldown_key = f"{contact_id}:qualification_improvement"
            if not self._is_in_cooldown(cooldown_key):
                actions.append(TriggeredAction(
                    trigger_id=f"qual_improvement_{contact_id}_{int(time.time())}",
                    action_type="priority_routing",
                    contact_id=contact_id,
                    trigger_type=TriggerType.QUALIFICATION_IMPROVEMENT,
                    confidence=confidence,
                    metadata={"improvement_score": improvement},
                    cooldown_until=datetime.now() + timedelta(hours=self.trigger_config['qualification_improvement']['cooldown_hours'])
                ))

                self._trigger_cooldowns[cooldown_key] = datetime.now() + timedelta(
                    hours=self.trigger_config['qualification_improvement']['cooldown_hours']
                )

        return actions

    async def _evaluate_inactivity_triggers(self, inactivity: InactivityRisk) -> List[TriggeredAction]:
        """Evaluate triggers for inactivity risk."""
        actions = []

        # Higher confidence for higher risk levels
        confidence_map = {"low": 0.6, "medium": 0.7, "high": 0.85, "critical": 0.95}
        confidence = confidence_map.get(inactivity.risk_level, 0.5)

        if confidence >= self.trigger_config['inactivity_risk']['min_confidence']:
            cooldown_key = f"{inactivity.contact_id}:inactivity_risk"
            if not self._is_in_cooldown(cooldown_key):
                actions.append(TriggeredAction(
                    trigger_id=f"inactivity_{inactivity.contact_id}_{int(time.time())}",
                    action_type="reengagement_sequence",
                    contact_id=inactivity.contact_id,
                    trigger_type=TriggerType.INACTIVITY_RISK,
                    confidence=confidence,
                    metadata={
                        "days_inactive": inactivity.days_inactive,
                        "risk_level": inactivity.risk_level
                    },
                    cooldown_until=datetime.now() + timedelta(hours=self.trigger_config['inactivity_risk']['cooldown_hours'])
                ))

                self._trigger_cooldowns[cooldown_key] = datetime.now() + timedelta(
                    hours=self.trigger_config['inactivity_risk']['cooldown_hours']
                )

        return actions

    async def _evaluate_buying_signal_triggers(self, contact_id: str, signals: List[str]) -> List[TriggeredAction]:
        """Evaluate triggers for buying signals."""
        actions = []

        # Higher confidence for more/stronger signals
        confidence = min(1.0, len(signals) / 3 + 0.3)

        if confidence >= self.trigger_config['buying_signal']['min_confidence']:
            cooldown_key = f"{contact_id}:buying_signal"
            if not self._is_in_cooldown(cooldown_key):
                actions.append(TriggeredAction(
                    trigger_id=f"buying_signal_{contact_id}_{int(time.time())}",
                    action_type="high_priority_follow_up",
                    contact_id=contact_id,
                    trigger_type=TriggerType.BUYING_SIGNAL,
                    confidence=confidence,
                    metadata={"signals": signals},
                    cooldown_until=datetime.now() + timedelta(hours=self.trigger_config['buying_signal']['cooldown_hours'])
                ))

                self._trigger_cooldowns[cooldown_key] = datetime.now() + timedelta(
                    hours=self.trigger_config['buying_signal']['cooldown_hours']
                )

        return actions

    def _is_in_cooldown(self, cooldown_key: str) -> bool:
        """Check if action is in cooldown period."""
        cooldown_until = self._trigger_cooldowns.get(cooldown_key)
        if cooldown_until and datetime.now() < cooldown_until:
            return True
        return False

    async def _filter_triggered_actions(self, actions: List[TriggeredAction]) -> List[TriggeredAction]:
        """Filter triggered actions by cooldowns and confidence."""
        filtered = []

        for action in actions:
            # Check if still in cooldown
            cooldown_key = f"{action.contact_id}:{action.trigger_type.value}"
            if not self._is_in_cooldown(cooldown_key):
                filtered.append(action)

                # Set cooldown if action has one
                if action.cooldown_until:
                    self._trigger_cooldowns[cooldown_key] = action.cooldown_until

        return filtered

    async def _cache_behavioral_patterns(self, contact_id: str) -> None:
        """Cache behavioral patterns for fast lookup."""
        if not self.cache_manager:
            return

        try:
            patterns = {
                'engagement_score': self._engagement_scores.get(contact_id, 0.0),
                'qualification_score': self._qualification_scores.get(contact_id, 0.5),
                'recent_events_count': len([
                    e for e in self._behavior_history.get(contact_id, [])
                    if e.timestamp > datetime.now() - timedelta(hours=24)
                ]),
                'last_updated': datetime.now().isoformat()
            }

            await self.cache_manager.set(
                f"behavioral_patterns:{contact_id}",
                patterns,
                ttl_seconds=1800  # 30 minutes
            )

        except Exception as e:
            logger.error(f"Error caching behavioral patterns for {contact_id}: {e}")

    def _update_avg_evaluation_time(self, processing_time_ms: float) -> None:
        """Update average evaluation time metric."""
        evaluations = self._performance_metrics['triggers_evaluated']
        if evaluations > 0:
            current_avg = self._performance_metrics['avg_evaluation_time_ms']
            self._performance_metrics['avg_evaluation_time_ms'] = (
                (current_avg * (evaluations - 1) + processing_time_ms) / evaluations
            )
        else:
            self._performance_metrics['avg_evaluation_time_ms'] = processing_time_ms

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            **self._performance_metrics,
            'trigger_fire_rate': (
                self._performance_metrics['triggers_fired'] /
                max(1, self._performance_metrics['triggers_evaluated'])
            ),
            'active_cooldowns': len([
                k for k, v in self._trigger_cooldowns.items()
                if datetime.now() < v
            ])
        }

    async def get_contact_behavioral_summary(self, contact_id: str) -> Dict[str, Any]:
        """Get comprehensive behavioral summary for contact."""
        try:
            events = self._behavior_history.get(contact_id, [])
            recent_events = [
                e for e in events
                if e.timestamp > datetime.now() - timedelta(days=7)
            ]

            engagement_score = await self.calculate_engagement_score(contact_id, 168)
            spike = await self.detect_engagement_spike(contact_id)
            inactivity = await self.detect_inactivity_risk(contact_id)
            buying_signals = await self._detect_buying_signals(contact_id)

            return {
                'contact_id': contact_id,
                'engagement_score': engagement_score,
                'qualification_score': self._qualification_scores.get(contact_id, 0.5),
                'total_events': len(events),
                'recent_events_7d': len(recent_events),
                'engagement_spike': spike.__dict__ if spike else None,
                'inactivity_risk': inactivity.__dict__ if inactivity else None,
                'buying_signals': buying_signals,
                'behavior_distribution': self._get_behavior_distribution(events),
                'last_activity': events[-1].timestamp.isoformat() if events else None
            }

        except Exception as e:
            logger.error(f"Error getting behavioral summary for {contact_id}: {e}")
            return {'contact_id': contact_id, 'error': str(e)}

    def _get_behavior_distribution(self, events: List[BehaviorEvent]) -> Dict[str, int]:
        """Get distribution of behavior types."""
        distribution = defaultdict(int)
        for event in events:
            distribution[event.behavior_type.value] += 1
        return dict(distribution)


# Singleton instance
_behavioral_trigger_service = None


def get_behavioral_trigger_service(**kwargs) -> BehavioralTriggerService:
    """Get singleton behavioral trigger service instance."""
    global _behavioral_trigger_service
    if _behavioral_trigger_service is None:
        _behavioral_trigger_service = BehavioralTriggerService(**kwargs)
    return _behavioral_trigger_service


# Export main classes
__all__ = [
    "BehavioralTriggerService",
    "BehaviorEvent",
    "BehaviorType",
    "EngagementSpike",
    "InactivityRisk",
    "TriggeredAction",
    "TriggerType",
    "get_behavioral_trigger_service"
]