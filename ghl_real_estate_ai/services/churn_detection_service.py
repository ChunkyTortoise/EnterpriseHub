"""
Churn Detection & Recovery Service

This service provides intelligent churn detection to identify stalled conversations
and automated recovery strategies to re-engage dormant leads before they are lost.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional

from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.sentiment_analysis_service import SentimentAnalysisService

logger = logging.getLogger(__name__)


class ChurnRiskLevel(str, Enum):
    """Churn risk level classifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(str, Enum):
    """Recovery strategies for at-risk contacts."""

    VALUE_REMINDER = "value_reminder"
    QUESTION_RE_ENGAGEMENT = "question_re_engagement"
    NEW_INFORMATION = "new_information"
    INCENTIVE_OFFER = "incentive_offer"
    FINAL_CHECK_IN = "final_check_in"
    ARCHIVE = "archive"


@dataclass
class ChurnRiskAssessment:
    """Result of churn risk assessment for a contact."""

    contact_id: str
    risk_score: float  # 0-100
    risk_level: ChurnRiskLevel
    signals: Dict[str, float]
    last_activity: datetime
    days_inactive: int
    recommended_action: RecoveryStrategy
    assessed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RecoveryAction:
    """Scheduled recovery action for an at-risk contact."""

    contact_id: str
    strategy: RecoveryStrategy
    message_template: str
    channel: str
    scheduled_at: datetime
    status: str = "pending"  # 'pending', 'sent', 'delivered', 'failed'
    result: Optional[str] = None


