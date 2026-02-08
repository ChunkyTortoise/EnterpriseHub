"""
Enhanced Lead Scoring Service - Phase 1 Foundation Service

Extends the existing intent_decoder.py with advanced lead intelligence capabilities:
- Multi-factor lead scoring beyond FRS/PCS
- Source quality analysis and attribution
- Real-time lead prioritization
- Advanced behavioral pattern recognition
- Integration with ML analytics pipeline

Following established architecture patterns:
- Singleton service pattern with get_enhanced_lead_scoring()
- Event-driven updates via get_event_publisher()
- Cache integration with get_cache_service()
- Multi-tenant isolation via location_id scoping
"""

import asyncio
import logging
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ml.closing_probability_model import get_ml_analytics_engine
from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile
from ghl_real_estate_ai.services.cache_service import TenantScopedCache, get_cache_service
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)


class LeadSourceType(Enum):
    """Lead source classification for quality scoring."""

    ORGANIC_SEARCH = "organic_search"
    PAID_SEARCH = "paid_search"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    DIRECT_WEBSITE = "direct_website"
    COLD_OUTREACH = "cold_outreach"
    RETARGETING = "retargeting"
    EMAIL_CAMPAIGN = "email_campaign"
    WEBINAR = "webinar"
    UNKNOWN = "unknown"


@dataclass
class SourceQualityScore:
    """Source quality analysis results."""

    source_type: LeadSourceType
    quality_score: float  # 0-100
    conversion_likelihood: float  # 0-1
    historical_performance: Optional[Dict[str, float]] = None
    attribution_confidence: float = 1.0
    quality_factors: List[str] = None

    def __post_init__(self):
        if self.quality_factors is None:
            self.quality_factors = []


@dataclass
class BehavioralSignals:
    """Advanced behavioral pattern analysis."""

    engagement_score: float  # 0-100
    response_velocity_ms: Optional[float] = None
    message_complexity_score: float = 0.0
    question_depth_score: float = 0.0
    objection_patterns: List[str] = None
    urgency_indicators: List[str] = None
    decision_authority_signals: List[str] = None

    def __post_init__(self):
        if self.objection_patterns is None:
            self.objection_patterns = []
        if self.urgency_indicators is None:
            self.urgency_indicators = []
        if self.decision_authority_signals is None:
            self.decision_authority_signals = []


@dataclass
class EnhancedLeadScore:
    """Comprehensive lead scoring beyond FRS/PCS."""

    lead_id: str
    location_id: str

    # Enhanced Scores (0-100 each)
    overall_score: float
    source_quality_score: float
    behavioral_engagement_score: float
    intent_clarity_score: float
    conversion_readiness_score: float

    # Source Analysis
    source_analysis: SourceQualityScore
    behavioral_analysis: BehavioralSignals

    # Integration with existing system
    base_frs_score: Optional[float] = None
    base_pcs_score: Optional[float] = None
    base_intent_profile: Optional[LeadIntentProfile] = None

    # ML Integration
    closing_probability: Optional[float] = None
    ml_confidence: Optional[float] = None
    risk_factors: List[str] = None
    positive_signals: List[str] = None

    # Metadata
    scoring_timestamp: datetime = None
    processing_time_ms: float = 0.0
    confidence_level: float = 0.0
    next_action_recommendations: List[str] = None

    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        if self.positive_signals is None:
            self.positive_signals = []
        if self.next_action_recommendations is None:
            self.next_action_recommendations = []
        if self.scoring_timestamp is None:
            self.scoring_timestamp = datetime.now(timezone.utc)


