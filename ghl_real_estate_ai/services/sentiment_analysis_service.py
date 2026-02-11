"""
Sentiment Analysis Service

This service provides emotion detection capabilities for bot conversations,
enabling sentiment-aware responses and automatic escalation triggers.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from anthropic import Anthropic
from google import generativeai as genai

from ghl_real_estate_ai.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class SentimentType(str, Enum):
    """Emotion categories for sentiment analysis."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    ANXIOUS = "anxious"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    DISAPPOINTED = "disappointed"
    CONFUSED = "confused"


class EscalationLevel(str, Enum):
    """Escalation levels for negative sentiment situations."""
    NONE = "none"
    MONITOR = "monitor"
    HUMAN_HANDOFF = "human_handoff"
    CRITICAL = "critical"


@dataclass
class SentimentResult:
    """Result of sentiment analysis for a single message."""
    sentiment: SentimentType
    confidence: float  # 0.0-1.0
    intensity: float  # 0.0-1.0
    key_phrases: List[str] = field(default_factory=list)
    escalation_required: EscalationLevel = EscalationLevel.NONE
    suggested_response_tone: str = "professional"
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationSentiment:
    """Aggregated sentiment analysis across a conversation."""
    overall_sentiment: SentimentType
    sentiment_trend: str  # "improving", "stable", "declining"
    message_results: List[SentimentResult] = field(default_factory=list)
    escalation_history: List[Dict] = field(default_factory=list)
    avg_confidence: float = 0.0


