"""
Standard Feature Engineering Implementation

Transforms behavioral events into feature vectors for machine learning models.
Provides comprehensive feature extraction for property, behavior, and contextual features.
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging

from ..interfaces import (
    IFeatureEngineer, IBehaviorTracker, BehavioralEvent,
    FeatureVector, EventType, FeatureType, FeatureExtractionError
)

logger = logging.getLogger(__name__)


class StandardFeatureEngineer(IFeatureEngineer):
    """
    Standard implementation of feature engineering pipeline.

    Extracts numerical, categorical, and behavioral features from events
    to create ML-ready feature vectors for personalization and recommendations.
    """

    def __init__(self, tracker: IBehaviorTracker, config: Dict[str, Any] = None):
        self.tracker = tracker
        self.config = config or {}

        # Feature extraction configuration
        self.lookback_days = self.config.get("lookback_days", 30)
        self.min_events_threshold = self.config.get("min_events_threshold", 5)
        self.session_timeout_minutes = self.config.get("session_timeout_minutes", 30)

        # Feature normalization settings
        self.normalize_features = self.config.get("normalize_features", True)
        self.feature_scaling_method = self.config.get("feature_scaling_method", "min_max")

        # Behavioral pattern detection
        self.pattern_window_hours = self.config.get("pattern_window_hours", 24)
        self.engagement_score_weights = self.config.get("engagement_score_weights", {
            "view": 1.0,
            "like": 2.0,
            "save": 3.0,
            "share": 2.5,
            "booking": 5.0
        })

        # Statistical tracking
        self.stats = {
            "features_extracted": 0,
            "feature_cache_hits": 0,
            "extraction_errors": 0,
            "processing_time_ms": []
        }

        # Feature cache for performance
        self._feature_cache: Dict[str, FeatureVector] = {}
        self._cache_ttl_minutes = self.config.get("cache_ttl_minutes", 15)

    async def extract_features(
        self,
        entity_id: str,
        entity_type: str,
        events: List[BehavioralEvent],
        context: Optional[Dict[str, Any]] = None
    ) -> FeatureVector:
        """Extract comprehensive feature vector for entity"""

        start_time = datetime.now()

        try:
            # Check cache first
            cache_key = f"{entity_type}_{entity_id}"
            cached_features = self._get_cached_features(cache_key)
            if cached_features:
                self.stats["feature_cache_hits"] += 1
                return cached_features

            # Filter events by lookback period
            cutoff_time = datetime.now() - timedelta(days=self.lookback_days)
            filtered_events = [e for e in events if e.timestamp >= cutoff_time]

            if len(filtered_events) < self.min_events_threshold:
                logger.warning(f"Insufficient events ({len(filtered_events)}) for {entity_type}:{entity_id}")
                # Return minimal feature vector
                return self._create_minimal_features(entity_id, entity_type)

            # Extract different types of features
            numerical_features = await self._extract_numerical_features(filtered_events, context)
            categorical_features = await self._extract_categorical_features(filtered_events, context)
            behavioral_features = await self._extract_behavioral_features(filtered_events, context)
            temporal_features = await self._extract_temporal_features(filtered_events, context)

            # Combine all features
            all_numerical = {
                **numerical_features,
                **behavioral_features,
                **temporal_features
            }

            # Normalize if configured
            if self.normalize_features:
                all_numerical = self._normalize_features(all_numerical)

            # Create feature vector
            feature_vector = FeatureVector(
                entity_id=entity_id,
                entity_type=entity_type,
                numerical_features=all_numerical,
                categorical_features=categorical_features,
                feature_names=list(all_numerical.keys()) + list(categorical_features.keys()),
                extraction_timestamp=datetime.now(),
                metadata={
                    "event_count": len(filtered_events),
                    "lookback_days": self.lookback_days,
                    "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "feature_extraction_version": "1.0.0"
                }
            )

            # Cache the result
            self._cache_features(cache_key, feature_vector)

            # Update stats
            self.stats["features_extracted"] += 1
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.stats["processing_time_ms"].append(processing_time)

            return feature_vector

        except Exception as e:
            self.stats["extraction_errors"] += 1
            logger.error(f"Feature extraction failed for {entity_type}:{entity_id}: {e}")
            raise FeatureExtractionError(f"Failed to extract features: {e}") from e

    async def extract_features_batch(
        self,
        entities: List[Tuple[str, str]],  # (entity_id, entity_type) pairs
        context: Optional[Dict[str, Any]] = None
    ) -> List[FeatureVector]:
        """Extract features for multiple entities efficiently"""

        # Process in parallel with controlled concurrency
        max_concurrent = self.config.get("max_concurrent_extractions", 10)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_single(entity_id: str, entity_type: str) -> FeatureVector:
            async with semaphore:
                return await self.extract_features(entity_id, entity_type, context)

        # Execute batch extraction
        tasks = [extract_single(entity_id, entity_type) for entity_id, entity_type in entities]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        feature_vectors = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                entity_id, entity_type = entities[i]
                logger.error(f"Batch extraction failed for {entity_type}:{entity_id}: {result}")
                self.stats["extraction_errors"] += 1
            else:
                feature_vectors.append(result)

        return feature_vectors

    async def _extract_numerical_features(
        self,
        events: List[BehavioralEvent],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Extract numerical features from events"""

        features = {}

        # Basic counting features
        features["total_events"] = float(len(events))
        features["unique_sessions"] = float(len(set(e.session_id for e in events if e.session_id)))
        features["unique_properties"] = float(len(set(e.property_id for e in events if e.property_id)))

        # Event type distribution
        event_counts = Counter(e.event_type for e in events)
        for event_type in EventType:
            features[f"{event_type.value}_count"] = float(event_counts.get(event_type, 0))

        # Time-based features
        if events:
            timestamps = [e.timestamp for e in events]
            time_span = (max(timestamps) - min(timestamps)).total_seconds()
            features["activity_time_span_hours"] = time_span / 3600.0
            features["avg_events_per_hour"] = features["total_events"] / max(time_span / 3600.0, 1)

        # Property interaction features
        property_events = [e for e in events if e.property_id]
        if property_events:
            property_view_durations = []
            for event in property_events:
                if event.event_type == EventType.PROPERTY_VIEW and event.event_data:
                    duration = event.event_data.get("view_duration_seconds", 0)
                    if duration > 0:
                        property_view_durations.append(duration)

            if property_view_durations:
                features["avg_view_duration_seconds"] = np.mean(property_view_durations)
                features["max_view_duration_seconds"] = max(property_view_durations)
                features["total_view_time_seconds"] = sum(property_view_durations)

        # Engagement scoring
        engagement_score = 0.0
        for event in events:
            event_weight = self._get_engagement_weight(event)
            engagement_score += event_weight

        features["engagement_score"] = engagement_score
        features["avg_engagement_per_event"] = engagement_score / max(len(events), 1)

        # Booking behavior
        booking_events = [e for e in events if e.event_type == EventType.BOOKING_REQUEST]
        features["booking_requests_count"] = float(len(booking_events))

        completed_bookings = [e for e in events if e.event_type == EventType.BOOKING_COMPLETED]
        features["booking_completions_count"] = float(len(completed_bookings))

        if booking_events:
            features["booking_completion_rate"] = len(completed_bookings) / len(booking_events)
        else:
            features["booking_completion_rate"] = 0.0

        return features

    async def _extract_categorical_features(
        self,
        events: List[BehavioralEvent],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Extract categorical features from events"""

        features = {}

        # Most common event type
        if events:
            event_counts = Counter(e.event_type for e in events)
            most_common_event = event_counts.most_common(1)[0][0]
            features["primary_event_type"] = most_common_event.value

        # Device preferences
        devices = [e.event_data.get("device_type") for e in events
                  if e.event_data and "device_type" in e.event_data]
        if devices:
            device_counts = Counter(devices)
            features["preferred_device"] = device_counts.most_common(1)[0][0]

        # Property type preferences
        property_types = []
        for event in events:
            if event.property_id and event.event_data:
                prop_type = event.event_data.get("property_type")
                if prop_type:
                    property_types.append(prop_type)

        if property_types:
            type_counts = Counter(property_types)
            features["preferred_property_type"] = type_counts.most_common(1)[0][0]

        # Time of day preference
        hour_counts = Counter(e.timestamp.hour for e in events)
        if hour_counts:
            preferred_hour = hour_counts.most_common(1)[0][0]
            if 6 <= preferred_hour < 12:
                features["preferred_time_period"] = "morning"
            elif 12 <= preferred_hour < 18:
                features["preferred_time_period"] = "afternoon"
            elif 18 <= preferred_hour < 22:
                features["preferred_time_period"] = "evening"
            else:
                features["preferred_time_period"] = "night"

        return features

    async def _extract_behavioral_features(
        self,
        events: List[BehavioralEvent],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Extract behavioral pattern features"""

        features = {}

        # Session-based features
        sessions = self._group_events_by_session(events)
        if sessions:
            session_lengths = [len(session_events) for session_events in sessions.values()]
            features["avg_session_length"] = np.mean(session_lengths)
            features["max_session_length"] = max(session_lengths)

            session_durations = []
            for session_events in sessions.values():
                if len(session_events) > 1:
                    timestamps = [e.timestamp for e in session_events]
                    duration = (max(timestamps) - min(timestamps)).total_seconds()
                    session_durations.append(duration)

            if session_durations:
                features["avg_session_duration_seconds"] = np.mean(session_durations)
                features["max_session_duration_seconds"] = max(session_durations)

        # Property exploration patterns
        property_sequences = self._extract_property_sequences(events)
        if property_sequences:
            features["avg_properties_per_sequence"] = np.mean([len(seq) for seq in property_sequences])
            features["max_properties_per_sequence"] = max(len(seq) for seq in property_sequences)

            # Calculate property revisit rate
            revisits = 0
            total_views = 0
            for sequence in property_sequences:
                unique_properties = set(sequence)
                total_views += len(sequence)
                revisits += len(sequence) - len(unique_properties)

            features["property_revisit_rate"] = revisits / max(total_views, 1)

        # Search refinement patterns
        search_events = [e for e in events if e.event_type == EventType.SEARCH_QUERY]
        filter_events = [e for e in events if e.event_type == EventType.FILTER_APPLIED]

        if search_events:
            features["searches_per_session"] = len(search_events) / max(len(sessions), 1)
            features["filters_per_search"] = len(filter_events) / len(search_events)

        # Conversion funnel features
        features.update(self._calculate_conversion_rates(events))

        return features

    async def _extract_temporal_features(
        self,
        events: List[BehavioralEvent],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Extract time-based features"""

        features = {}

        if not events:
            return features

        # Recency features
        now = datetime.now()
        latest_event = max(events, key=lambda e: e.timestamp)
        features["days_since_last_activity"] = (now - latest_event.timestamp).days

        # Activity frequency
        event_dates = [e.timestamp.date() for e in events]
        unique_dates = set(event_dates)
        features["active_days"] = float(len(unique_dates))
        features["events_per_active_day"] = len(events) / max(len(unique_dates), 1)

        # Weekly patterns
        weekday_counts = Counter(e.timestamp.weekday() for e in events)
        max_weekday = max(weekday_counts, key=weekday_counts.get) if weekday_counts else 0
        features["most_active_weekday"] = float(max_weekday)

        # Time distribution
        hours = [e.timestamp.hour for e in events]
        features["activity_time_std"] = float(np.std(hours))
        features["peak_activity_hour"] = float(Counter(hours).most_common(1)[0][0])

        return features

    def _get_engagement_weight(self, event: BehavioralEvent) -> float:
        """Calculate engagement weight for an event"""

        base_weights = {
            EventType.PROPERTY_VIEW: 1.0,
            EventType.PROPERTY_SWIPE: 2.0,
            EventType.PROPERTY_SAVE: 3.0,
            EventType.PROPERTY_SHARE: 2.5,
            EventType.BOOKING_REQUEST: 5.0,
            EventType.BOOKING_COMPLETED: 7.0,
            EventType.SEARCH_QUERY: 1.5,
            EventType.FILTER_APPLIED: 1.2
        }

        weight = base_weights.get(event.event_type, 1.0)

        # Apply modifiers based on event data
        if event.event_data:
            # Long view duration increases weight
            if event.event_type == EventType.PROPERTY_VIEW:
                duration = event.event_data.get("view_duration_seconds", 0)
                if duration > 60:
                    weight *= 1.5
                elif duration > 30:
                    weight *= 1.2

            # High urgency booking requests get higher weight
            if event.event_type == EventType.BOOKING_REQUEST:
                urgency = event.event_data.get("urgency", "medium")
                if urgency == "high":
                    weight *= 1.3
                elif urgency == "low":
                    weight *= 0.8

        return weight

    def _group_events_by_session(self, events: List[BehavioralEvent]) -> Dict[str, List[BehavioralEvent]]:
        """Group events by session ID"""
        sessions = defaultdict(list)
        for event in events:
            if event.session_id:
                sessions[event.session_id].append(event)
        return dict(sessions)

    def _extract_property_sequences(self, events: List[BehavioralEvent]) -> List[List[str]]:
        """Extract sequences of property interactions"""
        sequences = []
        current_sequence = []

        property_events = [e for e in events if e.property_id]
        property_events.sort(key=lambda e: e.timestamp)

        for event in property_events:
            if event.event_type in [EventType.PROPERTY_VIEW, EventType.PROPERTY_SWIPE]:
                current_sequence.append(event.property_id)
            elif event.event_type in [EventType.SEARCH_QUERY, EventType.FILTER_APPLIED]:
                if current_sequence:
                    sequences.append(current_sequence)
                    current_sequence = []

        if current_sequence:
            sequences.append(current_sequence)

        return sequences

    def _calculate_conversion_rates(self, events: List[BehavioralEvent]) -> Dict[str, float]:
        """Calculate conversion rates through the funnel"""

        features = {}

        # Count events at each funnel stage
        views = len([e for e in events if e.event_type == EventType.PROPERTY_VIEW])
        likes = len([e for e in events if e.event_type == EventType.PROPERTY_SWIPE
                    and e.event_data.get("liked", False)])
        saves = len([e for e in events if e.event_type == EventType.PROPERTY_SAVE])
        bookings = len([e for e in events if e.event_type == EventType.BOOKING_REQUEST])
        completed = len([e for e in events if e.event_type == EventType.BOOKING_COMPLETED])

        # Calculate conversion rates
        features["view_to_like_rate"] = likes / max(views, 1)
        features["view_to_save_rate"] = saves / max(views, 1)
        features["view_to_booking_rate"] = bookings / max(views, 1)
        features["save_to_booking_rate"] = bookings / max(saves, 1)
        features["booking_completion_rate"] = completed / max(bookings, 1)

        return features

    def _normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Normalize numerical features"""

        if self.feature_scaling_method == "min_max":
            return self._min_max_normalize(features)
        elif self.feature_scaling_method == "z_score":
            return self._z_score_normalize(features)
        else:
            return features

    def _min_max_normalize(self, features: Dict[str, float]) -> Dict[str, float]:
        """Min-max normalization"""
        if not features:
            return features

        values = list(features.values())
        if not values:
            return features

        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            return {k: 0.5 for k in features.keys()}

        normalized = {}
        for key, value in features.items():
            normalized[key] = (value - min_val) / (max_val - min_val)

        return normalized

    def _z_score_normalize(self, features: Dict[str, float]) -> Dict[str, float]:
        """Z-score normalization"""
        if not features:
            return features

        values = list(features.values())
        if not values:
            return features

        mean_val = np.mean(values)
        std_val = np.std(values)

        if std_val == 0:
            return {k: 0.0 for k in features.keys()}

        normalized = {}
        for key, value in features.items():
            normalized[key] = (value - mean_val) / std_val

        return normalized

    def _create_minimal_features(self, entity_id: str, entity_type: str) -> FeatureVector:
        """Create minimal feature vector for entities with insufficient data"""

        return FeatureVector(
            entity_id=entity_id,
            entity_type=entity_type,
            numerical_features={
                "total_events": 0.0,
                "engagement_score": 0.0,
                "days_since_last_activity": 999.0
            },
            categorical_features={
                "primary_event_type": "unknown",
                "preferred_device": "unknown"
            },
            feature_names=[
                "total_events", "engagement_score", "days_since_last_activity",
                "primary_event_type", "preferred_device"
            ],
            extraction_timestamp=datetime.now(),
            metadata={
                "minimal_features": True,
                "reason": "insufficient_events"
            }
        )

    def _get_cached_features(self, cache_key: str) -> Optional[FeatureVector]:
        """Retrieve cached features if still valid"""

        if cache_key not in self._feature_cache:
            return None

        cached_features = self._feature_cache[cache_key]
        cache_age = datetime.now() - cached_features.extraction_timestamp

        if cache_age.total_seconds() > self._cache_ttl_minutes * 60:
            del self._feature_cache[cache_key]
            return None

        return cached_features

    def _cache_features(self, cache_key: str, features: FeatureVector):
        """Cache extracted features"""
        self._feature_cache[cache_key] = features

        # Clean up old cache entries
        if len(self._feature_cache) > 1000:
            self._cleanup_cache()

    def _cleanup_cache(self):
        """Remove expired entries from cache"""
        now = datetime.now()
        expired_keys = []

        for key, features in self._feature_cache.items():
            cache_age = now - features.extraction_timestamp
            if cache_age.total_seconds() > self._cache_ttl_minutes * 60:
                expired_keys.append(key)

        for key in expired_keys:
            del self._feature_cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get feature engineering statistics"""

        processing_times = self.stats["processing_time_ms"]

        return {
            **self.stats,
            "avg_processing_time_ms": np.mean(processing_times) if processing_times else 0,
            "cache_size": len(self._feature_cache),
            "cache_hit_rate": (self.stats["feature_cache_hits"] /
                             max(self.stats["features_extracted"] + self.stats["feature_cache_hits"], 1)) * 100
        }

    async def clear_cache(self):
        """Clear feature cache"""
        self._feature_cache.clear()

    async def batch_extract_features(
        self,
        entities: List[Tuple[str, str]],
        events_by_entity: Dict[str, List[BehavioralEvent]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, FeatureVector]:
        """Extract features for multiple entities efficiently"""

        results = {}

        # Process in parallel with controlled concurrency
        max_concurrent = self.config.get("max_concurrent_extractions", 10)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_single(entity_id: str, entity_type: str) -> Tuple[str, FeatureVector]:
            async with semaphore:
                entity_key = f"{entity_type}_{entity_id}"
                events = events_by_entity.get(entity_key, [])
                features = await self.extract_features(entity_id, entity_type, events, context)
                return entity_key, features

        # Execute batch extraction
        tasks = [extract_single(entity_id, entity_type) for entity_id, entity_type in entities]
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(completed_results):
            if isinstance(result, Exception):
                entity_id, entity_type = entities[i]
                logger.error(f"Batch extraction failed for {entity_type}:{entity_id}: {result}")
                self.stats["extraction_errors"] += 1
            else:
                entity_key, features = result
                results[entity_key] = features

        return results

    def get_feature_names(self) -> List[str]:
        """Get list of feature names that will be extracted"""

        # Base numerical features
        numerical_features = [
            "total_events", "unique_sessions", "unique_properties",
            "property_view_count", "property_swipe_count", "property_save_count",
            "search_query_count", "filter_applied_count", "booking_request_count",
            "activity_time_span_hours", "avg_events_per_hour",
            "avg_view_duration_seconds", "max_view_duration_seconds", "total_view_time_seconds",
            "engagement_score", "avg_engagement_per_event",
            "booking_requests_count", "booking_completions_count", "booking_completion_rate",
            "avg_session_length", "max_session_length", "avg_session_duration_seconds",
            "max_session_duration_seconds", "avg_properties_per_sequence",
            "max_properties_per_sequence", "property_revisit_rate",
            "searches_per_session", "filters_per_search",
            "days_since_last_activity", "active_days", "events_per_active_day",
            "activity_time_std", "peak_activity_hour",
            "view_to_like_rate", "view_to_save_rate", "view_to_booking_rate",
            "save_to_booking_rate",
            # Property features
            "property_type_diversity", "most_viewed_type_ratio", "avg_price_viewed",
            "min_price_viewed", "max_price_viewed", "price_std", "price_range_span",
            "location_diversity", "location_concentration", "avg_size_preference",
            "size_preference_std", "avg_bedrooms_preference", "bedroom_preference_std",
            "property_features_diversity",
            # Behavioral features
            "total_engagement_score", "engagement_std", "max_engagement_event",
            "high_value_action_ratio", "avg_time_between_events", "interaction_velocity",
            "interaction_consistency", "burst_interaction_ratio", "like_ratio",
            "decision_confidence", "save_rate", "booking_follow_through",
            "exploration_ratio", "property_loyalty", "search_refinement_rate",
            # Session features
            "explicit_sessions_count", "inferred_sessions_count",
            "avg_inferred_session_length", "avg_inferred_session_duration",
            "max_events_per_day", "weekday_consistency", "time_concentration",
            # Temporal features
            "events_per_hour", "activity_hour_std", "avg_days_between_sessions",
            "session_regularity", "weekday_entropy", "hourly_entropy",
            "activity_trend_slope", "hours_since_last_activity",
            "recent_activity_count", "recent_activity_ratio"
        ]

        # Categorical features
        categorical_features = [
            "primary_event_type", "preferred_device", "preferred_property_type",
            "preferred_time_period"
        ]

        return numerical_features + categorical_features

    def get_feature_types(self) -> Dict[str, FeatureType]:
        """Get mapping of feature names to their types"""

        feature_names = self.get_feature_names()
        feature_types = {}

        # Categorical features
        categorical_features = {
            "primary_event_type", "preferred_device", "preferred_property_type",
            "preferred_time_period"
        }

        # Assign types
        for feature_name in feature_names:
            if feature_name in categorical_features:
                feature_types[feature_name] = FeatureType.CATEGORICAL
            else:
                feature_types[feature_name] = FeatureType.NUMERICAL

        return feature_types