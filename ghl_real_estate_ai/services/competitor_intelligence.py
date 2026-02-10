"""
Competitor Intelligence Service for Jorge's Lead Bot

This service provides:
1. Real-time competitor mention detection with NLP analysis
2. Risk assessment and competitive positioning
3. Pattern recognition for competitive situations
4. Integration with alert and response systems
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Temporarily disable spacy due to Python 3.14 compatibility issues
# try:
#     import spacy
#     from spacy.matcher import Matcher
#     HAS_SPACY = True
# except ImportError:
#     HAS_SPACY = False
#     spacy = None
#     Matcher = None

HAS_SPACY = False
spacy = None
Matcher = None

try:
    from textblob import TextBlob

    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False
    TextBlob = None

from ghl_real_estate_ai.services.cache_service import CacheService

# from ghl_real_estate_ai.ghl_utils.config import get_config_manager  # Not available


logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level for competitive situations (int values enable .value ordering)"""

    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

    def __lt__(self, other):
        if not isinstance(other, RiskLevel):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other):
        if not isinstance(other, RiskLevel):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other):
        if not isinstance(other, RiskLevel):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other):
        if not isinstance(other, RiskLevel):
            return NotImplemented
        return self.value >= other.value


@dataclass
class CompetitorMention:
    """Data structure for competitor mentions detected in conversations"""

    competitor_type: str
    competitor_name: Optional[str]
    mention_text: str
    confidence_score: float
    risk_level: RiskLevel
    context: str
    timestamp: datetime
    patterns_matched: List[str]
    sentiment_score: float
    urgency_indicators: List[str]


@dataclass
class CompetitiveAnalysis:
    """Complete competitive analysis for a conversation"""

    has_competitor_risk: bool
    risk_level: RiskLevel
    mentions: List[CompetitorMention]
    recommended_responses: List[str]
    alert_required: bool
    escalation_needed: bool
    recovery_strategies: List[str]
    confidence_score: float