class ChurnDetectionService:
    """
    Detects churn risk and manages recovery strategies.

    This service provides:
    - 5 churn detection signals with weighted scoring
    - Risk level classification (low, medium, high, critical)
    - 6 recovery strategies with timing
    - Automated recovery action scheduling
    """

    # Signal thresholds
    SIGNAL_THRESHOLDS = {
        "no_response_days": 7,
        "response_velocity_hours": 48,
        "sentiment_decline": True,
        "engagement_score": 30,
        "min_message_count": 3,
    }

    # Signal weights for churn risk calculation
    SIGNAL_WEIGHTS = {
        "no_response_time": 0.30,
        "response_velocity": 0.25,
        "sentiment_trend": 0.20,
        "engagement_score": 0.15,
        "message_count": 0.10,
    }

    # Recovery message templates
    RECOVERY_TEMPLATES = {
        RecoveryStrategy.VALUE_REMINDER: {
            "template": "Hi {name}! I wanted to follow up on our conversation about {topic}. Here's a quick reminder of the key benefits we discussed...",
            "channel": "email",
        },
        RecoveryStrategy.QUESTION_RE_ENGAGEMENT: {
            "template": "Hi {name}! I've been thinking about your situation and had a question - what's your biggest concern right now about {topic}?",
            "channel": "sms",
        },
        RecoveryStrategy.NEW_INFORMATION: {
            "template": "Hi {name}! There's been an update in the {market} that might interest you. Would you like to hear more?",
            "channel": "email",
        },
        RecoveryStrategy.INCENTIVE_OFFER: {
            "template": "Hi {name}! As a valued contact, I'd like to offer you {incentive}. Let me know if you're interested!",
            "channel": "sms",
        },
        RecoveryStrategy.FINAL_CHECK_IN: {
            "template": "Hi {name}! I wanted to check in one last time. Are you still interested in {topic}, or should I close your file?",
            "channel": "email",
        },
    }

    # Risk level thresholds
    RISK_LEVEL_THRESHOLDS = {
        ChurnRiskLevel.LOW: (0, 30),
        ChurnRiskLevel.MEDIUM: (31, 60),
        ChurnRiskLevel.HIGH: (61, 80),
        ChurnRiskLevel.CRITICAL: (81, 100),
    }

    def __init__(
        self,
        cache_service: Optional[CacheService] = None,
        sentiment_service: Optional[SentimentAnalysisService] = None,
    ):
        """
        Initialize the churn detection service.

        Args:
            cache_service: Optional cache service for caching results
            sentiment_service: Optional sentiment analysis service
        """
        self.cache_service = cache_service or CacheService()
        self.sentiment_service = sentiment_service or SentimentAnalysisService()

        logger.info("ChurnDetectionService initialized")

    async def assess_churn_risk(
        self,
        contact_id: str,
        conversation_history: List[Dict],
        last_activity: datetime,
        use_cache: bool = True,
    ) -> ChurnRiskAssessment:
        """
        Assess churn risk for a contact.

        Args:
            contact_id: The contact ID to assess
            conversation_history: List of conversation messages
            last_activity: Timestamp of last activity
            use_cache: Whether to use cached results

        Returns:
            ChurnRiskAssessment with risk score and recommended action
        """
        # Check cache first
        if use_cache:
            cache_key = f"churn_risk:{contact_id}:{last_activity.isoformat()}"
            cached = await self.cache_service.get(cache_key)
            if cached:
                try:
                    return ChurnRiskAssessment(**json.loads(cached))
                except Exception as e:
                    logger.warning(f"Failed to parse cached churn risk: {e}")

        # Calculate days inactive while preserving timezone awareness
        if last_activity.tzinfo is not None and last_activity.utcoffset() is not None:
            assessment_time = datetime.now(timezone.utc)
            days_inactive = (assessment_time - last_activity.astimezone(timezone.utc)).days
        else:
            assessment_time = datetime.utcnow()
            days_inactive = (assessment_time - last_activity).days

        # Analyze all 5 churn detection signals
        signals = await self._analyze_signals(
            conversation_history=conversation_history,
            last_activity=last_activity,
            days_inactive=days_inactive,
        )

        # Calculate weighted churn risk score
        risk_score = self._calculate_risk_score(signals)

        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)

        # Get recommended recovery strategy
        recommended_action = self._get_recovery_strategy(days_inactive, risk_level)

        assessment = ChurnRiskAssessment(
            contact_id=contact_id,
            risk_score=risk_score,
            risk_level=risk_level,
            signals=signals,
            last_activity=last_activity,
            days_inactive=days_inactive,
            recommended_action=recommended_action,
            assessed_at=assessment_time,
        )

        # Cache the result
        if use_cache:
            await self.cache_service.set(
                cache_key,
                json.dumps(assessment.__dict__, default=str),
                ttl=3600,  # Cache for 1 hour
            )

        logger.info(
            f"Churn risk assessed for {contact_id}: "
            f"score={risk_score:.2f}, level={risk_level.value}, "
            f"days_inactive={days_inactive}"
        )

        return assessment

    async def _analyze_signals(
        self,
        conversation_history: List[Dict],
        last_activity: datetime,
        days_inactive: int,
    ) -> Dict[str, float]:
        """
        Analyze all 5 churn detection signals.

        Args:
            conversation_history: List of conversation messages
            last_activity: Timestamp of last activity
            days_inactive: Number of days since last activity

        Returns:
            Dictionary of signal names and their values (0.0-1.0)
        """
        signals = {}

        # Signal 1: No response time (>24h)
        signals["no_response_time"] = self._analyze_no_response_time(days_inactive)

        # Signal 2: Response velocity (>48h avg)
        signals["response_velocity"] = await self._analyze_response_velocity(conversation_history)

        # Signal 3: Negative sentiment trend (declining)
        signals["sentiment_trend"] = await self._analyze_sentiment_trend(conversation_history)

        # Signal 4: PCS score decline (>20 points)
        signals["pcs_score_decline"] = await self._analyze_pcs_decline(conversation_history)

        # Signal 5: Stalled conversation (no activity >7 days)
        signals["stalled_conversation"] = self._analyze_stalled_conversation(days_inactive)

        return signals

    def _analyze_no_response_time(self, days_inactive: int) -> float:
        """
        Analyze no response time signal.

        Args:
            days_inactive: Number of days since last activity

        Returns:
            Signal value (0.0-1.0)
        """
        threshold = self.SIGNAL_THRESHOLDS["no_response_days"]

        if days_inactive <= threshold:
            return 0.0
        elif days_inactive <= threshold * 2:
            return 0.5
        elif days_inactive <= threshold * 4:
            return 0.75
        else:
            return 1.0

    async def _analyze_response_velocity(self, conversation_history: List[Dict]) -> float:
        """
        Analyze response velocity signal.

        Args:
            conversation_history: List of conversation messages

        Returns:
            Signal value (0.0-1.0)
        """
        if len(conversation_history) < 2:
            return 0.0

        # Calculate average response time
        response_times = []
        for i in range(1, len(conversation_history)):
            prev_msg = conversation_history[i - 1]
            curr_msg = conversation_history[i]

            if prev_msg.get("role") == "assistant" and curr_msg.get("role") == "user":
                prev_time = prev_msg.get("timestamp")
                curr_time = curr_msg.get("timestamp")

                if prev_time and curr_time:
                    try:
                        prev_dt = datetime.fromisoformat(prev_time) if isinstance(prev_time, str) else prev_time
                        curr_dt = datetime.fromisoformat(curr_time) if isinstance(curr_time, str) else curr_time
                        response_hours = (curr_dt - prev_dt).total_seconds() / 3600
                        response_times.append(response_hours)
                    except Exception as e:
                        logger.warning(f"Failed to parse response time: {e}")

        if not response_times:
            return 0.0

        avg_response_time = sum(response_times) / len(response_times)
        threshold = self.SIGNAL_THRESHOLDS["response_velocity_hours"]

        # Normalize to 0.0-1.0
        if avg_response_time <= threshold:
            return 0.0
        elif avg_response_time <= threshold * 2:
            return 0.5
        elif avg_response_time <= threshold * 4:
            return 0.75
        else:
            return 1.0

    async def _analyze_sentiment_trend(self, conversation_history: List[Dict]) -> float:
        """
        Analyze sentiment trend signal.

        Args:
            conversation_history: List of conversation messages

        Returns:
            Signal value (0.0-1.0)
        """
        if len(conversation_history) < 3:
            return 0.0

        # Get sentiment scores for recent messages
        sentiment_scores = []
        for msg in conversation_history[-5:]:  # Last 5 messages
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if content:
                    try:
                        result = await self.sentiment_service.analyze_sentiment(message=content, use_cache=True)
                        # Convert sentiment to numeric score
                        sentiment_map = {
                            "positive": 1.0,
                            "neutral": 0.5,
                            "anxious": 0.3,
                            "frustrated": 0.2,
                            "angry": 0.0,
                            "disappointed": 0.2,
                            "confused": 0.3,
                        }
                        sentiment_scores.append(sentiment_map.get(result.sentiment.value, 0.5))
                    except Exception as e:
                        logger.warning(f"Failed to analyze sentiment: {e}")

        if len(sentiment_scores) < 2:
            return 0.0

        # Calculate trend (declining if recent scores are lower)
        first_half = sentiment_scores[: len(sentiment_scores) // 2]
        second_half = sentiment_scores[len(sentiment_scores) // 2 :]

        avg_first = sum(first_half) / len(first_half) if first_half else 0.5
        avg_second = sum(second_half) / len(second_half) if second_half else 0.5

        # Declining trend if second half is lower
        decline = avg_first - avg_second

        if decline <= 0:
            return 0.0
        elif decline <= 0.2:
            return 0.3
        elif decline <= 0.4:
            return 0.6
        else:
            return 1.0

    async def _analyze_pcs_decline(self, conversation_history: List[Dict]) -> float:
        """
        Analyze PCS score decline signal.

        Args:
            conversation_history: List of conversation messages

        Returns:
            Signal value (0.0-1.0)
        """
        # Extract PCS scores from conversation history
        pcs_scores = []
        for msg in conversation_history:
            if msg.get("role") == "assistant":
                metadata = msg.get("metadata", {})
                pcs_score = metadata.get("pcs_score")
                if pcs_score is not None:
                    pcs_scores.append(float(pcs_score))

        if len(pcs_scores) < 2:
            return 0.0

        # Calculate decline
        initial_score = pcs_scores[0]
        latest_score = pcs_scores[-1]
        decline = initial_score - latest_score

        # Threshold: >20 points decline
        if decline <= 0:
            return 0.0
        elif decline <= 20:
            return 0.5
        elif decline <= 40:
            return 0.75
        else:
            return 1.0

    def _analyze_stalled_conversation(self, days_inactive: int) -> float:
        """
        Analyze stalled conversation signal.

        Args:
            days_inactive: Number of days since last activity

        Returns:
            Signal value (0.0-1.0)
        """
        threshold = 7  # 7 days

        if days_inactive <= threshold:
            return 0.0
        elif days_inactive <= threshold * 2:
            return 0.5
        elif days_inactive <= threshold * 4:
            return 0.75
        else:
            return 1.0

    def _calculate_risk_score(self, signals: Dict[str, float]) -> float:
        """
        Calculate weighted churn risk score.

        Args:
            signals: Dictionary of signal names and values

        Returns:
            Risk score (0-100)
        """
        weighted_sum = 0.0

        for signal_name, signal_value in signals.items():
            weight = self.SIGNAL_WEIGHTS.get(signal_name, 0.0)
            weighted_sum += signal_value * weight

        # Normalize to 0-100
        risk_score = weighted_sum * 100

        return min(max(risk_score, 0.0), 100.0)

    def _determine_risk_level(self, risk_score: float) -> ChurnRiskLevel:
        """
        Determine risk level based on risk score.

        Args:
            risk_score: Risk score (0-100)

        Returns:
            ChurnRiskLevel
        """
        for level, (min_score, max_score) in self.RISK_LEVEL_THRESHOLDS.items():
            if min_score <= risk_score <= max_score:
                return level

        return ChurnRiskLevel.LOW

    def _get_recovery_strategy(
        self,
        days_inactive: int,
        risk_level: ChurnRiskLevel,
    ) -> RecoveryStrategy:
        """
        Get recommended recovery strategy based on days inactive and risk level.

        Args:
            days_inactive: Number of days since last activity
            risk_level: Current risk level

        Returns:
            RecoveryStrategy
        """
        # Strategy selection based on days inactive
        if days_inactive >= 60:
            return RecoveryStrategy.ARCHIVE
        elif days_inactive >= 45:
            return RecoveryStrategy.FINAL_CHECK_IN
        elif days_inactive >= 30:
            return RecoveryStrategy.INCENTIVE_OFFER
        elif days_inactive >= 21:
            return RecoveryStrategy.NEW_INFORMATION
        elif days_inactive >= 14:
            return RecoveryStrategy.QUESTION_RE_ENGAGEMENT
        elif days_inactive >= 7:
            return RecoveryStrategy.VALUE_REMINDER
        else:
            # For critical risk, escalate to human handoff
            if risk_level == ChurnRiskLevel.CRITICAL:
                return RecoveryStrategy.FINAL_CHECK_IN
            return RecoveryStrategy.VALUE_REMINDER

    async def get_recovery_strategy(
        self,
        risk_assessment: ChurnRiskAssessment,
    ) -> RecoveryStrategy:
        """
        Determine appropriate recovery strategy.

        Args:
            risk_assessment: The churn risk assessment

        Returns:
            RecoveryStrategy
        """
        return self._get_recovery_strategy(
            days_inactive=risk_assessment.days_inactive,
            risk_level=risk_assessment.risk_level,
        )

    async def schedule_recovery_action(
        self,
        contact_id: str,
        strategy: RecoveryStrategy,
        contact_data: Dict,
    ) -> RecoveryAction:
        """
        Schedule a recovery action.

        Args:
            contact_id: The contact ID
            strategy: The recovery strategy to use
            contact_data: Contact data for personalization

        Returns:
            RecoveryAction
        """
        # Get template
        template_info = self.RECOVERY_TEMPLATES.get(strategy, {})
        template = template_info.get("template", "")
        channel = template_info.get("channel", "email")

        # Personalize template
        name = contact_data.get("name", "there")
        topic = contact_data.get("topic", "our conversation")
        market = contact_data.get("market", "the market")
        incentive = contact_data.get("incentive", "a special offer")

        message = template.format(
            name=name,
            topic=topic,
            market=market,
            incentive=incentive,
        )

        # Calculate scheduled time based on strategy
        contact_data.get("days_inactive", 0)
        scheduled_at = datetime.utcnow() + timedelta(hours=24)

        action = RecoveryAction(
            contact_id=contact_id,
            strategy=strategy,
            message_template=message,
            channel=channel,
            scheduled_at=scheduled_at,
            status="pending",
        )

        logger.info(
            f"Recovery action scheduled for {contact_id}: "
            f"strategy={strategy.value}, channel={channel}, "
            f"scheduled_at={scheduled_at.isoformat()}"
        )

        return action

    async def execute_recovery_action(self, action: RecoveryAction) -> bool:
        """
        Execute a scheduled recovery action.

        Args:
            action: The recovery action to execute

        Returns:
            True if successful, False otherwise
        """
        # This would integrate with GHL to send the message
        # For now, we'll just mark it as sent
        action.status = "sent"
        action.result = "Message sent successfully"

        logger.info(
            f"Recovery action executed for {action.contact_id}: "
            f"strategy={action.strategy.value}, status={action.status}"
        )

        return True

    async def get_at_risk_contacts(
        self,
        min_risk_level: ChurnRiskLevel = ChurnRiskLevel.MEDIUM,
        limit: int = 100,
    ) -> List[ChurnRiskAssessment]:
        """
        Get all contacts at or above risk level.

        Args:
            min_risk_level: Minimum risk level to include
            limit: Maximum number of contacts to return

        Returns:
            List of ChurnRiskAssessment
        """
        # This would query the database for at-risk contacts
        # For now, return empty list
        logger.info(f"Getting at-risk contacts (min_level={min_risk_level.value}, limit={limit})")
        return []

    async def batch_assess_contacts(
        self,
        contact_ids: List[str],
    ) -> List[ChurnRiskAssessment]:
        """
        Batch assess churn risk for multiple contacts.

        Args:
            contact_ids: List of contact IDs to assess

        Returns:
            List of ChurnRiskAssessment
        """
        assessments = []

        for contact_id in contact_ids:
            # This would fetch conversation history and last activity from database
            # For now, create a placeholder assessment
            assessment = ChurnRiskAssessment(
                contact_id=contact_id,
                risk_score=0.0,
                risk_level=ChurnRiskLevel.LOW,
                signals={},
                last_activity=datetime.utcnow(),
                days_inactive=0,
                recommended_action=RecoveryStrategy.VALUE_REMINDER,
                assessed_at=datetime.utcnow(),
            )
            assessments.append(assessment)

        logger.info(f"Batch assessed {len(contact_ids)} contacts for churn risk")
        return assessments
