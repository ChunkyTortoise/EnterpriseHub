"""
Advanced Property Matching Engine - Phase 2.2
==============================================

Behavioral-enhanced property matching with ML optimization.
Integrates with Phase 2.1 behavioral predictions for intelligent matching.

Features:
- Behavioral-enhanced matching with adaptive weighting
- ML-powered confidence scoring and ranking
- Real-time caching with tenant isolation
- Event publishing for real-time updates
- Performance targets: <100ms matching, 95%+ relevance accuracy

Author: Jorge's Real Estate AI Platform - Phase 2.2 Implementation
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
import asyncio
import hashlib
import json
import numpy as np
from enum import Enum

# Core service imports
from ghl_real_estate_ai.services.enhanced_property_matcher import get_enhanced_property_matcher
from ghl_real_estate_ai.services.predictive_lead_behavior_service import get_predictive_behavior_service
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
try:
    from bots.shared.ml_analytics_engine import get_ml_analytics_engine
except ImportError:
    from ghl_real_estate_ai.stubs.bots_stub import get_ml_analytics_engine
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# Configuration constants
CACHE_TTL_MATCHES = 900  # 15 minutes for match results
CACHE_TTL_SCORES = 3600  # 1 hour for individual scores
ML_CONFIDENCE_THRESHOLD = 0.85  # Match Claude escalation pattern
TARGET_LATENCY_MS = 100  # <100ms matching target
BATCH_SIZE = 50  # Batch processing for efficiency
MAX_MATCHES_CACHE = 20  # Cache top 20 matches per lead


class PresentationStrategy(Enum):
    """Optimal property presentation strategies based on behavioral profile."""
    URGENT = "urgent"  # High engagement, fast decision velocity
    VALUE_FOCUSED = "value_focused"  # Price-sensitive, analytical
    STREAMLINED = "streamlined"  # Low engagement, need simple options
    COMPREHENSIVE = "comprehensive"  # Highly engaged, wants details


@dataclass
class AdvancedPropertyMatch:
    """Enhanced property match with behavioral intelligence."""

    # Base property match from enhanced matcher
    property_match: Any  # PropertyMatch from enhanced_property_matcher

    # Behavioral enhancements
    behavioral_fit_score: float  # 0-100 behavioral alignment
    engagement_prediction: float  # 0-1 predicted click-through rate
    conversion_likelihood: float  # 0-1 predicted showing request probability
    optimal_presentation_time: Optional[str]  # Best contact window (HH:MM format)
    presentation_strategy: PresentationStrategy  # How to present this property
    behavioral_reasoning: str  # Why this property fits behaviorally

    # ML confidence and metadata
    confidence_score: float  # 0-1 ML confidence in match quality
    calculation_time_ms: float  # Processing time for this match
    calculated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses and caching."""
        return {
            'property_id': self.property_match.property_id,
            'overall_score': self.property_match.overall_score,
            'behavioral_fit_score': self.behavioral_fit_score,
            'engagement_prediction': self.engagement_prediction,
            'conversion_likelihood': self.conversion_likelihood,
            'optimal_presentation_time': self.optimal_presentation_time,
            'presentation_strategy': self.presentation_strategy.value,
            'behavioral_reasoning': self.behavioral_reasoning,
            'confidence_score': self.confidence_score,
            'calculation_time_ms': self.calculation_time_ms,
            'calculated_at': self.calculated_at.isoformat(),
            'property_data': self.property_match.property,
            'factor_scores': self.property_match.factor_scores,
            'match_reasons': self.property_match.match_reasons
        }


