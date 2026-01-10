"""
Lead Behavioral Features Model

Advanced feature engineering for ML-powered lead intelligence.
Extracts 50+ behavioral, temporal, and engagement features from lead interactions.

Key Features:
- Temporal feature engineering (rolling windows: 7d, 14d, 30d)
- Engagement pattern analysis and velocity metrics
- Communication preference detection
- Feature quality scoring and validation
- ML-ready numerical/categorical encoding
- Performance optimization with vectorized operations

Performance Targets:
- Feature extraction: <50ms per lead
- Batch feature engineering: <10ms per lead (100+ leads)
- Feature quality validation: <5ms
- Memory usage: <100MB for 1000 leads
"""

import json
import math
import time
import numpy as np
import pandas as pd
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict, Counter

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class EngagementTrend(Enum):
    """Engagement trend classification"""
    INCREASING = "increasing"
    STABLE = "stable"
    DECLINING = "declining"
    INACTIVE = "inactive"


class LeadLifecycleStage(Enum):
    """Lead lifecycle stages"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NURTURING = "nurturing"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class CommunicationChannel(Enum):
    """Communication channels"""
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    CHAT = "chat"
    UNKNOWN = "unknown"


@dataclass
class TemporalFeatures:
    """Time-based feature windows"""
    days_7: Dict[str, float] = field(default_factory=dict)
    days_14: Dict[str, float] = field(default_factory=dict)
    days_30: Dict[str, float] = field(default_factory=dict)

    # Trend metrics
    interaction_velocity_7d: float = 0.0
    interaction_velocity_14d: float = 0.0
    interaction_velocity_30d: float = 0.0

    # Seasonal patterns
    preferred_hour: int = 9  # 9 AM default
    preferred_day_of_week: int = 2  # Tuesday default
    weekend_activity: float = 0.0
    business_hours_ratio: float = 0.0


@dataclass
class EngagementPatterns:
    """Engagement behavior analysis"""
    total_interactions: int = 0
    unique_interaction_days: int = 0
    avg_interactions_per_day: float = 0.0
    max_interactions_per_day: int = 0

    # Response patterns
    avg_response_time_minutes: float = 0.0
    median_response_time_minutes: float = 0.0
    fastest_response_minutes: float = 0.0

    # Engagement quality
    session_duration_avg: float = 0.0
    bounce_rate: float = 0.0
    page_views_per_session: float = 0.0

    # Content engagement
    property_views: int = 0
    favorite_properties: int = 0
    shared_properties: int = 0
    search_queries: int = 0


@dataclass
class CommunicationPreferences:
    """Communication channel preferences"""
    preferred_channel: CommunicationChannel = CommunicationChannel.EMAIL
    channel_engagement_scores: Dict[str, float] = field(default_factory=dict)

    # Channel usage
    email_count: int = 0
    sms_count: int = 0
    phone_count: int = 0
    chat_count: int = 0

    # Channel effectiveness
    email_response_rate: float = 0.0
    sms_response_rate: float = 0.0
    phone_answer_rate: float = 0.0
    chat_response_rate: float = 0.0


@dataclass
class BehavioralSignals:
    """Advanced behavioral indicators"""
    urgency_score: float = 0.0
    intent_strength: float = 0.0
    price_sensitivity: float = 0.0
    location_flexibility: float = 0.0

    # Search behavior
    search_refinement_count: int = 0
    price_range_changes: int = 0
    location_searches: int = 0
    property_type_views: Dict[str, int] = field(default_factory=dict)

    # Interaction depth
    listing_detail_views: int = 0
    virtual_tour_starts: int = 0
    photo_gallery_views: int = 0
    floor_plan_views: int = 0
    neighborhood_research: int = 0


@dataclass
class FeatureQuality:
    """Feature quality indicators"""
    completeness_score: float = 0.0  # 0-1, percentage of features populated
    data_freshness_hours: float = 0.0  # hours since last data update
    source_reliability: float = 0.0  # 0-1, reliability of data sources
    validation_errors: List[str] = field(default_factory=list)

    # Individual feature quality
    temporal_quality: float = 0.0
    engagement_quality: float = 0.0
    communication_quality: float = 0.0
    behavioral_quality: float = 0.0


@dataclass
class LeadBehavioralFeatures:
    """
    Comprehensive behavioral feature set for ML lead intelligence.

    Contains 50+ features across multiple dimensions:
    - Demographics and basic info
    - Temporal engagement patterns
    - Communication preferences
    - Behavioral signals and intent
    - Feature quality metrics
    """

    # Core identifiers
    lead_id: str
    created_at: datetime
    last_updated: datetime
    tenant_id: str = ""

    # Basic demographics
    lead_source: str = ""
    lead_status: str = ""
    lifecycle_stage: LeadLifecycleStage = LeadLifecycleStage.NEW

    # Time-based metrics
    days_since_creation: float = 0.0
    days_since_last_activity: float = 0.0
    days_since_last_contact: float = 0.0

    # Feature groups
    temporal_features: TemporalFeatures = field(default_factory=TemporalFeatures)
    engagement_patterns: EngagementPatterns = field(default_factory=EngagementPatterns)
    communication_prefs: CommunicationPreferences = field(default_factory=CommunicationPreferences)
    behavioral_signals: BehavioralSignals = field(default_factory=BehavioralSignals)
    feature_quality: FeatureQuality = field(default_factory=FeatureQuality)

    # ML-ready feature vectors
    numerical_features: Dict[str, float] = field(default_factory=dict)
    categorical_features: Dict[str, str] = field(default_factory=dict)
    binary_features: Dict[str, bool] = field(default_factory=dict)

    # Derived scores
    engagement_score: float = 0.0
    intent_score: float = 0.0
    responsiveness_score: float = 0.0
    quality_score: float = 0.0


class LeadBehavioralFeatureExtractor:
    """
    High-performance feature extraction engine for lead behavioral analysis.

    Processes raw lead interaction data into ML-ready feature vectors with
    comprehensive validation and quality scoring.
    """

    def __init__(self):
        self.feature_definitions = self._load_feature_definitions()
        self.validation_rules = self._load_validation_rules()

    def extract_features(
        self,
        lead_data: Dict[str, Any],
        interaction_history: List[Dict[str, Any]]
    ) -> LeadBehavioralFeatures:
        """
        Extract comprehensive behavioral features from lead data.

        Args:
            lead_data: Basic lead information from GHL
            interaction_history: List of all lead interactions

        Returns:
            LeadBehavioralFeatures with 50+ engineered features
        """
        start_time = time.time()

        try:
            # Initialize feature object
            features = LeadBehavioralFeatures(
                lead_id=lead_data.get('id', ''),
                created_at=self._parse_datetime(lead_data.get('created_at')),
                last_updated=datetime.now(),
                tenant_id=lead_data.get('tenant_id', ''),
                lead_source=lead_data.get('source', ''),
                lead_status=lead_data.get('status', ''),
                lifecycle_stage=self._determine_lifecycle_stage(lead_data)
            )

            # Extract time-based metrics
            features = self._extract_temporal_metrics(features, interaction_history)

            # Extract engagement patterns
            features = self._extract_engagement_patterns(features, interaction_history)

            # Extract communication preferences
            features = self._extract_communication_preferences(features, interaction_history)

            # Extract behavioral signals
            features = self._extract_behavioral_signals(features, lead_data, interaction_history)

            # Generate ML-ready feature vectors
            features = self._generate_feature_vectors(features)

            # Calculate derived scores
            features = self._calculate_derived_scores(features)

            # Assess feature quality
            features.feature_quality = self._assess_feature_quality(features)

            # Validate features
            self._validate_features(features)

            extraction_time = (time.time() - start_time) * 1000
            logger.debug(f"Feature extraction completed in {extraction_time:.1f}ms for lead {features.lead_id}")

            return features

        except Exception as e:
            logger.error(f"Feature extraction failed for lead {lead_data.get('id', 'unknown')}: {e}")
            return self._create_fallback_features(lead_data)

    def extract_batch_features(
        self,
        leads_data: List[Dict[str, Any]],
        interaction_histories: Dict[str, List[Dict[str, Any]]]
    ) -> List[LeadBehavioralFeatures]:
        """
        Batch feature extraction for improved performance.

        Args:
            leads_data: List of lead data dictionaries
            interaction_histories: Lead ID -> interaction history mapping

        Returns:
            List of LeadBehavioralFeatures
        """
        start_time = time.time()

        features_list = []
        for lead_data in leads_data:
            lead_id = lead_data.get('id', '')
            interaction_history = interaction_histories.get(lead_id, [])

            features = self.extract_features(lead_data, interaction_history)
            features_list.append(features)

        extraction_time = (time.time() - start_time) * 1000
        avg_time_per_lead = extraction_time / len(leads_data) if leads_data else 0

        logger.info(f"Batch feature extraction: {len(leads_data)} leads in {extraction_time:.1f}ms "
                   f"(avg {avg_time_per_lead:.1f}ms per lead)")

        return features_list

    def _extract_temporal_metrics(
        self,
        features: LeadBehavioralFeatures,
        interactions: List[Dict[str, Any]]
    ) -> LeadBehavioralFeatures:
        """Extract time-based features and patterns"""

        now = datetime.now()

        # Basic time metrics
        features.days_since_creation = (now - features.created_at).days

        if interactions:
            last_interaction = max(interactions, key=lambda x: self._parse_datetime(x.get('timestamp', '')))
            features.days_since_last_activity = (now - self._parse_datetime(last_interaction.get('timestamp', ''))).days

        # Time window analysis
        temporal_features = TemporalFeatures()

        # 7-day window
        week_interactions = self._filter_interactions_by_days(interactions, 7)
        temporal_features.days_7 = self._analyze_interaction_window(week_interactions)
        temporal_features.interaction_velocity_7d = len(week_interactions) / 7.0

        # 14-day window
        two_week_interactions = self._filter_interactions_by_days(interactions, 14)
        temporal_features.days_14 = self._analyze_interaction_window(two_week_interactions)
        temporal_features.interaction_velocity_14d = len(two_week_interactions) / 14.0

        # 30-day window
        month_interactions = self._filter_interactions_by_days(interactions, 30)
        temporal_features.days_30 = self._analyze_interaction_window(month_interactions)
        temporal_features.interaction_velocity_30d = len(month_interactions) / 30.0

        # Activity patterns
        if interactions:
            hour_counts = Counter()
            dow_counts = Counter()

            for interaction in interactions:
                dt = self._parse_datetime(interaction.get('timestamp', ''))
                hour_counts[dt.hour] += 1
                dow_counts[dt.weekday()] += 1

            temporal_features.preferred_hour = hour_counts.most_common(1)[0][0] if hour_counts else 9
            temporal_features.preferred_day_of_week = dow_counts.most_common(1)[0][0] if dow_counts else 2

            # Weekend vs weekday activity
            weekend_interactions = sum(1 for i in interactions
                                     if self._parse_datetime(i.get('timestamp', '')).weekday() >= 5)
            temporal_features.weekend_activity = weekend_interactions / len(interactions) if interactions else 0.0

            # Business hours activity (9 AM - 5 PM)
            business_interactions = sum(1 for i in interactions
                                      if 9 <= self._parse_datetime(i.get('timestamp', '')).hour <= 17)
            temporal_features.business_hours_ratio = business_interactions / len(interactions) if interactions else 0.0

        features.temporal_features = temporal_features
        return features

    def _extract_engagement_patterns(
        self,
        features: LeadBehavioralFeatures,
        interactions: List[Dict[str, Any]]
    ) -> LeadBehavioralFeatures:
        """Extract engagement behavior patterns"""

        patterns = EngagementPatterns()

        if not interactions:
            features.engagement_patterns = patterns
            return features

        # Basic engagement metrics
        patterns.total_interactions = len(interactions)

        # Unique interaction days
        interaction_dates = set()
        for interaction in interactions:
            dt = self._parse_datetime(interaction.get('timestamp', ''))
            interaction_dates.add(dt.date())
        patterns.unique_interaction_days = len(interaction_dates)

        # Daily averages
        if patterns.unique_interaction_days > 0:
            patterns.avg_interactions_per_day = patterns.total_interactions / patterns.unique_interaction_days

        # Daily maximum
        daily_counts = Counter()
        for interaction in interactions:
            dt = self._parse_datetime(interaction.get('timestamp', ''))
            daily_counts[dt.date()] += 1
        patterns.max_interactions_per_day = max(daily_counts.values()) if daily_counts else 0

        # Response time analysis
        response_times = []
        for i in range(1, len(interactions)):
            prev_time = self._parse_datetime(interactions[i-1].get('timestamp', ''))
            curr_time = self._parse_datetime(interactions[i].get('timestamp', ''))

            # Only consider responses within 24 hours
            time_diff = (curr_time - prev_time).total_seconds() / 60  # minutes
            if 0 < time_diff <= 1440:  # 24 hours
                response_times.append(time_diff)

        if response_times:
            patterns.avg_response_time_minutes = np.mean(response_times)
            patterns.median_response_time_minutes = np.median(response_times)
            patterns.fastest_response_minutes = min(response_times)

        # Content-specific engagement
        for interaction in interactions:
            action = interaction.get('action', '').lower()

            if 'property' in action and 'view' in action:
                patterns.property_views += 1
            elif 'favorite' in action or 'save' in action:
                patterns.favorite_properties += 1
            elif 'share' in action:
                patterns.shared_properties += 1
            elif 'search' in action:
                patterns.search_queries += 1

        features.engagement_patterns = patterns
        return features

    def _extract_communication_preferences(
        self,
        features: LeadBehavioralFeatures,
        interactions: List[Dict[str, Any]]
    ) -> LeadBehavioralFeatures:
        """Extract communication channel preferences"""

        prefs = CommunicationPreferences()

        # Count interactions by channel
        channel_counts = Counter()
        channel_responses = defaultdict(list)

        for interaction in interactions:
            channel = interaction.get('channel', 'unknown').lower()

            if 'email' in channel:
                prefs.email_count += 1
                channel_counts['email'] += 1
            elif 'sms' in channel or 'text' in channel:
                prefs.sms_count += 1
                channel_counts['sms'] += 1
            elif 'phone' in channel or 'call' in channel:
                prefs.phone_count += 1
                channel_counts['phone'] += 1
            elif 'chat' in channel:
                prefs.chat_count += 1
                channel_counts['chat'] += 1

            # Track responses for effectiveness
            if interaction.get('is_response', False):
                channel_responses[channel].append(interaction)

        # Determine preferred channel
        if channel_counts:
            preferred_channel_str = channel_counts.most_common(1)[0][0]
            prefs.preferred_channel = {
                'email': CommunicationChannel.EMAIL,
                'sms': CommunicationChannel.SMS,
                'phone': CommunicationChannel.PHONE,
                'chat': CommunicationChannel.CHAT
            }.get(preferred_channel_str, CommunicationChannel.UNKNOWN)

        # Calculate response rates
        if prefs.email_count > 0:
            prefs.email_response_rate = len(channel_responses.get('email', [])) / prefs.email_count
        if prefs.sms_count > 0:
            prefs.sms_response_rate = len(channel_responses.get('sms', [])) / prefs.sms_count
        if prefs.phone_count > 0:
            prefs.phone_answer_rate = len(channel_responses.get('phone', [])) / prefs.phone_count
        if prefs.chat_count > 0:
            prefs.chat_response_rate = len(channel_responses.get('chat', [])) / prefs.chat_count

        # Channel engagement scores
        total_interactions = sum(channel_counts.values())
        if total_interactions > 0:
            for channel, count in channel_counts.items():
                engagement_score = count / total_interactions
                response_rate = len(channel_responses.get(channel, [])) / count if count > 0 else 0
                prefs.channel_engagement_scores[channel] = (engagement_score + response_rate) / 2

        features.communication_prefs = prefs
        return features

    def _extract_behavioral_signals(
        self,
        features: LeadBehavioralFeatures,
        lead_data: Dict[str, Any],
        interactions: List[Dict[str, Any]]
    ) -> LeadBehavioralFeatures:
        """Extract advanced behavioral indicators"""

        signals = BehavioralSignals()

        # Analyze search behavior
        search_interactions = [i for i in interactions if 'search' in i.get('action', '').lower()]

        # Search refinement pattern
        signals.search_refinement_count = len(search_interactions)

        # Price sensitivity analysis
        price_changes = []
        for interaction in search_interactions:
            if 'price_range' in interaction.get('data', {}):
                price_range = interaction['data']['price_range']
                price_changes.append(price_range)

        if len(price_changes) > 1:
            signals.price_range_changes = len(set(price_changes)) - 1

            # Calculate price sensitivity score
            price_values = []
            for price_range in price_changes:
                if isinstance(price_range, dict):
                    min_price = price_range.get('min', 0)
                    max_price = price_range.get('max', 0)
                    price_values.append((min_price + max_price) / 2)

            if len(price_values) > 1:
                price_std = np.std(price_values)
                price_mean = np.mean(price_values)
                signals.price_sensitivity = price_std / price_mean if price_mean > 0 else 0

        # Location search analysis
        location_searches = [i for i in interactions
                           if 'location' in i.get('action', '').lower() or
                              'area' in i.get('action', '').lower()]
        signals.location_searches = len(location_searches)

        # Property type interest
        property_type_actions = [i for i in interactions if 'property_type' in i.get('data', {})]
        for action in property_type_actions:
            prop_type = action['data']['property_type']
            signals.property_type_views[prop_type] = signals.property_type_views.get(prop_type, 0) + 1

        # Interaction depth analysis
        for interaction in interactions:
            action = interaction.get('action', '').lower()

            if 'listing_detail' in action:
                signals.listing_detail_views += 1
            elif 'virtual_tour' in action:
                signals.virtual_tour_starts += 1
            elif 'photo' in action or 'gallery' in action:
                signals.photo_gallery_views += 1
            elif 'floor_plan' in action:
                signals.floor_plan_views += 1
            elif 'neighborhood' in action or 'area_info' in action:
                signals.neighborhood_research += 1

        # Calculate urgency score based on interaction intensity
        recent_interactions = self._filter_interactions_by_days(interactions, 7)
        if recent_interactions:
            urgency_factors = [
                len(recent_interactions) / 7,  # daily interaction rate
                signals.search_refinement_count / 10,  # search activity
                signals.listing_detail_views / 20,  # detail interest
            ]
            signals.urgency_score = min(1.0, np.mean(urgency_factors))

        # Calculate intent strength
        intent_factors = [
            signals.property_views / 50,
            signals.virtual_tour_starts / 10,
            signals.neighborhood_research / 5,
            len(signals.property_type_views) / 3  # variety of property types
        ]
        signals.intent_strength = min(1.0, np.mean(intent_factors))

        # Location flexibility based on search patterns
        unique_locations = set()
        for interaction in location_searches:
            if 'location' in interaction.get('data', {}):
                unique_locations.add(interaction['data']['location'])

        signals.location_flexibility = min(1.0, len(unique_locations) / 5) if unique_locations else 0.5

        features.behavioral_signals = signals
        return features

    def _generate_feature_vectors(self, features: LeadBehavioralFeatures) -> LeadBehavioralFeatures:
        """Generate ML-ready numerical and categorical feature vectors"""

        # Numerical features
        numerical = {}

        # Time-based features
        numerical['days_since_creation'] = features.days_since_creation
        numerical['days_since_last_activity'] = features.days_since_last_activity
        numerical['interaction_velocity_7d'] = features.temporal_features.interaction_velocity_7d
        numerical['interaction_velocity_14d'] = features.temporal_features.interaction_velocity_14d
        numerical['interaction_velocity_30d'] = features.temporal_features.interaction_velocity_30d
        numerical['weekend_activity'] = features.temporal_features.weekend_activity
        numerical['business_hours_ratio'] = features.temporal_features.business_hours_ratio

        # Engagement features
        numerical['total_interactions'] = float(features.engagement_patterns.total_interactions)
        numerical['avg_interactions_per_day'] = features.engagement_patterns.avg_interactions_per_day
        numerical['avg_response_time_minutes'] = features.engagement_patterns.avg_response_time_minutes
        numerical['property_views'] = float(features.engagement_patterns.property_views)
        numerical['search_queries'] = float(features.engagement_patterns.search_queries)

        # Communication features
        numerical['email_count'] = float(features.communication_prefs.email_count)
        numerical['sms_count'] = float(features.communication_prefs.sms_count)
        numerical['phone_count'] = float(features.communication_prefs.phone_count)
        numerical['email_response_rate'] = features.communication_prefs.email_response_rate
        numerical['sms_response_rate'] = features.communication_prefs.sms_response_rate

        # Behavioral features
        numerical['urgency_score'] = features.behavioral_signals.urgency_score
        numerical['intent_strength'] = features.behavioral_signals.intent_strength
        numerical['price_sensitivity'] = features.behavioral_signals.price_sensitivity
        numerical['location_flexibility'] = features.behavioral_signals.location_flexibility
        numerical['search_refinement_count'] = float(features.behavioral_signals.search_refinement_count)
        numerical['listing_detail_views'] = float(features.behavioral_signals.listing_detail_views)
        numerical['virtual_tour_starts'] = float(features.behavioral_signals.virtual_tour_starts)

        # Categorical features
        categorical = {}
        categorical['lead_source'] = features.lead_source
        categorical['lead_status'] = features.lead_status
        categorical['lifecycle_stage'] = features.lifecycle_stage.value
        categorical['preferred_channel'] = features.communication_prefs.preferred_channel.value
        categorical['preferred_hour'] = str(features.temporal_features.preferred_hour)
        categorical['preferred_day_of_week'] = str(features.temporal_features.preferred_day_of_week)

        # Binary features
        binary = {}
        binary['is_weekend_active'] = features.temporal_features.weekend_activity > 0.3
        binary['is_business_hours_active'] = features.temporal_features.business_hours_ratio > 0.5
        binary['has_property_views'] = features.engagement_patterns.property_views > 0
        binary['has_virtual_tours'] = features.behavioral_signals.virtual_tour_starts > 0
        binary['is_price_sensitive'] = features.behavioral_signals.price_sensitivity > 0.2
        binary['is_location_flexible'] = features.behavioral_signals.location_flexibility > 0.7
        binary['is_high_intent'] = features.behavioral_signals.intent_strength > 0.6
        binary['is_urgent'] = features.behavioral_signals.urgency_score > 0.7

        features.numerical_features = numerical
        features.categorical_features = categorical
        features.binary_features = binary

        return features

    def _calculate_derived_scores(self, features: LeadBehavioralFeatures) -> LeadBehavioralFeatures:
        """Calculate composite scores from individual features"""

        # Engagement score (0-1)
        engagement_factors = [
            min(1.0, features.engagement_patterns.total_interactions / 20),
            min(1.0, features.engagement_patterns.avg_interactions_per_day / 5),
            min(1.0, features.engagement_patterns.property_views / 10),
            1.0 - min(1.0, features.days_since_last_activity / 30)  # recency bonus
        ]
        features.engagement_score = np.mean(engagement_factors)

        # Intent score (0-1)
        features.intent_score = features.behavioral_signals.intent_strength

        # Responsiveness score (0-1)
        responsiveness_factors = []
        if features.engagement_patterns.avg_response_time_minutes > 0:
            responsiveness_factors.append(min(1.0, 1440 / features.engagement_patterns.avg_response_time_minutes))

        response_rates = [
            features.communication_prefs.email_response_rate,
            features.communication_prefs.sms_response_rate,
            features.communication_prefs.phone_answer_rate
        ]
        avg_response_rate = np.mean([r for r in response_rates if r > 0])
        if avg_response_rate > 0:
            responsiveness_factors.append(avg_response_rate)

        features.responsiveness_score = np.mean(responsiveness_factors) if responsiveness_factors else 0.0

        return features

    def _assess_feature_quality(self, features: LeadBehavioralFeatures) -> FeatureQuality:
        """Assess the quality and completeness of extracted features"""

        quality = FeatureQuality()

        # Count populated features
        total_features = 0
        populated_features = 0

        # Check numerical features
        for value in features.numerical_features.values():
            total_features += 1
            if value is not None and not math.isnan(value) and value != 0:
                populated_features += 1

        # Check categorical features
        for value in features.categorical_features.values():
            total_features += 1
            if value and value != "unknown":
                populated_features += 1

        # Overall completeness
        quality.completeness_score = populated_features / total_features if total_features > 0 else 0

        # Data freshness
        if features.days_since_last_activity is not None:
            quality.data_freshness_hours = features.days_since_last_activity * 24

        # Component quality scores
        quality.temporal_quality = 1.0 if features.temporal_features.interaction_velocity_7d > 0 else 0.5
        quality.engagement_quality = min(1.0, features.engagement_patterns.total_interactions / 10)
        quality.communication_quality = 1.0 if any([
            features.communication_prefs.email_count,
            features.communication_prefs.sms_count,
            features.communication_prefs.phone_count
        ]) else 0.3
        quality.behavioral_quality = features.behavioral_signals.intent_strength

        # Overall quality score
        component_scores = [
            quality.temporal_quality,
            quality.engagement_quality,
            quality.communication_quality,
            quality.behavioral_quality
        ]
        quality.source_reliability = np.mean(component_scores)

        return quality

    def _validate_features(self, features: LeadBehavioralFeatures) -> None:
        """Validate feature values and add warnings for issues"""

        errors = []

        # Validate numerical ranges
        if features.engagement_score < 0 or features.engagement_score > 1:
            errors.append(f"engagement_score out of range: {features.engagement_score}")

        if features.intent_score < 0 or features.intent_score > 1:
            errors.append(f"intent_score out of range: {features.intent_score}")

        if features.days_since_creation < 0:
            errors.append(f"negative days_since_creation: {features.days_since_creation}")

        # Validate interaction counts are non-negative
        if features.engagement_patterns.total_interactions < 0:
            errors.append("negative total_interactions")

        # Check for suspicious response times
        if features.engagement_patterns.avg_response_time_minutes > 10080:  # more than a week
            errors.append(f"unrealistic response time: {features.engagement_patterns.avg_response_time_minutes} minutes")

        if errors:
            features.feature_quality.validation_errors = errors
            logger.warning(f"Feature validation errors for lead {features.lead_id}: {errors}")

    def _filter_interactions_by_days(self, interactions: List[Dict[str, Any]], days: int) -> List[Dict[str, Any]]:
        """Filter interactions to those within the last N days"""

        cutoff_date = datetime.now() - timedelta(days=days)
        filtered = []

        for interaction in interactions:
            timestamp = self._parse_datetime(interaction.get('timestamp', ''))
            if timestamp >= cutoff_date:
                filtered.append(interaction)

        return filtered

    def _analyze_interaction_window(self, interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze interactions within a time window"""

        analysis = {
            'count': len(interactions),
            'avg_per_day': 0.0,
            'unique_days': 0.0
        }

        if interactions:
            # Count unique days
            unique_dates = set()
            for interaction in interactions:
                dt = self._parse_datetime(interaction.get('timestamp', ''))
                unique_dates.add(dt.date())

            analysis['unique_days'] = len(unique_dates)
            analysis['avg_per_day'] = len(interactions) / len(unique_dates) if unique_dates else 0

        return analysis

    def _determine_lifecycle_stage(self, lead_data: Dict[str, Any]) -> LeadLifecycleStage:
        """Determine lead lifecycle stage from data"""

        status = lead_data.get('status', '').lower()

        if 'new' in status:
            return LeadLifecycleStage.NEW
        elif 'contacted' in status:
            return LeadLifecycleStage.CONTACTED
        elif 'qualified' in status:
            return LeadLifecycleStage.QUALIFIED
        elif 'nurturing' in status or 'follow' in status:
            return LeadLifecycleStage.NURTURING
        elif 'proposal' in status or 'quote' in status:
            return LeadLifecycleStage.PROPOSAL
        elif 'negotiation' in status:
            return LeadLifecycleStage.NEGOTIATION
        elif 'won' in status or 'closed' in status:
            return LeadLifecycleStage.CLOSED_WON
        elif 'lost' in status:
            return LeadLifecycleStage.CLOSED_LOST
        else:
            return LeadLifecycleStage.NEW

    def _parse_datetime(self, timestamp_str: str) -> datetime:
        """Parse datetime from various formats"""

        if not timestamp_str:
            return datetime.now()

        try:
            # Try ISO format first
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            logger.warning(f"Could not parse timestamp: {timestamp_str}")
            return datetime.now()

    def _create_fallback_features(self, lead_data: Dict[str, Any]) -> LeadBehavioralFeatures:
        """Create basic features when extraction fails"""

        return LeadBehavioralFeatures(
            lead_id=lead_data.get('id', ''),
            created_at=self._parse_datetime(lead_data.get('created_at', '')),
            last_updated=datetime.now(),
            tenant_id=lead_data.get('tenant_id', ''),
            lead_source=lead_data.get('source', ''),
            lead_status=lead_data.get('status', '')
        )

    def _load_feature_definitions(self) -> Dict[str, Any]:
        """Load feature definitions and metadata"""

        return {
            'numerical_features': list(range(25)),  # 25 numerical features
            'categorical_features': list(range(8)),  # 8 categorical features
            'binary_features': list(range(10)),     # 10 binary features
            'total_features': 43
        }

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load feature validation rules"""

        return {
            'score_range': (0.0, 1.0),
            'max_response_time_minutes': 10080,  # 1 week
            'max_days_since_creation': 365 * 5   # 5 years
        }


# Convenience functions
def extract_lead_features(
    lead_data: Dict[str, Any],
    interaction_history: List[Dict[str, Any]]
) -> LeadBehavioralFeatures:
    """
    Extract behavioral features for a single lead.

    Args:
        lead_data: Lead information from GHL
        interaction_history: List of lead interactions

    Returns:
        LeadBehavioralFeatures object
    """
    extractor = LeadBehavioralFeatureExtractor()
    return extractor.extract_features(lead_data, interaction_history)


def extract_batch_lead_features(
    leads_data: List[Dict[str, Any]],
    interaction_histories: Dict[str, List[Dict[str, Any]]]
) -> List[LeadBehavioralFeatures]:
    """
    Extract behavioral features for multiple leads.

    Args:
        leads_data: List of lead data dictionaries
        interaction_histories: Lead ID -> interaction history mapping

    Returns:
        List of LeadBehavioralFeatures objects
    """
    extractor = LeadBehavioralFeatureExtractor()
    return extractor.extract_batch_features(leads_data, interaction_histories)


def features_to_dict(features: LeadBehavioralFeatures) -> Dict[str, Any]:
    """Convert LeadBehavioralFeatures to dictionary for serialization"""
    return asdict(features)


def dict_to_features(data: Dict[str, Any]) -> LeadBehavioralFeatures:
    """Convert dictionary back to LeadBehavioralFeatures"""
    return LeadBehavioralFeatures(**data)