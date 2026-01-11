"""
AI-Powered Property Matching Engine with Behavioral Learning

Advanced property matching system that learns from user preferences,
market trends, and agent feedback to provide highly personalized recommendations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

from .feature_engineering import FeatureEngineer
from .memory_service import MemoryService
from .lead_scorer import LeadScorer

logger = logging.getLogger(__name__)


@dataclass
class PropertyMatch:
    """Enhanced property match with AI confidence and reasoning"""
    property_id: str
    match_score: float
    confidence: float
    reasons: List[str]
    behavioral_signals: Dict[str, float]
    market_factors: Dict[str, float]
    agent_notes: Optional[str] = None
    predicted_interest: float = 0.0
    estimated_viewing_probability: float = 0.0
    price_competitiveness: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'property_id': self.property_id,
            'match_score': round(self.match_score, 2),
            'confidence': round(self.confidence, 3),
            'reasons': self.reasons,
            'behavioral_signals': self.behavioral_signals,
            'market_factors': self.market_factors,
            'agent_notes': self.agent_notes,
            'predicted_interest': round(self.predicted_interest, 2),
            'estimated_viewing_probability': round(self.estimated_viewing_probability, 2),
            'price_competitiveness': round(self.price_competitiveness, 2)
        }


@dataclass
class LeadPreferences:
    """Comprehensive lead preferences from multiple sources"""
    explicit_requirements: Dict[str, Any] = field(default_factory=dict)
    behavioral_preferences: Dict[str, float] = field(default_factory=dict)
    historical_patterns: Dict[str, Any] = field(default_factory=dict)
    agent_observations: List[str] = field(default_factory=list)
    market_segment: Optional[str] = None
    urgency_level: float = 0.0
    budget_flexibility: float = 0.5


class AIPropertyMatcher:
    """
    Advanced AI-powered property matching with behavioral learning
    Combines explicit preferences, behavioral signals, and market intelligence
    """

    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.memory_service = MemoryService()
        self.lead_scorer = LeadScorer()

        # ML models for different aspects
        self.interest_predictor: Optional[RandomForestRegressor] = None
        self.viewing_predictor: Optional[GradientBoostingClassifier] = None
        self.preference_clusterer: Optional[KMeans] = None
        self.scaler = StandardScaler()

        # Behavioral learning state
        self.user_interactions = {}
        self.property_features_cache = {}
        self.market_insights = {}

        # Performance tracking
        self.match_feedback = []
        self.prediction_accuracy = {}

    async def initialize_models(self) -> None:
        """Initialize and train ML models from historical data"""
        try:
            # Load historical matching data
            historical_data = await self._load_historical_data()

            if len(historical_data) > 100:
                # Train interest prediction model
                await self._train_interest_predictor(historical_data)

                # Train viewing probability model
                await self._train_viewing_predictor(historical_data)

                # Train preference clustering
                await self._train_preference_clusters(historical_data)

                logger.info("✅ AI Property Matching models initialized successfully")
            else:
                logger.info("📚 Insufficient historical data, using rule-based matching")

        except Exception as e:
            logger.error(f"❌ Model initialization failed: {e}")
            # Fallback to rule-based matching

    async def find_matches(
        self,
        lead_id: str,
        tenant_id: str,
        properties: List[Dict],
        max_matches: int = 10,
        include_behavioral: bool = True
    ) -> List[PropertyMatch]:
        """
        Find AI-powered property matches for a lead

        Args:
            lead_id: Unique lead identifier
            tenant_id: Tenant identifier
            properties: List of available properties
            max_matches: Maximum number of matches to return
            include_behavioral: Whether to include behavioral learning

        Returns:
            List of PropertyMatch objects sorted by match score
        """
        start_time = datetime.utcnow()

        try:
            # 1. Gather comprehensive lead preferences
            lead_preferences = await self._gather_lead_preferences(lead_id, tenant_id)

            # 2. Generate property features and scores
            property_scores = []

            for property_data in properties:
                try:
                    match = await self._score_property_match(
                        property_data,
                        lead_preferences,
                        include_behavioral=include_behavioral
                    )

                    if match.match_score > 0.2:  # Minimum threshold
                        property_scores.append(match)

                except Exception as e:
                    logger.warning(f"Property scoring failed for {property_data.get('id', 'unknown')}: {e}")

            # 3. Sort by match score and confidence
            property_scores.sort(
                key=lambda x: (x.match_score * x.confidence),
                reverse=True
            )

            # 4. Apply diversity and market filters
            final_matches = await self._apply_matching_filters(
                property_scores[:max_matches * 2],  # Get more for filtering
                lead_preferences,
                max_matches
            )

            # 5. Log performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            await self._log_matching_performance({
                'lead_id': lead_id,
                'tenant_id': tenant_id,
                'properties_evaluated': len(properties),
                'matches_found': len(final_matches),
                'processing_time_ms': processing_time * 1000,
                'avg_match_score': np.mean([m.match_score for m in final_matches]) if final_matches else 0,
                'behavioral_included': include_behavioral
            })

            logger.info(f"🏠 Found {len(final_matches)} AI-matched properties for lead {lead_id} in {processing_time:.2f}s")

            return final_matches

        except Exception as e:
            logger.error(f"❌ Property matching failed for lead {lead_id}: {e}")
            return []

    async def _gather_lead_preferences(self, lead_id: str, tenant_id: str) -> LeadPreferences:
        """Gather comprehensive lead preferences from multiple sources"""
        preferences = LeadPreferences()

        try:
            # 1. Get explicit requirements from lead profile
            lead_data = await self.memory_service.get_lead_data(lead_id, tenant_id)

            if lead_data:
                preferences.explicit_requirements = {
                    'budget_min': lead_data.get('budget_min', 0),
                    'budget_max': lead_data.get('budget_max', float('inf')),
                    'bedrooms': lead_data.get('bedrooms_wanted'),
                    'bathrooms': lead_data.get('bathrooms_wanted'),
                    'property_type': lead_data.get('property_type_preference'),
                    'location_preferences': lead_data.get('location_preferences', []),
                    'must_haves': lead_data.get('must_have_features', []),
                    'nice_to_haves': lead_data.get('nice_to_have_features', [])
                }

                preferences.urgency_level = lead_data.get('urgency_score', 0.5)
                preferences.market_segment = lead_data.get('market_segment', 'general')

            # 2. Extract behavioral preferences from interactions
            if lead_id in self.user_interactions:
                behavioral_data = self.user_interactions[lead_id]

                preferences.behavioral_preferences = {
                    'price_sensitivity': behavioral_data.get('price_focus_score', 0.5),
                    'location_importance': behavioral_data.get('location_focus_score', 0.5),
                    'feature_importance': behavioral_data.get('features_focus_score', 0.5),
                    'visual_preference': behavioral_data.get('image_engagement_score', 0.5),
                    'description_engagement': behavioral_data.get('text_engagement_score', 0.5)
                }

                preferences.historical_patterns = {
                    'avg_time_per_property': behavioral_data.get('avg_viewing_time', 0),
                    'properties_viewed': behavioral_data.get('total_properties_viewed', 0),
                    'saved_properties': behavioral_data.get('properties_saved', []),
                    'rejected_properties': behavioral_data.get('properties_rejected', [])
                }

            # 3. Get agent observations and notes
            agent_notes = await self.memory_service.get_agent_notes(lead_id, tenant_id)
            if agent_notes:
                preferences.agent_observations = [
                    note['content'] for note in agent_notes
                    if 'preference' in note['content'].lower() or 'likes' in note['content'].lower()
                ]

            return preferences

        except Exception as e:
            logger.error(f"Failed to gather lead preferences: {e}")
            return preferences

    async def _score_property_match(
        self,
        property_data: Dict,
        lead_preferences: LeadPreferences,
        include_behavioral: bool = True
    ) -> PropertyMatch:
        """Score a single property match using AI and rules"""

        property_id = property_data.get('id', 'unknown')

        # 1. Extract property features
        property_features = await self._extract_property_features(property_data)

        # 2. Calculate explicit requirement match
        explicit_score, explicit_reasons = self._score_explicit_requirements(
            property_features, lead_preferences.explicit_requirements
        )

        # 3. Calculate behavioral match (if enabled and available)
        behavioral_score = 0.0
        behavioral_signals = {}

        if include_behavioral and lead_preferences.behavioral_preferences:
            behavioral_score, behavioral_signals = await self._score_behavioral_match(
                property_features, lead_preferences.behavioral_preferences
            )

        # 4. Calculate market factors
        market_score, market_factors = await self._score_market_factors(
            property_data, lead_preferences
        )

        # 5. Predict interest using ML (if model available)
        predicted_interest = 0.0
        viewing_probability = 0.0

        if self.interest_predictor:
            try:
                feature_vector = self._create_feature_vector(property_features, lead_preferences)
                predicted_interest = self.interest_predictor.predict([feature_vector])[0]

                if self.viewing_predictor:
                    viewing_probability = self.viewing_predictor.predict_proba([feature_vector])[0][1]

            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")

        # 6. Combine scores with weights
        weights = {
            'explicit': 0.4,
            'behavioral': 0.25 if include_behavioral else 0.0,
            'market': 0.2,
            'ml_prediction': 0.15 if self.interest_predictor else 0.0
        }

        # Normalize weights
        weight_sum = sum(weights.values())
        if weight_sum > 0:
            for key in weights:
                weights[key] /= weight_sum

        final_score = (
            explicit_score * weights['explicit'] +
            behavioral_score * weights['behavioral'] +
            market_score * weights['market'] +
            predicted_interest * weights['ml_prediction']
        )

        # 7. Calculate confidence based on data completeness
        confidence = self._calculate_confidence(
            lead_preferences, property_features, include_behavioral
        )

        # 8. Generate reasons
        all_reasons = explicit_reasons.copy()

        if behavioral_score > 0.6:
            all_reasons.append(f"Strong behavioral match ({behavioral_score:.1%})")

        if market_score > 0.7:
            all_reasons.append(f"Excellent market positioning ({market_score:.1%})")

        if predicted_interest > 0.8:
            all_reasons.append(f"High predicted interest ({predicted_interest:.1%})")

        # 9. Calculate price competitiveness
        price_competitiveness = await self._calculate_price_competitiveness(
            property_data, lead_preferences
        )

        return PropertyMatch(
            property_id=property_id,
            match_score=min(max(final_score, 0.0), 1.0),
            confidence=confidence,
            reasons=all_reasons,
            behavioral_signals=behavioral_signals,
            market_factors=market_factors,
            predicted_interest=predicted_interest,
            estimated_viewing_probability=viewing_probability,
            price_competitiveness=price_competitiveness
        )

    def _score_explicit_requirements(
        self,
        property_features: Dict,
        requirements: Dict
    ) -> Tuple[float, List[str]]:
        """Score based on explicit lead requirements"""
        score = 0.0
        reasons = []
        total_weight = 0.0

        # Budget match (high weight)
        budget_weight = 0.3
        price = property_features.get('price', 0)
        budget_min = requirements.get('budget_min', 0)
        budget_max = requirements.get('budget_max', float('inf'))

        if budget_min <= price <= budget_max:
            score += budget_weight
            reasons.append(f"Within budget range (${price:,.0f})")
        elif price < budget_min:
            # Below budget might be good
            score += budget_weight * 0.8
            reasons.append(f"Under budget by ${budget_min - price:,.0f}")
        else:
            # Over budget is bad, but not zero if close
            if price <= budget_max * 1.1:  # 10% over
                score += budget_weight * 0.3
                reasons.append(f"Slightly over budget (${price - budget_max:,.0f})")

        total_weight += budget_weight

        # Bedrooms match
        bed_weight = 0.25
        wanted_beds = requirements.get('bedrooms')
        property_beds = property_features.get('bedrooms', 0)

        if wanted_beds and property_beds:
            if property_beds >= wanted_beds:
                score += bed_weight
                if property_beds == wanted_beds:
                    reasons.append(f"Exact bedroom match ({property_beds} bed)")
                else:
                    reasons.append(f"Extra bedrooms ({property_beds} vs {wanted_beds} wanted)")
            elif property_beds == wanted_beds - 1:
                score += bed_weight * 0.5
                reasons.append(f"Close bedroom count ({property_beds} vs {wanted_beds} wanted)")

        total_weight += bed_weight

        # Bathrooms match
        bath_weight = 0.15
        wanted_baths = requirements.get('bathrooms')
        property_baths = property_features.get('bathrooms', 0)

        if wanted_baths and property_baths:
            if property_baths >= wanted_baths:
                score += bath_weight
                reasons.append(f"Sufficient bathrooms ({property_baths})")
            elif property_baths >= wanted_baths - 0.5:
                score += bath_weight * 0.7

        total_weight += bath_weight

        # Property type match
        type_weight = 0.2
        wanted_type = requirements.get('property_type')
        property_type = property_features.get('property_type', '').lower()

        if wanted_type and property_type:
            if wanted_type.lower() in property_type or property_type in wanted_type.lower():
                score += type_weight
                reasons.append(f"Property type match ({property_type})")
            elif self._are_similar_property_types(wanted_type, property_type):
                score += type_weight * 0.6
                reasons.append(f"Similar property type ({property_type})")

        total_weight += type_weight

        # Must-have features
        features_weight = 0.1
        must_haves = requirements.get('must_haves', [])
        property_features_list = property_features.get('features', [])

        if must_haves:
            matched_features = 0
            for feature in must_haves:
                if any(feature.lower() in pf.lower() for pf in property_features_list):
                    matched_features += 1

            feature_score = matched_features / len(must_haves)
            score += features_weight * feature_score

            if matched_features > 0:
                reasons.append(f"Has {matched_features}/{len(must_haves)} must-have features")

        total_weight += features_weight

        # Normalize score
        return (score / total_weight) if total_weight > 0 else 0.0, reasons

    async def _score_behavioral_match(
        self,
        property_features: Dict,
        behavioral_preferences: Dict
    ) -> Tuple[float, Dict[str, float]]:
        """Score based on learned behavioral preferences"""

        behavioral_signals = {}
        score = 0.0

        # Price sensitivity alignment
        price_focus = behavioral_preferences.get('price_sensitivity', 0.5)
        property_price_tier = self._get_price_tier(property_features.get('price', 0))

        # If user is price sensitive, favor lower-tier properties
        if price_focus > 0.7 and property_price_tier <= 0.4:
            score += 0.3
            behavioral_signals['price_alignment'] = 0.8
        elif price_focus < 0.3 and property_price_tier >= 0.6:
            score += 0.3
            behavioral_signals['price_alignment'] = 0.8
        else:
            behavioral_signals['price_alignment'] = 0.5

        # Location importance
        location_focus = behavioral_preferences.get('location_importance', 0.5)
        location_score = property_features.get('location_score', 0.5)

        if location_focus > 0.6:
            score += 0.25 * location_score
            behavioral_signals['location_match'] = location_score

        # Feature importance
        feature_focus = behavioral_preferences.get('feature_importance', 0.5)
        features_count = len(property_features.get('features', []))

        if feature_focus > 0.6 and features_count > 8:
            score += 0.2
            behavioral_signals['feature_richness'] = min(features_count / 15, 1.0)

        # Visual engagement prediction
        visual_pref = behavioral_preferences.get('visual_preference', 0.5)
        image_count = len(property_features.get('images', []))

        if visual_pref > 0.6 and image_count > 10:
            score += 0.15
            behavioral_signals['visual_appeal'] = min(image_count / 20, 1.0)

        # Description engagement
        desc_pref = behavioral_preferences.get('description_engagement', 0.5)
        desc_length = len(property_features.get('description', ''))

        if desc_pref > 0.6 and desc_length > 500:
            score += 0.1
            behavioral_signals['description_depth'] = min(desc_length / 1000, 1.0)

        return min(score, 1.0), behavioral_signals

    async def _score_market_factors(
        self,
        property_data: Dict,
        lead_preferences: LeadPreferences
    ) -> Tuple[float, Dict[str, float]]:
        """Score based on market conditions and competitiveness"""

        market_factors = {}
        score = 0.0

        # Days on market (fresher is often better)
        days_on_market = property_data.get('days_on_market', 30)
        if days_on_market < 7:
            score += 0.3
            market_factors['freshness'] = 0.9
        elif days_on_market < 30:
            score += 0.2
            market_factors['freshness'] = 0.7
        else:
            market_factors['freshness'] = max(0.1, 1.0 - (days_on_market / 180))

        # Price per square foot competitiveness
        price = property_data.get('price', 0)
        sqft = property_data.get('square_feet', 1)
        price_per_sqft = price / sqft if sqft > 0 else 0

        # Compare to market average (mock data - in production, use real market data)
        market_avg_price_per_sqft = 200  # This would come from market analysis
        price_ratio = price_per_sqft / market_avg_price_per_sqft if market_avg_price_per_sqft > 0 else 1.0

        if price_ratio < 0.9:  # Good deal
            score += 0.25
            market_factors['price_competitiveness'] = 0.9
        elif price_ratio < 1.1:  # Fair market
            score += 0.15
            market_factors['price_competitiveness'] = 0.7
        else:  # Expensive
            market_factors['price_competitiveness'] = max(0.2, 1.0 - (price_ratio - 1.0))

        # Neighborhood desirability (mock scoring)
        neighborhood = property_data.get('neighborhood', '').lower()
        desirable_neighborhoods = ['downtown', 'central', 'heights', 'grove']

        if any(area in neighborhood for area in desirable_neighborhoods):
            score += 0.2
            market_factors['neighborhood_desirability'] = 0.8
        else:
            market_factors['neighborhood_desirability'] = 0.5

        # Recent price changes
        price_change = property_data.get('recent_price_change', 0)
        if price_change < 0:  # Price reduction
            score += 0.15
            market_factors['price_trend'] = 0.8
        else:
            market_factors['price_trend'] = 0.5

        # School ratings (if available)
        school_rating = property_data.get('school_rating', 5)
        if school_rating >= 8:
            score += 0.1
            market_factors['school_quality'] = school_rating / 10
        else:
            market_factors['school_quality'] = school_rating / 10

        return min(score, 1.0), market_factors

    # Additional helper methods...

    async def _extract_property_features(self, property_data: Dict) -> Dict:
        """Extract and normalize property features"""
        return {
            'price': property_data.get('price', 0),
            'bedrooms': property_data.get('bedrooms', 0),
            'bathrooms': property_data.get('bathrooms', 0),
            'square_feet': property_data.get('square_feet', 0),
            'property_type': property_data.get('type', ''),
            'location': property_data.get('address', ''),
            'features': property_data.get('features', []),
            'images': property_data.get('images', []),
            'description': property_data.get('description', ''),
            'neighborhood': property_data.get('neighborhood', ''),
            'year_built': property_data.get('year_built', 1950),
            'lot_size': property_data.get('lot_size', 0),
            'garage': property_data.get('garage_spaces', 0),
            'pool': 'pool' in str(property_data.get('features', [])).lower(),
            'location_score': self._calculate_location_score(property_data)
        }

    def _calculate_location_score(self, property_data: Dict) -> float:
        """Calculate location desirability score"""
        # Mock implementation - in production, use real location analytics
        neighborhood = property_data.get('neighborhood', '').lower()

        premium_areas = ['downtown', 'central', 'heights']
        good_areas = ['north', 'south', 'east', 'west']

        if any(area in neighborhood for area in premium_areas):
            return 0.9
        elif any(area in neighborhood for area in good_areas):
            return 0.7
        else:
            return 0.5

    def _get_price_tier(self, price: float) -> float:
        """Get normalized price tier (0-1, where 1 is luxury)"""
        # Mock implementation - in production, use market percentiles
        if price < 300000:
            return 0.2
        elif price < 500000:
            return 0.4
        elif price < 800000:
            return 0.6
        elif price < 1200000:
            return 0.8
        else:
            return 1.0

    def _are_similar_property_types(self, type1: str, type2: str) -> bool:
        """Check if two property types are similar"""
        similar_groups = [
            ['house', 'single-family', 'detached'],
            ['condo', 'condominium', 'apartment'],
            ['townhouse', 'townhome', 'row house'],
            ['duplex', 'multi-family', 'triplex']
        ]

        type1_lower = type1.lower()
        type2_lower = type2.lower()

        for group in similar_groups:
            if any(t in type1_lower for t in group) and any(t in type2_lower for t in group):
                return True

        return False

    def _calculate_confidence(
        self,
        lead_preferences: LeadPreferences,
        property_features: Dict,
        include_behavioral: bool
    ) -> float:
        """Calculate matching confidence based on data completeness"""
        confidence_factors = []

        # Explicit requirements completeness
        explicit_reqs = lead_preferences.explicit_requirements
        req_completeness = sum([
            1 if explicit_reqs.get('budget_max') else 0,
            1 if explicit_reqs.get('bedrooms') else 0,
            1 if explicit_reqs.get('property_type') else 0,
            1 if explicit_reqs.get('location_preferences') else 0
        ]) / 4
        confidence_factors.append(req_completeness)

        # Property data completeness
        prop_completeness = sum([
            1 if property_features.get('price') else 0,
            1 if property_features.get('bedrooms') else 0,
            1 if property_features.get('square_feet') else 0,
            1 if property_features.get('features') else 0,
            1 if property_features.get('images') else 0
        ]) / 5
        confidence_factors.append(prop_completeness)

        # Behavioral data availability
        if include_behavioral and lead_preferences.behavioral_preferences:
            behavioral_completeness = len(lead_preferences.behavioral_preferences) / 5
            confidence_factors.append(behavioral_completeness)

        # Historical pattern depth
        if lead_preferences.historical_patterns.get('properties_viewed', 0) > 5:
            confidence_factors.append(0.9)
        elif lead_preferences.historical_patterns.get('properties_viewed', 0) > 0:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)

        return np.mean(confidence_factors)

    async def _calculate_price_competitiveness(
        self,
        property_data: Dict,
        lead_preferences: LeadPreferences
    ) -> float:
        """Calculate how competitive the property price is"""
        price = property_data.get('price', 0)
        budget_max = lead_preferences.explicit_requirements.get('budget_max', float('inf'))

        if budget_max == float('inf'):
            return 0.5  # No reference point

        price_ratio = price / budget_max

        if price_ratio <= 0.8:
            return 0.9  # Great value
        elif price_ratio <= 0.95:
            return 0.7  # Good value
        elif price_ratio <= 1.05:
            return 0.5  # Fair value
        else:
            return max(0.1, 1.1 - price_ratio)  # Expensive

    # Performance tracking and learning methods

    async def record_interaction(
        self,
        lead_id: str,
        property_id: str,
        interaction_type: str,
        details: Dict = None
    ) -> None:
        """Record lead interaction with property for learning"""
        if lead_id not in self.user_interactions:
            self.user_interactions[lead_id] = {
                'total_properties_viewed': 0,
                'properties_saved': [],
                'properties_rejected': [],
                'avg_viewing_time': 0,
                'price_focus_score': 0.5,
                'location_focus_score': 0.5,
                'features_focus_score': 0.5,
                'image_engagement_score': 0.5,
                'text_engagement_score': 0.5
            }

        user_data = self.user_interactions[lead_id]

        if interaction_type == 'view':
            user_data['total_properties_viewed'] += 1
            viewing_time = details.get('time_spent', 0) if details else 0

            # Update average viewing time (exponential moving average)
            alpha = 0.2
            user_data['avg_viewing_time'] = (
                alpha * viewing_time + (1 - alpha) * user_data['avg_viewing_time']
            )

        elif interaction_type == 'save':
            if property_id not in user_data['properties_saved']:
                user_data['properties_saved'].append(property_id)

        elif interaction_type == 'reject':
            if property_id not in user_data['properties_rejected']:
                user_data['properties_rejected'].append(property_id)

        # Update engagement scores based on interaction details
        if details:
            if 'price_focused' in details:
                user_data['price_focus_score'] = self._update_score(
                    user_data['price_focus_score'], details['price_focused']
                )

            if 'location_focused' in details:
                user_data['location_focus_score'] = self._update_score(
                    user_data['location_focus_score'], details['location_focused']
                )

    def _update_score(self, current_score: float, new_signal: float, alpha: float = 0.1) -> float:
        """Update engagement score using exponential moving average"""
        return alpha * new_signal + (1 - alpha) * current_score

    async def _log_matching_performance(self, metrics: Dict) -> None:
        """Log matching performance for monitoring and optimization"""
        try:
            # Store performance metrics
            await self.memory_service.store_data(
                f"matching_performance_{datetime.utcnow().strftime('%Y%m%d_%H')}",
                "system",
                metrics
            )

            # Update running averages
            if 'avg_processing_time' not in self.prediction_accuracy:
                self.prediction_accuracy['avg_processing_time'] = metrics['processing_time_ms']
            else:
                alpha = 0.1
                self.prediction_accuracy['avg_processing_time'] = (
                    alpha * metrics['processing_time_ms'] +
                    (1 - alpha) * self.prediction_accuracy['avg_processing_time']
                )

        except Exception as e:
            logger.warning(f"Failed to log performance metrics: {e}")

    # Additional methods for ML model training and filtering...
    async def _load_historical_data(self) -> List[Dict]:
        """Load historical matching data for model training"""
        # Mock implementation - in production, load from database
        return []

    async def _train_interest_predictor(self, data: List[Dict]) -> None:
        """Train ML model to predict property interest"""
        # Mock implementation - in production, implement full ML pipeline
        self.interest_predictor = RandomForestRegressor(n_estimators=100, random_state=42)

    async def _train_viewing_predictor(self, data: List[Dict]) -> None:
        """Train ML model to predict viewing probability"""
        self.viewing_predictor = GradientBoostingClassifier(random_state=42)

    async def _train_preference_clusters(self, data: List[Dict]) -> None:
        """Train preference clustering model"""
        self.preference_clusterer = KMeans(n_clusters=5, random_state=42)

    def _create_feature_vector(self, property_features: Dict, lead_preferences: LeadPreferences) -> np.ndarray:
        """Create feature vector for ML prediction"""
        # Mock implementation - create comprehensive feature vector
        return np.array([
            property_features.get('price', 0) / 1000000,  # Normalized price
            property_features.get('bedrooms', 0) / 5,
            property_features.get('bathrooms', 0) / 4,
            property_features.get('square_feet', 0) / 5000,
            len(property_features.get('features', [])) / 20,
            lead_preferences.urgency_level,
            # Add more features as needed
        ])

    async def _apply_matching_filters(
        self,
        matches: List[PropertyMatch],
        lead_preferences: LeadPreferences,
        max_matches: int
    ) -> List[PropertyMatch]:
        """Apply diversity and quality filters to matches"""

        if not matches:
            return []

        # 1. Remove very low confidence matches
        filtered_matches = [m for m in matches if m.confidence > 0.3]

        # 2. Ensure diversity in price ranges
        price_diverse_matches = self._ensure_price_diversity(filtered_matches)

        # 3. Ensure diversity in property types
        type_diverse_matches = self._ensure_type_diversity(price_diverse_matches)

        # 4. Sort by combined score and confidence
        final_matches = sorted(
            type_diverse_matches,
            key=lambda x: x.match_score * x.confidence,
            reverse=True
        )

        return final_matches[:max_matches]

    def _ensure_price_diversity(self, matches: List[PropertyMatch]) -> List[PropertyMatch]:
        """Ensure price diversity in matches"""
        # Group matches by price tiers and ensure representation from different tiers
        if len(matches) <= 5:
            return matches

        # Simple implementation - in production, use more sophisticated diversity algorithms
        sorted_by_score = sorted(matches, key=lambda x: x.match_score, reverse=True)
        return sorted_by_score  # Placeholder

    def _ensure_type_diversity(self, matches: List[PropertyMatch]) -> List[PropertyMatch]:
        """Ensure property type diversity in matches"""
        return matches  # Placeholder


# Global instance
ai_property_matcher = AIPropertyMatcher()


# Convenience functions
async def find_ai_property_matches(
    lead_id: str,
    tenant_id: str,
    properties: List[Dict],
    max_matches: int = 10
) -> List[PropertyMatch]:
    """Find AI-powered property matches"""
    return await ai_property_matcher.find_matches(lead_id, tenant_id, properties, max_matches)


async def record_property_interaction(
    lead_id: str,
    property_id: str,
    interaction_type: str,
    details: Dict = None
) -> None:
    """Record property interaction for behavioral learning"""
    await ai_property_matcher.record_interaction(lead_id, property_id, interaction_type, details)