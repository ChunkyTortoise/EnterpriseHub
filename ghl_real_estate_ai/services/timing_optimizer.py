"""
Timing Optimization Service for Intelligent Workflow Scheduling

Analyzes lead behavior patterns and optimizes message timing for maximum engagement.
Uses machine learning to predict optimal send times per lead and channel.
"""

import asyncio
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Channel(Enum):
    """Communication channels"""

    EMAIL = "email"
    SMS = "sms"
    VOICE = "voice"
    SOCIAL = "social"


class TimeZone(Enum):
    """Common time zones"""

    EST = "America/New_York"
    CST = "America/Chicago"
    MST = "America/Denver"
    PST = "America/Los_Angeles"


@dataclass
class EngagementEvent:
    """Lead engagement event data"""

    lead_id: str
    channel: Channel
    event_type: str  # 'open', 'click', 'reply', 'call_answered'
    timestamp: datetime
    message_sent_at: datetime
    time_to_engagement: timedelta = field(init=False)

    def __post_init__(self):
        self.time_to_engagement = self.timestamp - self.message_sent_at


@dataclass
class LeadTimingProfile:
    """Individual lead's timing preferences"""

    lead_id: str
    timezone: str
    preferred_hours: Dict[Channel, List[int]] = field(default_factory=dict)
    best_days: Dict[Channel, List[int]] = field(default_factory=dict)  # 0=Monday
    engagement_patterns: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0


@dataclass
class TimingRecommendation:
    """Optimized timing recommendation"""

    recommended_time: datetime
    confidence_score: float
    reasoning: str
    alternatives: List[Tuple[datetime, float]] = field(default_factory=list)
    channel: Channel = Channel.EMAIL


