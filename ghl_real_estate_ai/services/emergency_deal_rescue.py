"""
Emergency Deal Rescue System - Proactive Deal Protection
======================================================

Real-time deal risk monitoring with instant response protocols.
Detects churn signals and triggers immediate rescue strategies to save high-value deals.

Builds on existing churn prediction with emergency intervention automation.

Author: Enhanced from research recommendations - January 2026
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.churn_prediction_engine import ChurnPredictionEngine
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.claude_conversation_intelligence import ClaudeConversationIntelligenceService
from ghl_real_estate_ai.services.ghl_deal_intelligence_service import GHLDealData, get_ghl_deal_intelligence_service
from ghl_real_estate_ai.utils.score_utils import clamp_score

logger = get_logger(__name__)


class RescueUrgencyLevel(Enum):
    """Urgency levels for deal rescue interventions."""

    CRITICAL = "critical"  # Immediate intervention required (< 2 hours)
    HIGH = "high"  # Urgent intervention needed (< 24 hours)
    MEDIUM = "medium"  # Moderate risk, intervention helpful (< 72 hours)
    LOW = "low"  # Monitoring recommended (< 1 week)


class RescueStrategy(Enum):
    """Types of rescue strategies available."""

    PRICE_ADJUSTMENT = "price_adjustment"
    TIMELINE_FLEXIBILITY = "timeline_flexibility"
    CONTINGENCY_MODIFICATION = "contingency_modification"
    INCENTIVE_OFFERING = "incentive_offering"
    COMMUNICATION_INTERVENTION = "communication_intervention"
    THIRD_PARTY_MEDIATION = "third_party_mediation"
    ALTERNATIVE_SOLUTIONS = "alternative_solutions"


class ChurnSignalType(Enum):
    """Types of signals that indicate deal risk."""

    SENTIMENT_DETERIORATION = "sentiment_deterioration"
    COMMUNICATION_SILENCE = "communication_silence"
    OBJECTION_ESCALATION = "objection_escalation"
    TIMELINE_PRESSURE = "timeline_pressure"
    FINANCIAL_STRESS = "financial_stress"
    COMPETITIVE_PRESSURE = "competitive_pressure"
    INSPECTION_CONCERNS = "inspection_concerns"
    APPRAISAL_SHORTFALL = "appraisal_shortfall"


@dataclass
class ChurnSignal:
    """Individual signal indicating deal risk."""

    signal_type: ChurnSignalType
    severity: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    source: str  # Where signal was detected
    context: str  # Description of the signal
    detected_at: datetime
    related_messages: List[str]  # Associated conversation messages


@dataclass
class DealRiskProfile:
    """Comprehensive risk assessment for a deal."""

    deal_id: str
    deal_value: float
    commission_value: float

    # Risk metrics
    overall_churn_risk: float  # 0.0-1.0
    urgency_level: RescueUrgencyLevel
    time_to_expected_loss: Optional[int]  # Hours until expected loss

    # Signal analysis
    active_signals: List[ChurnSignal]
    risk_factors: List[str]
    protective_factors: List[str]

    # Context
    days_since_contract: int
    planned_close_date: datetime
    buyer_profile: Dict[str, Any]
    property_details: Dict[str, Any]

    # Metadata
    last_assessment: datetime
    assessment_confidence: float


@dataclass
class RescueRecommendation:
    """AI-generated rescue strategy recommendation."""

    strategy: RescueStrategy
    priority: int  # 1-5 (1 = highest priority)
    description: str
    specific_actions: List[str]
    expected_effectiveness: float  # 0.0-1.0
    implementation_urgency: str  # "immediate", "today", "this_week"
    resource_requirements: List[str]
    risks: List[str]
    success_probability: float


@dataclass
class RescueAlert:
    """Alert generated when deal rescue is needed."""

    alert_id: str
    deal_id: str
    urgency_level: RescueUrgencyLevel

    # Alert content
    headline: str
    summary: str
    key_risk_factors: List[str]

    # Recommendations
    recommended_strategies: List[RescueRecommendation]
    immediate_actions: List[str]

    # Context for agent
    buyer_psychology: str
    negotiation_position: str
    market_factors: str

    # Escalation
    escalation_needed: bool
    escalation_timeline: Optional[str]

    generated_at: datetime
    expires_at: datetime


class EmergencyDealRescue:
    """
    Proactive deal monitoring and rescue system.

    Features:
    - Real-time churn signal detection
    - AI-powered risk assessment
    - Automated rescue strategy generation
    - Escalation and alert management
    - Success probability modeling
    """

    def __init__(self):
        self.churn_engine = ChurnPredictionEngine()
        self.conversation_intel = ClaudeConversationIntelligenceService()
        self.claude = ClaudeAssistant()
        self.cache = get_cache_service()
        self.analytics = AnalyticsService()

        # GHL Deal Intelligence (lazy-loaded)
        self._ghl_deal_service = None

        # Configuration
        self.monitoring_interval = 300  # 5 minutes
        self.cache_ttl = 1800  # 30 minutes

        # Risk thresholds
        self.urgency_thresholds = {
            RescueUrgencyLevel.CRITICAL: 0.85,
            RescueUrgencyLevel.HIGH: 0.70,
            RescueUrgencyLevel.MEDIUM: 0.50,
            RescueUrgencyLevel.LOW: 0.30,
        }

        # Deal value thresholds for alerts
        self.value_thresholds = {
            "critical_alert": 750000,  # $750K+ deals get critical monitoring
            "high_alert": 500000,  # $500K+ deals get high priority
            "standard_alert": 300000,  # $300K+ deals get standard monitoring
        }

    async def get_ghl_deal_service(self):
        """Get GHL deal intelligence service (lazy loading)."""
        if self._ghl_deal_service is None:
            self._ghl_deal_service = await get_ghl_deal_intelligence_service()
        return self._ghl_deal_service

    async def assess_deal_risk(self, deal_id: str, conversation_context: Optional[Dict] = None) -> DealRiskProfile:
        """
        Comprehensive deal risk assessment.

        Args:
            deal_id: Unique deal identifier
            conversation_context: Recent conversation data for analysis

        Returns:
            Complete risk profile with signals and recommendations
        """

        # Load deal data (in production, this would come from CRM/database)
        deal_data = await self._load_deal_data(deal_id)
        if not deal_data:
            raise ValueError(f"Deal {deal_id} not found")

        # Detect churn signals from multiple sources
        signals = await self._detect_churn_signals(deal_id, conversation_context)

        # Calculate overall churn risk
        overall_risk = await self._calculate_overall_risk(signals, deal_data)

        # Determine urgency level
        urgency = self._determine_urgency_level(overall_risk, deal_data["deal_value"])

        # Calculate time to expected loss
        time_to_loss = await self._estimate_time_to_loss(signals, deal_data)

        # Generate risk and protective factors
        risk_factors = self._extract_risk_factors(signals, deal_data)
        protective_factors = self._identify_protective_factors(signals, deal_data)

        # Calculate assessment confidence
        confidence = self._calculate_assessment_confidence(signals, deal_data)

        return DealRiskProfile(
            deal_id=deal_id,
            deal_value=deal_data["deal_value"],
            commission_value=deal_data["commission_value"],
            overall_churn_risk=overall_risk,
            urgency_level=urgency,
            time_to_expected_loss=time_to_loss,
            active_signals=signals,
            risk_factors=risk_factors,
            protective_factors=protective_factors,
            days_since_contract=deal_data["days_since_contract"],
            planned_close_date=deal_data["planned_close_date"],
            buyer_profile=deal_data["buyer_profile"],
            property_details=deal_data["property_details"],
            last_assessment=datetime.now(),
            assessment_confidence=confidence,
        )

    async def _detect_churn_signals(self, deal_id: str, conversation_context: Optional[Dict]) -> List[ChurnSignal]:
        """Detect and classify churn signals from multiple sources."""
        signals = []

        try:
            # Get conversation-based signals
            if conversation_context:
                conv_signals = await self._analyze_conversation_signals(conversation_context)
                signals.extend(conv_signals)

            # Get behavioral signals from churn engine
            churn_analysis = await self.churn_engine.analyze_churn_risk_comprehensive(
                lead_id=deal_id,  # Using deal_id as lead_id for this context
                conversation_history=conversation_context.get("messages", []) if conversation_context else [],
            )

            # Convert churn analysis to signals
            behavioral_signals = await self._convert_churn_analysis_to_signals(churn_analysis)
            signals.extend(behavioral_signals)

            # Get timeline-based signals
            timeline_signals = await self._detect_timeline_signals(deal_id)
            signals.extend(timeline_signals)

        except Exception as e:
            logger.error(f"Error detecting churn signals for deal {deal_id}: {e}")

        # Sort by severity and confidence
        signals.sort(key=lambda s: s.severity * s.confidence, reverse=True)
        return signals

    async def _analyze_conversation_signals(self, conversation_context: Dict) -> List[ChurnSignal]:
        """Analyze conversation data for churn signals."""
        signals = []

        messages = conversation_context.get("messages", [])
        if not messages:
            return signals

        # Analyze sentiment drift
        recent_messages = messages[-5:]  # Last 5 messages

        for i, message in enumerate(recent_messages):
            # Simple sentiment analysis (in production, use more sophisticated NLP)
            content = message.get("content", "").lower()

            # Detect negative sentiment patterns
            negative_patterns = [
                "concerned about",
                "worried",
                "not sure",
                "hesitant",
                "changed my mind",
                "second thoughts",
                "maybe we should",
                "found another",
                "different agent",
                "thinking of waiting",
            ]

            for pattern in negative_patterns:
                if pattern in content:
                    signals.append(
                        ChurnSignal(
                            signal_type=ChurnSignalType.SENTIMENT_DETERIORATION,
                            severity=0.6 + (i * 0.1),  # More recent = higher severity
                            confidence=0.75,
                            source="conversation",
                            context=f"Negative sentiment detected: '{pattern}'",
                            detected_at=datetime.now(),
                            related_messages=[content],
                        )
                    )

        # Detect communication silence (gaps in conversation)
        if messages:
            last_message_time = datetime.fromisoformat(messages[-1].get("timestamp", datetime.now().isoformat()))
            hours_since_last = (datetime.now() - last_message_time).total_seconds() / 3600

            if hours_since_last > 48:  # 48+ hours silence
                signals.append(
                    ChurnSignal(
                        signal_type=ChurnSignalType.COMMUNICATION_SILENCE,
                        severity=min(0.9, hours_since_last / 120),  # Cap at 90% after 5 days
                        confidence=0.85,
                        source="communication_timing",
                        context=f"{hours_since_last:.1f} hours since last communication",
                        detected_at=datetime.now(),
                        related_messages=[],
                    )
                )

        return signals

    async def _convert_churn_analysis_to_signals(self, churn_analysis: Dict) -> List[ChurnSignal]:
        """Convert churn prediction engine output to standardized signals."""
        signals = []

        try:
            # Extract key metrics from churn analysis
            churn_risk = churn_analysis.get("overall_churn_risk", 0)
            risk_factors = churn_analysis.get("risk_factors", [])

            # Convert high churn risk to signal
            if churn_risk > 0.6:
                signals.append(
                    ChurnSignal(
                        signal_type=ChurnSignalType.SENTIMENT_DETERIORATION,
                        severity=churn_risk,
                        confidence=0.8,
                        source="churn_prediction_engine",
                        context=f"High churn probability: {churn_risk:.2%}",
                        detected_at=datetime.now(),
                        related_messages=[],
                    )
                )

            # Convert specific risk factors to signals
            factor_mapping = {
                "financial_stress": ChurnSignalType.FINANCIAL_STRESS,
                "timeline_pressure": ChurnSignalType.TIMELINE_PRESSURE,
                "competitive_activity": ChurnSignalType.COMPETITIVE_PRESSURE,
            }

            for factor in risk_factors[:3]:  # Top 3 risk factors
                if factor["factor"] in factor_mapping:
                    signals.append(
                        ChurnSignal(
                            signal_type=factor_mapping[factor["factor"]],
                            severity=factor.get("severity", 0.5),
                            confidence=factor.get("confidence", 0.7),
                            source="behavioral_analysis",
                            context=factor.get("description", f"Risk factor: {factor['factor']}"),
                            detected_at=datetime.now(),
                            related_messages=[],
                        )
                    )

        except Exception as e:
            logger.error(f"Error converting churn analysis: {e}")

        return signals

    async def _detect_timeline_signals(self, deal_id: str) -> List[ChurnSignal]:
        """Detect signals related to deal timeline and milestones."""
        signals = []

        # Load deal timeline data
        deal_data = await self._load_deal_data(deal_id)
        if not deal_data:
            return signals

        planned_close = deal_data.get("planned_close_date")
        if isinstance(planned_close, str):
            planned_close = datetime.fromisoformat(planned_close)

        days_to_close = (planned_close - datetime.now()).days

        # Detect timeline pressure
        if days_to_close <= 7 and days_to_close > 0:
            signals.append(
                ChurnSignal(
                    signal_type=ChurnSignalType.TIMELINE_PRESSURE,
                    severity=max(0.3, (7 - days_to_close) / 7),
                    confidence=0.9,
                    source="timeline_analysis",
                    context=f"Close date in {days_to_close} days - timeline pressure increasing",
                    detected_at=datetime.now(),
                    related_messages=[],
                )
            )
        elif days_to_close < 0:
            signals.append(
                ChurnSignal(
                    signal_type=ChurnSignalType.TIMELINE_PRESSURE,
                    severity=0.95,
                    confidence=0.95,
                    source="timeline_analysis",
                    context=f"Deal {abs(days_to_close)} days past planned close date",
                    detected_at=datetime.now(),
                    related_messages=[],
                )
            )

        return signals

    async def _load_deal_data(self, deal_id: str) -> Optional[Dict]:
        """Load deal data from GHL CRM."""
        try:
            ghl_service = await self.get_ghl_deal_service()
            ghl_deal = await ghl_service.get_deal_by_id(deal_id)

            if not ghl_deal:
                logger.warning(f"Deal {deal_id} not found in GHL CRM")
                return None

            # Convert GHL deal data to legacy format for compatibility
            deal_data = {
                "deal_id": ghl_deal.deal_id,
                "deal_value": ghl_deal.deal_value,
                "commission_value": ghl_deal.commission_value,
                "days_since_contract": ghl_deal.days_since_creation,
                "planned_close_date": ghl_deal.expected_close_date or (datetime.now() + timedelta(days=30)),
                "buyer_profile": {
                    "type": self._classify_buyer_type(ghl_deal),
                    "financing": "conventional",  # Default - could be extracted from custom fields
                    "qualification_score": self._calculate_buyer_qualification_score(ghl_deal),
                },
                "property_details": {
                    "type": ghl_deal.property_type or "single_family",
                    "price_range": self._classify_price_range(ghl_deal.deal_value),
                    "location": self._extract_location_from_address(ghl_deal.property_address),
                    "address": ghl_deal.property_address,
                    "value": ghl_deal.property_value,
                },
                "contact_info": {
                    "name": ghl_deal.contact_name,
                    "email": ghl_deal.contact_email,
                    "phone": ghl_deal.contact_phone,
                },
                "deal_stage": ghl_deal.deal_stage,
                "pipeline_id": ghl_deal.pipeline_id,
                "last_contact_date": ghl_deal.last_contact_date,
                "conversation_count": ghl_deal.conversation_count,
                "recent_messages": ghl_deal.recent_messages,
                "deal_source": ghl_deal.deal_source,
                "tags": ghl_deal.tags,
                "custom_fields": ghl_deal.custom_fields,
                "created_date": ghl_deal.created_date,
                "updated_date": ghl_deal.updated_date,
            }

            return deal_data

        except Exception as e:
            logger.error(f"Error loading deal data from GHL for {deal_id}: {e}")
            return None

    def _classify_buyer_type(self, deal: GHLDealData) -> str:
        """Classify buyer type based on deal characteristics."""
        tags = [tag.lower() for tag in deal.tags]

        if any(tag in tags for tag in ["first_time", "firsttime", "fthb"]):
            return "first_time_buyer"
        elif any(tag in tags for tag in ["investor", "investment", "rental"]):
            return "investor"
        elif any(tag in tags for tag in ["relocating", "relocation", "transfer"]):
            return "relocating"
        elif deal.deal_value > 1000000:
            return "luxury_buyer"
        else:
            return "repeat_buyer"

    def _calculate_buyer_qualification_score(self, deal: GHLDealData) -> int:
        """Calculate buyer qualification score based on available data."""
        score = 50  # Base score

        # Adjust based on communication activity
        if deal.conversation_count > 10:
            score += 20
        elif deal.conversation_count > 5:
            score += 10

        # Adjust based on deal value vs timeline
        if deal.days_since_creation < 30 and deal.deal_value > 500000:
            score += 15  # Well-qualified, moves quickly

        # Adjust based on deal stage progression
        if deal.deal_stage.lower() in ["qualified", "contract", "under_contract"]:
            score += 20

        # Recent communication is positive
        if deal.last_contact_date and (datetime.now() - deal.last_contact_date).days < 3:
            score += 10

        return clamp_score(score, min_val=10)

    def _classify_price_range(self, deal_value: float) -> str:
        """Classify deal into price range categories."""
        if deal_value >= 1000000:
            return "luxury"
        elif deal_value >= 500000:
            return "high_end"
        elif deal_value >= 300000:
            return "mid_market"
        else:
            return "entry_level"

    def _extract_location_from_address(self, address: Optional[str]) -> str:
        """Extract location/ZIP code from property address."""
        if not address:
            return "91730"  # Default Rancho Cucamonga ZIP

        # Try to extract ZIP code
        import re

        zip_match = re.search(r"\b(78\d{3})\b", address)
        if zip_match:
            return zip_match.group(1)

        # Try to extract city/area
        if "rancho_cucamonga" in address.lower():
            return "91730"
        elif "cedar park" in address.lower():
            return "78613"
        elif "round rock" in address.lower():
            return "78664"

        return "91730"  # Default

    async def _calculate_overall_risk(self, signals: List[ChurnSignal], deal_data: Dict) -> float:
        """Calculate composite risk score from all signals."""
        if not signals:
            return 0.1  # Baseline risk

        # Weight signals by severity and confidence
        weighted_scores = []
        weights = []

        for signal in signals:
            weight = signal.confidence
            score = signal.severity

            # Apply signal type multipliers
            type_multipliers = {
                ChurnSignalType.COMMUNICATION_SILENCE: 1.2,
                ChurnSignalType.SENTIMENT_DETERIORATION: 1.1,
                ChurnSignalType.FINANCIAL_STRESS: 1.3,
                ChurnSignalType.TIMELINE_PRESSURE: 1.0,
                ChurnSignalType.COMPETITIVE_PRESSURE: 1.4,
            }

            multiplier = type_multipliers.get(signal.signal_type, 1.0)
            weighted_scores.append(score * multiplier * weight)
            weights.append(weight)

        if sum(weights) == 0:
            return 0.1

        # Calculate weighted average
        base_risk = sum(weighted_scores) / sum(weights)

        # Apply deal context adjustments
        context_multiplier = 1.0

        # Higher value deals get more scrutiny
        if deal_data.get("deal_value", 0) > 1000000:
            context_multiplier *= 1.1

        # Timeline pressure multiplier
        days_since_contract = deal_data.get("days_since_contract", 0)
        if days_since_contract > 30:  # Deals taking too long
            context_multiplier *= 1.2

        return min(0.95, base_risk * context_multiplier)

    def _determine_urgency_level(self, risk_score: float, deal_value: float) -> RescueUrgencyLevel:
        """Determine urgency level based on risk and deal value."""

        # Adjust thresholds based on deal value
        value_multiplier = 1.0
        if deal_value > self.value_thresholds["critical_alert"]:
            value_multiplier = 0.9  # Lower threshold for high-value deals
        elif deal_value > self.value_thresholds["high_alert"]:
            value_multiplier = 0.95

        adjusted_risk = risk_score / value_multiplier

        if adjusted_risk >= self.urgency_thresholds[RescueUrgencyLevel.CRITICAL]:
            return RescueUrgencyLevel.CRITICAL
        elif adjusted_risk >= self.urgency_thresholds[RescueUrgencyLevel.HIGH]:
            return RescueUrgencyLevel.HIGH
        elif adjusted_risk >= self.urgency_thresholds[RescueUrgencyLevel.MEDIUM]:
            return RescueUrgencyLevel.MEDIUM
        else:
            return RescueUrgencyLevel.LOW

    async def _estimate_time_to_loss(self, signals: List[ChurnSignal], deal_data: Dict) -> Optional[int]:
        """Estimate hours until deal is expected to be lost."""

        # Find the most urgent signals
        urgent_signals = [s for s in signals if s.severity > 0.7]
        if not urgent_signals:
            return None

        # Calculate based on signal types and severity
        min_time_estimates = []

        for signal in urgent_signals:
            if signal.signal_type == ChurnSignalType.COMMUNICATION_SILENCE:
                # Silence compounds over time
                hours_since_detection = (datetime.now() - signal.detected_at).total_seconds() / 3600
                estimated_hours = max(6, 72 - hours_since_detection)
                min_time_estimates.append(estimated_hours)

            elif signal.signal_type == ChurnSignalType.TIMELINE_PRESSURE:
                # Timeline pressure has hard deadlines
                min_time_estimates.append(48)  # 2 days to address timeline issues

            elif signal.signal_type == ChurnSignalType.COMPETITIVE_PRESSURE:
                # Competition can move fast
                min_time_estimates.append(24)  # 1 day before potentially losing to competitor

            elif signal.signal_type == ChurnSignalType.FINANCIAL_STRESS:
                # Financial issues need quick resolution
                min_time_estimates.append(48)  # 2 days to address financial concerns

        if min_time_estimates:
            return int(min(min_time_estimates))

        return None

    def _extract_risk_factors(self, signals: List[ChurnSignal], deal_data: Dict) -> List[str]:
        """Extract human-readable risk factors."""
        factors = []

        # Group signals by type
        signal_groups = {}
        for signal in signals:
            signal_type = signal.signal_type.value
            if signal_type not in signal_groups:
                signal_groups[signal_type] = []
            signal_groups[signal_type].append(signal)

        # Convert to risk factors
        for signal_type, group_signals in signal_groups.items():
            if len(group_signals) > 0:
                avg_severity = np.mean([s.severity for s in group_signals])
                if avg_severity > 0.5:
                    factors.append(f"{signal_type.replace('_', ' ').title()}: {avg_severity:.1%} risk level")

        return factors[:5]  # Top 5 risk factors

    def _identify_protective_factors(self, signals: List[ChurnSignal], deal_data: Dict) -> List[str]:
        """Identify factors that help protect the deal."""
        factors = []

        # Check for positive indicators
        buyer_score = deal_data.get("buyer_profile", {}).get("qualification_score", 0)
        if buyer_score > 80:
            factors.append("High buyer qualification score indicates strong commitment")

        days_since_contract = deal_data.get("days_since_contract", 0)
        if 10 <= days_since_contract <= 25:
            factors.append("Deal in optimal timeline window - good momentum")

        deal_value = deal_data.get("deal_value", 0)
        if 400000 <= deal_value <= 800000:
            factors.append("Deal in sweet spot price range - easier to finance")

        # Check for absence of critical signals
        critical_signals = [s for s in signals if s.severity > 0.8]
        if len(critical_signals) == 0:
            factors.append("No critical risk signals detected")

        return factors

    def _calculate_assessment_confidence(self, signals: List[ChurnSignal], deal_data: Dict) -> float:
        """Calculate confidence in the risk assessment."""

        # Base confidence from signal quality
        if signals:
            signal_confidence = np.mean([s.confidence for s in signals])
        else:
            signal_confidence = 0.3  # Low confidence if no signals

        # Data quality factor
        data_quality = 0.8  # Assume good data quality (adjust based on actual data availability)

        # Signal diversity factor (more signal types = higher confidence)
        unique_signal_types = len(set(s.signal_type for s in signals))
        diversity_factor = min(1.0, unique_signal_types / 5)  # Up to 5 types expected

        return signal_confidence * 0.6 + data_quality * 0.3 + diversity_factor * 0.1

    async def generate_rescue_alert(
        self, deal_id: str, conversation_context: Optional[Dict] = None
    ) -> Optional[RescueAlert]:
        """Generate rescue alert if deal meets alert criteria."""

        # Assess deal risk
        risk_profile = await self.assess_deal_risk(deal_id, conversation_context)

        # Check if alert is warranted
        if not self._should_generate_alert(risk_profile):
            return None

        # Generate rescue recommendations
        recommendations = await self._generate_rescue_recommendations(risk_profile)

        # Generate alert content
        alert_content = await self._generate_alert_content(risk_profile, recommendations)

        # Calculate alert expiration
        urgency_expiry = {
            RescueUrgencyLevel.CRITICAL: 2,  # 2 hours
            RescueUrgencyLevel.HIGH: 24,  # 24 hours
            RescueUrgencyLevel.MEDIUM: 72,  # 3 days
            RescueUrgencyLevel.LOW: 168,  # 1 week
        }

        expires_at = datetime.now() + timedelta(hours=urgency_expiry[risk_profile.urgency_level])

        return RescueAlert(
            alert_id=f"rescue_{deal_id}_{int(datetime.now().timestamp())}",
            deal_id=deal_id,
            urgency_level=risk_profile.urgency_level,
            headline=alert_content["headline"],
            summary=alert_content["summary"],
            key_risk_factors=risk_profile.risk_factors,
            recommended_strategies=recommendations,
            immediate_actions=alert_content["immediate_actions"],
            buyer_psychology=alert_content["buyer_psychology"],
            negotiation_position=alert_content["negotiation_position"],
            market_factors=alert_content["market_factors"],
            escalation_needed=risk_profile.urgency_level in [RescueUrgencyLevel.CRITICAL, RescueUrgencyLevel.HIGH],
            escalation_timeline=f"within {urgency_expiry[risk_profile.urgency_level]} hours"
            if risk_profile.urgency_level != RescueUrgencyLevel.LOW
            else None,
            generated_at=datetime.now(),
            expires_at=expires_at,
        )

    def _should_generate_alert(self, risk_profile: DealRiskProfile) -> bool:
        """Determine if an alert should be generated."""

        # Always alert for critical and high urgency
        if risk_profile.urgency_level in [RescueUrgencyLevel.CRITICAL, RescueUrgencyLevel.HIGH]:
            return True

        # Alert for medium urgency if deal value is high
        if (
            risk_profile.urgency_level == RescueUrgencyLevel.MEDIUM
            and risk_profile.deal_value > self.value_thresholds["high_alert"]
        ):
            return True

        # Alert for any urgency if deal value is critical
        if risk_profile.deal_value > self.value_thresholds["critical_alert"]:
            return True

        return False

    async def _generate_rescue_recommendations(self, risk_profile: DealRiskProfile) -> List[RescueRecommendation]:
        """Generate AI-powered rescue strategy recommendations."""
        recommendations = []

        # Analyze primary risk factors
        primary_signals = [s for s in risk_profile.active_signals if s.severity > 0.6]

        for signal in primary_signals[:3]:  # Top 3 signals
            if signal.signal_type == ChurnSignalType.COMMUNICATION_SILENCE:
                recommendations.append(
                    RescueRecommendation(
                        strategy=RescueStrategy.COMMUNICATION_INTERVENTION,
                        priority=1,
                        description="Proactive outreach to re-establish communication",
                        specific_actions=[
                            "Send personalized check-in message",
                            "Schedule brief phone call",
                            "Offer virtual property tour or market update",
                        ],
                        expected_effectiveness=0.75,
                        implementation_urgency="immediate",
                        resource_requirements=["Agent time: 30 minutes"],
                        risks=["May seem pushy if buyer needs space"],
                        success_probability=0.7,
                    )
                )

            elif signal.signal_type == ChurnSignalType.FINANCIAL_STRESS:
                recommendations.append(
                    RescueRecommendation(
                        strategy=RescueStrategy.ALTERNATIVE_SOLUTIONS,
                        priority=1,
                        description="Explore financing alternatives and concessions",
                        specific_actions=[
                            "Connect with alternative lenders",
                            "Explore seller financing options",
                            "Negotiate price adjustment or credits",
                            "Review closing cost assistance programs",
                        ],
                        expected_effectiveness=0.65,
                        implementation_urgency="today",
                        resource_requirements=["Lender relationships", "Financial analysis"],
                        risks=["May reduce commission or sale price"],
                        success_probability=0.6,
                    )
                )

            elif signal.signal_type == ChurnSignalType.TIMELINE_PRESSURE:
                recommendations.append(
                    RescueRecommendation(
                        strategy=RescueStrategy.TIMELINE_FLEXIBILITY,
                        priority=2,
                        description="Negotiate timeline adjustments and expedite process",
                        specific_actions=[
                            "Request extension from seller",
                            "Expedite inspection and appraisal",
                            "Coordinate with all parties for faster closing",
                            "Explore rent-back options",
                        ],
                        expected_effectiveness=0.8,
                        implementation_urgency="today",
                        resource_requirements=["Coordination effort", "Vendor relationships"],
                        risks=["Seller may reject extension request"],
                        success_probability=0.75,
                    )
                )

        # Sort by priority and expected effectiveness
        recommendations.sort(key=lambda r: (r.priority, -r.expected_effectiveness))

        return recommendations[:4]  # Top 4 recommendations

    async def _generate_alert_content(
        self, risk_profile: DealRiskProfile, recommendations: List[RescueRecommendation]
    ) -> Dict[str, Any]:
        """Generate human-readable alert content."""

        deal_value_formatted = f"${risk_profile.deal_value:,.0f}"
        commission_formatted = f"${risk_profile.commission_value:,.0f}"

        # Generate headline based on urgency and value
        if risk_profile.urgency_level == RescueUrgencyLevel.CRITICAL:
            headline = f"🚨 CRITICAL: {deal_value_formatted} deal at immediate risk"
        elif risk_profile.urgency_level == RescueUrgencyLevel.HIGH:
            headline = f"⚠️ HIGH ALERT: {deal_value_formatted} deal needs intervention"
        else:
            headline = f"📊 Deal Monitor: {deal_value_formatted} showing risk signals"

        # Generate summary
        top_risk = risk_profile.active_signals[0] if risk_profile.active_signals else None
        summary = f"""
        Deal {risk_profile.deal_id} ({deal_value_formatted}, {commission_formatted} commission)
        showing {risk_profile.overall_churn_risk:.0%} churn probability.

        Primary concern: {top_risk.context if top_risk else "Multiple risk factors detected"}

        Time to intervention: {risk_profile.time_to_expected_loss or "TBD"} hours
        """

        # Immediate actions
        immediate_actions = []
        for rec in recommendations[:2]:  # Top 2 recommendations
            immediate_actions.extend(rec.specific_actions[:2])  # First 2 actions from each

        # Buyer psychology analysis
        buyer_psychology = (
            "Buyer may be experiencing decision fatigue and uncertainty. Focus on reassurance and clear next steps."
        )

        # Negotiation position
        negotiation_position = f"Moderate leverage. Deal {risk_profile.days_since_contract} days old, {(risk_profile.planned_close_date - datetime.now()).days} days to close."

        # Market factors
        market_factors = "Stable market conditions. Interest rates holding steady, inventory levels normal."

        return {
            "headline": headline,
            "summary": summary.strip(),
            "immediate_actions": immediate_actions,
            "buyer_psychology": buyer_psychology,
            "negotiation_position": negotiation_position,
            "market_factors": market_factors,
        }


# Singleton instance
_rescue_system = None


async def get_emergency_deal_rescue() -> EmergencyDealRescue:
    """Get singleton emergency deal rescue system."""
    global _rescue_system
    if _rescue_system is None:
        _rescue_system = EmergencyDealRescue()
    return _rescue_system