class SentimentAnalysisService:
    """
    Analyzes sentiment in conversation messages using Claude/Gemini AI.
    
    This service provides:
    - Emotion detection for 7 sentiment types
    - Confidence scoring (0.0-1.0)
    - Escalation triggers for critical emotions
    - Response tone adaptation based on sentiment
    """
    
    # Keyword-based sentiment detection (fallback)
    NEGATIVE_KEYWORDS = {
        "angry": [
            "hate", "terrible", "awful", "worst", "ridiculous", 
            "unacceptable", "furious", "outraged", "disgusting"
        ],
        "frustrated": [
            "frustrating", "annoying", "fed up", "again", "still waiting",
            "useless", "pointless", "waste of time"
        ],
        "anxious": [
            "worried", "concerned", "nervous", "afraid", "not sure",
            "scared", "anxious", "overwhelmed"
        ],
        "disappointed": [
            "disappointed", "let down", "expected better", "unhappy",
            "not what I expected", "sad"
        ],
        "confused": [
            "confused", "don't understand", "unclear", "what does this mean",
            "doesn't make sense", "lost"
        ],
    }
    
    POSITIVE_KEYWORDS = [
        "great", "excellent", "amazing", "wonderful", "perfect",
        "happy", "excited", "love", "thank", "appreciate"
    ]
    
    # Escalation triggers: (sentiment, confidence_threshold, escalation_level)
    ESCALATION_TRIGGERS = [
        (SentimentType.ANGRY, 0.7, EscalationLevel.CRITICAL),
        (SentimentType.ANGRY, 0.5, EscalationLevel.HUMAN_HANDOFF),
        (SentimentType.FRUSTRATED, 0.8, EscalationLevel.HUMAN_HANDOFF),
        (SentimentType.FRUSTRATED, 0.6, EscalationLevel.MONITOR),
        (SentimentType.DISAPPOINTED, 0.8, EscalationLevel.HUMAN_HANDOFF),
    ]
    
    # Response tone adjustments per sentiment
    TONE_ADJUSTMENTS = {
        SentimentType.POSITIVE: {
            "tone": "enthusiastic",
            "pace": "normal",
            "emojis": True,
            "phrases": ["Great to hear!", "Exciting times!", "Wonderful!"],
        },
        SentimentType.NEUTRAL: {
            "tone": "professional",
            "pace": "normal",
            "emojis": False,
            "phrases": [],
        },
        SentimentType.ANXIOUS: {
            "tone": "empathetic",
            "pace": "slower",
            "emojis": True,
            "phrases": [
                "I understand this can feel overwhelming",
                "Let's take this step by step",
                "You're not alone in this process"
            ],
        },
        SentimentType.FRUSTRATED: {
            "tone": "apologetic",
            "pace": "faster",
            "emojis": False,
            "phrases": [
                "I apologize for the frustration",
                "Let me help resolve this",
                "I hear you and want to make this right"
            ],
        },
        SentimentType.ANGRY: {
            "tone": "calm",
            "pace": "slow",
            "emojis": False,
            "phrases": [
                "I understand your concern",
                "Let me connect you with a specialist",
                "Your feedback is important to us"
            ],
        },
        SentimentType.DISAPPOINTED: {
            "tone": "empathetic",
            "pace": "normal",
            "emojis": False,
            "phrases": [
                "I understand this isn't what you expected",
                "Here's what we can do",
                "Let's find a solution together"
            ],
        },
        SentimentType.CONFUSED: {
            "tone": "patient",
            "pace": "slower",
            "emojis": True,
            "phrases": [
                "Let me clarify that",
                "Here's a simple breakdown",
                "I'm happy to explain further"
            ],
        },
    }
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        cache_service: Optional[CacheService] = None,
    ):
        """
        Initialize the sentiment analysis service.
        
        Args:
            anthropic_api_key: Claude API key (primary)
            gemini_api_key: Gemini API key (fallback)
            cache_service: Optional cache service for caching results
        """
        self.anthropic_api_key = anthropic_api_key
        self.gemini_api_key = gemini_api_key
        self.cache_service = cache_service or CacheService()
        
        # Initialize AI clients
        self.anthropic_client = None
        self.gemini_client = None
        
        if self.anthropic_api_key:
            try:
                self.anthropic_client = Anthropic(api_key=self.anthropic_api_key)
                logger.info("Claude client initialized for sentiment analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize Claude client: {e}")
        
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_client = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini client initialized for sentiment analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")
    
    async def analyze_sentiment(
        self,
        message: str,
        conversation_history: Optional[List[str]] = None,
        use_cache: bool = True,
    ) -> SentimentResult:
        """
        Analyze sentiment of a single message.
        
        Args:
            message: The message to analyze
            conversation_history: Optional previous messages for context
            use_cache: Whether to use cached results
            
        Returns:
            SentimentResult with detected sentiment and metadata
        """
        # Check cache first
        if use_cache:
            cache_key = f"sentiment:{hash(message)}"
            cached = await self.cache_service.get(cache_key)
            if cached:
                try:
                    return SentimentResult(**json.loads(cached))
                except Exception as e:
                    logger.warning(f"Failed to parse cached sentiment: {e}")
        
        # Try AI-based analysis first
        sentiment_result = await self._analyze_with_ai(message, conversation_history)
        
        # Fallback to keyword-based analysis if AI fails
        if not sentiment_result or sentiment_result.confidence < 0.5:
            sentiment_result = self._analyze_with_keywords(message)
        
        # Determine escalation level
        sentiment_result.escalation_required = self._determine_escalation_level(
            sentiment_result
        )
        
        # Set suggested response tone
        sentiment_result.suggested_response_tone = self.TONE_ADJUSTMENTS.get(
            sentiment_result.sentiment, {}
        ).get("tone", "professional")
        
        # Cache the result
        if use_cache:
            await self.cache_service.set(
                cache_key,
                json.dumps(sentiment_result.__dict__, default=str),
                ttl=3600  # Cache for 1 hour
            )
        
        logger.info(
            f"Sentiment analyzed: {sentiment_result.sentiment.value} "
            f"(confidence: {sentiment_result.confidence:.2f}, "
            f"escalation: {sentiment_result.escalation_required.value})"
        )
        
        return sentiment_result
    
    async def _analyze_with_ai(
        self,
        message: str,
        conversation_history: Optional[List[str]] = None,
    ) -> Optional[SentimentResult]:
        """
        Analyze sentiment using Claude (primary) or Gemini (fallback).
        
        Args:
            message: The message to analyze
            conversation_history: Optional previous messages for context
            
        Returns:
            SentimentResult or None if AI analysis fails
        """
        # Build context from conversation history
        context = ""
        if conversation_history:
            context = "\n".join([
                f"Message {i+1}: {msg}" 
                for i, msg in enumerate(conversation_history[-3:])  # Last 3 messages
            ])
            context += "\n\n"
        
        # Build prompt for AI
        prompt = f"""Analyze the sentiment of the following message in a real estate conversation context.

{context}Current message: "{message}"

Identify the primary emotion from these options:
- positive: Happy, excited, satisfied
- neutral: Calm, informational
- anxious: Worried, uncertain
- frustrated: Annoyed, impatient
- angry: Irritated, upset
- disappointed: Let down, dissatisfied
- confused: Unclear, seeking help

Respond with a JSON object in this exact format:
{{
    "sentiment": "sentiment_type",
    "confidence": 0.0-1.0,
    "intensity": 0.0-1.0,
    "key_phrases": ["phrase1", "phrase2"]
}}

Only respond with the JSON, no other text."""
        
        # Try Claude first
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                content = response.content[0].text.strip()
                result = json.loads(content)
                
                return SentimentResult(
                    sentiment=SentimentType(result.get("sentiment", "neutral")),
                    confidence=float(result.get("confidence", 0.5)),
                    intensity=float(result.get("intensity", 0.5)),
                    key_phrases=result.get("key_phrases", []),
                )
            except Exception as e:
                logger.warning(f"Claude sentiment analysis failed: {e}")
        
        # Fallback to Gemini
        if self.gemini_client:
            try:
                response = self.gemini_client.generate_content(prompt)
                content = response.text.strip()
                
                # Extract JSON from response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content)
                
                return SentimentResult(
                    sentiment=SentimentType(result.get("sentiment", "neutral")),
                    confidence=float(result.get("confidence", 0.5)),
                    intensity=float(result.get("intensity", 0.5)),
                    key_phrases=result.get("key_phrases", []),
                )
            except Exception as e:
                logger.warning(f"Gemini sentiment analysis failed: {e}")
        
        return None
    
    def _analyze_with_keywords(self, message: str) -> SentimentResult:
        """
        Fallback keyword-based sentiment analysis.
        
        Args:
            message: The message to analyze
            
        Returns:
            SentimentResult based on keyword matching
        """
        message_lower = message.lower()
        
        # Check for angry keywords
        angry_matches = [
            kw for kw in self.NEGATIVE_KEYWORDS["angry"]
            if kw in message_lower
        ]
        if angry_matches:
            return SentimentResult(
                sentiment=SentimentType.ANGRY,
                confidence=0.6,
                intensity=0.7,
                key_phrases=angry_matches,
            )
        
        # Check for frustrated keywords
        frustrated_matches = [
            kw for kw in self.NEGATIVE_KEYWORDS["frustrated"]
            if kw in message_lower
        ]
        if frustrated_matches:
            return SentimentResult(
                sentiment=SentimentType.FRUSTRATED,
                confidence=0.6,
                intensity=0.6,
                key_phrases=frustrated_matches,
            )
        
        # Check for anxious keywords
        anxious_matches = [
            kw for kw in self.NEGATIVE_KEYWORDS["anxious"]
            if kw in message_lower
        ]
        if anxious_matches:
            return SentimentResult(
                sentiment=SentimentType.ANXIOUS,
                confidence=0.6,
                intensity=0.5,
                key_phrases=anxious_matches,
            )
        
        # Check for disappointed keywords
        disappointed_matches = [
            kw for kw in self.NEGATIVE_KEYWORDS["disappointed"]
            if kw in message_lower
        ]
        if disappointed_matches:
            return SentimentResult(
                sentiment=SentimentType.DISAPPOINTED,
                confidence=0.6,
                intensity=0.5,
                key_phrases=disappointed_matches,
            )
        
        # Check for confused keywords
        confused_matches = [
            kw for kw in self.NEGATIVE_KEYWORDS["confused"]
            if kw in message_lower
        ]
        if confused_matches:
            return SentimentResult(
                sentiment=SentimentType.CONFUSED,
                confidence=0.6,
                intensity=0.4,
                key_phrases=confused_matches,
            )
        
        # Check for positive keywords
        positive_matches = [
            kw for kw in self.POSITIVE_KEYWORDS
            if kw in message_lower
        ]
        if positive_matches:
            return SentimentResult(
                sentiment=SentimentType.POSITIVE,
                confidence=0.6,
                intensity=0.6,
                key_phrases=positive_matches,
            )
        
        # Default to neutral
        return SentimentResult(
            sentiment=SentimentType.NEUTRAL,
            confidence=0.5,
            intensity=0.3,
            key_phrases=[],
        )
    
    def _determine_escalation_level(
        self,
        sentiment_result: SentimentResult
    ) -> EscalationLevel:
        """
        Determine if escalation is required based on sentiment.
        
        Args:
            sentiment_result: The sentiment analysis result
            
        Returns:
            EscalationLevel indicating required action
        """
        for sentiment, threshold, level in self.ESCALATION_TRIGGERS:
            if sentiment_result.sentiment == sentiment:
                if sentiment_result.confidence >= threshold:
                    return level
        
        # Check for critical keywords regardless of sentiment
        critical_keywords = ["lawyer", "sue", "complaint", "legal action"]
        if any(kw in sentiment_result.key_phrases for kw in critical_keywords):
            return EscalationLevel.CRITICAL
        
        return EscalationLevel.NONE
    
    def get_response_tone_adjustment(
        self,
        sentiment: SentimentType
    ) -> Dict[str, any]:
        """
        Get tone adjustments for bot response based on sentiment.
        
        Args:
            sentiment: The detected sentiment
            
        Returns:
            Dictionary with tone, pace, emojis, and suggested phrases
        """
        return self.TONE_ADJUSTMENTS.get(sentiment, self.TONE_ADJUSTMENTS[SentimentType.NEUTRAL])
    
    async def analyze_conversation(
        self,
        messages: List[str]
    ) -> ConversationSentiment:
        """
        Analyze sentiment across full conversation history.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            ConversationSentiment with aggregated analysis
        """
        if not messages:
            return ConversationSentiment(
                overall_sentiment=SentimentType.NEUTRAL,
                sentiment_trend="stable",
                avg_confidence=0.0,
            )
        
        # Analyze each message
        message_results = []
        for i, message in enumerate(messages):
            result = await self.analyze_sentiment(
                message=message,
                conversation_history=messages[:i],
                use_cache=True,
            )
            message_results.append(result)
        
        # Calculate overall sentiment
        sentiment_counts = {}
        for result in message_results:
            sentiment = result.sentiment.value
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        overall_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        
        # Calculate average confidence
        avg_confidence = sum(r.confidence for r in message_results) / len(message_results)
        
        # Determine trend
        if len(message_results) >= 3:
            recent = message_results[-3:]
            earlier = message_results[:-3] if len(message_results) > 3 else message_results[:1]
            
            # Compare negative sentiment frequency
            recent_negative = sum(1 for r in recent if r.sentiment in [
                SentimentType.ANGRY, SentimentType.FRUSTRATED, SentimentType.DISAPPOINTED
            ])
            earlier_negative = sum(1 for r in earlier if r.sentiment in [
                SentimentType.ANGRY, SentimentType.FRUSTRATED, SentimentType.DISAPPOINTED
            ])
            
            if recent_negative > earlier_negative:
                trend = "declining"
            elif recent_negative < earlier_negative:
                trend = "improving"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Track escalation history
        escalation_history = [
            {
                "message_index": i,
                "sentiment": r.sentiment.value,
                "escalation_level": r.escalation_required.value,
            }
            for i, r in enumerate(message_results)
            if r.escalation_required != EscalationLevel.NONE
        ]
        
        return ConversationSentiment(
            overall_sentiment=SentimentType(overall_sentiment),
            sentiment_trend=trend,
            message_results=message_results,
            escalation_history=escalation_history,
            avg_confidence=avg_confidence,
        )