class TimingOptimizer:
    """Intelligent timing optimization service"""

    def __init__(self):
        self.engagement_history: Dict[str, List[EngagementEvent]] = defaultdict(list)
        self.lead_profiles: Dict[str, LeadTimingProfile] = {}
        self.global_patterns: Dict[str, Any] = {
            "best_hours_by_channel": {},
            "best_days_by_channel": {},
            "timezone_patterns": {},
            "industry_patterns": {},
        }
        self.ml_models_trained = False

    async def record_engagement(
        self, lead_id: str, channel: Channel, event_type: str, timestamp: datetime, message_sent_at: datetime
    ) -> bool:
        """Record lead engagement for learning"""
        try:
            event = EngagementEvent(
                lead_id=lead_id,
                channel=channel,
                event_type=event_type,
                timestamp=timestamp,
                message_sent_at=message_sent_at,
            )

            self.engagement_history[lead_id].append(event)

            # Update lead profile
            await self._update_lead_profile(lead_id, event)

            # Update global patterns
            await self._update_global_patterns(event)

            logger.debug(f"Recorded engagement: {event_type} for lead {lead_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to record engagement: {e}")
            return False

    async def get_optimal_send_time(
        self,
        lead_id: str,
        channel: Channel,
        base_time: Optional[datetime] = None,
        lead_data: Optional[Dict[str, Any]] = None,
    ) -> TimingRecommendation:
        """Get optimal send time for specific lead and channel"""
        try:
            if base_time is None:
                base_time = datetime.now()

            # Get lead-specific profile
            lead_profile = self.lead_profiles.get(lead_id)

            if lead_profile and lead_profile.confidence_score > 0.7:
                # Use lead-specific optimization
                recommendation = await self._get_personalized_timing(lead_profile, channel, base_time)
            else:
                # Use global patterns and heuristics
                recommendation = await self._get_heuristic_timing(lead_id, channel, base_time, lead_data)

            return recommendation

        except Exception as e:
            logger.error(f"Failed to get optimal send time: {e}")
            return TimingRecommendation(
                recommended_time=base_time,
                confidence_score=0.1,
                reasoning="Fallback to immediate send due to error",
                channel=channel,
            )

    async def _get_personalized_timing(
        self, lead_profile: LeadTimingProfile, channel: Channel, base_time: datetime
    ) -> TimingRecommendation:
        """Get timing based on lead-specific patterns"""

        # Get preferred hours for this channel
        preferred_hours = lead_profile.preferred_hours.get(channel, [9, 10, 11, 14, 15, 16])
        preferred_days = lead_profile.best_days.get(channel, [0, 1, 2, 3, 4])  # Weekdays

        # Find next optimal time slot
        optimal_time = await self._find_next_optimal_slot(
            base_time, preferred_hours, preferred_days, lead_profile.timezone
        )

        confidence = lead_profile.confidence_score

        reasoning = (
            f"Based on {len(self.engagement_history.get(lead_profile.lead_id, []))} "
            f"engagement events, optimal hours: {preferred_hours}"
        )

        # Generate alternatives
        alternatives = await self._generate_timing_alternatives(
            base_time, preferred_hours, preferred_days, lead_profile.timezone
        )

        return TimingRecommendation(
            recommended_time=optimal_time,
            confidence_score=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            channel=channel,
        )

    async def _get_heuristic_timing(
        self, lead_id: str, channel: Channel, base_time: datetime, lead_data: Optional[Dict[str, Any]]
    ) -> TimingRecommendation:
        """Get timing based on heuristics and global patterns"""

        # Default patterns by channel
        default_patterns = {
            Channel.EMAIL: {
                "preferred_hours": [9, 10, 11, 14, 15, 16],
                "preferred_days": [0, 1, 2, 3, 4],  # Weekdays
                "avoid_hours": [0, 1, 2, 3, 4, 5, 22, 23],
            },
            Channel.SMS: {
                "preferred_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17],
                "preferred_days": [0, 1, 2, 3, 4, 5, 6],  # All days
                "avoid_hours": [22, 23, 0, 1, 2, 3, 4, 5, 6, 7],
            },
            Channel.VOICE: {
                "preferred_hours": [9, 10, 11, 14, 15, 16],
                "preferred_days": [0, 1, 2, 3, 4],  # Weekdays only
                "avoid_hours": [0, 1, 2, 3, 4, 5, 6, 7, 18, 19, 20, 21, 22, 23],
            },
        }

        pattern = default_patterns.get(channel, default_patterns[Channel.EMAIL])

        # Adjust for lead data if available
        if lead_data:
            pattern = await self._adjust_for_lead_data(pattern, lead_data)

        # Determine timezone
        timezone = self._determine_timezone(lead_data) if lead_data else "America/New_York"

        # Find optimal time
        optimal_time = await self._find_next_optimal_slot(
            base_time, pattern["preferred_hours"], pattern["preferred_days"], timezone
        )

        # Calculate confidence based on available data
        confidence = 0.5  # Moderate confidence for heuristic-based timing

        if lead_data:
            # Higher confidence if we have lead demographics
            if any(key in lead_data for key in ["timezone", "industry", "job_title"]):
                confidence = 0.6

        reasoning = f"Based on {channel.value} best practices and general patterns"

        alternatives = await self._generate_timing_alternatives(
            base_time, pattern["preferred_hours"], pattern["preferred_days"], timezone
        )

        return TimingRecommendation(
            recommended_time=optimal_time,
            confidence_score=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            channel=channel,
        )

    async def _find_next_optimal_slot(
        self, base_time: datetime, preferred_hours: List[int], preferred_days: List[int], timezone: str
    ) -> datetime:
        """Find next available optimal time slot"""

        current_time = base_time
        max_days_ahead = 14  # Don't schedule more than 2 weeks out

        for day_offset in range(max_days_ahead):
            check_time = current_time + timedelta(days=day_offset)

            # Check if day is preferred
            if check_time.weekday() not in preferred_days:
                continue

            # Check for optimal hours on this day
            for hour in preferred_hours:
                candidate_time = check_time.replace(hour=hour, minute=0, second=0, microsecond=0)

                # Must be in future
                if candidate_time > base_time:
                    # Check for conflicts or restrictions
                    if await self._is_time_available(candidate_time):
                        return candidate_time

        # Fallback: schedule for next business hour
        return await self._get_next_business_hour(base_time)

    async def _generate_timing_alternatives(
        self,
        base_time: datetime,
        preferred_hours: List[int],
        preferred_days: List[int],
        timezone: str,
        max_alternatives: int = 3,
    ) -> List[Tuple[datetime, float]]:
        """Generate alternative timing options"""

        alternatives = []
        current_time = base_time

        # Generate alternatives over next few days
        for day_offset in range(1, 8):  # Next 7 days
            check_time = current_time + timedelta(days=day_offset)

            if check_time.weekday() in preferred_days:
                # Pick best hour for this day
                for hour in preferred_hours[:2]:  # Top 2 hours only
                    candidate_time = check_time.replace(hour=hour, minute=0, second=0, microsecond=0)

                    if candidate_time > base_time:
                        # Calculate confidence based on day and hour preference
                        confidence = 0.8 if hour in preferred_hours[:2] else 0.6
                        if check_time.weekday() in preferred_days[:3]:
                            confidence += 0.1

                        alternatives.append((candidate_time, min(confidence, 0.95)))

                        if len(alternatives) >= max_alternatives:
                            return alternatives

        return alternatives

    async def _update_lead_profile(self, lead_id: str, engagement_event: EngagementEvent):
        """Update individual lead's timing profile"""

        if lead_id not in self.lead_profiles:
            self.lead_profiles[lead_id] = LeadTimingProfile(
                lead_id=lead_id,
                timezone="America/New_York",  # Default
            )

        profile = self.lead_profiles[lead_id]

        # Extract timing insights from engagement
        hour = engagement_event.timestamp.hour
        day_of_week = engagement_event.timestamp.weekday()
        channel = engagement_event.channel

        # Update preferred hours
        if channel not in profile.preferred_hours:
            profile.preferred_hours[channel] = []

        # Add hour to preferences (weighted by engagement quality)
        self._get_engagement_weight(engagement_event.event_type)

        # Simple frequency-based learning
        profile.preferred_hours[channel].append(hour)

        # Keep only recent preferences (sliding window)
        if len(profile.preferred_hours[channel]) > 20:
            profile.preferred_hours[channel] = profile.preferred_hours[channel][-20:]

        # Update preferred days
        if channel not in profile.best_days:
            profile.best_days[channel] = []

        profile.best_days[channel].append(day_of_week)
        if len(profile.best_days[channel]) > 10:
            profile.best_days[channel] = profile.best_days[channel][-10:]

        # Update confidence score based on engagement history
        engagement_count = len(self.engagement_history[lead_id])
        profile.confidence_score = min(0.95, engagement_count * 0.1)

        profile.last_updated = datetime.now()

    def _get_engagement_weight(self, event_type: str) -> float:
        """Get weight for different engagement types"""
        weights = {"click": 1.0, "reply": 1.5, "call_answered": 2.0, "open": 0.5, "view": 0.3}
        return weights.get(event_type, 0.5)

    async def _update_global_patterns(self, engagement_event: EngagementEvent):
        """Update global timing patterns"""

        channel_key = engagement_event.channel.value

        # Update global best hours
        if channel_key not in self.global_patterns["best_hours_by_channel"]:
            self.global_patterns["best_hours_by_channel"][channel_key] = []

        hour_data = {
            "hour": engagement_event.timestamp.hour,
            "weight": self._get_engagement_weight(engagement_event.event_type),
            "timestamp": engagement_event.timestamp,
        }

        self.global_patterns["best_hours_by_channel"][channel_key].append(hour_data)

        # Keep recent data only
        cutoff_date = datetime.now() - timedelta(days=30)
        self.global_patterns["best_hours_by_channel"][channel_key] = [
            h for h in self.global_patterns["best_hours_by_channel"][channel_key] if h["timestamp"] > cutoff_date
        ]

    def _determine_timezone(self, lead_data: Dict[str, Any]) -> str:
        """Determine lead's timezone from available data"""

        # Check explicit timezone field
        if "timezone" in lead_data:
            return lead_data["timezone"]

        # Infer from location data
        if "state" in lead_data:
            state_timezones = {
                "CA": "America/Los_Angeles",
                "NY": "America/New_York",
                "TX": "America/Chicago",
                "FL": "America/New_York",
                "IL": "America/Chicago",
                "CO": "America/Denver",
                # Add more states as needed
            }
            return state_timezones.get(lead_data["state"], "America/New_York")

        if "city" in lead_data:
            city_timezones = {
                "los angeles": "America/Los_Angeles",
                "new york": "America/New_York",
                "chicago": "America/Chicago",
                "denver": "America/Denver",
                "phoenix": "America/Phoenix",
                "miami": "America/New_York",
                # Add more cities as needed
            }
            city_lower = lead_data["city"].lower()
            for city, tz in city_timezones.items():
                if city in city_lower:
                    return tz

        # Default to EST
        return "America/New_York"

    async def _adjust_for_lead_data(self, base_pattern: Dict[str, Any], lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust timing patterns based on lead demographics"""

        adjusted_pattern = base_pattern.copy()

        # Industry-specific adjustments
        industry = lead_data.get("industry", "").lower()

        if "healthcare" in industry:
            # Healthcare professionals often check email early
            adjusted_pattern["preferred_hours"] = [7, 8, 9, 10, 11, 13, 14, 15]
        elif "retail" in industry:
            # Retail often works evenings/weekends
            adjusted_pattern["preferred_hours"] = [10, 11, 12, 13, 14, 15, 16, 17]
            adjusted_pattern["preferred_days"] = [0, 1, 2, 3, 4, 5, 6]  # All days
        elif "finance" in industry:
            # Finance typically strict business hours
            adjusted_pattern["preferred_hours"] = [9, 10, 11, 14, 15, 16]
            adjusted_pattern["preferred_days"] = [0, 1, 2, 3, 4]  # Weekdays only

        # Job title adjustments
        job_title = lead_data.get("job_title", "").lower()

        if any(title in job_title for title in ["ceo", "president", "executive"]):
            # Executives often check email early/late
            adjusted_pattern["preferred_hours"] = [7, 8, 9, 17, 18, 19]
        elif "manager" in job_title:
            # Managers often busiest mid-day
            adjusted_pattern["preferred_hours"] = [8, 9, 10, 15, 16, 17]

        return adjusted_pattern

    async def _is_time_available(self, candidate_time: datetime) -> bool:
        """Check if time slot is available (no conflicts)"""

        # Check for business hours (basic validation)
        hour = candidate_time.hour
        day_of_week = candidate_time.weekday()

        # Avoid very early morning or very late night
        if hour < 6 or hour > 21:
            return False

        # Weekend restrictions for professional communications
        if day_of_week in [5, 6]:  # Saturday, Sunday
            if hour < 10 or hour > 18:
                return False

        return True

    async def _get_next_business_hour(self, base_time: datetime) -> datetime:
        """Get next available business hour"""

        # Business hours: 9 AM - 5 PM, weekdays
        business_hours = [9, 10, 11, 12, 13, 14, 15, 16, 17]
        business_days = [0, 1, 2, 3, 4]  # Monday-Friday

        current_time = base_time
        max_days_ahead = 7

        for day_offset in range(max_days_ahead):
            check_time = current_time + timedelta(days=day_offset)

            if check_time.weekday() in business_days:
                for hour in business_hours:
                    candidate_time = check_time.replace(hour=hour, minute=0, second=0, microsecond=0)

                    if candidate_time > base_time:
                        return candidate_time

        # Fallback: next Monday 9 AM
        days_until_monday = (7 - base_time.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7

        next_monday = base_time + timedelta(days=days_until_monday)
        return next_monday.replace(hour=9, minute=0, second=0, microsecond=0)

    async def get_channel_performance_analysis(
        self, lead_id: Optional[str] = None, days_back: int = 30
    ) -> Dict[str, Any]:
        """Analyze performance across different channels and times"""

        cutoff_date = datetime.now() - timedelta(days=days_back)

        analysis = {"channel_performance": {}, "best_hours_global": {}, "best_days_global": {}, "lead_specific": None}

        # Analyze specific lead if provided
        if lead_id and lead_id in self.engagement_history:
            events = [e for e in self.engagement_history[lead_id] if e.timestamp > cutoff_date]

            if events:
                analysis["lead_specific"] = await self._analyze_lead_patterns(events)

        # Global analysis across all leads
        all_events = []
        for events_list in self.engagement_history.values():
            all_events.extend([e for e in events_list if e.timestamp > cutoff_date])

        if all_events:
            analysis["channel_performance"] = await self._analyze_channel_performance(all_events)
            analysis["best_hours_global"] = await self._analyze_best_hours(all_events)
            analysis["best_days_global"] = await self._analyze_best_days(all_events)

        return analysis

    async def _analyze_lead_patterns(self, events: List[EngagementEvent]) -> Dict[str, Any]:
        """Analyze patterns for specific lead"""

        by_channel = defaultdict(list)
        by_hour = defaultdict(int)
        by_day = defaultdict(int)

        for event in events:
            by_channel[event.channel].append(event)
            by_hour[event.timestamp.hour] += 1
            by_day[event.timestamp.weekday()] += 1

        # Find best performing hours and days
        best_hours = sorted(by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
        best_days = sorted(by_day.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            "total_engagements": len(events),
            "channels_used": list(by_channel.keys()),
            "best_hours": [h[0] for h in best_hours],
            "best_days": [d[0] for d in best_days],
            "engagement_by_channel": {str(channel): len(events) for channel, events in by_channel.items()},
        }

    async def _analyze_channel_performance(self, events: List[EngagementEvent]) -> Dict[str, Any]:
        """Analyze performance across channels"""

        by_channel = defaultdict(list)
        for event in events:
            by_channel[event.channel].append(event)

        performance = {}
        for channel, channel_events in by_channel.items():
            # Calculate average time to engagement
            times_to_engagement = [
                e.time_to_engagement.total_seconds() / 3600  # Convert to hours
                for e in channel_events
            ]

            avg_time = statistics.mean(times_to_engagement) if times_to_engagement else 0

            performance[str(channel)] = {
                "total_engagements": len(channel_events),
                "avg_time_to_engagement_hours": round(avg_time, 2),
                "engagement_rate": len(channel_events) / len(events) if events else 0,
            }

        return performance

    async def _analyze_best_hours(self, events: List[EngagementEvent]) -> Dict[str, List[int]]:
        """Analyze best hours by channel"""

        by_channel_hour = defaultdict(lambda: defaultdict(int))

        for event in events:
            by_channel_hour[event.channel][event.timestamp.hour] += 1

        best_hours = {}
        for channel, hour_counts in by_channel_hour.items():
            sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
            best_hours[str(channel)] = [hour for hour, count in sorted_hours[:5]]

        return best_hours

    async def _analyze_best_days(self, events: List[EngagementEvent]) -> Dict[str, List[int]]:
        """Analyze best days by channel"""

        by_channel_day = defaultdict(lambda: defaultdict(int))

        for event in events:
            by_channel_day[event.channel][event.timestamp.weekday()] += 1

        best_days = {}
        for channel, day_counts in by_channel_day.items():
            sorted_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)
            best_days[str(channel)] = [day for day, count in sorted_days]

        return best_days

    async def optimize_workflow_timing(
        self, workflow_steps: List[Dict[str, Any]], lead_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Optimize timing for entire workflow"""

        optimized_steps = []
        current_time = datetime.now()

        for step in workflow_steps:
            step_copy = step.copy()

            # Skip if not a communication step
            if step.get("type") not in ["send_email", "send_sms", "make_call"]:
                optimized_steps.append(step_copy)
                continue

            # Determine channel
            channel_map = {"send_email": Channel.EMAIL, "send_sms": Channel.SMS, "make_call": Channel.VOICE}

            channel = channel_map.get(step["type"], Channel.EMAIL)

            # Get optimal timing
            timing_rec = await self.get_optimal_send_time(lead_data.get("id", ""), channel, current_time, lead_data)

            # Update step with optimized timing
            if "delay_config" not in step_copy:
                step_copy["delay_config"] = {}

            # Calculate delay from current time
            delay_seconds = (timing_rec.recommended_time - current_time).total_seconds()
            step_copy["delay_config"]["seconds"] = max(0, int(delay_seconds))
            step_copy["delay_config"]["type"] = "optimal_timing"
            step_copy["delay_config"]["reasoning"] = timing_rec.reasoning

            # Update current time for next step
            current_time = timing_rec.recommended_time + timedelta(minutes=5)

            optimized_steps.append(step_copy)

        return optimized_steps

    def get_lead_profile_summary(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of lead's timing profile"""

        if lead_id not in self.lead_profiles:
            return None

        profile = self.lead_profiles[lead_id]
        engagement_count = len(self.engagement_history.get(lead_id, []))

        return {
            "lead_id": lead_id,
            "timezone": profile.timezone,
            "confidence_score": profile.confidence_score,
            "engagement_count": engagement_count,
            "preferred_hours": profile.preferred_hours,
            "best_days": profile.best_days,
            "last_updated": profile.last_updated.isoformat(),
        }

    async def bulk_optimize_timing(
        self, lead_ids: List[str], channel: Channel, base_time: Optional[datetime] = None
    ) -> Dict[str, TimingRecommendation]:
        """Optimize timing for multiple leads simultaneously"""

        if base_time is None:
            base_time = datetime.now()

        recommendations = {}

        # Process leads in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(lead_ids), batch_size):
            batch = lead_ids[i : i + batch_size]

            tasks = [self.get_optimal_send_time(lead_id, channel, base_time) for lead_id in batch]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for lead_id, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to optimize timing for {lead_id}: {result}")
                    # Provide fallback recommendation
                    recommendations[lead_id] = TimingRecommendation(
                        recommended_time=base_time,
                        confidence_score=0.1,
                        reasoning="Error occurred, using fallback timing",
                        channel=channel,
                    )
                else:
                    recommendations[lead_id] = result

        return recommendations
