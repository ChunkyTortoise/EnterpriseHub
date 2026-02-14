"""
Specialized Feature Extractors

Modular feature extraction components for different aspects of user behavior.
Each extractor focuses on a specific ontario_mills of features.
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np

from ..interfaces import BehavioralEvent, EventType

logger = logging.getLogger(__name__)


class PropertyFeatureExtractor:
    """
    Extracts features related to property interactions and preferences.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.price_ranges = self.config.get(
            "price_ranges", [(0, 300000), (300000, 600000), (600000, 1000000), (1000000, float("inf"))]
        )

    def extract_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Extract property-related features"""

        features = {}
        property_events = [e for e in events if e.property_id and e.event_data]

        if not property_events:
            return self._empty_property_features()

        # Property type preferences
        property_types = [
            e.event_data.get("property_type") for e in property_events if e.event_data.get("property_type")
        ]
        if property_types:
            type_counter = Counter(property_types)
            features["property_type_diversity"] = len(type_counter) / len(property_types)
            features["most_viewed_type_ratio"] = type_counter.most_common(1)[0][1] / len(property_types)

        # Price range analysis
        prices = [
            e.event_data.get("price")
            for e in property_events
            if e.event_data.get("price") and isinstance(e.event_data.get("price"), (int, float))
        ]

        if prices:
            features["avg_price_viewed"] = np.mean(prices)
            features["min_price_viewed"] = min(prices)
            features["max_price_viewed"] = max(prices)
            features["price_std"] = np.std(prices)
            features["price_range_span"] = max(prices) - min(prices)

            # Price range preferences
            range_counts = self._categorize_prices_by_range(prices)
            total_views = sum(range_counts.values())
            for i, count in range_counts.items():
                features[f"price_range_{i}_ratio"] = count / total_views

        # Location preferences
        locations = [e.event_data.get("location") for e in property_events if e.event_data.get("location")]
        if locations:
            location_counter = Counter(locations)
            features["location_diversity"] = len(location_counter) / len(locations)
            features["location_concentration"] = location_counter.most_common(1)[0][1] / len(locations)

        # Property size preferences
        sizes = [
            e.event_data.get("square_feet")
            for e in property_events
            if e.event_data.get("square_feet") and isinstance(e.event_data.get("square_feet"), (int, float))
        ]
        if sizes:
            features["avg_size_preference"] = np.mean(sizes)
            features["size_preference_std"] = np.std(sizes)

        bedrooms = [
            e.event_data.get("bedrooms")
            for e in property_events
            if e.event_data.get("bedrooms") and isinstance(e.event_data.get("bedrooms"), int)
        ]
        if bedrooms:
            features["avg_bedrooms_preference"] = np.mean(bedrooms)
            features["bedroom_preference_std"] = np.std(bedrooms)

        # Property feature preferences
        features_mentioned = []
        for event in property_events:
            if event.event_data.get("features"):
                features_mentioned.extend(event.event_data["features"])

        if features_mentioned:
            feature_counter = Counter(features_mentioned)
            features["property_features_diversity"] = len(feature_counter) / len(features_mentioned)

        return features

    def _categorize_prices_by_range(self, prices: List[float]) -> Dict[int, int]:
        """Categorize prices into predefined ranges"""
        range_counts = defaultdict(int)

        for price in prices:
            for i, (min_price, max_price) in enumerate(self.price_ranges):
                if min_price <= price < max_price:
                    range_counts[i] += 1
                    break

        return dict(range_counts)

    def _empty_property_features(self) -> Dict[str, float]:
        """Return default values when no property data available"""
        return {
            "property_type_diversity": 0.0,
            "avg_price_viewed": 0.0,
            "location_diversity": 0.0,
            "avg_size_preference": 0.0,
        }


class BehaviorFeatureExtractor:
    """
    Extracts features related to user behavior patterns and engagement.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.engagement_weights = self.config.get(
            "engagement_weights",
            {
                EventType.PROPERTY_VIEW.value: 1.0,
                EventType.PROPERTY_SWIPE.value: 2.0,
                EventType.PROPERTY_SAVE.value: 3.0,
                EventType.PROPERTY_SHARE.value: 2.5,
                EventType.BOOKING_REQUEST.value: 5.0,
                EventType.BOOKING_COMPLETED.value: 7.0,
            },
        )

    def extract_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Extract behavioral pattern features"""

        features = {}

        if not events:
            return self._empty_behavior_features()

        # Engagement patterns
        features.update(self._calculate_engagement_features(events))

        # Interaction velocity
        features.update(self._calculate_velocity_features(events))

        # Decision patterns
        features.update(self._calculate_decision_features(events))

        # Exploration vs exploitation
        features.update(self._calculate_exploration_features(events))

        return features

    def _calculate_engagement_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Calculate engagement-related features"""

        features = {}

        # Basic engagement metrics
        total_engagement = sum(self.engagement_weights.get(e.event_type.value, 1.0) for e in events)
        features["total_engagement_score"] = total_engagement
        features["avg_engagement_per_event"] = total_engagement / len(events)

        # Engagement distribution
        engagement_scores = [self.engagement_weights.get(e.event_type.value, 1.0) for e in events]
        features["engagement_std"] = np.std(engagement_scores)
        features["max_engagement_event"] = max(engagement_scores)

        # High-value action ratio
        high_value_actions = sum(1 for e in events if self.engagement_weights.get(e.event_type.value, 1.0) >= 3.0)
        features["high_value_action_ratio"] = high_value_actions / len(events)

        return features

    def _calculate_velocity_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Calculate interaction velocity features"""

        features = {}

        if len(events) < 2:
            return {"interaction_velocity": 0.0}

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Calculate time between consecutive events
        time_deltas = []
        for i in range(1, len(sorted_events)):
            delta = (sorted_events[i].timestamp - sorted_events[i - 1].timestamp).total_seconds()
            time_deltas.append(delta)

        if time_deltas:
            features["avg_time_between_events"] = np.mean(time_deltas)
            features["interaction_velocity"] = 1.0 / max(np.mean(time_deltas), 1)  # Events per second
            features["interaction_consistency"] = 1.0 / (1.0 + np.std(time_deltas))

        # Burst patterns
        short_intervals = sum(1 for delta in time_deltas if delta < 30)  # Less than 30 seconds
        features["burst_interaction_ratio"] = short_intervals / len(time_deltas) if time_deltas else 0

        return features

    def _calculate_decision_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Calculate decision-making pattern features"""

        features = {}

        # Like/dislike patterns
        swipe_events = [e for e in events if e.event_type == EventType.PROPERTY_SWIPE]
        if swipe_events:
            likes = sum(1 for e in swipe_events if e.event_data and e.event_data.get("liked", False))
            features["like_ratio"] = likes / len(swipe_events)
            features["decision_confidence"] = abs(features["like_ratio"] - 0.5) * 2  # Distance from neutral

        # Save behavior
        save_events = [e for e in events if e.event_type == EventType.PROPERTY_SAVE]
        view_events = [e for e in events if e.event_type == EventType.PROPERTY_VIEW]
        if view_events:
            features["save_rate"] = len(save_events) / len(view_events)

        # Booking decisiveness
        booking_requests = [e for e in events if e.event_type == EventType.BOOKING_REQUEST]
        booking_completions = [e for e in events if e.event_type == EventType.BOOKING_COMPLETED]
        if booking_requests:
            features["booking_follow_through"] = len(booking_completions) / len(booking_requests)

        return features

    def _calculate_exploration_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Calculate exploration vs exploitation patterns"""

        features = {}

        property_events = [e for e in events if e.property_id]
        if not property_events:
            return {"exploration_ratio": 0.0}

        # Unique properties vs total property interactions
        unique_properties = set(e.property_id for e in property_events)
        features["exploration_ratio"] = len(unique_properties) / len(property_events)

        # Property revisit patterns
        property_counts = Counter(e.property_id for e in property_events)
        revisited_properties = sum(1 for count in property_counts.values() if count > 1)
        features["property_loyalty"] = revisited_properties / len(unique_properties)

        # Search refinement behavior
        search_events = [e for e in events if e.event_type == EventType.SEARCH_QUERY]
        filter_events = [e for e in events if e.event_type == EventType.FILTER_APPLIED]

        if search_events:
            features["search_refinement_rate"] = len(filter_events) / len(search_events)

        return features

    def _empty_behavior_features(self) -> Dict[str, float]:
        """Return default values when no behavioral data available"""
        return {
            "total_engagement_score": 0.0,
            "avg_engagement_per_event": 0.0,
            "interaction_velocity": 0.0,
            "like_ratio": 0.5,
            "exploration_ratio": 0.0,
        }


class SessionFeatureExtractor:
    """
    Extracts features related to user sessions and temporal patterns.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.session_timeout_minutes = self.config.get("session_timeout_minutes", 30)

    def extract_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Extract session-related features"""

        features = {}

        if not events:
            return self._empty_session_features()

        # Explicit session analysis
        features.update(self._analyze_explicit_sessions(events))

        # Inferred session analysis
        features.update(self._analyze_inferred_sessions(events))

        # Cross-session patterns
        features.update(self._analyze_cross_session_patterns(events))

        return features

    def _analyze_explicit_sessions(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Analyze sessions based on session IDs"""

        features = {}
        session_events = defaultdict(list)

        # Group events by session ID
        for event in events:
            if event.session_id:
                session_events[event.session_id].append(event)

        if not session_events:
            return {"explicit_sessions_count": 0.0}

        # Session statistics
        features["explicit_sessions_count"] = float(len(session_events))

        session_lengths = [len(events) for events in session_events.values()]
        features["avg_session_length"] = np.mean(session_lengths)
        features["max_session_length"] = max(session_lengths)
        features["session_length_std"] = np.std(session_lengths)

        # Session duration analysis
        session_durations = []
        for events in session_events.values():
            if len(events) > 1:
                sorted_events = sorted(events, key=lambda e: e.timestamp)
                duration = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()
                session_durations.append(duration)

        if session_durations:
            features["avg_session_duration_seconds"] = np.mean(session_durations)
            features["max_session_duration_seconds"] = max(session_durations)

        return features

    def _analyze_inferred_sessions(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Infer sessions based on time gaps"""

        features = {}

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Identify session boundaries based on time gaps
        sessions = []
        current_session = [sorted_events[0]]

        for i in range(1, len(sorted_events)):
            time_gap = (sorted_events[i].timestamp - sorted_events[i - 1].timestamp).total_seconds()

            if time_gap > self.session_timeout_minutes * 60:
                # Start new session
                sessions.append(current_session)
                current_session = [sorted_events[i]]
            else:
                # Continue current session
                current_session.append(sorted_events[i])

        sessions.append(current_session)  # Add final session

        # Analyze inferred sessions
        features["inferred_sessions_count"] = float(len(sessions))

        session_lengths = [len(session) for session in sessions]
        features["avg_inferred_session_length"] = np.mean(session_lengths)

        session_durations = []
        for session in sessions:
            if len(session) > 1:
                duration = (session[-1].timestamp - session[0].timestamp).total_seconds()
                session_durations.append(duration)

        if session_durations:
            features["avg_inferred_session_duration"] = np.mean(session_durations)

        return features

    def _analyze_cross_session_patterns(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Analyze patterns across sessions"""

        features = {}

        # Group events by date
        daily_events = defaultdict(list)
        for event in events:
            date_key = event.timestamp.date()
            daily_events[date_key].append(event)

        if daily_events:
            features["active_days"] = float(len(daily_events))

            daily_event_counts = [len(events) for events in daily_events.values()]
            features["avg_events_per_day"] = np.mean(daily_event_counts)
            features["max_events_per_day"] = max(daily_event_counts)

        # Weekly patterns
        weekday_counts = Counter(event.timestamp.weekday() for event in events)
        if weekday_counts:
            features["weekday_consistency"] = 1.0 - (
                np.std(list(weekday_counts.values())) / np.mean(list(weekday_counts.values()))
            )

        # Time of day patterns
        hourly_counts = Counter(event.timestamp.hour for event in events)
        if hourly_counts:
            features["time_concentration"] = max(hourly_counts.values()) / sum(hourly_counts.values())

        return features

    def _empty_session_features(self) -> Dict[str, float]:
        """Return default values when no session data available"""
        return {
            "explicit_sessions_count": 0.0,
            "avg_session_length": 0.0,
            "inferred_sessions_count": 0.0,
            "active_days": 0.0,
        }


class TimeFeatureExtractor:
    """
    Extracts temporal and time-based features from user behavior.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def extract_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Extract temporal features"""

        features = {}

        if not events:
            return self._empty_temporal_features()

        # Basic temporal statistics
        features.update(self._calculate_basic_temporal_features(events))

        # Periodicity features
        features.update(self._calculate_periodicity_features(events))

        # Trend features
        features.update(self._calculate_trend_features(events))

        # Recency features
        features.update(self._calculate_recency_features(events))

        return features

    def _calculate_basic_temporal_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Calculate basic temporal statistics"""

        features = {}

        timestamps = [event.timestamp for event in events]

        # Time span
        time_span = (max(timestamps) - min(timestamps)).total_seconds()
        features["activity_time_span_hours"] = time_span / 3600.0

        # Activity density
        features["events_per_hour"] = len(events) / max(time_span / 3600.0, 1)

        # Time distribution
        hours = [ts.hour for ts in timestamps]
        features["activity_hour_std"] = np.std(hours)
        features["peak_activity_hour"] = float(Counter(hours).most_common(1)[0][0])

        return features

    def _calculate_periodicity_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Calculate periodicity and regularity features"""

        features = {}

        # Daily patterns
        dates = [event.timestamp.date() for event in events]
        unique_dates = sorted(set(dates))

        if len(unique_dates) > 1:
            # Calculate gaps between active days
            date_gaps = []
            for i in range(1, len(unique_dates)):
                gap = (unique_dates[i] - unique_dates[i - 1]).days
                date_gaps.append(gap)

            if date_gaps:
                features["avg_days_between_sessions"] = np.mean(date_gaps)
                features["session_regularity"] = 1.0 / (1.0 + np.std(date_gaps))

        # Weekly patterns
        weekdays = [event.timestamp.weekday() for event in events]
        weekday_distribution = [weekdays.count(i) for i in range(7)]
        features["weekday_entropy"] = self._calculate_entropy(weekday_distribution)

        # Hourly patterns
        hours = [event.timestamp.hour for event in events]
        hourly_distribution = [hours.count(i) for i in range(24)]
        features["hourly_entropy"] = self._calculate_entropy(hourly_distribution)

        return features

    def _calculate_trend_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Calculate trend and evolution features"""

        features = {}

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Activity trend over time
        if len(sorted_events) >= 7:  # Need enough data points
            # Divide timeline into segments and analyze activity levels
            total_duration = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()
            segment_duration = total_duration / 5  # 5 segments

            segment_counts = []
            for i in range(5):
                segment_start = sorted_events[0].timestamp.timestamp() + (i * segment_duration)
                segment_end = segment_start + segment_duration

                count = sum(1 for event in sorted_events if segment_start <= event.timestamp.timestamp() < segment_end)
                segment_counts.append(count)

            # Calculate trend slope
            x = np.arange(len(segment_counts))
            if np.std(x) > 0 and np.std(segment_counts) > 0:
                correlation = np.corrcoef(x, segment_counts)[0, 1]
                features["activity_trend_slope"] = correlation
            else:
                features["activity_trend_slope"] = 0.0

        return features

    def _calculate_recency_features(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Calculate recency and freshness features"""

        features = {}

        now = datetime.now()
        latest_event = max(events, key=lambda e: e.timestamp)

        # Time since last activity
        time_since_last = (now - latest_event.timestamp).total_seconds()
        features["hours_since_last_activity"] = time_since_last / 3600.0
        features["days_since_last_activity"] = time_since_last / (24 * 3600.0)

        # Recent activity patterns
        recent_cutoff = now - timedelta(hours=24)
        recent_events = [e for e in events if e.timestamp >= recent_cutoff]
        features["recent_activity_count"] = float(len(recent_events))
        features["recent_activity_ratio"] = len(recent_events) / len(events)

        return features

    def _calculate_entropy(self, distribution: List[int]) -> float:
        """Calculate entropy of a distribution"""

        total = sum(distribution)
        if total == 0:
            return 0.0

        probabilities = [count / total for count in distribution if count > 0]
        entropy = -sum(p * np.log2(p) for p in probabilities)

        # Normalize by maximum possible entropy
        max_entropy = np.log2(len(distribution))
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def _empty_temporal_features(self) -> Dict[str, float]:
        """Return default values when no temporal data available"""
        return {
            "activity_time_span_hours": 0.0,
            "events_per_hour": 0.0,
            "hours_since_last_activity": 999.0,
            "recent_activity_count": 0.0,
        }
