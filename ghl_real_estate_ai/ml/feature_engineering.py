"""
Feature Engineering Pipeline for Predictive Lead Scoring.

Extracts advanced features from conversation data, market conditions,
and historical patterns to predict closing probability.
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from textblob import TextBlob

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)
cache = get_cache_service()


@dataclass
class ConversationFeatures:
    """Structured features extracted from conversation data."""

    # Basic conversation metrics
    message_count: int
    avg_response_time: float
    conversation_duration_minutes: float

    # Sentiment and engagement
    overall_sentiment: float  # -1 to 1
    urgency_score: float  # 0 to 1
    engagement_score: float  # 0 to 1

    # Content analysis
    question_asking_frequency: float
    price_mention_count: int
    timeline_urgency_signals: int
    location_specificity: float

    # Budget alignment
    budget_to_market_ratio: Optional[float]
    budget_confidence: float  # 0 to 1

    # Qualifying information completeness
    qualification_completeness: float  # 0 to 1 (7 key questions)
    missing_critical_info: List[str]

    # Behavioral patterns
    message_length_variance: float
    response_consistency: float
    weekend_activity: bool
    late_night_activity: bool


@dataclass
class MarketFeatures:
    """Market condition features for lead scoring."""

    inventory_level: float  # 0 to 1 (0 = low inventory, high competition)
    average_days_on_market: int
    price_trend: float  # -1 to 1 (negative = declining, positive = rising)
    seasonal_factor: float  # 0 to 1 based on month
    competition_level: float  # 0 to 1 in target areas
    interest_rate_level: float  # Current mortgage rates


class FeatureEngineer:
    """Advanced feature engineering for predictive lead scoring."""

    def __init__(self):
        self.cache_ttl = 3600  # 1 hour for feature cache

    async def extract_conversation_features(self, conversation_context: Dict[str, Any]) -> ConversationFeatures:
        """
        Extract comprehensive features from conversation data.

        Args:
            conversation_context: Full conversation context with history and preferences

        Returns:
            ConversationFeatures object with all extracted features
        """
        cache_key = f"conv_features:{hash(str(conversation_context))}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        try:
            messages = conversation_context.get("conversation_history", [])
            prefs = conversation_context.get("extracted_preferences", {})
            created_at = conversation_context.get("created_at", datetime.now())

            # Basic conversation metrics
            features = await self._extract_basic_metrics(messages, created_at)

            # Sentiment and engagement analysis
            sentiment_features = await self._analyze_sentiment_engagement(messages)

            # Content analysis
            content_features = await self._analyze_conversation_content(messages)

            # Budget and market alignment
            budget_features = await self._analyze_budget_alignment(prefs)

            # Qualification completeness
            qualification_features = await self._analyze_qualification_completeness(prefs)

            # Behavioral patterns
            behavioral_features = await self._analyze_behavioral_patterns(messages)

            # Combine all features
            conversation_features = ConversationFeatures(
                # Basic metrics
                message_count=features["message_count"],
                avg_response_time=features["avg_response_time"],
                conversation_duration_minutes=features["duration_minutes"],
                # Sentiment and engagement
                overall_sentiment=sentiment_features["sentiment"],
                urgency_score=sentiment_features["urgency"],
                engagement_score=sentiment_features["engagement"],
                # Content analysis
                question_asking_frequency=content_features["question_frequency"],
                price_mention_count=content_features["price_mentions"],
                timeline_urgency_signals=content_features["urgency_signals"],
                location_specificity=content_features["location_specificity"],
                # Budget alignment
                budget_to_market_ratio=budget_features["budget_ratio"],
                budget_confidence=budget_features["confidence"],
                # Qualification completeness
                qualification_completeness=qualification_features["completeness"],
                missing_critical_info=qualification_features["missing_info"],
                # Behavioral patterns
                message_length_variance=behavioral_features["length_variance"],
                response_consistency=behavioral_features["consistency"],
                weekend_activity=behavioral_features["weekend_activity"],
                late_night_activity=behavioral_features["late_night_activity"],
            )

            await cache.set(cache_key, conversation_features, self.cache_ttl)
            return conversation_features

        except Exception as e:
            logger.error(f"Error extracting conversation features: {e}")
            # Return default features on error
            return ConversationFeatures(
                message_count=len(messages),
                avg_response_time=300.0,  # 5 minutes default
                conversation_duration_minutes=30.0,
                overall_sentiment=0.0,
                urgency_score=0.5,
                engagement_score=0.5,
                question_asking_frequency=0.0,
                price_mention_count=0,
                timeline_urgency_signals=0,
                location_specificity=0.5,
                budget_to_market_ratio=None,
                budget_confidence=0.5,
                qualification_completeness=0.0,
                missing_critical_info=[],
                message_length_variance=0.0,
                response_consistency=0.5,
                weekend_activity=False,
                late_night_activity=False,
            )

    async def _extract_basic_metrics(self, messages: List[Dict], created_at: datetime) -> Dict[str, float]:
        """Extract basic conversation metrics."""
        message_count = len(messages)

        if message_count == 0:
            return {"message_count": 0, "avg_response_time": 300.0, "duration_minutes": 0.0}

        # Calculate conversation duration
        now = datetime.now()
        if isinstance(created_at, str):
            # Handle possible ISO formats with 'Z' or offsets
            try:
                if created_at.endswith("Z"):
                    created_at = created_at[:-1] + "+00:00"
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                # Fallback if parsing fails
                created_at = now

        # Ensure we're comparing naive datetimes
        if created_at.tzinfo is not None:
            created_at = created_at.replace(tzinfo=None)

        duration_minutes = (now - created_at).total_seconds() / 60

        # Calculate average response time (simplified)
        # In production, you'd analyze actual message timestamps
        avg_response_time = min(duration_minutes * 60 / max(message_count, 1), 3600)  # Cap at 1 hour

        return {
            "message_count": message_count,
            "avg_response_time": avg_response_time,
            "duration_minutes": duration_minutes,
        }

    async def _analyze_sentiment_engagement(self, messages: List[Dict]) -> Dict[str, float]:
        """Analyze sentiment and engagement from conversation."""
        if not messages:
            return {"sentiment": 0.0, "urgency": 0.5, "engagement": 0.5}

        # Combine all messages for sentiment analysis
        all_text = " ".join(
            [
                msg.get("text", "")
                for msg in messages
                if msg.get("role") == "user"  # Only analyze user messages
            ]
        )

        if not all_text.strip():
            return {"sentiment": 0.0, "urgency": 0.5, "engagement": 0.5}

        # Sentiment analysis
        blob = TextBlob(all_text)
        sentiment = blob.sentiment.polarity  # -1 to 1

        # Urgency analysis based on keywords
        urgency_keywords = [
            "asap",
            "urgent",
            "quickly",
            "soon",
            "immediately",
            "now",
            "this week",
            "this month",
            "deadline",
            "time sensitive",
        ]
        urgency_score = sum(1 for keyword in urgency_keywords if keyword in all_text.lower())
        urgency_score = min(urgency_score / 3, 1.0)  # Normalize to 0-1

        # Engagement based on message length and question asking
        question_marks = all_text.count("?")
        avg_message_length = len(all_text) / len(messages) if messages else 0
        engagement_score = min((question_marks * 0.1 + avg_message_length / 100) / 2, 1.0)

        return {"sentiment": sentiment, "urgency": urgency_score, "engagement": engagement_score}

    async def _analyze_conversation_content(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze conversation content for specific patterns."""
        if not messages:
            return {"question_frequency": 0.0, "price_mentions": 0, "urgency_signals": 0, "location_specificity": 0.0}

        all_text = " ".join([msg.get("text", "") for msg in messages])

        # Question asking frequency
        question_count = all_text.count("?")
        question_frequency = question_count / len(messages) if messages else 0

        # Price mentions
        price_patterns = [
            r"\$[\d,]+",  # $500,000
            r"[\d,]+\s*k",  # 500k
            r"[\d,]+\s*thousand",  # 500 thousand
            r"[\d,]+\s*million",  # 1.5 million
        ]
        price_mentions = sum(len(re.findall(pattern, all_text, re.IGNORECASE)) for pattern in price_patterns)

        # Urgency signals
        urgency_patterns = [
            "need to move",
            "relocating",
            "job transfer",
            "school district",
            "lease ending",
            "rent increase",
            "growing family",
            "divorce",
            "retirement",
            "downsize",
            "investment opportunity",
        ]
        urgency_signals = sum(1 for pattern in urgency_patterns if pattern in all_text.lower())

        # Location specificity (check for specific neighborhoods, schools, etc.)
        location_indicators = [
            "school",
            "district",
            "neighborhood",
            "area",
            "zip",
            "code",
            "commute",
            "work",
            "downtown",
            "suburb",
            "highway",
            "metro",
        ]
        location_specificity = min(
            sum(1 for indicator in location_indicators if indicator in all_text.lower()) / 5, 1.0
        )

        return {
            "question_frequency": question_frequency,
            "price_mentions": price_mentions,
            "urgency_signals": urgency_signals,
            "location_specificity": location_specificity,
        }

    async def _analyze_budget_alignment(self, prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze budget alignment with market conditions."""
        budget = prefs.get("budget")
        location = prefs.get("location", "")

        if not budget:
            return {"budget_ratio": None, "confidence": 0.0}

        try:
            # Extract numeric budget
            if isinstance(budget, str):
                # Parse budget from string like "$500,000" or "500k"
                budget_str = re.sub(r"[^\d.]", "", budget)
                if "k" in budget.lower():
                    budget_num = float(budget_str) * 1000
                elif "m" in budget.lower():
                    budget_num = float(budget_str) * 1000000
                else:
                    budget_num = float(budget_str)
            else:
                budget_num = float(budget)

            # Estimate market price for the area (simplified)
            # In production, integrate with MLS data or Zillow API
            market_estimates = {
                "downtown": 800000,
                "suburban": 600000,
                "urban": 750000,
                "rural": 400000,
                "luxury": 1200000,
                "default": 650000,
            }

            estimated_market_price = market_estimates.get("default", 650000)
            for area_type, price in market_estimates.items():
                if area_type in location.lower():
                    estimated_market_price = price
                    break

            # Calculate budget to market ratio
            budget_ratio = budget_num / estimated_market_price

            # Calculate confidence based on budget clarity
            confidence = 1.0 if isinstance(budget, (int, float)) else 0.7

            return {"budget_ratio": budget_ratio, "confidence": confidence}

        except (ValueError, TypeError):
            return {"budget_ratio": None, "confidence": 0.0}

    async def _analyze_qualification_completeness(self, prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how complete the lead qualification is."""
        required_fields = ["budget", "location", "timeline", "bedrooms", "financing", "motivation", "must_haves"]

        completed_fields = 0
        missing_info = []

        for field in required_fields:
            if prefs.get(field):
                completed_fields += 1
            else:
                missing_info.append(field)

        completeness = completed_fields / len(required_fields)

        return {"completeness": completeness, "missing_info": missing_info}

    async def _analyze_behavioral_patterns(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze behavioral patterns in conversation."""
        if not messages:
            return {"length_variance": 0.0, "consistency": 1.0, "weekend_activity": False, "late_night_activity": False}

        # Message length variance
        message_lengths = [len(msg.get("text", "")) for msg in messages]
        length_variance = np.var(message_lengths) if message_lengths else 0.0

        # Response consistency (simplified - would analyze response patterns)
        consistency = 1.0 - min(length_variance / 10000, 1.0)  # Normalize

        # Time-based activity patterns (simplified)
        # In production, you'd analyze actual message timestamps
        weekend_activity = False  # Would check if messages sent on weekends
        late_night_activity = False  # Would check if messages sent late night

        return {
            "length_variance": length_variance,
            "consistency": consistency,
            "weekend_activity": weekend_activity,
            "late_night_activity": late_night_activity,
        }

    async def extract_market_features(self, location: str = None) -> MarketFeatures:
        """
        Extract market condition features.

        Args:
            location: Target location for market analysis

        Returns:
            MarketFeatures object with market conditions
        """
        cache_key = f"market_features:{location or 'general'}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        try:
            # In production, integrate with real market data APIs
            # For now, using simplified mock data with seasonal patterns

            current_month = datetime.now().month

            # Seasonal factor (higher in spring/summer)
            seasonal_factors = {
                1: 0.3,
                2: 0.4,
                3: 0.6,
                4: 0.8,
                5: 1.0,
                6: 0.9,
                7: 0.8,
                8: 0.7,
                9: 0.6,
                10: 0.5,
                11: 0.4,
                12: 0.3,
            }
            seasonal_factor = seasonal_factors.get(current_month, 0.5)

            # Mock market data (in production, fetch from MLS/Zillow)
            market_features = MarketFeatures(
                inventory_level=0.7,  # 70% inventory level
                average_days_on_market=25,
                price_trend=0.1,  # 10% price appreciation
                seasonal_factor=seasonal_factor,
                competition_level=0.6,  # 60% competition
                interest_rate_level=7.2,  # Current mortgage rates
            )

            # Cache for 4 hours (market data doesn't change frequently)
            await cache.set(cache_key, market_features, 14400)
            return market_features

        except Exception as e:
            logger.error(f"Error extracting market features: {e}")
            return MarketFeatures(
                inventory_level=0.5,
                average_days_on_market=30,
                price_trend=0.0,
                seasonal_factor=0.5,
                competition_level=0.5,
                interest_rate_level=7.0,
            )

    def create_feature_vector(self, conv_features: ConversationFeatures, market_features: MarketFeatures) -> np.ndarray:
        """
        Create a feature vector for ML model input.

        Args:
            conv_features: Conversation-based features
            market_features: Market condition features

        Returns:
            NumPy array of normalized features ready for ML model
        """
        features = [
            # Conversation metrics (normalized)
            min(conv_features.message_count / 50, 1.0),  # Normalize to 0-1
            min(conv_features.avg_response_time / 3600, 1.0),  # Hours, max 1
            min(conv_features.conversation_duration_minutes / 1440, 1.0),  # Days, max 1
            # Sentiment and engagement (already 0-1)
            (conv_features.overall_sentiment + 1) / 2,  # Convert -1,1 to 0,1
            conv_features.urgency_score,
            conv_features.engagement_score,
            # Content analysis
            min(conv_features.question_asking_frequency, 1.0),
            min(conv_features.price_mention_count / 10, 1.0),  # Normalize
            min(conv_features.timeline_urgency_signals / 5, 1.0),  # Normalize
            conv_features.location_specificity,
            # Budget alignment
            min(conv_features.budget_to_market_ratio or 0.5, 2.0) / 2.0,  # Normalize, cap at 2x
            conv_features.budget_confidence,
            # Qualification
            conv_features.qualification_completeness,
            # Behavioral patterns
            min(conv_features.message_length_variance / 10000, 1.0),  # Normalize
            conv_features.response_consistency,
            float(conv_features.weekend_activity),
            float(conv_features.late_night_activity),
            # Market features
            market_features.inventory_level,
            min(market_features.average_days_on_market / 120, 1.0),  # Normalize
            (market_features.price_trend + 1) / 2,  # Convert -1,1 to 0,1
            market_features.seasonal_factor,
            market_features.competition_level,
            min(market_features.interest_rate_level / 10, 1.0),  # Normalize
        ]

        return np.array(features, dtype=np.float32)

    def get_feature_names(self) -> List[str]:
        """Get names of all features in the feature vector."""
        return [
            "message_count_norm",
            "avg_response_time_norm",
            "conversation_duration_norm",
            "sentiment_norm",
            "urgency_score",
            "engagement_score",
            "question_frequency",
            "price_mentions_norm",
            "urgency_signals_norm",
            "location_specificity",
            "budget_market_ratio",
            "budget_confidence",
            "qualification_completeness",
            "message_variance_norm",
            "response_consistency",
            "weekend_activity",
            "late_night_activity",
            "inventory_level",
            "days_on_market_norm",
            "price_trend_norm",
            "seasonal_factor",
            "competition_level",
            "interest_rate_norm",
        ]
