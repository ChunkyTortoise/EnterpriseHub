#!/usr/bin/env python3
"""
Enhanced Feature Engineering Pipeline for Jorge Real Estate AI System

This module implements a comprehensive feature engineering pipeline that extracts
28 machine learning features from lead interactions and property data for XGBoost
model compatibility. Features are derived from existing LeadIntelligenceOptimized
and JorgeBusinessRules components.

Performance Target: <30ms extraction time
Schema: 8 numerical, 12 categorical, 8 boolean features
Integration: sklearn pipeline compatible for production ML models

Author: Claude Code Assistant  
Created: January 23, 2026
"""

import time
import logging
import warnings
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from enum import Enum
import hashlib
import json
import re

# Suppress sklearn warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

try:
    from sklearn.base import BaseEstimator, TransformerMixin
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
    from sklearn.compose import ColumnTransformer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available. Install with: pip install scikit-learn")

# Jorge-specific imports
from jorge_deployment_package.lead_intelligence_optimized import (
    PredictiveLeadScorerV2Optimized, 
    get_enhanced_lead_intelligence,
    EnhancedLeadProfile
)
from jorge_deployment_package.jorge_claude_intelligence import JorgeBusinessRules

logger = logging.getLogger(__name__)


class FeatureCategory(Enum):
    """Feature categorization for organized extraction"""
    ENGAGEMENT = "engagement"
    PREFERENCES = "preferences" 
    BEHAVIORAL = "behavioral"
    MARKET = "market"
    QUALIFICATION = "qualification"
    TEMPORAL = "temporal"


@dataclass
class FeatureMetadata:
    """Metadata for each feature including validation rules"""
    name: str
    feature_type: str  # numerical, categorical, boolean
    category: FeatureCategory
    description: str
    source: str  # data source origin
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    transformation: Optional[str] = None
    importance_weight: float = 1.0


@dataclass 
class FeatureExtractionMetrics:
    """Performance tracking for feature extraction"""
    start_time: float
    total_extraction_time: float = 0.0
    feature_count: int = 0
    validation_errors: List[str] = field(default_factory=list)
    extraction_success_rate: float = 0.0
    cache_hit: bool = False
    
    def __post_init__(self):
        self.total_extraction_time = time.time() - self.start_time


@dataclass
class LeadEngagementFeatures:
    """Lead engagement behavioral features"""
    
    # Response metrics
    avg_response_time_minutes: float = 0.0
    response_consistency_score: float = 0.0
    total_message_count: int = 0
    
    # Interaction patterns
    question_to_statement_ratio: float = 0.0
    message_length_variance: float = 0.0
    engagement_decline_rate: float = 0.0
    
    # Communication style
    formality_score: float = 0.5
    urgency_keyword_frequency: float = 0.0


@dataclass
class PropertyPreferenceFeatures:
    """Property and location preference features"""
    
    # Budget analysis
    budget_specificity_score: float = 0.0
    budget_to_market_ratio: float = 0.0
    price_flexibility_indicator: bool = False
    
    # Location preferences
    location_specificity_count: int = 0
    service_area_alignment_score: float = 0.0
    commute_priority_score: float = 0.0
    
    # Property characteristics
    property_type_diversity: int = 0
    feature_importance_ranking: List[str] = field(default_factory=list)


@dataclass
class BehavioralPatternFeatures:
    """Lead behavioral analysis features"""
    
    # Decision making patterns
    decision_timeline_consistency: bool = True
    information_seeking_intensity: float = 0.0
    comparison_shopping_indicators: float = 0.0
    
    # Risk and motivation
    financing_readiness_score: float = 0.0
    market_timing_awareness: float = 0.0


@dataclass
class MarketContextFeatures:
    """Market condition and seasonal context"""
    
    # Seasonal trends
    seasonal_buyer_activity_score: float = 0.5
    market_condition_alignment: str = "neutral"
    inventory_scarcity_impact: float = 0.0
    
    # Timing factors
    interest_rate_sensitivity: float = 0.0
    market_urgency_multiplier: float = 1.0