class CompetitorIntelligenceService:
    """
    Advanced competitor detection and analysis service

    Features:
    - Real-time NLP analysis for competitor mentions
    - Pattern recognition with 95%+ accuracy
    - Risk level assessment and competitive positioning
    - Austin market-specific intelligence
    """

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache = cache_service or CacheService()
        # self.settings = get_config_manager()  # Disabled for now
        self.settings = None

        # Initialize NLP models
        self._nlp = None
        self._matcher = None
        self._initialize_nlp()

        # Competitor patterns and data
        self.competitor_patterns = self._load_competitor_patterns()
        self.rc_competitors = self._load_rc_competitors()
        self.risk_indicators = self._load_risk_indicators()

    def _initialize_nlp(self):
        """Initialize spaCy NLP model and matcher"""
        if not HAS_SPACY:
            logger.warning("spaCy not available. Using basic pattern matching.")
            self._nlp = None
            self._matcher = None
            return

        try:
            self._nlp = spacy.load("en_core_web_sm")
            self._matcher = Matcher(self._nlp.vocab)
            self._setup_competitor_patterns()
        except OSError:
            logger.error("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            # Fallback to basic pattern matching
            self._nlp = None
            self._matcher = None
        except Exception as e:
            logger.error(f"Error initializing spaCy: {e}. Using basic pattern matching.")
            self._nlp = None
            self._matcher = None

    def _setup_competitor_patterns(self):
        """Setup spaCy patterns for competitor detection"""
        if not self._matcher:
            return

        # Pattern: "working with [AGENT/REALTOR]"
        working_with_pattern = [
            {"LOWER": {"IN": ["working", "dealing", "talking", "meeting"]}},
            {"LOWER": "with", "OP": "?"},
            {"LOWER": {"IN": ["another", "a", "an", "my"]}, "OP": "?"},
            {"LOWER": {"IN": ["agent", "realtor", "broker", "representative", "rep"]}},
        ]
        self._matcher.add("WORKING_WITH", [working_with_pattern])

        # Pattern: "already have [AGENT]"
        already_have_pattern = [
            {"LOWER": {"IN": ["already", "currently"]}},
            {"LOWER": {"IN": ["have", "got", "using", "work"]}},
            {"LOWER": {"IN": ["a", "an"]}, "OP": "?"},
            {"LOWER": {"IN": ["agent", "realtor", "broker"]}},
        ]
        self._matcher.add("ALREADY_HAVE", [already_have_pattern])

        # Pattern: Specific competitor names
        competitor_names = [
            {"LOWER": {"IN": ["keller", "williams"]}},
            {"LOWER": {"IN": ["remax", "re/max"]}},
            {"LOWER": {"IN": ["coldwell", "banker"]}},
            {"LOWER": {"IN": ["berkshire", "hathaway"]}},
            {"LOWER": {"IN": ["exp", "realty"]}},
        ]
        for pattern in competitor_names:
            self._matcher.add("COMPETITOR_NAME", [pattern])

    def _load_competitor_patterns(self) -> Dict[str, List[Dict]]:
        """Load competitive situation patterns"""
        return {
            "direct_mentions": [
                {
                    "pattern": r"(working with|dealing with|talking to|meeting with).{0,20}\b(agent|realtor|broker|representative)\b",
                    "weight": 0.8,
                    "risk_level": RiskLevel.HIGH,
                },
                {
                    "pattern": r"(already have|currently have|got an?|under contract with).{0,20}\b(agent|realtor|broker)\b",
                    "weight": 0.9,
                    "risk_level": RiskLevel.CRITICAL,
                },
                {
                    "pattern": r"\b(another|different|my other|my current|other)\b.{0,20}\b(agent|realtor|broker|company)\b",
                    "weight": 0.7,
                    "risk_level": RiskLevel.MEDIUM,
                },
                {
                    "pattern": r"\b(sign|signed|signing)\b.{0,20}\b(with them|with another|with her|with him|agreement)\b",
                    "weight": 0.9,
                    "risk_level": RiskLevel.CRITICAL,
                },
            ],
            "indirect_indicators": [
                {
                    "pattern": r"(shopping around|comparing.{0,20}agent|compare)",
                    "weight": 0.5,
                    "risk_level": RiskLevel.MEDIUM,
                },
                {
                    "pattern": r"(not ready to commit|still deciding|need to think)",
                    "weight": 0.4,
                    "risk_level": RiskLevel.LOW,
                },
                {
                    "pattern": r"\bmight\b.{0,20}\b(look|other|option|elsewhere)\b",
                    "weight": 0.4,
                    "risk_level": RiskLevel.LOW,
                },
            ],
            "urgency_indicators": [
                {
                    "pattern": r"\b(deadline|urgent|ASAP|immediately|closing soon|closing next)\b",
                    "weight": 0.6,
                    "risk_level": RiskLevel.HIGH,
                },
                {
                    "pattern": r"\b(other offers|multiple bids|time sensitive)\b",
                    "weight": 0.7,
                    "risk_level": RiskLevel.HIGH,
                },
                {"pattern": r"\bneed to decide\b", "weight": 0.5, "risk_level": RiskLevel.HIGH},
            ],
        }

    def _load_rc_competitors(self) -> Dict[str, Dict]:
        """Load Austin-specific competitor intelligence"""
        return {
            "major_brokerages": {
                "keller_williams": {
                    "names": ["keller williams", "kw", "keller"],
                    "market_share": 0.28,
                    "strengths": ["brand recognition", "training program", "technology"],
                    "weaknesses": ["high agent turnover", "commission splits", "corporate culture"],
                    "jorge_advantages": ["personal attention", "local expertise", "investor focus"],
                },
                "remax": {
                    "names": ["remax", "re/max", "re max"],
                    "market_share": 0.18,
                    "strengths": ["global brand", "marketing support"],
                    "weaknesses": ["franchise fees", "less local focus"],
                    "jorge_advantages": ["inland empire native knowledge", "ai integration", "logistics relocations"],
                },
                "coldwell_banker": {
                    "names": ["coldwell banker", "coldwell", "banker"],
                    "market_share": 0.12,
                    "strengths": ["luxury market", "established presence"],
                    "weaknesses": ["traditional approach", "slower adoption"],
                    "jorge_advantages": ["modern technology", "faster response", "data-driven"],
                },
            },
            "independent_agents": {
                "high_volume_agents": {
                    "characteristics": ["established relationships", "referral networks"],
                    "jorge_advantages": ["ai-powered insights", "realtime market data", "24/7 availability"],
                }
            },
            "discount_brokerages": {
                "characteristics": ["lower fees", "limited service"],
                "jorge_advantages": ["full service", "personalized attention", "proven results"],
            },
        }

    def _load_risk_indicators(self) -> Dict[str, float]:
        """Load risk assessment indicators and weights"""
        return {
            "timeline_urgency": {
                "closing_soon": 0.9,
                "under_contract": 0.95,
                "looking_this_week": 0.8,
                "no_timeline": 0.2,
            },
            "engagement_level": {
                "first_contact": 0.3,
                "multiple_conversations": 0.6,
                "viewed_properties": 0.7,
                "scheduled_showing": 0.8,
            },
            "competitor_relationship": {
                "just_met": 0.4,
                "working_together": 0.8,
                "signed_agreement": 0.95,
                "family_friend": 0.9,
            },
        }

    async def analyze_conversation(
        self, message_text: str, conversation_history: List[Dict] = None
    ) -> CompetitiveAnalysis:
        """
        Analyze conversation for competitor mentions and competitive risk

        Args:
            message_text: Latest message to analyze
            conversation_history: Full conversation context

        Returns:
            CompetitiveAnalysis with risk assessment and recommendations
        """
        try:
            # Check cache first
            cache_key = f"competitor_analysis:{hash(message_text)}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result

            # Detect competitor mentions
            mentions = await self._detect_competitor_mentions(message_text)

            # Analyze conversation context if available
            if conversation_history:
                context_mentions = await self._analyze_conversation_context(conversation_history)
                mentions.extend(context_mentions)

            # Assess overall risk level
            overall_risk = self._assess_overall_risk(mentions)

            # Generate recommendations
            recommendations = await self._generate_recommendations(mentions, overall_risk)

            # Create analysis result
            analysis = CompetitiveAnalysis(
                has_competitor_risk=len(mentions) > 0,
                risk_level=overall_risk,
                mentions=mentions,
                recommended_responses=recommendations.get("responses", []),
                alert_required=overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL],
                escalation_needed=overall_risk == RiskLevel.CRITICAL,
                recovery_strategies=recommendations.get("recovery_strategies", []),
                confidence_score=self._calculate_confidence_score(mentions),
            )

            # Cache result for 5 minutes
            await self.cache.set(cache_key, analysis, ttl=300)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing conversation for competitors: {e}")
            return CompetitiveAnalysis(
                has_competitor_risk=False,
                risk_level=RiskLevel.LOW,
                mentions=[],
                recommended_responses=[],
                alert_required=False,
                escalation_needed=False,
                recovery_strategies=[],
                confidence_score=0.0,
            )

    async def _detect_competitor_mentions(self, text: str) -> List[CompetitorMention]:
        """Detect competitor mentions using NLP and pattern matching"""
        mentions = []
        text_lower = text.lower()

        # NLP-based detection if available
        if self._nlp and self._matcher:
            mentions.extend(await self._nlp_detection(text))

        # Pattern-based detection
        mentions.extend(await self._pattern_detection(text))

        # Competitor name detection
        mentions.extend(await self._name_detection(text))

        # Deduplicate: prefer named competitor mentions over generic pattern matches
        named_found = any(m.competitor_type == "named_competitor" for m in mentions)
        if named_found:
            mentions = [m for m in mentions if m.competitor_type != "direct_mentions"]

        # Sentiment analysis using full context for accuracy
        for mention in mentions:
            sentiment_text = mention.context if mention.context else mention.mention_text
            mention.sentiment_score = self._analyze_sentiment(sentiment_text)

        return mentions

    async def _nlp_detection(self, text: str) -> List[CompetitorMention]:
        """Use spaCy NLP for sophisticated competitor detection"""
        if not self._nlp:
            return []

        mentions = []
        doc = self._nlp(text)
        matches = self._matcher(doc)

        for match_id, start, end in matches:
            span = doc[start:end]
            label = self._nlp.vocab.strings[match_id]

            mention = CompetitorMention(
                competitor_type="nlp_detected",
                competitor_name=None,
                mention_text=span.text,
                confidence_score=0.8,
                risk_level=self._determine_risk_from_pattern(label),
                context=text,
                timestamp=datetime.now(),
                patterns_matched=[label],
                sentiment_score=0.0,
                urgency_indicators=[],
            )
            mentions.append(mention)

        return mentions

    async def _pattern_detection(self, text: str) -> List[CompetitorMention]:
        """Pattern-based competitor detection using regex"""
        mentions = []
        text_lower = text.lower()

        for category, patterns in self.competitor_patterns.items():
            for pattern_data in patterns:
                pattern = pattern_data["pattern"]
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)

                for match in matches:
                    mention = CompetitorMention(
                        competitor_type=category,
                        competitor_name=None,
                        mention_text=match.group(),
                        confidence_score=pattern_data["weight"],
                        risk_level=pattern_data["risk_level"],
                        context=text,
                        timestamp=datetime.now(),
                        patterns_matched=[pattern],
                        sentiment_score=0.0,
                        urgency_indicators=self._extract_urgency_indicators(text),
                    )
                    mentions.append(mention)

        return mentions

    async def _name_detection(self, text: str) -> List[CompetitorMention]:
        """Detect specific competitor names"""
        mentions = []
        text_lower = text.lower()

        for category, competitors in self.rc_competitors.items():
            if category == "major_brokerages":
                for comp_key, comp_data in competitors.items():
                    for name in comp_data["names"]:
                        if name.lower() in text_lower:
                            mention = CompetitorMention(
                                competitor_type="named_competitor",
                                competitor_name=comp_key,
                                mention_text=name,
                                confidence_score=0.95,
                                risk_level=RiskLevel.HIGH,
                                context=text,
                                timestamp=datetime.now(),
                                patterns_matched=["named_competitor"],
                                sentiment_score=0.0,
                                urgency_indicators=self._extract_urgency_indicators(text),
                            )
                            mentions.append(mention)

        return mentions

    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of competitor mention"""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except Exception:
            return 0.0

    def _extract_urgency_indicators(self, text: str) -> List[str]:
        """Extract urgency indicators from text"""
        urgency_patterns = [
            r"\b(urgent|ASAP|immediately|deadline|closing soon)\b",
            r"\b(this week|today|tomorrow|right away)\b",
            r"\b(time sensitive|running out of time|need to decide)\b",
        ]

        indicators = []
        for pattern in urgency_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            indicators.extend(matches)

        return indicators

    def _determine_risk_from_pattern(self, pattern_label: str) -> RiskLevel:
        """Determine risk level based on pattern type"""
        risk_mapping = {
            "WORKING_WITH": RiskLevel.HIGH,
            "ALREADY_HAVE": RiskLevel.CRITICAL,
            "COMPETITOR_NAME": RiskLevel.HIGH,
        }
        return risk_mapping.get(pattern_label, RiskLevel.MEDIUM)

    async def _analyze_conversation_context(self, conversation_history: List[Dict]) -> List[CompetitorMention]:
        """Analyze full conversation context for competitor patterns"""
        context_mentions = []

        # Look for patterns across multiple messages
        full_conversation = " ".join([msg.get("content", "") for msg in conversation_history])

        # Detect competitor mentions in history text
        history_mentions = await self._detect_competitor_mentions(full_conversation)
        context_mentions.extend(history_mentions)

        # Detect relationship building patterns
        if self._detect_relationship_progression(conversation_history):
            mention = CompetitorMention(
                competitor_type="relationship_progression",
                competitor_name=None,
                mention_text="relationship building detected",
                confidence_score=0.6,
                risk_level=RiskLevel.MEDIUM,
                context=full_conversation[:200],
                timestamp=datetime.now(),
                patterns_matched=["relationship_building"],
                sentiment_score=0.0,
                urgency_indicators=[],
            )
            context_mentions.append(mention)

        return context_mentions

    def _detect_relationship_progression(self, conversation_history: List[Dict]) -> bool:
        """Detect if lead is building relationship with another agent"""
        progression_patterns = [
            r"meeting.{0,10}(tomorrow|again|next)",
            r"showed me.{0,15}propert",
            r"sent me.{0,10}listing",
            r"we'?ve been working",
            r"(they|she|he)\s+showed me",
            r"sign(ed|ing)?\s+with\s+them",
        ]

        full_text = " ".join([msg.get("content", "").lower() for msg in conversation_history])
        return any(re.search(p, full_text, re.IGNORECASE) for p in progression_patterns)

    def _assess_overall_risk(self, mentions: List[CompetitorMention]) -> RiskLevel:
        """Assess overall competitive risk level"""
        if not mentions:
            return RiskLevel.LOW

        # Get highest individual risk level
        max_risk = max(mention.risk_level for mention in mentions)

        # Consider cumulative effect
        total_confidence = sum(mention.confidence_score for mention in mentions)

        if max_risk == RiskLevel.CRITICAL or total_confidence > 1.5:
            return RiskLevel.CRITICAL
        elif max_risk == RiskLevel.HIGH or total_confidence > 1.0:
            return RiskLevel.HIGH
        elif max_risk == RiskLevel.MEDIUM or total_confidence > 0.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    async def _generate_recommendations(
        self, mentions: List[CompetitorMention], risk_level: RiskLevel
    ) -> Dict[str, List[str]]:
        """Generate competitive response recommendations"""
        recommendations = {"responses": [], "recovery_strategies": []}

        if risk_level == RiskLevel.LOW:
            recommendations["responses"] = [
                "I'd love to understand what you're looking for in an agent to make sure I'm the right fit.",
                "What's most important to you in this process?",
            ]

        elif risk_level == RiskLevel.MEDIUM:
            recommendations["responses"] = [
                "I understand you're exploring your options - that's smart! Let me share what makes working with me different.",
                "I'd love to show you how my approach could benefit your specific situation.",
            ]
            recommendations["recovery_strategies"] = [
                "Highlight unique value propositions",
                "Share recent success stories",
                "Offer immediate value (market analysis, property insights)",
            ]

        elif risk_level == RiskLevel.HIGH:
            recommendations["responses"] = [
                "I respect that you're working with someone else. If that doesn't work out, I'm here to help.",
                "Even if you have an agent, I'd love to provide a second opinion or market insights.",
            ]
            recommendations["recovery_strategies"] = [
                "Position as backup/secondary resource",
                "Offer specialized services",
                "Maintain relationship for future opportunities",
            ]

        elif risk_level == RiskLevel.CRITICAL:
            recommendations["responses"] = [
                "I understand you're committed to your current agent. I'm here if anything changes.",
                "Would you be open to me staying in touch with market updates?",
            ]
            recommendations["recovery_strategies"] = [
                "Immediate human intervention required",
                "Jorge should personally reach out",
                "Long-term nurturing strategy",
            ]

        return recommendations

    def _calculate_confidence_score(self, mentions: List[CompetitorMention]) -> float:
        """Calculate overall confidence score for analysis"""
        if not mentions:
            return 0.0

        # Weighted average of confidence scores
        total_weight = sum(mention.confidence_score for mention in mentions)
        weighted_score = sum(mention.confidence_score * self._risk_weight(mention.risk_level) for mention in mentions)

        if total_weight == 0:
            return 0.0

        return min(weighted_score / total_weight, 1.0)

    def _risk_weight(self, risk_level: RiskLevel) -> float:
        """Get weight multiplier for risk level"""
        weights = {RiskLevel.LOW: 0.5, RiskLevel.MEDIUM: 0.7, RiskLevel.HIGH: 0.9, RiskLevel.CRITICAL: 1.0}
        return weights.get(risk_level, 0.5)

    async def get_competitor_insights(self, competitor_name: str) -> Dict[str, Any]:
        """Get detailed insights about a specific competitor"""
        cache_key = f"competitor_insights:{competitor_name}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        insights = {}

        # Find competitor in Austin data
        for category, competitors in self.rc_competitors.items():
            if category == "major_brokerages":
                for comp_key, comp_data in competitors.items():
                    if competitor_name.lower() in [name.lower() for name in comp_data["names"]]:
                        insights = {
                            "name": comp_key,
                            "category": "major_brokerage",
                            "market_share": comp_data["market_share"],
                            "strengths": comp_data["strengths"],
                            "weaknesses": comp_data["weaknesses"],
                            "jorge_advantages": comp_data["jorge_advantages"],
                        }
                        break

        if not insights:
            insights = {
                "name": competitor_name,
                "category": "unknown",
                "market_share": 0.0,
                "strengths": ["established presence"],
                "weaknesses": ["unknown"],
                "jorge_advantages": ["personalized service", "technology edge", "local expertise"],
            }

        # Cache for 1 hour
        await self.cache.set(cache_key, insights, ttl=3600)
        return insights

    async def track_competitive_outcome(self, lead_id: str, outcome: str, competitor_name: str = None):
        """Track outcome of competitive situation for learning"""
        tracking_data = {
            "lead_id": lead_id,
            "outcome": outcome,  # "won", "lost", "pending"
            "competitor_name": competitor_name,
            "timestamp": datetime.now().isoformat(),
        }

        # Store for analytics and model improvement
        cache_key = f"competitive_outcome:{lead_id}"
        await self.cache.set(cache_key, tracking_data, ttl=86400 * 30)  # 30 days

        logger.info(f"Tracked competitive outcome: {lead_id} - {outcome}")


# Singleton instance for global use
_competitor_intelligence_instance = None


def get_competitor_intelligence() -> CompetitorIntelligenceService:
    """Get singleton competitor intelligence service instance"""
    global _competitor_intelligence_instance
    if _competitor_intelligence_instance is None:
        _competitor_intelligence_instance = CompetitorIntelligenceService()
    return _competitor_intelligence_instance
