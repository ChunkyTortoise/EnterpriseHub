"""
Business Sentiment & Brand Intelligence Analyzer

Analyzes brand sentiment, competitor reputation, and market perception through:
- Multi-platform social media sentiment analysis
- Brand mention tracking and reputation scoring
- Competitor sentiment comparison and competitive positioning
- Crisis detection through sentiment pattern analysis
- Customer feedback analysis and brand perception insights

Adapted from EnterpriseHub seller psychology analyzer for universal business intelligence.

Author: Claude Code Agent - Competitive Intelligence Specialist
Created: 2026-01-19
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import asyncio
import re
import json
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from decimal import Decimal

# Sentiment analysis libraries
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class SentimentType(Enum):
    """Sentiment classification types."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class BrandHealthStatus(Enum):
    """Overall brand health status."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    CONCERNING = "concerning"
    CRITICAL = "critical"


class TrendDirection(Enum):
    """Sentiment trend direction."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


class ReputationRisk(Enum):
    """Brand reputation risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SentimentMetrics:
    """Comprehensive sentiment metrics for a brand."""
    sentiment_score: float  # -1.0 to 1.0
    sentiment_type: SentimentType
    confidence: float  # 0.0 to 1.0
    total_mentions: int
    positive_mentions: int
    negative_mentions: int
    neutral_mentions: int
    sentiment_distribution: Dict[str, float]
    trending_keywords: List[str]
    time_period: str


@dataclass
class BrandReputationProfile:
    """Complete brand reputation analysis profile."""
    brand_name: str
    overall_sentiment: SentimentMetrics
    platform_breakdown: Dict[str, SentimentMetrics]
    competitor_comparison: Dict[str, SentimentMetrics]
    trend_analysis: Dict[str, Any]
    reputation_score: float  # 0 to 100
    brand_health: BrandHealthStatus
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    last_updated: datetime


@dataclass
class CompetitorSentimentComparison:
    """Competitive sentiment analysis and positioning."""
    primary_brand: str
    competitors: List[str]
    sentiment_rankings: Dict[str, int]  # Brand -> rank (1 = best sentiment)
    sentiment_gaps: Dict[str, float]  # Brand -> gap from leader
    competitive_advantages: List[str]
    competitive_threats: List[str]
    market_share_correlation: Optional[Dict[str, float]] = None


class BusinessSentimentAnalyzer:
    """
    Advanced sentiment analyzer for business competitive intelligence.

    Capabilities:
    - Multi-platform sentiment analysis (social media, reviews, news)
    - Brand reputation scoring and health assessment
    - Competitor sentiment comparison and competitive positioning
    - Crisis detection through sentiment pattern analysis
    - Trend analysis and predictive reputation insights
    """

    def __init__(self):
        # Initialize sentiment analysis tools
        self.vader_analyzer = SentimentIntensityAnalyzer()

        # Sentiment analysis weights for different sources
        self.source_weights = {
            'social_media': 0.4,
            'reviews': 0.3,
            'news': 0.2,
            'forums': 0.1
        }

        # Crisis detection thresholds
        self.crisis_thresholds = {
            'sentiment_drop': -0.3,  # 30% drop in sentiment
            'negative_volume_spike': 0.7,  # 70% negative mentions
            'rapid_decline': 0.5  # 50% decline in 24h
        }

        # Brand health scoring weights
        self.health_weights = {
            'sentiment_score': 0.4,
            'mention_volume': 0.2,
            'trend_stability': 0.2,
            'competitor_position': 0.2
        }

    async def analyze_brand_sentiment(
        self,
        brand_name: str,
        mention_data: List[Dict[str, Any]],
        competitor_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        time_period_days: int = 30
    ) -> BrandReputationProfile:
        """
        Comprehensive brand sentiment analysis with competitive intelligence.

        Args:
            brand_name: Name of the brand to analyze
            mention_data: List of brand mentions with content and metadata
            competitor_data: Optional competitor mention data for comparison
            time_period_days: Analysis time period in days
        """
        logger.info(f"Analyzing sentiment for brand: {brand_name}")

        # Analyze overall sentiment
        overall_sentiment = self._calculate_sentiment_metrics(
            mention_data, f"{time_period_days}d"
        )

        # Platform breakdown analysis
        platform_breakdown = self._analyze_platform_sentiment(mention_data)

        # Competitor comparison (if data available)
        competitor_comparison = {}
        if competitor_data:
            competitor_comparison = self._analyze_competitor_sentiment(
                brand_name, overall_sentiment, competitor_data
            )

        # Trend analysis
        trend_analysis = self._analyze_sentiment_trends(
            mention_data, time_period_days
        )

        # Calculate reputation score
        reputation_score = self._calculate_reputation_score(
            overall_sentiment, trend_analysis, competitor_comparison
        )

        # Determine brand health
        brand_health = self._assess_brand_health(
            overall_sentiment, trend_analysis, reputation_score
        )

        # Risk assessment
        risk_assessment = self._assess_reputation_risks(
            overall_sentiment, trend_analysis, mention_data
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_sentiment, trend_analysis, risk_assessment, competitor_comparison
        )

        return BrandReputationProfile(
            brand_name=brand_name,
            overall_sentiment=overall_sentiment,
            platform_breakdown=platform_breakdown,
            competitor_comparison=competitor_comparison,
            trend_analysis=trend_analysis,
            reputation_score=reputation_score,
            brand_health=brand_health,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            last_updated=datetime.now()
        )

    def _calculate_sentiment_metrics(
        self,
        mentions: List[Dict[str, Any]],
        time_period: str
    ) -> SentimentMetrics:
        """Calculate comprehensive sentiment metrics from mentions."""
        if not mentions:
            return SentimentMetrics(
                sentiment_score=0.0,
                sentiment_type=SentimentType.NEUTRAL,
                confidence=0.0,
                total_mentions=0,
                positive_mentions=0,
                negative_mentions=0,
                neutral_mentions=0,
                sentiment_distribution={},
                trending_keywords=[],
                time_period=time_period
            )

        # Calculate sentiment scores for each mention
        sentiment_scores = []
        sentiment_types = []
        all_keywords = []

        for mention in mentions:
            content = mention.get('content', '')

            # Use VADER sentiment analysis
            vader_scores = self.vader_analyzer.polarity_scores(content)
            sentiment_score = vader_scores['compound']
            sentiment_scores.append(sentiment_score)

            # Classify sentiment
            if sentiment_score >= 0.5:
                sentiment_type = SentimentType.VERY_POSITIVE
            elif sentiment_score >= 0.1:
                sentiment_type = SentimentType.POSITIVE
            elif sentiment_score <= -0.5:
                sentiment_type = SentimentType.VERY_NEGATIVE
            elif sentiment_score <= -0.1:
                sentiment_type = SentimentType.NEGATIVE
            else:
                sentiment_type = SentimentType.NEUTRAL

            sentiment_types.append(sentiment_type)

            # Extract keywords
            keywords = mention.get('keywords', [])
            all_keywords.extend(keywords)

        # Calculate aggregate metrics
        overall_sentiment = np.mean(sentiment_scores)
        confidence = np.std(sentiment_scores)  # Lower std = higher confidence

        # Count sentiment types
        positive_count = sum(1 for s in sentiment_types
                           if s in [SentimentType.POSITIVE, SentimentType.VERY_POSITIVE])
        negative_count = sum(1 for s in sentiment_types
                           if s in [SentimentType.NEGATIVE, SentimentType.VERY_NEGATIVE])
        neutral_count = sum(1 for s in sentiment_types if s == SentimentType.NEUTRAL)

        # Determine overall sentiment type
        if overall_sentiment >= 0.5:
            overall_type = SentimentType.VERY_POSITIVE
        elif overall_sentiment >= 0.1:
            overall_type = SentimentType.POSITIVE
        elif overall_sentiment <= -0.5:
            overall_type = SentimentType.VERY_NEGATIVE
        elif overall_sentiment <= -0.1:
            overall_type = SentimentType.NEGATIVE
        else:
            overall_type = SentimentType.NEUTRAL

        # Calculate sentiment distribution
        total_mentions = len(mentions)
        sentiment_distribution = {
            'very_positive': sum(1 for s in sentiment_types if s == SentimentType.VERY_POSITIVE) / total_mentions,
            'positive': sum(1 for s in sentiment_types if s == SentimentType.POSITIVE) / total_mentions,
            'neutral': neutral_count / total_mentions,
            'negative': sum(1 for s in sentiment_types if s == SentimentType.NEGATIVE) / total_mentions,
            'very_negative': sum(1 for s in sentiment_types if s == SentimentType.VERY_NEGATIVE) / total_mentions
        }

        # Get trending keywords
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        trending_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        trending_keywords = [kw[0] for kw in trending_keywords]

        return SentimentMetrics(
            sentiment_score=overall_sentiment,
            sentiment_type=overall_type,
            confidence=max(0.0, min(1.0, 1.0 - confidence)),
            total_mentions=total_mentions,
            positive_mentions=positive_count,
            negative_mentions=negative_count,
            neutral_mentions=neutral_count,
            sentiment_distribution=sentiment_distribution,
            trending_keywords=trending_keywords,
            time_period=time_period
        )

    def _analyze_platform_sentiment(
        self,
        mentions: List[Dict[str, Any]]
    ) -> Dict[str, SentimentMetrics]:
        """Analyze sentiment breakdown by platform."""
        platform_data = {}

        # Group mentions by platform
        for mention in mentions:
            platform = mention.get('platform', 'unknown')
            if platform not in platform_data:
                platform_data[platform] = []
            platform_data[platform].append(mention)

        # Calculate sentiment for each platform
        platform_sentiment = {}
        for platform, platform_mentions in platform_data.items():
            platform_sentiment[platform] = self._calculate_sentiment_metrics(
                platform_mentions, "platform_analysis"
            )

        return platform_sentiment

    def _analyze_competitor_sentiment(
        self,
        brand_name: str,
        brand_sentiment: SentimentMetrics,
        competitor_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, SentimentMetrics]:
        """Analyze sentiment for competitors and compare with brand."""
        competitor_sentiment = {}

        for competitor, mentions in competitor_data.items():
            competitor_sentiment[competitor] = self._calculate_sentiment_metrics(
                mentions, "competitor_analysis"
            )

        return competitor_sentiment

    def _analyze_sentiment_trends(
        self,
        mentions: List[Dict[str, Any]],
        time_period_days: int
    ) -> Dict[str, Any]:
        """Analyze sentiment trends over time."""
        if not mentions:
            return {
                'trend_direction': TrendDirection.STABLE,
                'sentiment_change': 0.0,
                'volatility': 0.0,
                'daily_breakdown': []
            }

        # Sort mentions by timestamp
        sorted_mentions = sorted(
            mentions,
            key=lambda x: x.get('timestamp', datetime.now()),
            reverse=True
        )

        # Group by day
        daily_sentiment = {}
        for mention in sorted_mentions:
            timestamp = mention.get('timestamp', datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            day_key = timestamp.strftime('%Y-%m-%d')
            if day_key not in daily_sentiment:
                daily_sentiment[day_key] = []
            daily_sentiment[day_key].append(mention)

        # Calculate daily sentiment scores
        daily_scores = []
        for day, day_mentions in daily_sentiment.items():
            day_metrics = self._calculate_sentiment_metrics(day_mentions, "1d")
            daily_scores.append({
                'date': day,
                'sentiment_score': day_metrics.sentiment_score,
                'mention_count': len(day_mentions)
            })

        # Sort by date
        daily_scores.sort(key=lambda x: x['date'])

        # Calculate trend
        if len(daily_scores) >= 2:
            recent_scores = [d['sentiment_score'] for d in daily_scores[-7:]]  # Last 7 days
            older_scores = [d['sentiment_score'] for d in daily_scores[-14:-7]]  # Previous 7 days

            if older_scores:
                recent_avg = np.mean(recent_scores)
                older_avg = np.mean(older_scores)
                sentiment_change = recent_avg - older_avg
            else:
                sentiment_change = 0.0

            # Determine trend direction
            if sentiment_change > 0.1:
                trend_direction = TrendDirection.IMPROVING
            elif sentiment_change < -0.1:
                trend_direction = TrendDirection.DECLINING
            else:
                trend_direction = TrendDirection.STABLE

            # Calculate volatility
            all_scores = [d['sentiment_score'] for d in daily_scores]
            volatility = np.std(all_scores) if len(all_scores) > 1 else 0.0

        else:
            sentiment_change = 0.0
            trend_direction = TrendDirection.STABLE
            volatility = 0.0

        return {
            'trend_direction': trend_direction,
            'sentiment_change': sentiment_change,
            'volatility': volatility,
            'daily_breakdown': daily_scores
        }

    def _calculate_reputation_score(
        self,
        sentiment_metrics: SentimentMetrics,
        trend_analysis: Dict[str, Any],
        competitor_comparison: Dict[str, SentimentMetrics]
    ) -> float:
        """Calculate overall reputation score (0-100)."""
        # Base score from sentiment (40% weight)
        sentiment_component = (sentiment_metrics.sentiment_score + 1) * 50  # Convert -1,1 to 0,100

        # Trend stability component (20% weight)
        trend_component = 50  # Neutral starting point
        if trend_analysis['trend_direction'] == TrendDirection.IMPROVING:
            trend_component = 70
        elif trend_analysis['trend_direction'] == TrendDirection.DECLINING:
            trend_component = 30

        # Volatility penalty
        volatility_penalty = min(20, trend_analysis['volatility'] * 100)
        trend_component -= volatility_penalty

        # Mention volume component (20% weight)
        volume_component = min(100, sentiment_metrics.total_mentions / 10 * 10)  # Scale to 100

        # Competitive position component (20% weight)
        competitive_component = 50  # Neutral if no competitor data
        if competitor_comparison:
            # Calculate relative position
            all_scores = [sentiment_metrics.sentiment_score]
            for comp_metrics in competitor_comparison.values():
                all_scores.append(comp_metrics.sentiment_score)

            sorted_scores = sorted(all_scores, reverse=True)
            rank = sorted_scores.index(sentiment_metrics.sentiment_score) + 1
            total_competitors = len(all_scores)

            # Convert rank to component score
            competitive_component = (total_competitors - rank + 1) / total_competitors * 100

        # Calculate weighted score
        reputation_score = (
            sentiment_component * 0.4 +
            trend_component * 0.2 +
            volume_component * 0.2 +
            competitive_component * 0.2
        )

        return max(0, min(100, reputation_score))

    def _assess_brand_health(
        self,
        sentiment_metrics: SentimentMetrics,
        trend_analysis: Dict[str, Any],
        reputation_score: float
    ) -> BrandHealthStatus:
        """Assess overall brand health status."""
        if reputation_score >= 80:
            return BrandHealthStatus.EXCELLENT
        elif reputation_score >= 65:
            return BrandHealthStatus.GOOD
        elif reputation_score >= 45:
            return BrandHealthStatus.AVERAGE
        elif reputation_score >= 25:
            return BrandHealthStatus.CONCERNING
        else:
            return BrandHealthStatus.CRITICAL

    def _assess_reputation_risks(
        self,
        sentiment_metrics: SentimentMetrics,
        trend_analysis: Dict[str, Any],
        mentions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess reputation risks and crisis indicators."""
        risks = []
        risk_level = ReputationRisk.LOW

        # Check for high negative sentiment
        negative_ratio = sentiment_metrics.negative_mentions / max(1, sentiment_metrics.total_mentions)
        if negative_ratio > 0.7:
            risks.append("High negative sentiment ratio")
            risk_level = ReputationRisk.CRITICAL

        # Check for declining trend
        if trend_analysis['trend_direction'] == TrendDirection.DECLINING:
            risks.append("Declining sentiment trend")
            if risk_level == ReputationRisk.LOW:
                risk_level = ReputationRisk.MEDIUM

        # Check for high volatility
        if trend_analysis['volatility'] > 0.5:
            risks.append("High sentiment volatility")
            if risk_level == ReputationRisk.LOW:
                risk_level = ReputationRisk.MEDIUM

        # Check for crisis keywords in recent mentions
        crisis_keywords = ['crisis', 'scandal', 'lawsuit', 'hack', 'breach', 'failure', 'disaster']
        recent_mentions = mentions[-50:]  # Last 50 mentions

        crisis_mentions = 0
        for mention in recent_mentions:
            content = mention.get('content', '').lower()
            if any(keyword in content for keyword in crisis_keywords):
                crisis_mentions += 1

        if crisis_mentions > 5:
            risks.append("Crisis-related keywords detected in recent mentions")
            risk_level = ReputationRisk.HIGH

        return {
            'risk_level': risk_level,
            'identified_risks': risks,
            'crisis_probability': min(1.0, (negative_ratio + trend_analysis['volatility']) / 2),
            'immediate_attention_required': risk_level in [ReputationRisk.HIGH, ReputationRisk.CRITICAL]
        }

    def _generate_recommendations(
        self,
        sentiment_metrics: SentimentMetrics,
        trend_analysis: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        competitor_comparison: Dict[str, SentimentMetrics]
    ) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Sentiment-based recommendations
        if sentiment_metrics.sentiment_score < -0.2:
            recommendations.append("Develop crisis communication strategy to address negative sentiment")
            recommendations.append("Implement proactive customer outreach to address concerns")

        # Trend-based recommendations
        if trend_analysis['trend_direction'] == TrendDirection.DECLINING:
            recommendations.append("Investigate causes of declining sentiment and implement corrective measures")
            recommendations.append("Increase positive brand messaging and community engagement")

        # Risk-based recommendations
        if risk_assessment['risk_level'] in [ReputationRisk.HIGH, ReputationRisk.CRITICAL]:
            recommendations.append("Activate crisis management protocol immediately")
            recommendations.append("Monitor social media channels 24/7 for emerging issues")

        # Competitive recommendations
        if competitor_comparison:
            # Find best performing competitor
            best_competitor = max(
                competitor_comparison.items(),
                key=lambda x: x[1].sentiment_score
            )

            if best_competitor[1].sentiment_score > sentiment_metrics.sentiment_score:
                recommendations.append(f"Analyze {best_competitor[0]} successful strategies for improvement opportunities")

        # General recommendations
        if sentiment_metrics.total_mentions < 10:
            recommendations.append("Increase brand visibility and engagement to generate more mentions")

        if len(recommendations) == 0:
            recommendations.append("Continue current brand management strategy - metrics look healthy")

        return recommendations

    async def compare_competitor_sentiment(
        self,
        brands: List[str],
        mention_data: Dict[str, List[Dict[str, Any]]]
    ) -> CompetitorSentimentComparison:
        """Compare sentiment across multiple competitors."""
        if not brands or len(brands) < 2:
            raise ValueError("Need at least 2 brands for comparison")

        primary_brand = brands[0]
        competitors = brands[1:]

        # Calculate sentiment for all brands
        brand_sentiment = {}
        for brand in brands:
            if brand in mention_data:
                brand_sentiment[brand] = self._calculate_sentiment_metrics(
                    mention_data[brand], "comparison"
                )

        # Create rankings
        sorted_brands = sorted(
            brand_sentiment.items(),
            key=lambda x: x[1].sentiment_score,
            reverse=True
        )

        sentiment_rankings = {}
        sentiment_gaps = {}
        leader_score = sorted_brands[0][1].sentiment_score if sorted_brands else 0

        for rank, (brand, metrics) in enumerate(sorted_brands, 1):
            sentiment_rankings[brand] = rank
            sentiment_gaps[brand] = leader_score - metrics.sentiment_score

        # Identify advantages and threats
        primary_sentiment = brand_sentiment.get(primary_brand)
        competitive_advantages = []
        competitive_threats = []

        if primary_sentiment:
            primary_rank = sentiment_rankings.get(primary_brand, len(brands))

            if primary_rank == 1:
                competitive_advantages.append("Leading sentiment position in market")
            elif primary_rank <= len(brands) // 2:
                competitive_advantages.append("Above-average sentiment position")
            else:
                competitive_threats.append("Below-average sentiment position")

            # Compare with each competitor
            for competitor in competitors:
                comp_sentiment = brand_sentiment.get(competitor)
                if comp_sentiment:
                    if primary_sentiment.sentiment_score > comp_sentiment.sentiment_score:
                        competitive_advantages.append(f"Higher sentiment than {competitor}")
                    else:
                        competitive_threats.append(f"Lower sentiment than {competitor}")

        return CompetitorSentimentComparison(
            primary_brand=primary_brand,
            competitors=competitors,
            sentiment_rankings=sentiment_rankings,
            sentiment_gaps=sentiment_gaps,
            competitive_advantages=competitive_advantages,
            competitive_threats=competitive_threats
        )