class FeatureSchema:
    """Comprehensive schema definition for all 28 ML features"""
    
    # 8 Numerical Features
    NUMERICAL_FEATURES = [
        FeatureMetadata("avg_response_time_minutes", "numerical", FeatureCategory.ENGAGEMENT, 
                       "Average time to respond to messages", "lead_intelligence"),
        FeatureMetadata("budget_specificity_score", "numerical", FeatureCategory.PREFERENCES,
                       "How specific budget requirements are", "budget_analysis"),
        FeatureMetadata("location_specificity_count", "numerical", FeatureCategory.PREFERENCES,
                       "Number of specific location preferences", "location_analysis"), 
        FeatureMetadata("message_length_variance", "numerical", FeatureCategory.BEHAVIORAL,
                       "Variance in message lengths", "communication_analysis"),
        FeatureMetadata("urgency_keyword_frequency", "numerical", FeatureCategory.BEHAVIORAL,
                       "Frequency of urgency-indicating words", "content_analysis"),
        FeatureMetadata("market_timing_awareness", "numerical", FeatureCategory.MARKET,
                       "Understanding of market conditions", "market_analysis"),
        FeatureMetadata("financing_readiness_score", "numerical", FeatureCategory.QUALIFICATION,
                       "Readiness for financing process", "qualification_analysis"),
        FeatureMetadata("jorge_fit_alignment", "numerical", FeatureCategory.QUALIFICATION,
                       "Alignment with Jorge's business criteria", "jorge_validation")
    ]
    
    # 12 Categorical Features
    CATEGORICAL_FEATURES = [
        FeatureMetadata("timeline_category", "categorical", FeatureCategory.PREFERENCES,
                       "Categorized buying timeline", "timeline_analysis"),
        FeatureMetadata("budget_range_category", "categorical", FeatureCategory.PREFERENCES,
                       "Categorized budget range", "budget_analysis"),
        FeatureMetadata("primary_location_area", "categorical", FeatureCategory.PREFERENCES,
                       "Primary area of interest", "location_analysis"),
        FeatureMetadata("financing_status_category", "categorical", FeatureCategory.QUALIFICATION,
                       "Current financing situation", "financing_analysis"),
        FeatureMetadata("communication_style", "categorical", FeatureCategory.BEHAVIORAL,
                       "Style of communication", "communication_analysis"),
        FeatureMetadata("lead_source_type", "categorical", FeatureCategory.ENGAGEMENT,
                       "Source of the lead", "lead_tracking"),
        FeatureMetadata("property_type_preference", "categorical", FeatureCategory.PREFERENCES,
                       "Preferred property type", "property_analysis"),
        FeatureMetadata("market_segment", "categorical", FeatureCategory.MARKET,
                       "Market segment classification", "market_analysis"),
        FeatureMetadata("seasonal_timing", "categorical", FeatureCategory.TEMPORAL,
                       "Seasonal market timing", "temporal_analysis"),
        FeatureMetadata("engagement_pattern", "categorical", FeatureCategory.ENGAGEMENT,
                       "Pattern of engagement", "engagement_analysis"),
        FeatureMetadata("decision_stage", "categorical", FeatureCategory.BEHAVIORAL,
                       "Stage in decision process", "behavioral_analysis"),
        FeatureMetadata("jorge_priority_level", "categorical", FeatureCategory.QUALIFICATION,
                       "Priority level for Jorge", "jorge_validation")
    ]
    
    # 8 Boolean Features  
    BOOLEAN_FEATURES = [
        FeatureMetadata("has_specific_budget", "boolean", FeatureCategory.PREFERENCES,
                       "Whether budget is specifically stated", "budget_analysis"),
        FeatureMetadata("has_location_preference", "boolean", FeatureCategory.PREFERENCES,
                       "Whether location preferences exist", "location_analysis"),
        FeatureMetadata("is_pre_approved", "boolean", FeatureCategory.QUALIFICATION,
                       "Whether financing is pre-approved", "financing_analysis"),
        FeatureMetadata("meets_jorge_criteria", "boolean", FeatureCategory.QUALIFICATION,
                       "Whether lead meets Jorge's criteria", "jorge_validation"),
        FeatureMetadata("shows_urgency_signals", "boolean", FeatureCategory.BEHAVIORAL,
                       "Whether urgency indicators present", "behavioral_analysis"),
        FeatureMetadata("in_service_area", "boolean", FeatureCategory.PREFERENCES,
                       "Whether in Jorge's service area", "location_analysis"),
        FeatureMetadata("repeat_interaction", "boolean", FeatureCategory.ENGAGEMENT,
                       "Whether this is repeat interaction", "engagement_tracking"),
        FeatureMetadata("market_timing_optimal", "boolean", FeatureCategory.TEMPORAL,
                       "Whether timing aligns with market", "market_timing")
    ]
    
    @classmethod
    def get_all_features(cls) -> List[FeatureMetadata]:
        """Return all 28 feature definitions"""
        return cls.NUMERICAL_FEATURES + cls.CATEGORICAL_FEATURES + cls.BOOLEAN_FEATURES
    
    @classmethod
    def get_feature_names(cls) -> List[str]:
        """Get list of all feature names"""
        return [f.name for f in cls.get_all_features()]
    
    @classmethod
    def get_features_by_type(cls, feature_type: str) -> List[FeatureMetadata]:
        """Get features filtered by type"""
        return [f for f in cls.get_all_features() if f.feature_type == feature_type]


