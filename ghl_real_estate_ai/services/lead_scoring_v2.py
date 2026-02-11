"""
Lead Scoring v2 Service

This service provides composite lead scoring that combines FRS, PCS, sentiment,
and engagement metrics into a unified score with confidence intervals.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ghl_real_estate_ai.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class LeadClassification(str, Enum):
    """Lead classification based on composite score."""
    HOT = "hot"
    WARM = "warm"
    LUKEWARM = "lukewarm"
    COLD = "cold"
    UNQUALIFIED = "unqualified"


@dataclass
class CompositeScore:
    """Result of composite lead score calculation."""
    total_score: float  # 0-100
    classification: LeadClassification
    confidence_level: float  # 0-100
    confidence_interval: Tuple[float, float]  # (lower_bound, upper_bound)
    component_scores: Dict[str, float] = field(default_factory=dict)
    scoring_weights: Dict[str, float] = field(default_factory=dict)
    data_completeness: float = 0.0  # 0-100
    conversation_depth: float = 0.0  # 0-100
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ScoreHistory:
    """Historical score trends for a lead."""
    contact_id: str
    scores: List[CompositeScore] = field(default_factory=list)
    trend: str = "stable"  # "improving", "stable", "declining"
    avg_score: float = 0.0
    score_velocity: float = 0.0  # points per day


class LeadScoringServiceV2:
    """
    Enhanced lead scoring with composite scores and confidence intervals.
    
    This service provides:
    - Composite score calculation combining FRS, PCS, sentiment, and engagement
    - Confidence intervals based on data completeness
    - Score classification (hot, warm, lukewarm, cold, unqualified)
    - Historical score tracking and trend analysis
    - Custom weights support for A/B testing
    """
    
    DEFAULT_WEIGHTS = {
        "frs": 0.40,
        "pcs": 0.35,
        "sentiment": 0.15,
        "engagement": 0.10,
    }
    
    CLASSIFICATION_THRESHOLDS = {
        LeadClassification.HOT: 80,
        LeadClassification.WARM: 60,
        LeadClassification.LUKEWARM: 40,
        LeadClassification.COLD: 20,
    }
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        """Initialize the lead scoring service."""
        self.cache_service = cache_service or CacheService()
    
    async def calculate_composite_score(
        self,
        frs_score: float,
        pcs_score: float,
        sentiment_score: float,
        engagement_score: float,
        data_completeness: float,
        conversation_depth: float,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> CompositeScore:
        """
        Calculate composite lead score with confidence interval.
        
        Args:
            frs_score: Financial Readiness Score (0-100)
            pcs_score: Psychological Commitment Score (0-100)
            sentiment_score: Normalized sentiment score (0-100)
            engagement_score: Engagement velocity score (0-100)
            data_completeness: Percentage of required fields populated (0-100)
            conversation_depth: Conversation depth score (0-100)
            custom_weights: Optional custom weights for scoring
        
        Returns:
            CompositeScore with total score, classification, and confidence interval
        """
        try:
            # Use custom weights if provided, otherwise use defaults
            weights = custom_weights or self.DEFAULT_WEIGHTS.copy()
            
            # Validate weights sum to 1.0
            weight_sum = sum(weights.values())
            if abs(weight_sum - 1.0) > 0.01:
                logger.warning(
                    f"Weights sum to {weight_sum}, normalizing to 1.0"
                )
                weights = {k: v / weight_sum for k, v in weights.items()}
            
            # Calculate composite score
            total_score = (
                (frs_score * weights.get("frs", 0.40)) +
                (pcs_score * weights.get("pcs", 0.35)) +
                (sentiment_score * weights.get("sentiment", 0.15)) +
                (engagement_score * weights.get("engagement", 0.10))
            )
            
            # Clamp score to 0-100 range
            total_score = max(0.0, min(100.0, total_score))
            
            # Determine classification
            classification = self._determine_classification(total_score)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(
                data_completeness, conversation_depth
            )
            
            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(
                total_score, confidence_level
            )
            
            # Build component scores dict
            component_scores = {
                "frs": frs_score,
                "pcs": pcs_score,
                "sentiment": sentiment_score,
                "engagement": engagement_score,
            }
            
            logger.info(
                f"Calculated composite score: {total_score:.2f} "
                f"(classification: {classification.value}, "
                f"confidence: {confidence_level:.2f})"
            )
            
            return CompositeScore(
                total_score=total_score,
                classification=classification,
                confidence_level=confidence_level,
                confidence_interval=confidence_interval,
                component_scores=component_scores,
                scoring_weights=weights,
                data_completeness=data_completeness,
                conversation_depth=conversation_depth,
            )
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            raise
    
    async def update_lead_score(
        self,
        contact_id: str,
        conversation_history: List[Dict],
        lead_data: Dict
    ) -> CompositeScore:
        """
        Update lead score with new conversation data.
        
        Args:
            contact_id: Contact ID
            conversation_history: List of conversation messages
            lead_data: Lead data including FRS, PCS, sentiment scores
        
        Returns:
            Updated CompositeScore
        """
        try:
            # Extract component scores from lead data
            frs_score = lead_data.get("frs_score", 0.0)
            pcs_score = lead_data.get("pcs_score", 0.0)
            sentiment_score = lead_data.get("sentiment_score", 50.0)
            
            # Calculate engagement score from conversation patterns
            engagement_score = self._calculate_engagement_score(conversation_history)
            
            # Calculate data completeness
            data_completeness = self._calculate_data_completeness(lead_data)
            
            # Calculate conversation depth
            conversation_depth = min(100.0, len(conversation_history) * 10.0)
            
            # Calculate composite score
            composite_score = await self.calculate_composite_score(
                frs_score=frs_score,
                pcs_score=pcs_score,
                sentiment_score=sentiment_score,
                engagement_score=engagement_score,
                data_completeness=data_completeness,
                conversation_depth=conversation_depth,
            )
            
            # Cache the score
            cache_key = f"composite_score:{contact_id}"
            await self.cache_service.set(
                cache_key,
                composite_score,
                ttl=3600  # 1 hour
            )
            
            return composite_score
            
        except Exception as e:
            logger.error(f"Error updating lead score for {contact_id}: {e}")
            raise
    
    async def get_score_history(
        self,
        contact_id: str,
        days: int = 30
    ) -> ScoreHistory:
        """
        Get historical score trends for a lead.
        
        Args:
            contact_id: Contact ID
            days: Number of days to look back
        
        Returns:
            ScoreHistory with trend analysis
        """
        try:
            # This would typically query the database for historical scores
            # For now, return a placeholder
            return ScoreHistory(
                contact_id=contact_id,
                trend="stable",
                avg_score=0.0,
                score_velocity=0.0,
            )
            
        except Exception as e:
            logger.error(f"Error getting score history for {contact_id}: {e}")
            raise
    
    async def get_top_leads(
        self,
        classification: LeadClassification,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get top leads by classification.
        
        Args:
            classification: Lead classification to filter by
            limit: Maximum number of leads to return
        
        Returns:
            List of lead dictionaries with score information
        """
        try:
            # This would typically query the database
            # For now, return a placeholder
            return []
            
        except Exception as e:
            logger.error(f"Error getting top leads for {classification}: {e}")
            raise
    
    def _calculate_confidence_interval(
        self,
        score: float,
        confidence_level: float
    ) -> Tuple[float, float]:
        """
        Calculate statistical confidence interval.
        
        Args:
            score: Composite score
            confidence_level: Confidence level (0-100)
        
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Calculate interval width based on confidence level
        # Lower confidence = wider interval
        interval_width = (100 - confidence_level) * 0.5
        
        lower_bound = max(0.0, score - interval_width)
        upper_bound = min(100.0, score + interval_width)
        
        return (lower_bound, upper_bound)
    
    def _determine_classification(
        self,
        score: float
    ) -> LeadClassification:
        """
        Determine lead classification from score.
        
        Args:
            score: Composite score (0-100)
        
        Returns:
            LeadClassification
        """
        if score >= self.CLASSIFICATION_THRESHOLDS[LeadClassification.HOT]:
            return LeadClassification.HOT
        elif score >= self.CLASSIFICATION_THRESHOLDS[LeadClassification.WARM]:
            return LeadClassification.WARM
        elif score >= self.CLASSIFICATION_THRESHOLDS[LeadClassification.LUKEWARM]:
            return LeadClassification.LUKEWARM
        elif score >= self.CLASSIFICATION_THRESHOLDS[LeadClassification.COLD]:
            return LeadClassification.COLD
        else:
            return LeadClassification.UNQUALIFIED
    
    def _calculate_confidence_level(
        self,
        data_completeness: float,
        conversation_depth: float
    ) -> float:
        """
        Calculate confidence level based on data completeness and conversation depth.
        
        Args:
            data_completeness: Percentage of required fields populated (0-100)
            conversation_depth: Conversation depth score (0-100)
        
        Returns:
            Confidence level (0-100)
        """
        # Weighted combination of data completeness and conversation depth
        confidence_level = (data_completeness * 0.6) + (conversation_depth * 0.4)
        
        # Clamp to 0-100 range
        return max(0.0, min(100.0, confidence_level))
    
    def _calculate_engagement_score(
        self,
        conversation_history: List[Dict]
    ) -> float:
        """
        Calculate engagement score from conversation patterns.
        
        Args:
            conversation_history: List of conversation messages
        
        Returns:
            Engagement score (0-100)
        """
        if not conversation_history:
            return 0.0
        
        # Calculate based on:
        # - Number of messages
        # - Response time (if available)
        # - Message length
        # - Question asking
        
        message_count = len(conversation_history)
        
        # Base score from message count (max 50 points)
        message_score = min(50.0, message_count * 5.0)
        
        # Additional score from message length (max 30 points)
        total_length = sum(
            len(msg.get("content", "")) 
            for msg in conversation_history
        )
        length_score = min(30.0, total_length / 100.0)
        
        # Additional score from questions (max 20 points)
        question_count = sum(
            1 for msg in conversation_history
            if "?" in msg.get("content", "")
        )
        question_score = min(20.0, question_count * 5.0)
        
        return message_score + length_score + question_score
    
    def _calculate_data_completeness(
        self,
        lead_data: Dict
    ) -> float:
        """
        Calculate data completeness percentage.
        
        Args:
            lead_data: Lead data dictionary
        
        Returns:
            Data completeness percentage (0-100)
        """
        required_fields = [
            "frs_score",
            "pcs_score",
            "sentiment_score",
            "budget",
            "timeline",
            "preferences",
        ]
        
        populated_fields = sum(
            1 for field in required_fields
            if lead_data.get(field) is not None
            and lead_data.get(field) != ""
        )
        
        return (populated_fields / len(required_fields)) * 100.0