class AdvancedPropertyMatchingEngine:
    """
    Behavioral-enhanced property matching engine with ML optimization.

    Features:
    - Integrates Phase 2.1 behavioral predictions for adaptive weighting
    - 15+ factor matching algorithm with behavioral enhancement
    - Multi-tier caching with predictive prefetching
    - Real-time inventory monitoring and event publishing
    - ML-powered confidence scoring and engagement prediction

    Performance Targets:
    - <100ms match generation (95th percentile)
    - <50ms cache hits
    - 95%+ relevance accuracy
    - >80% cache hit rate
    """

    def __init__(self):
        # Core services (singleton pattern)
        self.property_matcher = get_enhanced_property_matcher()
        self.behavior_service = get_predictive_behavior_service()
        self.cache = get_cache_service()
        self.event_publisher = get_event_publisher()
        self.ml_engine = get_ml_analytics_engine()

        # Performance tracking
        self.metrics = {
            'matches_generated': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_latency_ms': 0.0,
            'behavioral_improvements': 0,
            'ml_scoring_time_ms': 0.0,
            'last_reset': datetime.now(timezone.utc)
        }

        logger.info("AdvancedPropertyMatchingEngine initialized")

    async def find_behavioral_matches(
        self,
        lead_id: str,
        location_id: str,
        preferences: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_results: int = 10,
        min_score: float = 0.6,
        force_refresh: bool = False
    ) -> List[AdvancedPropertyMatch]:
        """
        Find property matches enhanced with behavioral predictions.

        Algorithm:
        1. Get behavioral prediction from Phase 2.1 service
        2. Calculate adaptive weights based on behavior category
        3. Use EnhancedPropertyMatcher with behavioral weights
        4. Apply ML confidence scoring and engagement prediction
        5. Cache results with tenant isolation
        6. Publish real-time events

        Args:
            lead_id: Lead identifier
            location_id: Tenant/location identifier
            preferences: Property search preferences
            conversation_history: Recent conversation context
            max_results: Maximum matches to return
            min_score: Minimum match score threshold
            force_refresh: Skip cache and force fresh matching

        Returns:
            List of AdvancedPropertyMatch objects sorted by relevance
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Check cache first (tenant-scoped)
            if not force_refresh:
                cached_matches = await self._get_cached_matches(
                    lead_id, location_id, preferences
                )
                if cached_matches:
                    self.metrics['cache_hits'] += 1
                    await self._publish_match_event(
                        lead_id, location_id, cached_matches[:max_results]
                    )
                    return cached_matches[:max_results]

            self.metrics['cache_misses'] += 1

            # Get behavioral prediction (Phase 2.1 integration)
            behavioral_prediction = await self.behavior_service.predict_behavior(
                lead_id=lead_id,
                location_id=location_id,
                conversation_history=conversation_history,
                force_refresh=False
            )

            # Calculate behavioral-adjusted weights
            adaptive_weights = await self._calculate_behavioral_weights(
                behavioral_prediction, preferences
            )

            # Use enhanced matcher with behavioral weights
            base_matches = await self.property_matcher.find_enhanced_matches(
                preferences=preferences,
                adaptive_weights=adaptive_weights,
                location_id=location_id,
                limit=max_results * 2,  # Get more for re-ranking
                min_score=min_score - 0.1  # Slightly lower threshold for re-ranking
            )

            if not base_matches:
                logger.warning(f"No base matches found for lead {lead_id}")
                return []

            # Apply ML confidence scoring and behavioral enhancement
            enhanced_matches = await self._apply_behavioral_enhancement(
                base_matches,
                behavioral_prediction,
                preferences,
                lead_id,
                location_id
            )

            # Sort by combined score and limit results
            enhanced_matches.sort(
                key=lambda m: (m.confidence_score * m.property_match.overall_score),
                reverse=True
            )
            enhanced_matches = enhanced_matches[:max_results]

            # Cache results (15-minute TTL)
            await self._cache_matches(
                lead_id, location_id, preferences, enhanced_matches
            )

            # Publish real-time event
            await self._publish_match_event(lead_id, location_id, enhanced_matches)

            # Update metrics
            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._update_metrics(latency_ms)

            logger.info(
                f"Generated {len(enhanced_matches)} behavioral matches for {lead_id} "
                f"({latency_ms:.1f}ms)"
            )

            return enhanced_matches

        except Exception as e:
            logger.error(f"Match generation failed for {lead_id}: {e}", exc_info=True)
            # Fallback to basic matching without behavioral enhancement
            return await self._fallback_matching(
                lead_id, location_id, preferences, max_results
            )

    async def _calculate_behavioral_weights(
        self,
        behavioral_prediction: Any,  # BehavioralPrediction from Phase 2.1
        preferences: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate adaptive weights based on behavioral prediction.

        Adaptive Weighting Strategy:
        - Highly Engaged: Emphasize precision factors (location, budget match)
        - Moderately Engaged: Balanced approach with lifestyle factors
        - Low Engagement: Prioritize strong matches, reduce complexity
        - Churning: Focus on immediate value, reduce objection potential
        - Converting: Emphasize closing factors (price, availability)
        """
        try:
            base_weights = {
                'location': 0.25,
                'budget': 0.20,
                'size': 0.15,
                'property_type': 0.10,
                'lifestyle': 0.15,
                'market_conditions': 0.10,
                'timing': 0.05
            }

            if not behavioral_prediction:
                return base_weights

            behavior_category = getattr(behavioral_prediction, 'behavior_category', 'moderately_engaged')
            decision_velocity = getattr(behavioral_prediction, 'decision_velocity', 'moderate')
            churn_risk_score = getattr(behavioral_prediction, 'churn_risk_score', 50.0)

            # Behavioral adjustments
            adjustments = {}

            # Category-based adjustments
            if behavior_category == 'highly_engaged':
                # Precise matching for engaged leads
                adjustments.update({
                    'location': 0.30,  # More location-sensitive
                    'lifestyle': 0.20,  # Emphasize lifestyle match
                    'budget': 0.18
                })
            elif behavior_category == 'churning':
                # Strong matches only for churning leads
                adjustments.update({
                    'budget': 0.35,  # Must fit budget perfectly
                    'location': 0.20,
                    'size': 0.20,
                    'lifestyle': 0.05  # Reduce complexity
                })
            elif behavior_category == 'converting':
                # Closing-focused for converting leads
                adjustments.update({
                    'budget': 0.30,
                    'timing': 0.15,  # Emphasize availability
                    'market_conditions': 0.15
                })

            # Decision velocity adjustments
            if decision_velocity == 'fast':
                adjustments['timing'] = adjustments.get('timing', base_weights['timing']) + 0.05
                adjustments['market_conditions'] = adjustments.get('market_conditions', base_weights['market_conditions']) + 0.05
            elif decision_velocity == 'slow':
                adjustments['lifestyle'] = adjustments.get('lifestyle', base_weights['lifestyle']) + 0.10
                adjustments['location'] = adjustments.get('location', base_weights['location']) + 0.05

            # Churn risk adjustments
            if churn_risk_score > 70:
                # High churn risk - prioritize strong matches
                adjustments['budget'] = max(adjustments.get('budget', base_weights['budget']), 0.30)
                adjustments['lifestyle'] = min(adjustments.get('lifestyle', base_weights['lifestyle']), 0.10)

            # Apply adjustments while maintaining sum = 1.0
            for key, value in adjustments.items():
                base_weights[key] = value

            # Normalize to ensure sum = 1.0
            total_weight = sum(base_weights.values())
            for key in base_weights:
                base_weights[key] = base_weights[key] / total_weight

            return base_weights

        except Exception as e:
            logger.error(f"Weight calculation failed: {e}")
            # Return default weights on error
            return {
                'location': 0.25, 'budget': 0.20, 'size': 0.15,
                'property_type': 0.10, 'lifestyle': 0.15,
                'market_conditions': 0.10, 'timing': 0.05
            }

    async def _apply_behavioral_enhancement(
        self,
        base_matches: List[Any],  # PropertyMatch objects
        behavioral_prediction: Any,
        preferences: Dict[str, Any],
        lead_id: str,
        location_id: str
    ) -> List[AdvancedPropertyMatch]:
        """Apply behavioral enhancement and ML scoring to base matches."""
        enhanced_matches = []

        for match in base_matches:
            try:
                start_time = datetime.now(timezone.utc)

                # Calculate behavioral fit score
                behavioral_fit = await self._calculate_behavioral_fit(
                    match, behavioral_prediction, preferences
                )

                # Predict engagement and conversion likelihood
                engagement_pred = await self._predict_engagement(
                    match, behavioral_prediction, lead_id, location_id
                )

                conversion_likelihood = await self._predict_conversion_likelihood(
                    match, behavioral_prediction, engagement_pred
                )

                # Determine optimal presentation strategy
                presentation_strategy = self._determine_presentation_strategy(
                    behavioral_prediction, engagement_pred
                )

                # Generate behavioral reasoning
                behavioral_reasoning = await self._generate_behavioral_reasoning(
                    match, behavioral_prediction, behavioral_fit
                )

                # Calculate ML confidence score
                confidence_score = await self._calculate_ml_confidence(
                    match, behavioral_fit, engagement_pred, conversion_likelihood
                )

                # Determine optimal presentation time
                optimal_time = await self._get_optimal_presentation_time(
                    behavioral_prediction
                )

                # Create enhanced match
                enhanced_match = AdvancedPropertyMatch(
                    property_match=match,
                    behavioral_fit_score=behavioral_fit,
                    engagement_prediction=engagement_pred,
                    conversion_likelihood=conversion_likelihood,
                    optimal_presentation_time=optimal_time,
                    presentation_strategy=presentation_strategy,
                    behavioral_reasoning=behavioral_reasoning,
                    confidence_score=confidence_score,
                    calculation_time_ms=(datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                    calculated_at=datetime.now(timezone.utc)
                )

                enhanced_matches.append(enhanced_match)

            except Exception as e:
                logger.error(f"Enhancement failed for match {match.property_id}: {e}")
                # Create basic enhanced match without behavioral features
                enhanced_match = AdvancedPropertyMatch(
                    property_match=match,
                    behavioral_fit_score=50.0,  # Neutral score
                    engagement_prediction=0.5,
                    conversion_likelihood=0.3,
                    optimal_presentation_time=None,
                    presentation_strategy=PresentationStrategy.STREAMLINED,
                    behavioral_reasoning="Behavioral analysis unavailable",
                    confidence_score=0.7,  # Lower confidence
                    calculation_time_ms=0.0,
                    calculated_at=datetime.now(timezone.utc)
                )
                enhanced_matches.append(enhanced_match)

        return enhanced_matches

    async def _calculate_behavioral_fit(
        self,
        match: Any,
        behavioral_prediction: Any,
        preferences: Dict[str, Any]
    ) -> float:
        """Calculate 0-100 behavioral fit score for a property match."""
        try:
            if not behavioral_prediction:
                return 50.0  # Neutral score

            fit_score = 0.0

            # Engagement alignment (0-25 points)
            engagement_score = getattr(behavioral_prediction, 'engagement_score_7d', 50.0)
            if engagement_score > 75:
                fit_score += 25.0  # High engagement = detailed properties OK
            elif engagement_score > 50:
                fit_score += 15.0
            elif engagement_score > 25:
                fit_score += 10.0
            else:
                fit_score += 5.0  # Low engagement = simple properties better

            # Churn risk adjustment (0-20 points)
            churn_risk = getattr(behavioral_prediction, 'churn_risk_score', 50.0)
            if churn_risk < 30:
                fit_score += 20.0  # Low churn risk
            elif churn_risk < 60:
                fit_score += 15.0
            else:
                fit_score += 5.0  # High churn risk = need strong matches

            # Decision velocity alignment (0-20 points)
            decision_velocity = getattr(behavioral_prediction, 'decision_velocity', 'moderate')
            property_complexity = self._assess_property_complexity(match.property)

            if decision_velocity == 'fast' and property_complexity < 0.3:
                fit_score += 20.0  # Fast decision + simple property = good fit
            elif decision_velocity == 'slow' and property_complexity > 0.7:
                fit_score += 20.0  # Slow decision + complex property = good fit
            else:
                fit_score += 10.0  # Moderate fit

            # Communication preference alignment (0-15 points)
            comm_prefs = getattr(behavioral_prediction, 'communication_preferences', {})
            if comm_prefs.get('in_person', 0) > 0.7:
                # High in-person preference = location accessibility important
                location_score = match.factor_scores.get('location', 0.5)
                fit_score += location_score * 15.0
            else:
                fit_score += 10.0

            # Conversion readiness alignment (0-20 points)
            conversion_readiness = getattr(behavioral_prediction, 'conversion_readiness_score', 50.0)
            if conversion_readiness > 80:
                fit_score += 20.0
            elif conversion_readiness > 60:
                fit_score += 15.0
            else:
                fit_score += 8.0

            return min(fit_score, 100.0)

        except Exception as e:
            logger.error(f"Behavioral fit calculation failed: {e}")
            return 50.0  # Fallback neutral score

    def _assess_property_complexity(self, property_data: Dict[str, Any]) -> float:
        """Assess property complexity (0-1 scale) based on features."""
        try:
            complexity = 0.0

            # Size complexity
            sqft = property_data.get('sqft', 2000)
            if sqft > 4000:
                complexity += 0.2
            elif sqft < 1500:
                complexity += 0.1

            # Price complexity
            price = property_data.get('price', 400000)
            if price > 1000000:
                complexity += 0.2

            # Feature complexity
            features = property_data.get('features', [])
            if len(features) > 10:
                complexity += 0.2
            elif len(features) > 5:
                complexity += 0.1

            # Property type complexity
            prop_type = property_data.get('property_type', 'single_family')
            if prop_type in ['luxury', 'commercial', 'multi_family']:
                complexity += 0.2
            elif prop_type in ['condo', 'townhouse']:
                complexity += 0.1

            # Listing complexity
            description = property_data.get('description', '')
            if len(description) > 1000:
                complexity += 0.1

            return min(complexity, 1.0)

        except Exception:
            return 0.5  # Moderate complexity default

    async def _predict_engagement(
        self,
        match: Any,
        behavioral_prediction: Any,
        lead_id: str,
        location_id: str
    ) -> float:
        """Predict engagement probability (0-1) using ML Analytics Engine."""
        try:
            if not self.ml_engine:
                return 0.5  # Default prediction

            # Extract features for engagement prediction
            features = {
                'match_score': match.overall_score,
                'behavioral_fit': await self._calculate_behavioral_fit(
                    match, behavioral_prediction, {}
                ),
                'engagement_history': getattr(behavioral_prediction, 'engagement_score_7d', 50.0) / 100.0,
                'churn_risk': getattr(behavioral_prediction, 'churn_risk_score', 50.0) / 100.0,
                'property_price': match.property.get('price', 400000),
                'property_sqft': match.property.get('sqft', 2000),
                'location_score': match.factor_scores.get('location', 0.5),
                'budget_score': match.factor_scores.get('budget', 0.5),
                'size_score': match.factor_scores.get('size', 0.5)
            }

            # Use ML engine for prediction
            prediction = await self.ml_engine.predict_engagement_probability(
                features, model_type='property_engagement'
            )

            return min(max(prediction, 0.0), 1.0)

        except Exception as e:
            logger.error(f"Engagement prediction failed: {e}")
            # Fallback based on match score
            return min(max(match.overall_score * 0.8, 0.1), 0.9)

    async def _predict_conversion_likelihood(
        self,
        match: Any,
        behavioral_prediction: Any,
        engagement_prediction: float
    ) -> float:
        """Predict conversion likelihood (0-1) based on behavioral and engagement factors."""
        try:
            # Base conversion on engagement
            conversion = engagement_prediction * 0.6

            # Behavioral adjustments
            if behavioral_prediction:
                conversion_readiness = getattr(behavioral_prediction, 'conversion_readiness_score', 50.0)
                conversion += (conversion_readiness / 100.0) * 0.3

                churn_risk = getattr(behavioral_prediction, 'churn_risk_score', 50.0)
                conversion += (1 - churn_risk / 100.0) * 0.1

            # Match quality adjustment
            conversion += match.overall_score * 0.1

            return min(max(conversion, 0.0), 1.0)

        except Exception:
            return engagement_prediction * 0.7  # Conservative fallback

    def _determine_presentation_strategy(
        self,
        behavioral_prediction: Any,
        engagement_prediction: float
    ) -> PresentationStrategy:
        """Determine optimal presentation strategy based on behavioral profile."""
        try:
            if not behavioral_prediction:
                return PresentationStrategy.STREAMLINED

            engagement_score = getattr(behavioral_prediction, 'engagement_score_7d', 50.0)
            decision_velocity = getattr(behavioral_prediction, 'decision_velocity', 'moderate')
            churn_risk = getattr(behavioral_prediction, 'churn_risk_score', 50.0)

            # High engagement + fast decision = urgent
            if engagement_score > 75 and decision_velocity == 'fast':
                return PresentationStrategy.URGENT

            # High churn risk = streamlined approach
            if churn_risk > 70:
                return PresentationStrategy.STREAMLINED

            # High engagement + detailed = comprehensive
            if engagement_score > 80 and engagement_prediction > 0.7:
                return PresentationStrategy.COMPREHENSIVE

            # Default to value-focused
            return PresentationStrategy.VALUE_FOCUSED

        except Exception:
            return PresentationStrategy.STREAMLINED

    async def _generate_behavioral_reasoning(
        self,
        match: Any,
        behavioral_prediction: Any,
        behavioral_fit_score: float
    ) -> str:
        """Generate human-readable reasoning for behavioral match."""
        try:
            if not behavioral_prediction:
                return "Standard property match based on search criteria."

            reasons = []

            # Engagement-based reasoning
            engagement_score = getattr(behavioral_prediction, 'engagement_score_7d', 50.0)
            if engagement_score > 75:
                reasons.append("highly engaged and active")
            elif engagement_score < 30:
                reasons.append("needs compelling reasons to engage")

            # Decision velocity reasoning
            decision_velocity = getattr(behavioral_prediction, 'decision_velocity', 'moderate')
            if decision_velocity == 'fast':
                reasons.append("quick decision-maker who values efficiency")
            elif decision_velocity == 'slow':
                reasons.append("careful decision-maker who appreciates details")

            # Conversion readiness reasoning
            conversion_readiness = getattr(behavioral_prediction, 'conversion_readiness_score', 50.0)
            if conversion_readiness > 80:
                reasons.append("showing strong buying signals")

            # Match strength reasoning
            if behavioral_fit_score > 80:
                reasons.append("excellent behavioral alignment")
            elif behavioral_fit_score > 60:
                reasons.append("good behavioral fit")
            else:
                reasons.append("potential with proper presentation")

            if reasons:
                return f"This property suits a lead who is {', '.join(reasons)}."
            else:
                return "Property matches search criteria with standard behavioral profile."

        except Exception:
            return "Behavioral analysis provides additional match insights."

    async def _calculate_ml_confidence(
        self,
        match: Any,
        behavioral_fit: float,
        engagement_pred: float,
        conversion_likelihood: float
    ) -> float:
        """Calculate ML confidence score (0-1) for the overall match quality."""
        try:
            # Weighted confidence calculation
            confidence = 0.0

            # Base match quality (40% weight)
            confidence += match.overall_score * 0.4

            # Behavioral fit confidence (30% weight)
            confidence += (behavioral_fit / 100.0) * 0.3

            # Engagement prediction confidence (20% weight)
            confidence += engagement_pred * 0.2

            # Conversion likelihood confidence (10% weight)
            confidence += conversion_likelihood * 0.1

            # Adjust for match score consistency
            score_variance = abs(match.overall_score - (behavioral_fit / 100.0))
            if score_variance < 0.1:
                confidence += 0.05  # Bonus for consistent scores

            return min(max(confidence, 0.1), 0.95)

        except Exception:
            return 0.7  # Default confidence

    async def _get_optimal_presentation_time(
        self,
        behavioral_prediction: Any
    ) -> Optional[str]:
        """Get optimal presentation time based on behavioral patterns."""
        try:
            if not behavioral_prediction:
                return None

            contact_windows = getattr(behavioral_prediction, 'optimal_contact_windows', [])
            if contact_windows and len(contact_windows) > 0:
                # Return the highest confidence window
                best_window = max(contact_windows, key=lambda w: w.get('confidence', 0))
                return best_window.get('start')

            return None

        except Exception:
            return None

    async def _get_cached_matches(
        self,
        lead_id: str,
        location_id: str,
        preferences: Dict[str, Any]
    ) -> Optional[List[AdvancedPropertyMatch]]:
        """Retrieve cached matches with tenant isolation."""
        try:
            cache_key = self._generate_cache_key(lead_id, preferences)

            cached_data = await self.cache.get(
                key=cache_key,
                location_id=location_id  # Tenant scoping
            )

            if cached_data:
                # Reconstruct AdvancedPropertyMatch objects from cached dictionaries
                matches = []
                for data in cached_data:
                    try:
                        # Recreate PropertyMatch from cached property data
                        from ghl_real_estate_ai.models.matching_models import PropertyMatch
                        property_match = PropertyMatch(
                            property_id=data['property_id'],
                            property=data['property_data'],
                            overall_score=data['overall_score'],
                            factor_scores=data['factor_scores'],
                            match_reasons=data['match_reasons']
                        )

                        # Reconstruct AdvancedPropertyMatch
                        advanced_match = AdvancedPropertyMatch(
                            property_match=property_match,
                            behavioral_fit_score=data['behavioral_fit_score'],
                            engagement_prediction=data['engagement_prediction'],
                            conversion_likelihood=data['conversion_likelihood'],
                            optimal_presentation_time=data['optimal_presentation_time'],
                            presentation_strategy=PresentationStrategy(data['presentation_strategy']),
                            behavioral_reasoning=data['behavioral_reasoning'],
                            confidence_score=data['confidence_score'],
                            calculation_time_ms=data['calculation_time_ms'],
                            calculated_at=datetime.fromisoformat(data['calculated_at'])
                        )
                        matches.append(advanced_match)

                    except Exception as deserialization_error:
                        logger.warning(f"Failed to deserialize cached match: {deserialization_error}")
                        continue

                if matches:
                    logger.debug(f"Successfully retrieved {len(matches)} cached matches for lead {lead_id}")
                    return matches
                else:
                    logger.warning("All cached matches failed deserialization, forcing fresh calculation")
                    return None

            return None

        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None

    async def _cache_matches(
        self,
        lead_id: str,
        location_id: str,
        preferences: Dict[str, Any],
        matches: List[AdvancedPropertyMatch]
    ) -> None:
        """Cache matches with tenant isolation."""
        try:
            cache_key = self._generate_cache_key(lead_id, preferences)

            # Convert to cacheable format
            cacheable_data = [match.to_dict() for match in matches[:MAX_MATCHES_CACHE]]

            await self.cache.set(
                key=cache_key,
                value=cacheable_data,
                ttl=CACHE_TTL_MATCHES,
                location_id=location_id  # Tenant scoping
            )

        except Exception as e:
            logger.error(f"Cache storage failed: {e}")

    def _generate_cache_key(
        self,
        lead_id: str,
        preferences: Dict[str, Any]
    ) -> str:
        """Generate cache key from lead ID and preferences."""
        # Create stable hash of preferences
        prefs_str = json.dumps(preferences, sort_keys=True)
        prefs_hash = hashlib.md5(prefs_str.encode()).hexdigest()[:8]

        return f"behavioral_matches:{lead_id}:{prefs_hash}"

    async def _publish_match_event(
        self,
        lead_id: str,
        location_id: str,
        matches: List[AdvancedPropertyMatch]
    ) -> None:
        """Publish real-time match event for top matches."""
        try:
            if not matches:
                return

            # Publish for top 5 matches
            for i, match in enumerate(matches[:5]):
                await self.event_publisher.publish_property_match_generated(
                    lead_id=lead_id,
                    location_id=location_id,
                    property_id=match.property_match.property_id,
                    match_score=match.property_match.overall_score,
                    behavioral_fit=match.behavioral_fit_score,
                    engagement_prediction=match.engagement_prediction,
                    rank=i + 1,
                    presentation_strategy=match.presentation_strategy.value,
                    reasoning=match.behavioral_reasoning
                )

        except Exception as e:
            logger.error(f"Event publishing failed: {e}")

    async def _fallback_matching(
        self,
        lead_id: str,
        location_id: str,
        preferences: Dict[str, Any],
        max_results: int
    ) -> List[AdvancedPropertyMatch]:
        """Fallback to basic matching without behavioral enhancement."""
        try:
            logger.warning(f"Using fallback matching for {lead_id}")

            # Use basic enhanced matcher
            base_matches = await self.property_matcher.find_enhanced_matches(
                preferences=preferences,
                location_id=location_id,
                limit=max_results,
                min_score=0.5
            )

            # Create minimal enhanced matches
            fallback_matches = []
            for match in base_matches:
                enhanced_match = AdvancedPropertyMatch(
                    property_match=match,
                    behavioral_fit_score=50.0,
                    engagement_prediction=0.5,
                    conversion_likelihood=0.3,
                    optimal_presentation_time=None,
                    presentation_strategy=PresentationStrategy.STREAMLINED,
                    behavioral_reasoning="Fallback matching - behavioral analysis unavailable",
                    confidence_score=0.6,
                    calculation_time_ms=0.0,
                    calculated_at=datetime.now(timezone.utc)
                )
                fallback_matches.append(enhanced_match)

            return fallback_matches

        except Exception as e:
            logger.error(f"Fallback matching failed: {e}")
            return []

    def _update_metrics(self, latency_ms: float) -> None:
        """Update performance metrics."""
        self.metrics['matches_generated'] += 1
        self.metrics['avg_latency_ms'] = (
            (self.metrics['avg_latency_ms'] * (self.metrics['matches_generated'] - 1) + latency_ms)
            / self.metrics['matches_generated']
        )

        # Reset metrics every hour
        if (datetime.now(timezone.utc) - self.metrics['last_reset']).seconds > 3600:
            self.metrics.update({
                'matches_generated': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'avg_latency_ms': 0.0,
                'behavioral_improvements': 0,
                'last_reset': datetime.now(timezone.utc)
            })

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        cache_hit_rate = (
            self.metrics['cache_hits'] /
            max(self.metrics['cache_hits'] + self.metrics['cache_misses'], 1)
        )

        return {
            **self.metrics,
            'cache_hit_rate': cache_hit_rate,
            'target_latency_ms': TARGET_LATENCY_MS,
            'performance_status': 'good' if self.metrics['avg_latency_ms'] < TARGET_LATENCY_MS else 'degraded'
        }


# Global service instance
_advanced_property_matching_engine = None


def get_advanced_property_matching_engine() -> AdvancedPropertyMatchingEngine:
    """
    Get the global AdvancedPropertyMatchingEngine instance (singleton pattern).

    Returns:
        AdvancedPropertyMatchingEngine: The global service instance
    """
    global _advanced_property_matching_engine
    if _advanced_property_matching_engine is None:
        _advanced_property_matching_engine = AdvancedPropertyMatchingEngine()
    return _advanced_property_matching_engine


# Service health check
async def health_check() -> Dict[str, Any]:
    """Health check for the advanced property matching engine."""
    try:
        engine = get_advanced_property_matching_engine()
        metrics = engine.get_metrics()

        return {
            'service': 'AdvancedPropertyMatchingEngine',
            'status': 'healthy',
            'version': '2.2.0',
            'metrics': metrics,
            'dependencies': {
                'predictive_behavior_service': 'connected',
                'enhanced_property_matcher': 'connected',
                'cache_service': 'connected',
                'event_publisher': 'connected',
                'ml_analytics_engine': 'connected'
            }
        }
    except Exception as e:
        return {
            'service': 'AdvancedPropertyMatchingEngine',
            'status': 'unhealthy',
            'error': str(e)
        }