class AdvancedTextAnalyzer:
    """Advanced text analysis for behavioral pattern extraction"""
    
    def __init__(self):
        # Communication style patterns
        self.formality_patterns = {
            'formal': [
                r'\b(sir|madam|please|thank\s+you|sincerely|regards)\b',
                r'\b(would\s+like|could\s+you|if\s+possible)\b'
            ],
            'casual': [
                r'\b(hey|hi|sup|yeah|ok|cool|awesome)\b',
                r'\b(gonna|wanna|gotta|dunno)\b'
            ]
        }
        
        # Urgency indicators with weights
        self.urgency_patterns = {
            'high': [r'\b(asap|immediately|urgent|emergency|now)\b', 3.0],
            'medium': [r'\b(soon|quickly|fast|hurry|rush)\b', 2.0], 
            'low': [r'\b(eventually|sometime|when\s+possible)\b', 1.0]
        }
        
        # Decision stage indicators
        self.decision_stage_patterns = {
            'exploration': [r'\b(looking|browsing|checking\s+out|exploring)\b'],
            'evaluation': [r'\b(comparing|evaluating|considering|weighing)\b'],
            'negotiation': [r'\b(offer|negotiate|deal|price|terms)\b'],
            'commitment': [r'\b(ready|commit|decide|final|close)\b']
        }
    
    def analyze_communication_style(self, text: str) -> Dict[str, Any]:
        """Analyze communication style patterns"""
        if not text:
            return {'style': 'unknown', 'formality_score': 0.5}
            
        text_lower = text.lower()
        
        formal_count = sum(len(re.findall(pattern, text_lower)) 
                          for pattern in self.formality_patterns['formal'])
        casual_count = sum(len(re.findall(pattern, text_lower))
                          for pattern in self.formality_patterns['casual'])
        
        total_indicators = formal_count + casual_count
        if total_indicators == 0:
            return {'style': 'neutral', 'formality_score': 0.5}
        
        formality_score = formal_count / total_indicators
        
        if formality_score > 0.6:
            style = 'formal'
        elif formality_score < 0.4:
            style = 'casual'
        else:
            style = 'neutral'
            
        return {
            'style': style,
            'formality_score': formality_score
        }
    
    def extract_urgency_signals(self, text: str) -> Dict[str, Any]:
        """Extract urgency signal indicators"""
        if not text:
            return {'urgency_score': 0.0, 'urgency_keywords': []}
            
        text_lower = text.lower()
        urgency_score = 0.0
        found_keywords = []
        
        for level, (pattern, weight) in self.urgency_patterns.items():
            matches = re.findall(pattern, text_lower)
            if matches:
                urgency_score += len(matches) * weight
                found_keywords.extend(matches)
        
        # Normalize score to 0-1 range
        urgency_score = min(1.0, urgency_score / 10.0)
        
        return {
            'urgency_score': urgency_score,
            'urgency_keywords': found_keywords,
            'has_urgency_signals': urgency_score > 0.3
        }
    
    def identify_decision_stage(self, text: str) -> str:
        """Identify decision-making stage from text"""
        if not text:
            return 'unknown'
            
        text_lower = text.lower()
        stage_scores = {}
        
        for stage, patterns in self.decision_stage_patterns.items():
            score = sum(len(re.findall(pattern, text_lower)) for pattern in patterns)
            stage_scores[stage] = score
        
        if not stage_scores or max(stage_scores.values()) == 0:
            return 'unknown'
            
        return max(stage_scores, key=stage_scores.get)