# Factory function for easy integration
def get_business_sentiment_analyzer() -> BusinessSentimentAnalyzer:
    """Get a configured business sentiment analyzer instance."""
    return BusinessSentimentAnalyzer()


# Example usage and demo
if __name__ == "__main__":
    # Example mention data
    example_mentions = [
        {
            'content': 'Love this new product from BrandX! Amazing quality.',
            'platform': 'twitter',
            'timestamp': '2026-01-19T10:00:00Z',
            'keywords': ['product', 'quality']
        },
        {
            'content': 'BrandX customer service was terrible. Very disappointed.',
            'platform': 'reddit',
            'timestamp': '2026-01-19T11:00:00Z',
            'keywords': ['customer service', 'disappointed']
        },
        {
            'content': 'BrandX is okay, nothing special.',
            'platform': 'facebook',
            'timestamp': '2026-01-19T12:00:00Z',
            'keywords': ['okay']
        }
    ]

    async def demo_sentiment_analysis():
        analyzer = get_business_sentiment_analyzer()

        # Analyze brand sentiment
        profile = await analyzer.analyze_brand_sentiment(
            brand_name="BrandX",
            mention_data=example_mentions,
            time_period_days=7
        )

        print(f"Brand: {profile.brand_name}")
        print(f"Overall Sentiment: {profile.overall_sentiment.sentiment_type.value}")
        print(f"Sentiment Score: {profile.overall_sentiment.sentiment_score:.2f}")
        print(f"Reputation Score: {profile.reputation_score:.1f}/100")
        print(f"Brand Health: {profile.brand_health.value}")
        print(f"Risk Level: {profile.risk_assessment['risk_level'].value}")

        print("\nRecommendations:")
        for rec in profile.recommendations:
            print(f"  • {rec}")

    # Run demo
    asyncio.run(demo_sentiment_analysis())