class EnhancedLeadScoringService:
    """
    Enhanced Lead Scoring Service with advanced intelligence capabilities.

    Extends the basic FRS/PCS scoring with:
    - Multi-source attribution analysis
    - Advanced behavioral pattern recognition
    - ML-powered conversion prediction
    - Real-time lead prioritization
    - Intelligent caching and performance optimization
    """

    def __init__(self):
        """Initialize the enhanced lead scoring service."""
        self.cache = get_cache_service()
        self.event_publisher = get_event_publisher()
        self.intent_decoder = LeadIntentDecoder()

        # Source quality scoring weights
        self.source_quality_weights = {
            LeadSourceType.REFERRAL: 95,
            LeadSourceType.ORGANIC_SEARCH: 85,
            LeadSourceType.WEBINAR: 80,
            LeadSourceType.DIRECT_WEBSITE: 75,
            LeadSourceType.PAID_SEARCH: 70,
            LeadSourceType.RETARGETING: 65,
            LeadSourceType.SOCIAL_MEDIA: 60,
            LeadSourceType.EMAIL_CAMPAIGN: 55,
            LeadSourceType.COLD_OUTREACH: 45,
            LeadSourceType.UNKNOWN: 35,
        }

        # Behavioral pattern recognition
        self.urgency_indicators = [
            "asap",
            "urgent",
            "immediately",
            "right away",
            "need to move fast",
            "time sensitive",
            "deadline",
            "closing soon",
            "opportunity closing",
        ]

        self.authority_indicators = [
            "decision maker",
            "i decide",
            "my choice",
            "i'm in charge",
            "my business",
            "i own",
            "final say",
            "up to me",
        ]

        self.engagement_indicators = [
            "tell me more",
            "how does",
            "what about",
            "can you explain",
            "interested in",
            "sounds good",
            "like the idea",
        ]

    async def analyze_lead_comprehensive(
        self,
        contact_id: str,
        location_id: str,
        conversation_history: List[Dict[str, Any]],
        source_info: Optional[Dict[str, Any]] = None,
        attribution_data: Optional[Dict[str, Any]] = None,
    ) -> EnhancedLeadScore:
        """
        Comprehensive lead analysis with enhanced scoring.

        Args:
            contact_id: Unique contact identifier
            location_id: Tenant/location identifier for isolation
            conversation_history: Full conversation history
            source_info: Lead source information (UTM, referrer, etc.)
            attribution_data: Multi-touch attribution data

        Returns:
            EnhancedLeadScore with comprehensive analysis
        """
        start_time = time.perf_counter()

        # Create tenant-scoped cache for isolation
        tenant_cache = TenantScopedCache(location_id, self.cache)

        # Check cache first
        cache_key = f"enhanced_score:{contact_id}"
        cached_score = await tenant_cache.get(cache_key)
        if cached_score:
            logger.debug(f"Enhanced lead score cache hit for {contact_id}")
            return cached_score

        try:
            # 1. Base Intent Analysis (existing system)
            base_intent_profile = self.intent_decoder.analyze_lead(contact_id, conversation_history)

            # 2. Enhanced Source Quality Analysis
            source_analysis = await self._analyze_source_quality(source_info or {}, attribution_data or {}, location_id)

            # 3. Advanced Behavioral Analysis
            behavioral_analysis = self._analyze_behavioral_patterns(conversation_history)

            # 4. ML-Powered Conversion Prediction
            ml_prediction = await self._get_ml_conversion_prediction(
                contact_id, conversation_history, base_intent_profile, location_id
            )

            # 5. Calculate Enhanced Composite Score
            enhanced_score = self._calculate_composite_score(
                base_intent_profile, source_analysis, behavioral_analysis, ml_prediction
            )

            # 6. Generate Action Recommendations
            recommendations = self._generate_action_recommendations(enhanced_score)

            processing_time = (time.perf_counter() - start_time) * 1000

            # 7. Create Enhanced Lead Score
            result = EnhancedLeadScore(
                lead_id=contact_id,
                location_id=location_id,
                overall_score=enhanced_score,
                source_quality_score=source_analysis.quality_score,
                behavioral_engagement_score=behavioral_analysis.engagement_score,
                intent_clarity_score=base_intent_profile.frs.total_score if base_intent_profile else 0,
                conversion_readiness_score=ml_prediction.get("closing_probability", 0) * 100,
                source_analysis=source_analysis,
                behavioral_analysis=behavioral_analysis,
                base_frs_score=base_intent_profile.frs.total_score if base_intent_profile else None,
                base_pcs_score=base_intent_profile.pcs.total_score if base_intent_profile else None,
                base_intent_profile=base_intent_profile,
                closing_probability=ml_prediction.get("closing_probability"),
                ml_confidence=ml_prediction.get("confidence"),
                risk_factors=ml_prediction.get("risk_factors", []),
                positive_signals=ml_prediction.get("positive_signals", []),
                processing_time_ms=processing_time,
                confidence_level=self._calculate_confidence_level(source_analysis, behavioral_analysis, ml_prediction),
                next_action_recommendations=recommendations,
            )

            # 8. Cache result (5 minute TTL for real-time updates)
            await tenant_cache.set(cache_key, result, ttl=300)

            # 9. Publish real-time event
            await self._publish_enhanced_scoring_event(result)

            logger.info(
                f"Enhanced lead scoring complete: {contact_id} -> {enhanced_score:.1f} "
                f"(source: {source_analysis.quality_score:.1f}, behavioral: {behavioral_analysis.engagement_score:.1f}, "
                f"ML: {result.conversion_readiness_score:.1f}) [{processing_time:.2f}ms]"
            )

            return result

        except Exception as e:
            logger.error(f"Enhanced lead scoring failed for {contact_id}: {e}")
            # Return fallback score based on base intent only
            fallback_score = self._create_fallback_score(contact_id, location_id, conversation_history)
            await tenant_cache.set(cache_key, fallback_score, ttl=60)  # Short TTL for retry
            return fallback_score

    async def _analyze_source_quality(
        self, source_info: Dict[str, Any], attribution_data: Dict[str, Any], location_id: str
    ) -> SourceQualityScore:
        """Analyze lead source quality and attribution."""

        # Determine source type from UTM/referrer data
        source_type = self._classify_source_type(source_info)

        # Get base quality score
        base_quality = self.source_quality_weights.get(source_type, 50)

        # Analyze historical performance for this source
        tenant_cache = TenantScopedCache(location_id, self.cache)
        historical_key = f"source_performance:{source_type.value}"
        historical_perf = await tenant_cache.get(historical_key) or {}

        # Apply historical performance adjustments
        if historical_perf:
            conversion_rate = historical_perf.get("conversion_rate", 0.5)
            avg_deal_value = historical_perf.get("avg_deal_value", 0)

            # Boost score for high-performing sources
            if conversion_rate > 0.15:  # Above 15% conversion
                base_quality += 10
            elif conversion_rate < 0.05:  # Below 5% conversion
                base_quality -= 15

        # Attribution confidence based on tracking quality
        attribution_confidence = self._calculate_attribution_confidence(source_info, attribution_data)

        quality_factors = self._identify_quality_factors(source_type, source_info, historical_perf)

        return SourceQualityScore(
            source_type=source_type,
            quality_score=max(0, min(100, base_quality)),
            conversion_likelihood=historical_perf.get("conversion_rate", 0.1),
            historical_performance=historical_perf,
            attribution_confidence=attribution_confidence,
            quality_factors=quality_factors,
        )

    def _analyze_behavioral_patterns(self, conversation_history: List[Dict[str, Any]]) -> BehavioralSignals:
        """Advanced behavioral pattern analysis."""

        if not conversation_history:
            return BehavioralSignals(engagement_score=0)

        all_text = " ".join([msg.get("content", "").lower() for msg in conversation_history])

        # Calculate engagement indicators
        engagement_signals = 0
        for indicator in self.engagement_indicators:
            if indicator in all_text:
                engagement_signals += 1

        # Message complexity analysis
        avg_word_count = sum(len(msg.get("content", "").split()) for msg in conversation_history) / len(
            conversation_history
        )
        complexity_score = min(100, avg_word_count * 3)  # 3 points per word, max 100

        # Question depth analysis
        question_count = sum(1 for msg in conversation_history if "?" in msg.get("content", ""))
        question_score = min(100, question_count * 15)  # 15 points per question

        # Urgency pattern detection
        urgency_signals = [indicator for indicator in self.urgency_indicators if indicator in all_text]

        # Authority pattern detection
        authority_signals = [indicator for indicator in self.authority_indicators if indicator in all_text]

        # Objection pattern detection
        objection_patterns = self._detect_objection_patterns(all_text)

        # Calculate overall engagement score
        engagement_score = min(
            100,
            (
                engagement_signals * 10  # 10 points per engagement signal
                + min(20, len(urgency_signals) * 5)  # 5 points per urgency signal, max 20
                + min(15, len(authority_signals) * 5)  # 5 points per authority signal, max 15
                + min(10, complexity_score * 0.1)  # Complexity contribution
            ),
        )

        return BehavioralSignals(
            engagement_score=engagement_score,
            message_complexity_score=complexity_score,
            question_depth_score=question_score,
            objection_patterns=objection_patterns,
            urgency_indicators=urgency_signals,
            decision_authority_signals=authority_signals,
        )

    async def _get_ml_conversion_prediction(
        self,
        contact_id: str,
        conversation_history: List[Dict[str, Any]],
        base_intent_profile: Optional[LeadIntentProfile],
        location_id: str,
    ) -> Dict[str, Any]:
        """Get ML-powered conversion prediction."""

        try:
            # Try to get ML analytics engine (may not be available in all environments)
            ml_engine = await get_ml_analytics_engine()

            # Prepare features for ML model
            features = self._prepare_ml_features(contact_id, conversation_history, base_intent_profile)

            # Get prediction
            prediction = await ml_engine.predict(features)

            return {
                "closing_probability": prediction.closing_probability,
                "confidence": prediction.model_confidence,
                "risk_factors": prediction.risk_factors,
                "positive_signals": prediction.positive_signals,
            }

        except Exception as e:
            logger.debug(f"ML prediction unavailable for {contact_id}: {e}")
            # Fallback to heuristic-based prediction
            return self._heuristic_conversion_prediction(conversation_history, base_intent_profile)

    def _calculate_composite_score(
        self,
        base_intent_profile: Optional[LeadIntentProfile],
        source_analysis: SourceQualityScore,
        behavioral_analysis: BehavioralSignals,
        ml_prediction: Dict[str, Any],
    ) -> float:
        """Calculate composite enhanced lead score."""

        # Weight distribution for composite score
        weights = {
            "source_quality": 0.25,
            "behavioral": 0.25,
            "intent_frs": 0.20,
            "intent_pcs": 0.15,
            "ml_prediction": 0.15,
        }

        # Component scores
        source_score = source_analysis.quality_score
        behavioral_score = behavioral_analysis.engagement_score
        frs_score = base_intent_profile.frs.total_score if base_intent_profile else 50
        pcs_score = base_intent_profile.pcs.total_score if base_intent_profile else 50
        ml_score = ml_prediction.get("closing_probability", 0.5) * 100

        # Calculate weighted average
        composite_score = (
            source_score * weights["source_quality"]
            + behavioral_score * weights["behavioral"]
            + frs_score * weights["intent_frs"]
            + pcs_score * weights["intent_pcs"]
            + ml_score * weights["ml_prediction"]
        )

        return round(composite_score, 2)

    def _generate_action_recommendations(self, enhanced_score: float) -> List[str]:
        """Generate intelligent action recommendations based on score."""

        recommendations = []

        if enhanced_score >= 85:
            recommendations.extend(
                [
                    "🔥 URGENT: Call immediately - Hot lead alert",
                    "📞 Schedule property tour within 24 hours",
                    "📧 Send high-priority listing matches",
                    "🎯 Assign to top-performing agent",
                ]
            )
        elif enhanced_score >= 70:
            recommendations.extend(
                [
                    "📞 Schedule follow-up call within 2-3 hours",
                    "📲 Send personalized SMS with market insights",
                    "📈 Share relevant market reports",
                    "⏰ Add to high-priority follow-up queue",
                ]
            )
        elif enhanced_score >= 50:
            recommendations.extend(
                [
                    "📧 Send automated nurture sequence",
                    "📊 Provide property valuation tool",
                    "📅 Schedule callback in 2-3 days",
                    "📖 Share educational content",
                ]
            )
        else:
            recommendations.extend(
                [
                    "🔄 Add to long-term nurture campaign",
                    "📚 Send educational newsletter",
                    "⏳ Requalify in 30 days",
                    "🎯 Consider lead scoring optimization",
                ]
            )

        return recommendations

    async def _publish_enhanced_scoring_event(self, enhanced_score: EnhancedLeadScore):
        """Publish real-time enhanced scoring event."""

        try:
            await self.event_publisher.publish_intent_analysis_complete(
                contact_id=enhanced_score.lead_id,
                processing_time_ms=enhanced_score.processing_time_ms,
                confidence_score=enhanced_score.confidence_level,
                intent_category=self._get_score_category(enhanced_score.overall_score),
                frs_score=enhanced_score.base_frs_score,
                pcs_score=enhanced_score.base_pcs_score,
                recommendations=enhanced_score.next_action_recommendations,
                location_id=enhanced_score.location_id,
            )

        except Exception as e:
            logger.warning(f"Failed to publish enhanced scoring event: {e}")

    # Helper methods for classification and analysis

    def _classify_source_type(self, source_info: Dict[str, Any]) -> LeadSourceType:
        """Classify lead source from UTM/referrer data."""

        utm_source = source_info.get("utm_source", "").lower()
        utm_medium = source_info.get("utm_medium", "").lower()
        referrer = source_info.get("referrer", "").lower()

        if "referral" in utm_medium or "referral" in utm_source:
            return LeadSourceType.REFERRAL
        elif utm_medium == "organic":
            return LeadSourceType.ORGANIC_SEARCH
        elif utm_medium in ["cpc", "ppc", "paid"]:
            return LeadSourceType.PAID_SEARCH
        elif "facebook" in referrer or "linkedin" in referrer or "social" in utm_source:
            return LeadSourceType.SOCIAL_MEDIA
        elif "webinar" in utm_source or "webinar" in utm_medium:
            return LeadSourceType.WEBINAR
        elif "email" in utm_medium:
            return LeadSourceType.EMAIL_CAMPAIGN
        elif not referrer or referrer == "(direct)":
            return LeadSourceType.DIRECT_WEBSITE
        else:
            return LeadSourceType.UNKNOWN

    def _calculate_attribution_confidence(self, source_info: Dict[str, Any], attribution_data: Dict[str, Any]) -> float:
        """Calculate confidence level in attribution data."""

        confidence = 1.0

        # Reduce confidence for missing tracking
        if not source_info.get("utm_source"):
            confidence -= 0.2
        if not source_info.get("utm_medium"):
            confidence -= 0.1

        # Boost confidence for multi-touch attribution
        if attribution_data and len(attribution_data.get("touchpoints", [])) > 1:
            confidence += 0.1

        return max(0.1, min(1.0, confidence))

    def _identify_quality_factors(
        self, source_type: LeadSourceType, source_info: Dict[str, Any], historical_perf: Dict[str, Any]
    ) -> List[str]:
        """Identify factors contributing to source quality score."""

        factors = []

        if source_type == LeadSourceType.REFERRAL:
            factors.append("High-intent referral source")
        elif source_type == LeadSourceType.ORGANIC_SEARCH:
            factors.append("Active search behavior indicates intent")

        if source_info.get("utm_campaign"):
            factors.append("Trackable campaign source")

        if historical_perf:
            conv_rate = historical_perf.get("conversion_rate", 0)
            if conv_rate > 0.15:
                factors.append("High historical conversion rate")
            elif conv_rate < 0.05:
                factors.append("Below-average conversion rate")

        return factors

    def _detect_objection_patterns(self, text: str) -> List[str]:
        """Detect common objection patterns in conversation."""

        objection_indicators = [
            "too expensive",
            "can't afford",
            "need to think",
            "not ready",
            "talk to spouse",
            "timing isn't right",
            "economic uncertainty",
            "market might crash",
            "rates too high",
        ]

        return [obj for obj in objection_indicators if obj in text]

    def _prepare_ml_features(
        self,
        contact_id: str,
        conversation_history: List[Dict[str, Any]],
        base_intent_profile: Optional[LeadIntentProfile],
    ) -> Dict[str, Any]:
        """Prepare features for ML model prediction."""

        return {
            "conversation_length": len(conversation_history),
            "avg_message_length": sum(len(msg.get("content", "").split()) for msg in conversation_history)
            / max(1, len(conversation_history)),
            "question_count": sum(1 for msg in conversation_history if "?" in msg.get("content", "")),
            "frs_score": base_intent_profile.frs.total_score if base_intent_profile else 50,
            "pcs_score": base_intent_profile.pcs.total_score if base_intent_profile else 50,
            "urgency_mentions": len(
                [
                    msg
                    for msg in conversation_history
                    if any(urgent in msg.get("content", "").lower() for urgent in self.urgency_indicators)
                ]
            ),
            "authority_mentions": len(
                [
                    msg
                    for msg in conversation_history
                    if any(auth in msg.get("content", "").lower() for auth in self.authority_indicators)
                ]
            ),
        }

    def _heuristic_conversion_prediction(
        self, conversation_history: List[Dict[str, Any]], base_intent_profile: Optional[LeadIntentProfile]
    ) -> Dict[str, Any]:
        """Fallback heuristic-based prediction when ML is unavailable."""

        # Simple heuristic based on intent scores and conversation patterns
        frs = base_intent_profile.frs.total_score if base_intent_profile else 50
        pcs = base_intent_profile.pcs.total_score if base_intent_profile else 50

        avg_score = (frs + pcs) / 2
        closing_probability = max(0.05, min(0.95, avg_score / 100))

        risk_factors = []
        positive_signals = []

        if frs < 30:
            risk_factors.append("Low financial readiness score")
        if pcs < 30:
            risk_factors.append("Low psychological commitment")

        if frs > 75:
            positive_signals.append("High financial readiness")
        if pcs > 75:
            positive_signals.append("Strong psychological commitment")

        return {
            "closing_probability": closing_probability,
            "confidence": 0.7,  # Lower confidence for heuristic
            "risk_factors": risk_factors,
            "positive_signals": positive_signals,
        }

    def _calculate_confidence_level(
        self, source_analysis: SourceQualityScore, behavioral_analysis: BehavioralSignals, ml_prediction: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence level in the enhanced scoring."""

        # Base confidence factors
        source_confidence = source_analysis.attribution_confidence
        behavioral_confidence = 1.0 if behavioral_analysis.engagement_score > 0 else 0.5
        ml_confidence = ml_prediction.get("confidence", 0.7)

        # Weighted average
        overall_confidence = source_confidence * 0.3 + behavioral_confidence * 0.3 + ml_confidence * 0.4

        return round(overall_confidence, 3)

    def _get_score_category(self, score: float) -> str:
        """Get categorical classification for score."""

        if score >= 85:
            return "Hot"
        elif score >= 70:
            return "Warm"
        elif score >= 50:
            return "Lukewarm"
        else:
            return "Cold"

    def _create_fallback_score(
        self, contact_id: str, location_id: str, conversation_history: List[Dict[str, Any]]
    ) -> EnhancedLeadScore:
        """Create fallback score when full analysis fails."""

        # Basic analysis with reduced functionality
        basic_engagement = len(conversation_history) * 10  # 10 points per message
        basic_score = min(100, basic_engagement)

        return EnhancedLeadScore(
            lead_id=contact_id,
            location_id=location_id,
            overall_score=basic_score,
            source_quality_score=50,  # Unknown source
            behavioral_engagement_score=basic_engagement,
            intent_clarity_score=50,  # Default
            conversion_readiness_score=basic_score,
            source_analysis=SourceQualityScore(LeadSourceType.UNKNOWN, 50, 0.1),
            behavioral_analysis=BehavioralSignals(basic_engagement),
            confidence_level=0.3,  # Low confidence for fallback
            next_action_recommendations=["Manual review required"],
        )

    async def get_lead_score_history(
        self, contact_id: str, location_id: str, days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get historical lead scoring data for trend analysis."""

        tenant_cache = TenantScopedCache(location_id, self.cache)

        # In a full implementation, this would query a time-series database
        # For now, return recent cached scores
        cache_keys = [f"enhanced_score:{contact_id}:day_{i}" for i in range(days_back)]
        historical_data = await tenant_cache.get_many(cache_keys)

        return [
            {
                "date": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(),
                "score": score.overall_score if score else None,
                "source_quality": score.source_quality_score if score else None,
                "behavioral": score.behavioral_engagement_score if score else None,
            }
            for i, score in enumerate(historical_data.values())
            if score
        ]

    async def bulk_score_leads(
        self, contact_ids: List[str], location_id: str, batch_size: int = 10
    ) -> Dict[str, EnhancedLeadScore]:
        """Bulk lead scoring for performance optimization."""

        results = {}

        # Process in batches to avoid overwhelming the system
        for i in range(0, len(contact_ids), batch_size):
            batch = contact_ids[i : i + batch_size]

            batch_tasks = []
            for contact_id in batch:
                # In a full implementation, would fetch conversation history for each
                task = self.analyze_lead_comprehensive(
                    contact_id=contact_id,
                    location_id=location_id,
                    conversation_history=[],  # Placeholder - would fetch real data
                    source_info=None,
                    attribution_data=None,
                )
                batch_tasks.append(task)

            # Execute batch concurrently
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Collect successful results
            for contact_id, result in zip(batch, batch_results):
                if not isinstance(result, Exception):
                    results[contact_id] = result
                else:
                    logger.warning(f"Bulk scoring failed for {contact_id}: {result}")

        return results


# Singleton accessor following established pattern
_enhanced_lead_scoring_service = None


def get_enhanced_lead_scoring() -> EnhancedLeadScoringService:
    """Get singleton enhanced lead scoring service instance."""
    global _enhanced_lead_scoring_service
    if _enhanced_lead_scoring_service is None:
        _enhanced_lead_scoring_service = EnhancedLeadScoringService()
    return _enhanced_lead_scoring_service


# Convenience functions for common operations
async def analyze_lead(
    contact_id: str, location_id: str, conversation_history: List[Dict[str, Any]], **kwargs
) -> EnhancedLeadScore:
    """Convenience function for comprehensive lead analysis."""
    service = get_enhanced_lead_scoring()
    return await service.analyze_lead_comprehensive(contact_id, location_id, conversation_history, **kwargs)


async def get_bulk_lead_scores(
    contact_ids: List[str], location_id: str, batch_size: int = 10
) -> Dict[str, EnhancedLeadScore]:
    """Convenience function for bulk lead scoring."""
    service = get_enhanced_lead_scoring()
    return await service.bulk_score_leads(contact_ids, location_id, batch_size)