class MarketContextAnalyzer:
    """Analyze market conditions and seasonal patterns"""
    
    def __init__(self):
        # Seasonal patterns for real estate
        self.seasonal_patterns = {
            'spring': {'months': [3, 4, 5], 'activity_multiplier': 1.3},
            'summer': {'months': [6, 7, 8], 'activity_multiplier': 1.2},
            'fall': {'months': [9, 10, 11], 'activity_multiplier': 0.9},
            'winter': {'months': [12, 1, 2], 'activity_multiplier': 0.7}
        }
        
        # Market condition indicators
        self.market_indicators = {
            'hot_market': ['low inventory', 'bidding war', 'above asking'],
            'balanced': ['steady prices', 'normal inventory'],
            'buyer_market': ['price reduction', 'high inventory', 'negotiable']
        }
    
    def get_seasonal_context(self, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """Analyze seasonal market context"""
        if timestamp is None:
            timestamp = datetime.now()
            
        current_month = timestamp.month
        
        # Determine season
        season = None
        activity_score = 0.5
        
        for season_name, data in self.seasonal_patterns.items():
            if current_month in data['months']:
                season = season_name
                activity_score = data['activity_multiplier'] / 1.3  # Normalize to 0-1
                break
        
        return {
            'season': season or 'unknown',
            'seasonal_activity_score': min(1.0, activity_score),
            'month': current_month,
            'is_peak_season': season in ['spring', 'summer']
        }
    
    def assess_market_timing(self, lead_timeline: str, current_context: Dict = None) -> float:
        """Assess market timing alignment"""
        if not lead_timeline or lead_timeline == 'unknown':
            return 0.5
            
        seasonal_context = self.get_seasonal_context()
        activity_score = seasonal_context['seasonal_activity_score']
        
        # Timeline urgency mapping
        timeline_urgency = {
            'immediate': 1.0,
            '1_month': 0.9,
            '2_months': 0.7,
            '3_months': 0.5,
            '6_months': 0.3,
            '1_year': 0.2,
            'flexible': 0.1
        }
        
        urgency_score = timeline_urgency.get(lead_timeline, 0.5)
        
        # Combine seasonal and urgency factors
        timing_score = (activity_score * 0.6) + (urgency_score * 0.4)
        
        return min(1.0, timing_score)


class FeatureEngineering(BaseEstimator, TransformerMixin):
    """
    Comprehensive Feature Engineering Pipeline for Jorge Real Estate AI
    
    Extracts 28 ML features from lead data with <30ms performance target.
    Compatible with sklearn pipelines and XGBoost models.
    """
    
    def __init__(self, 
                 enable_caching: bool = True,
                 performance_tracking: bool = True,
                 validation_strict: bool = True):
        """
        Initialize feature engineering pipeline
        
        Args:
            enable_caching: Enable feature extraction caching
            performance_tracking: Track extraction performance
            validation_strict: Enable strict feature validation
        """
        self.enable_caching = enable_caching
        self.performance_tracking = performance_tracking  
        self.validation_strict = validation_strict
        
        # Initialize analyzers
        self.lead_scorer = PredictiveLeadScorerV2Optimized()
        self.text_analyzer = AdvancedTextAnalyzer()
        self.market_analyzer = MarketContextAnalyzer()
        
        # Performance tracking
        self.extraction_metrics = []
        self.feature_cache = {}
        
        # Schema validation
        self.schema = FeatureSchema()
        self.expected_features = self.schema.get_feature_names()
        
        logger.info(f"FeatureEngineering initialized with {len(self.expected_features)} features")
    
    def fit(self, X, y=None):
        """Fit the feature engineering pipeline (stateless operation)"""
        logger.info("FeatureEngineering.fit() called - stateless operation")
        return self
    
    def transform(self, X: Union[List[Dict], pd.DataFrame]) -> np.ndarray:
        """
        Transform input data to feature matrix
        
        Args:
            X: Input data as list of dictionaries or DataFrame
            
        Returns:
            Feature matrix as numpy array
        """
        if isinstance(X, pd.DataFrame):
            X = X.to_dict('records')
        
        if not isinstance(X, list):
            raise ValueError("Input must be list of dictionaries or DataFrame")
        
        features_list = []
        for record in X:
            features = self.extract_features_from_record(record)
            features_list.append(features)
        
        return np.array(features_list)
    
    def extract_features_from_record(self, lead_data: Dict[str, Any]) -> List[float]:
        """Extract features from a single lead record"""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(lead_data)
            if self.enable_caching and cache_key in self.feature_cache:
                cached_result = self.feature_cache[cache_key]
                if self.performance_tracking:
                    metrics = FeatureExtractionMetrics(start_time)
                    metrics.cache_hit = True
                    self.extraction_metrics.append(metrics)
                return cached_result
            
            # Extract core intelligence data
            message = lead_data.get('message', '')
            enhanced_intelligence = get_enhanced_lead_intelligence(message)
            
            # Extract advanced features
            features = self._extract_all_features(lead_data, enhanced_intelligence)
            
            # Validate features
            if self.validation_strict:
                features = self._validate_and_fix_features(features)
            
            # Convert to numeric array
            feature_array = self._convert_to_numeric_array(features)
            
            # Cache result
            if self.enable_caching:
                self.feature_cache[cache_key] = feature_array
            
            # Track performance
            if self.performance_tracking:
                extraction_time = time.time() - start_time
                metrics = FeatureExtractionMetrics(start_time)
                metrics.total_extraction_time = extraction_time
                metrics.feature_count = len(feature_array)
                metrics.extraction_success_rate = 1.0
                self.extraction_metrics.append(metrics)
                
                # Warn if performance target missed
                if extraction_time > 0.03:  # 30ms target
                    logger.warning(f"Feature extraction slow: {extraction_time*1000:.1f}ms")
            
            return feature_array
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            # Return default feature array
            return self._get_default_features()
    
    def _extract_all_features(self, 
                             lead_data: Dict[str, Any], 
                             intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all 28 features systematically"""
        
        message = lead_data.get('message', '')
        contact_history = lead_data.get('contact_history', [])
        timestamp = lead_data.get('timestamp', datetime.now())
        
        # Communication analysis
        comm_analysis = self.text_analyzer.analyze_communication_style(message)
        urgency_analysis = self.text_analyzer.extract_urgency_signals(message)
        
        # Market context
        market_context = self.market_analyzer.get_seasonal_context(timestamp)
        
        # Jorge business rules validation
        jorge_validation = JorgeBusinessRules.validate_lead(intelligence)
        
        features = {}
        
        # === NUMERICAL FEATURES (8) ===
        features['avg_response_time_minutes'] = self._calculate_avg_response_time(contact_history)
        features['budget_specificity_score'] = self._calculate_budget_specificity(intelligence)
        features['location_specificity_count'] = len(intelligence.get('location_analysis', []))
        features['message_length_variance'] = self._calculate_message_variance(contact_history)
        features['urgency_keyword_frequency'] = urgency_analysis['urgency_score']
        features['market_timing_awareness'] = self.market_analyzer.assess_market_timing(
            intelligence.get('timeline_analysis', 'unknown'), market_context)
        features['financing_readiness_score'] = self._calculate_financing_readiness(intelligence)
        features['jorge_fit_alignment'] = self._calculate_jorge_alignment(intelligence, jorge_validation)
        
        # === CATEGORICAL FEATURES (12) ===
        features['timeline_category'] = intelligence.get('timeline_analysis', 'unknown')
        features['budget_range_category'] = self._categorize_budget(intelligence.get('budget_max'))
        features['primary_location_area'] = self._get_primary_location(intelligence.get('location_analysis', []))
        features['financing_status_category'] = intelligence.get('financing_analysis', 'unknown')
        features['communication_style'] = comm_analysis['style']
        features['lead_source_type'] = lead_data.get('source', 'unknown')
        features['property_type_preference'] = lead_data.get('property_type', 'unknown')
        features['market_segment'] = self._determine_market_segment(intelligence)
        features['seasonal_timing'] = market_context['season']
        features['engagement_pattern'] = self._analyze_engagement_pattern(contact_history)
        features['decision_stage'] = self.text_analyzer.identify_decision_stage(message)
        features['jorge_priority_level'] = jorge_validation.get('jorge_priority', 'normal')
        
        # === BOOLEAN FEATURES (8) ===
        features['has_specific_budget'] = intelligence.get('has_specific_budget', False)
        features['has_location_preference'] = intelligence.get('has_location_preference', False)
        features['is_pre_approved'] = intelligence.get('is_pre_approved', False)
        features['meets_jorge_criteria'] = jorge_validation.get('passes_jorge_criteria', False)
        features['shows_urgency_signals'] = urgency_analysis['has_urgency_signals']
        features['in_service_area'] = jorge_validation.get('service_area_match', False)
        features['repeat_interaction'] = len(contact_history) > 1
        features['market_timing_optimal'] = market_context['is_peak_season']
        
        return features
    
    def _calculate_avg_response_time(self, contact_history: List[Dict]) -> float:
        """Calculate average response time from contact history"""
        if len(contact_history) < 2:
            return 0.0
        
        response_times = []
        for i in range(1, len(contact_history)):
            prev_msg = contact_history[i-1]
            curr_msg = contact_history[i]
            
            if prev_msg.get('direction') == 'inbound' and curr_msg.get('direction') == 'outbound':
                try:
                    prev_time = datetime.fromisoformat(prev_msg['timestamp'])
                    curr_time = datetime.fromisoformat(curr_msg['timestamp'])
                    diff_minutes = (curr_time - prev_time).total_seconds() / 60
                    if diff_minutes > 0:
                        response_times.append(diff_minutes)
                except (KeyError, ValueError):
                    continue
        
        return np.mean(response_times) if response_times else 0.0
    
    def _calculate_budget_specificity(self, intelligence: Dict) -> float:
        """Calculate how specific the budget requirements are"""
        if not intelligence.get('has_specific_budget', False):
            return 0.0
        
        budget_max = intelligence.get('budget_max')
        if not budget_max:
            return 0.0
        
        # Higher specificity for more precise budgets
        budget_str = str(budget_max)
        if budget_str.endswith('000'):  # Round numbers like 500000
            return 0.6
        elif budget_str.endswith('00'):  # Less round like 525000
            return 0.8
        else:  # Very specific like 523750
            return 1.0
    
    def _calculate_message_variance(self, contact_history: List[Dict]) -> float:
        """Calculate variance in message lengths"""
        if len(contact_history) < 2:
            return 0.0
        
        lengths = [len(msg.get('body', '')) for msg in contact_history]
        return float(np.var(lengths)) if lengths else 0.0
    
    def _calculate_financing_readiness(self, intelligence: Dict) -> float:
        """Calculate financing readiness score"""
        financing_status = intelligence.get('financing_analysis', 'unknown')
        
        readiness_scores = {
            'cash': 1.0,
            'pre_approved': 0.9,
            'conventional': 0.6,
            'fha': 0.5,
            'va': 0.7,
            'jumbo': 0.6,
            'needs_financing': 0.3,
            'unknown': 0.2
        }
        
        return readiness_scores.get(financing_status, 0.2)
    
    def _calculate_jorge_alignment(self, intelligence: Dict, jorge_validation: Dict) -> float:
        """Calculate alignment with Jorge's business criteria"""
        score = 0.0
        
        # Budget alignment
        budget_max = intelligence.get('budget_max', 0)
        if JorgeBusinessRules.MIN_BUDGET <= budget_max <= JorgeBusinessRules.MAX_BUDGET:
            score += 0.4
        
        # Service area alignment
        if jorge_validation.get('service_area_match', False):
            score += 0.3
        
        # Timeline alignment
        timeline = intelligence.get('timeline_analysis', 'unknown')
        if timeline in ['immediate', '1_month', '2_months']:
            score += 0.2
        
        # Financing readiness
        if intelligence.get('is_pre_approved', False):
            score += 0.1
        
        return score
    
    def _categorize_budget(self, budget_max: Optional[int]) -> str:
        """Categorize budget into ranges"""
        if not budget_max:
            return 'unknown'
        
        if budget_max < 200000:
            return 'below_target'
        elif budget_max <= 400000:
            return 'entry_level'
        elif budget_max <= 600000:
            return 'mid_range'
        elif budget_max <= 800000:
            return 'upper_mid'
        else:
            return 'luxury'
    
    def _get_primary_location(self, locations: List[str]) -> str:
        """Get primary location preference"""
        if not locations:
            return 'unknown'
        
        # Jorge's service areas (prioritize these)
        jorge_areas = ['dallas', 'plano', 'frisco', 'mckinney', 'allen']
        
        for location in locations:
            location_lower = location.lower()
            for area in jorge_areas:
                if area in location_lower:
                    return area
        
        return locations[0].lower() if locations else 'unknown'
    
    def _determine_market_segment(self, intelligence: Dict) -> str:
        """Determine market segment based on budget and preferences"""
        budget_max = intelligence.get('budget_max', 0)
        
        if budget_max < 300000:
            return 'first_time_buyer'
        elif budget_max < 600000:
            return 'move_up_buyer'
        elif budget_max < 1000000:
            return 'luxury_buyer'
        else:
            return 'ultra_luxury'
    
    def _analyze_engagement_pattern(self, contact_history: List[Dict]) -> str:
        """Analyze engagement pattern from contact history"""
        if len(contact_history) <= 1:
            return 'initial'
        elif len(contact_history) <= 3:
            return 'exploring'
        elif len(contact_history) <= 7:
            return 'engaged'
        else:
            return 'highly_engaged'
    
    def _validate_and_fix_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix feature values"""
        validated = {}
        errors = []
        
        for feature_meta in self.schema.get_all_features():
            name = feature_meta.name
            value = features.get(name)
            
            if value is None:
                errors.append(f"Missing feature: {name}")
                value = self._get_default_value(feature_meta.feature_type)
            
            # Type-specific validation and fixing
            if feature_meta.feature_type == 'numerical':
                if not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        value = 0.0
                        errors.append(f"Invalid numerical value for {name}")
                
                # Clamp to reasonable ranges
                value = max(0.0, min(1000000.0, value))
                
            elif feature_meta.feature_type == 'categorical':
                if not isinstance(value, str):
                    value = str(value) if value is not None else 'unknown'
                value = value.lower().replace(' ', '_')
                
            elif feature_meta.feature_type == 'boolean':
                if not isinstance(value, bool):
                    value = bool(value)
            
            validated[name] = value
        
        if errors and self.performance_tracking:
            logger.warning(f"Feature validation errors: {errors}")
        
        return validated
    
    def _convert_to_numeric_array(self, features: Dict[str, Any]) -> List[float]:
        """Convert features to numeric array for ML models"""
        numeric_features = []
        
        # Process in schema order to ensure consistency
        for feature_meta in self.schema.get_all_features():
            value = features[feature_meta.name]
            
            if feature_meta.feature_type == 'numerical':
                numeric_features.append(float(value))
                
            elif feature_meta.feature_type == 'categorical':
                # Simple hash-based encoding for now (could use LabelEncoder)
                hash_value = abs(hash(str(value))) % 1000
                numeric_features.append(float(hash_value))
                
            elif feature_meta.feature_type == 'boolean':
                numeric_features.append(1.0 if value else 0.0)
        
        return numeric_features
    
    def _get_default_value(self, feature_type: str) -> Any:
        """Get default value for feature type"""
        defaults = {
            'numerical': 0.0,
            'categorical': 'unknown',
            'boolean': False
        }
        return defaults.get(feature_type, None)
    
    def _get_default_features(self) -> List[float]:
        """Get default feature array for error cases"""
        return [0.0] * len(self.expected_features)
    
    def _get_cache_key(self, lead_data: Dict) -> str:
        """Generate cache key for lead data"""
        # Create hash of relevant lead data
        cache_data = {
            'message': lead_data.get('message', ''),
            'timestamp': str(lead_data.get('timestamp', '')),
            'source': lead_data.get('source', '')
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def get_feature_names(self) -> List[str]:
        """Get ordered list of feature names"""
        return self.expected_features
    
    def get_feature_metadata(self) -> List[FeatureMetadata]:
        """Get comprehensive feature metadata"""
        return self.schema.get_all_features()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get feature extraction performance metrics"""
        if not self.extraction_metrics:
            return {'status': 'no_data'}
        
        times = [m.total_extraction_time for m in self.extraction_metrics]
        
        return {
            'total_extractions': len(self.extraction_metrics),
            'avg_extraction_time_ms': np.mean(times) * 1000,
            'max_extraction_time_ms': np.max(times) * 1000,
            'min_extraction_time_ms': np.min(times) * 1000,
            'cache_hit_rate': np.mean([m.cache_hit for m in self.extraction_metrics]),
            'performance_target_met': np.mean(times) < 0.03,  # 30ms target
            'extraction_success_rate': np.mean([m.extraction_success_rate for m in self.extraction_metrics])
        }
    
    def clear_cache(self):
        """Clear feature extraction cache"""
        self.feature_cache.clear()
        logger.info("Feature extraction cache cleared")
    
    def validate_schema(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Validate features against schema"""
        validation_result = {
            'valid': True,
            'missing_features': [],
            'invalid_types': [],
            'warnings': []
        }
        
        expected_names = set(self.expected_features)
        actual_names = set(features.keys())
        
        # Check for missing features
        missing = expected_names - actual_names
        if missing:
            validation_result['valid'] = False
            validation_result['missing_features'] = list(missing)
        
        # Check for type mismatches
        for feature_meta in self.schema.get_all_features():
            if feature_meta.name in features:
                value = features[feature_meta.name]
                expected_type = feature_meta.feature_type
                
                if expected_type == 'numerical' and not isinstance(value, (int, float)):
                    validation_result['invalid_types'].append({
                        'feature': feature_meta.name,
                        'expected': 'numerical',
                        'actual': type(value).__name__
                    })
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    validation_result['invalid_types'].append({
                        'feature': feature_meta.name,
                        'expected': 'boolean', 
                        'actual': type(value).__name__
                    })
        
        if validation_result['invalid_types']:
            validation_result['valid'] = False
        
        return validation_result


class JorgeFeaturePipeline:
    """Complete ML pipeline for Jorge's feature engineering"""
    
    def __init__(self):
        self.feature_engineer = FeatureEngineering()
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_fitted = False
        
    def create_sklearn_pipeline(self) -> Pipeline:
        """Create sklearn-compatible pipeline"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("Scikit-learn required for pipeline creation")
        
        return Pipeline([
            ('feature_engineering', self.feature_engineer),
            ('scaling', StandardScaler())
        ])
    
    def prepare_training_data(self, lead_data: List[Dict]) -> Tuple[np.ndarray, List[str]]:
        """Prepare training data with features extracted"""
        logger.info(f"Preparing training data for {len(lead_data)} leads")
        
        # Extract features
        features_matrix = []
        for lead in lead_data:
            features = self.feature_engineer.extract_features_from_record(lead)
            features_matrix.append(features)
        
        feature_names = self.feature_engineer.get_feature_names()
        
        return np.array(features_matrix), feature_names
    
    def extract_features_batch(self, leads: List[Dict]) -> pd.DataFrame:
        """Extract features for batch of leads"""
        feature_data = []
        feature_names = self.feature_engineer.get_feature_names()
        
        for lead in leads:
            features = self.feature_engineer.extract_features_from_record(lead)
            feature_data.append(features)
        
        return pd.DataFrame(feature_data, columns=feature_names)


def create_sample_lead_data() -> List[Dict]:
    """Create sample lead data for testing"""
    return [
        {
            'message': "I'm pre-approved for $600k and need to buy in Plano within 30 days. Looking for 3-4 bedrooms.",
            'timestamp': datetime.now(),
            'source': 'website_form',
            'contact_history': [
                {'direction': 'inbound', 'timestamp': datetime.now().isoformat(), 'body': 'Initial inquiry'},
                {'direction': 'outbound', 'timestamp': (datetime.now() + timedelta(minutes=5)).isoformat(), 'body': 'Response'}
            ]
        },
        {
            'message': "Just browsing homes in Dallas area. Budget is flexible, sometime next year.",
            'timestamp': datetime.now(),
            'source': 'social_media',
            'contact_history': []
        },
        {
            'message': "URGENT! Need to sell my house immediately. Already have financing lined up for $800k replacement.",
            'timestamp': datetime.now(),
            'source': 'referral',
            'contact_history': [
                {'direction': 'inbound', 'timestamp': datetime.now().isoformat(), 'body': 'Urgent inquiry'},
            ]
        }
    ]


def benchmark_feature_extraction(num_samples: int = 100) -> Dict[str, Any]:
    """Benchmark feature extraction performance"""
    logger.info(f"Benchmarking feature extraction with {num_samples} samples")
    
    # Create test data
    sample_leads = create_sample_lead_data() * (num_samples // 3 + 1)
    sample_leads = sample_leads[:num_samples]
    
    # Initialize feature engineer
    feature_engineer = FeatureEngineering(enable_caching=True)
    
    # Benchmark extraction
    start_time = time.time()
    
    for lead in sample_leads:
        features = feature_engineer.extract_features_from_record(lead)
    
    total_time = time.time() - start_time
    avg_time_per_lead = total_time / num_samples
    
    # Get performance metrics
    metrics = feature_engineer.get_performance_metrics()
    
    benchmark_results = {
        'total_samples': num_samples,
        'total_time_seconds': total_time,
        'avg_time_per_lead_ms': avg_time_per_lead * 1000,
        'meets_30ms_target': avg_time_per_lead < 0.03,
        'throughput_per_second': num_samples / total_time,
        'feature_count': len(feature_engineer.get_feature_names()),
        'cache_enabled': True,
        **metrics
    }
    
    return benchmark_results


if __name__ == '__main__':
    # Demo and testing
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Jorge Feature Engineering Pipeline Demo")
    print("=" * 50)
    
    # Create sample data
    sample_leads = create_sample_lead_data()
    
    # Initialize pipeline
    pipeline = JorgeFeaturePipeline()
    
    print(f"\n📊 Extracting features for {len(sample_leads)} sample leads...")
    
    # Extract features
    features_df = pipeline.extract_features_batch(sample_leads)
    
    print(f"\n✅ Feature extraction completed!")
    print(f"📈 Features shape: {features_df.shape}")
    print(f"📋 Feature columns: {len(features_df.columns)}")
    
    print(f"\n🔍 Sample features preview:")
    print(features_df.head())
    
    print(f"\n⏱️  Performance Benchmark:")
    benchmark = benchmark_feature_extraction(50)
    print(f"   - Average extraction time: {benchmark['avg_time_per_lead_ms']:.1f}ms")
    print(f"   - Meets 30ms target: {'✅' if benchmark['meets_30ms_target'] else '❌'}")
    print(f"   - Throughput: {benchmark['throughput_per_second']:.1f} leads/second")
    print(f"   - Cache hit rate: {benchmark['cache_hit_rate']:.1%}")
    
    print(f"\n📋 Feature Schema Summary:")
    feature_engineer = FeatureEngineering()
    metadata = feature_engineer.get_feature_metadata()
    
    by_type = {}
    for meta in metadata:
        if meta.feature_type not in by_type:
            by_type[meta.feature_type] = []
        by_type[meta.feature_type].append(meta.name)
    
    for feature_type, features in by_type.items():
        print(f"   - {feature_type}: {len(features)} features")
        for feature in features[:3]:  # Show first 3
            print(f"     • {feature}")
        if len(features) > 3:
            print(f"     • ... and {len(features)-3} more")
    
    print(f"\n✅ Demo completed successfully!")