"""
Market Sentiment Radar - Advanced Lead Timing Intelligence
=========================================================

Enhanced sentiment analysis that combines social media, permit data, economic indicators,
and neighborhood intelligence to predict motivated sellers and optimal timing.

Builds on existing sentiment analysis with external data sources for competitive advantage.

Author: Enhanced from research recommendations - January 2026
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.economic_indicators_service import get_economic_indicators_service

# Import after sentiment_types to avoid circular dependency
from ghl_real_estate_ai.services.san_bernardino_county_permits import get_san_bernardino_county_permit_service
from ghl_real_estate_ai.services.sentiment_drift_engine import SentimentDriftEngine
from ghl_real_estate_ai.services.sentiment_types import (
    AlertPriority,
    DataSourceInterface,
    SentimentSignal,
    SentimentTriggerType,
)
from ghl_real_estate_ai.utils.json_utils import safe_json_dumps

logger = get_logger(__name__)


@dataclass
class MarketSentimentProfile:
    """Comprehensive sentiment profile for a geographic area."""

    location: str
    overall_sentiment: float  # Composite sentiment score
    trend_direction: str  # "improving", "stable", "declining"
    velocity: float  # Rate of sentiment change per day

    # Individual signal categories
    social_sentiment: float  # Social media and community discussions
    permit_pressure: float  # Permit delays, denials, disputes
    economic_stress: float  # Tax increases, insurance spikes, HOA issues
    infrastructure_concerns: float  # Traffic, crime, development pressure

    # Predictive signals
    seller_motivation_index: float  # 0-100, probability of motivated sellers emerging
    optimal_outreach_window: str  # "immediate", "1-week", "2-weeks", "month+"

    # Supporting data
    key_signals: List[SentimentSignal]
    confidence_score: float
    last_updated: datetime


@dataclass
class SentimentAlert:
    """Alert for high-priority sentiment changes requiring action."""

    alert_id: str
    priority: AlertPriority
    location: str
    trigger_type: SentimentTriggerType
    message: str
    recommended_action: str
    target_audience: str  # Property owner profile to target
    timing_window: str  # When to act
    expected_lead_quality: float  # 0-100
    generated_at: datetime


class PerplexityMarketNewsSource(DataSourceInterface):
    """Perplexity API-powered local market news and sentiment analysis.

    Queries Perplexity for real-time local market intelligence and parses
    sentiment from the AI-generated response. Falls back to cached results
    when the API is unavailable.
    """

    def __init__(self):
        import os

        self._api_key = os.getenv("PERPLEXITY_API_KEY", "")
        self._api_url = "https://api.perplexity.ai/chat/completions"
        self._cache = get_cache_service()

    async def fetch_sentiment_data(self, location: str, timeframe_days: int = 30) -> List[SentimentSignal]:
        """Query Perplexity for local market sentiment signals."""
        cache_key = f"perplexity_sentiment:{location}:{timeframe_days}"
        cached = await self._cache.get(cache_key)
        if cached:
            return [SentimentSignal(**s) for s in cached]

        if not self._api_key:
            logger.debug("PERPLEXITY_API_KEY not set, skipping Perplexity source")
            return []

        try:
            import aiohttp

            prompt = (
                f"Analyze the current real estate market sentiment in {location} "
                f"over the past {timeframe_days} days. Focus on: "
                f"1) Local economic stress (taxes, insurance, HOA) "
                f"2) Infrastructure and development concerns "
                f"3) Permit activity and neighborhood changes "
                f"4) General buyer/seller confidence. "
                f"For each issue found, rate sentiment from -100 (very negative) to +100 "
                f"(very positive) and assign a confidence 0.0-1.0. "
                f"Return JSON array: "
                f'[{{"category": "economic_stress|infrastructure|permits|confidence", '
                f'"sentiment": <int>, "confidence": <float>, "summary": "<str>"}}]'
            )

            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
                "temperature": 0.1,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._api_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"Perplexity API returned {resp.status}")
                        return []
                    data = await resp.json()

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            signals = self._parse_perplexity_response(content, location)

            # Cache for 2 hours
            await self._cache.set(
                cache_key,
                [
                    {
                        "source": s.source,
                        "signal_type": s.signal_type.value,
                        "location": s.location,
                        "sentiment_score": s.sentiment_score,
                        "confidence": s.confidence,
                        "raw_content": s.raw_content,
                        "detected_at": s.detected_at.isoformat(),
                        "urgency_multiplier": s.urgency_multiplier,
                    }
                    for s in signals
                ],
                ttl=7200,
            )
            logger.info(f"Perplexity returned {len(signals)} signals for {location}")
            return signals

        except Exception as e:
            logger.warning(f"Perplexity API error for {location}: {e}")
            return []

    def _parse_perplexity_response(self, content: str, location: str) -> List[SentimentSignal]:
        """Parse Perplexity JSON response into SentimentSignals."""
        signals = []
        category_map = {
            "economic_stress": SentimentTriggerType.ECONOMIC_STRESS,
            "infrastructure": SentimentTriggerType.INFRASTRUCTURE_CONCERN,
            "permits": SentimentTriggerType.PERMIT_DISRUPTION,
            "confidence": SentimentTriggerType.ECONOMIC_STRESS,
        }

        try:
            # Extract JSON array from response
            start = content.find("[")
            end = content.rfind("]") + 1
            if start < 0 or end <= start:
                return signals
            items = json.loads(content[start:end])
        except (json.JSONDecodeError, ValueError):
            logger.debug("Could not parse Perplexity response as JSON")
            return signals

        for item in items:
            category = item.get("category", "confidence")
            signal_type = category_map.get(category, SentimentTriggerType.ECONOMIC_STRESS)
            sentiment = int(item.get("sentiment", 0))
            confidence = float(item.get("confidence", 0.5))
            summary = item.get("summary", "Market signal detected")

            urgency = 1.0 + abs(sentiment) / 50.0  # Scale urgency with magnitude

            signals.append(
                SentimentSignal(
                    source="perplexity",
                    signal_type=signal_type,
                    location=location,
                    sentiment_score=sentiment,
                    confidence=min(1.0, max(0.0, confidence)),
                    raw_content=summary,
                    detected_at=datetime.now(),
                    urgency_multiplier=urgency,
                )
            )

        return signals


class MarketSentimentRadar:
    """
    Advanced sentiment analysis engine combining multiple data sources
    to identify motivated sellers and optimal outreach timing.

    Features:
    - Multi-source sentiment aggregation
    - Predictive seller motivation scoring
    - Real-time alert generation
    - Geographic sentiment mapping
    - Optimal timing recommendations
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.sentiment_engine = SentimentDriftEngine()  # Existing sentiment service
        self.claude = ClaudeAssistant()

        # Initialize data sources (real Perplexity API + existing real sources)
        self.data_sources: List[DataSourceInterface] = [
            PerplexityMarketNewsSource(),
        ]

        # Configuration
        self.cache_ttl = 3600  # 1 hour cache
        self.alert_thresholds = {
            AlertPriority.CRITICAL: -70,  # Very negative sentiment
            AlertPriority.HIGH: -50,
            AlertPriority.MEDIUM: -30,
            AlertPriority.LOW: -15,
        }

    async def analyze_market_sentiment(self, location: str, timeframe_days: int = 30) -> MarketSentimentProfile:
        """
        Comprehensive sentiment analysis for a geographic location.

        Args:
            location: ZIP code, neighborhood, or address
            timeframe_days: Historical timeframe for analysis

        Returns:
            Complete sentiment profile with scoring and recommendations
        """
        # Check cache first
        cache_key = f"market_sentiment:{location}:{timeframe_days}"
        cached_profile = await self.cache.get(cache_key)
        if cached_profile:
            return MarketSentimentProfile(**json.loads(cached_profile))

        # Collect signals from all data sources
        all_signals = []

        # Get static mock sources
        for source in self.data_sources:
            try:
                signals = await source.fetch_sentiment_data(location, timeframe_days)
                all_signals.extend(signals)
                logger.debug(f"Collected {len(signals)} signals from {source.__class__.__name__}")
            except Exception as e:
                logger.warning(f"Error fetching from {source.__class__.__name__}: {e}")

        # Get real data sources dynamically
        try:
            # San Bernardino County permit data (real data)
            permit_service = await get_san_bernardino_county_permit_service()
            permit_signals = await permit_service.fetch_sentiment_data(location, timeframe_days)
            all_signals.extend(permit_signals)
            logger.info(f"Collected {len(permit_signals)} real permit signals for {location}")
        except Exception as e:
            logger.warning(f"Error fetching real permit data: {e}")

        try:
            # Economic indicators (real data)
            economic_service = await get_economic_indicators_service()
            economic_signals = await economic_service.fetch_sentiment_data(location, timeframe_days)
            all_signals.extend(economic_signals)
            logger.info(f"Collected {len(economic_signals)} real economic signals for {location}")
        except Exception as e:
            logger.warning(f"Error fetching real economic data: {e}")

        # Analyze signals and build profile
        profile = await self._build_sentiment_profile(location, all_signals)

        # Cache result
        await self.cache.set(cache_key, safe_json_dumps(asdict(profile)), ttl=self.cache_ttl)

        return profile

    async def _build_sentiment_profile(self, location: str, signals: List[SentimentSignal]) -> MarketSentimentProfile:
        """Build comprehensive sentiment profile from collected signals."""
        if not signals:
            # Return neutral profile if no signals
            return MarketSentimentProfile(
                location=location,
                overall_sentiment=0.0,
                trend_direction="stable",
                velocity=0.0,
                social_sentiment=0.0,
                permit_pressure=0.0,
                economic_stress=0.0,
                infrastructure_concerns=0.0,
                seller_motivation_index=15.0,  # Baseline motivation
                optimal_outreach_window="month+",
                key_signals=[],
                confidence_score=0.3,
                last_updated=datetime.now(),
            )

        # Categorize signals by type (updated to include real data sources)
        social_signals = [s for s in signals if s.source in ["twitter", "nextdoor", "facebook"]]
        permit_signals = [s for s in signals if s.source in ["permits", "san_bernardino_county_permits"]]
        economic_signals = [
            s
            for s in signals
            if s.source in ["local_news", "economic_indicators"]
            or s.signal_type == SentimentTriggerType.ECONOMIC_STRESS
        ]
        infrastructure_signals = [s for s in signals if s.signal_type == SentimentTriggerType.INFRASTRUCTURE_CONCERN]

        # Calculate category scores
        social_sentiment = self._calculate_category_sentiment(social_signals)
        permit_pressure = abs(
            self._calculate_category_sentiment(permit_signals)
        )  # Absolute value - pressure is always negative
        economic_stress = abs(self._calculate_category_sentiment(economic_signals))
        infrastructure_concerns = abs(self._calculate_category_sentiment(infrastructure_signals))

        # Calculate overall sentiment with weighted averages
        weights = {"social": 0.25, "permit": 0.30, "economic": 0.35, "infrastructure": 0.10}

        overall_sentiment = (
            social_sentiment * weights["social"]
            + permit_pressure * weights["permit"] * -1  # Convert back to negative
            + economic_stress * weights["economic"] * -1
            + infrastructure_concerns * weights["infrastructure"] * -1
        )

        # Calculate trend and velocity
        recent_signals = [s for s in signals if s.detected_at > datetime.now() - timedelta(days=7)]
        older_signals = [s for s in signals if s.detected_at <= datetime.now() - timedelta(days=7)]

        recent_avg = np.mean([s.sentiment_score for s in recent_signals]) if recent_signals else 0
        older_avg = np.mean([s.sentiment_score for s in older_signals]) if older_signals else 0

        velocity = (recent_avg - older_avg) / 7  # Change per day

        if velocity < -2:
            trend_direction = "declining"
        elif velocity > 2:
            trend_direction = "improving"
        else:
            trend_direction = "stable"

        # Calculate seller motivation index
        seller_motivation_index = self._calculate_seller_motivation(
            overall_sentiment, permit_pressure, economic_stress, infrastructure_concerns, velocity
        )

        # Determine optimal outreach window
        optimal_window = self._calculate_optimal_window(seller_motivation_index, velocity, signals)

        # Filter top signals for insights
        key_signals = sorted(signals, key=lambda s: abs(s.sentiment_score) * s.confidence, reverse=True)[:5]

        # Calculate confidence based on signal quality and quantity
        confidence_score = min(1.0, (len(signals) / 20) * np.mean([s.confidence for s in signals]))

        return MarketSentimentProfile(
            location=location,
            overall_sentiment=overall_sentiment,
            trend_direction=trend_direction,
            velocity=velocity,
            social_sentiment=social_sentiment,
            permit_pressure=permit_pressure,
            economic_stress=economic_stress,
            infrastructure_concerns=infrastructure_concerns,
            seller_motivation_index=seller_motivation_index,
            optimal_outreach_window=optimal_window,
            key_signals=key_signals,
            confidence_score=confidence_score,
            last_updated=datetime.now(),
        )

    def _calculate_category_sentiment(self, signals: List[SentimentSignal]) -> float:
        """Calculate weighted average sentiment for a category."""
        if not signals:
            return 0.0

        # Weight by confidence and urgency
        weighted_scores = []
        weights = []

        for signal in signals:
            weight = signal.confidence * signal.urgency_multiplier
            weighted_scores.append(signal.sentiment_score * weight)
            weights.append(weight)

        if sum(weights) == 0:
            return 0.0

        return sum(weighted_scores) / sum(weights)

    def _calculate_seller_motivation(
        self,
        overall_sentiment: float,
        permit_pressure: float,
        economic_stress: float,
        infrastructure_concerns: float,
        velocity: float,
    ) -> float:
        """Calculate probability of motivated sellers emerging (0-100)."""

        # Base motivation from negative sentiment
        base_motivation = max(0, -overall_sentiment * 0.8)  # Convert negative to positive motivation

        # Additional motivation from specific factors
        permit_motivation = permit_pressure * 0.6  # Permit issues create urgency
        economic_motivation = economic_stress * 0.9  # Financial pressure strongest motivator
        infrastructure_motivation = infrastructure_concerns * 0.4  # Infrastructure issues moderate motivator

        # Velocity bonus - rapid changes create urgency
        velocity_bonus = max(0, -velocity * 5)  # Negative velocity (declining sentiment) increases motivation

        total_motivation = (
            base_motivation + permit_motivation + economic_motivation + infrastructure_motivation + velocity_bonus
        )

        # Baseline motivation (even in neutral areas, some people always want to sell)
        baseline = 15

        return min(95, baseline + total_motivation)

    def _calculate_optimal_window(
        self, motivation_index: float, velocity: float, signals: List[SentimentSignal]
    ) -> str:
        """Determine optimal timing for outreach."""

        # Immediate action for critical situations
        critical_signals = [s for s in signals if s.urgency_multiplier > 3.0]
        if critical_signals and motivation_index > 70:
            return "immediate"

        # Short-term for high motivation
        if motivation_index > 60 or velocity < -3:
            return "1-week"
        elif motivation_index > 40:
            return "2-weeks"
        else:
            return "month+"

    async def generate_sentiment_alerts(self, locations: List[str]) -> List[SentimentAlert]:
        """Generate prioritized alerts for multiple locations."""
        alerts = []

        for location in locations:
            try:
                profile = await self.analyze_market_sentiment(location)

                # Check if alert thresholds are met
                alert_priority = self._determine_alert_priority(profile)

                if alert_priority:
                    alert = await self._create_sentiment_alert(location, profile, alert_priority)
                    alerts.append(alert)

            except Exception as e:
                logger.error(f"Error generating alert for {location}: {e}")

        # Sort by priority and motivation index
        priority_order = {
            AlertPriority.CRITICAL: 4,
            AlertPriority.HIGH: 3,
            AlertPriority.MEDIUM: 2,
            AlertPriority.LOW: 1,
        }
        alerts.sort(key=lambda a: (priority_order[a.priority], a.expected_lead_quality), reverse=True)

        return alerts

    def _determine_alert_priority(self, profile: MarketSentimentProfile) -> Optional[AlertPriority]:
        """Determine if profile warrants an alert and at what priority."""

        if profile.seller_motivation_index > 80 and profile.velocity < -3:
            return AlertPriority.CRITICAL
        elif profile.seller_motivation_index > 65:
            return AlertPriority.HIGH
        elif profile.seller_motivation_index > 45:
            return AlertPriority.MEDIUM
        elif profile.seller_motivation_index > 30 and profile.trend_direction == "declining":
            return AlertPriority.LOW

        return None

    async def _create_sentiment_alert(
        self, location: str, profile: MarketSentimentProfile, priority: AlertPriority
    ) -> SentimentAlert:
        """Create detailed sentiment alert with AI-generated recommendations."""

        # Analyze key triggers
        main_triggers = {}
        for signal in profile.key_signals[:3]:
            trigger_type = signal.signal_type.value
            if trigger_type not in main_triggers:
                main_triggers[trigger_type] = []
            main_triggers[trigger_type].append(signal)

        primary_trigger = (
            max(main_triggers.keys(), key=lambda k: len(main_triggers[k])) if main_triggers else "general_sentiment"
        )

        # Generate AI-powered message and recommendations
        prompt = f"""
        Analyze this market sentiment data for {location} and create a concise alert:

        Seller Motivation Index: {profile.seller_motivation_index:.1f}/100
        Overall Sentiment: {profile.overall_sentiment:.1f}
        Trend: {profile.trend_direction} (velocity: {profile.velocity:.1f}/day)

        Key Issues:
        - Economic Stress: {profile.economic_stress:.1f}
        - Permit Pressure: {profile.permit_pressure:.1f}
        - Infrastructure Concerns: {profile.infrastructure_concerns:.1f}

        Top Signals:
        {chr(10).join([f"- {s.source}: {s.raw_content}" for s in profile.key_signals[:3]])}

        Create a one-sentence alert message and recommend specific outreach strategy.
        Focus on actionable intelligence for a real estate agent.
        """

        try:
            ai_response = await self.claude.process_message(prompt)
            message = ai_response.get("content", f"High seller motivation detected in {location}")

            # Extract recommendation (simple parsing)
            lines = message.split("\n")
            alert_message = lines[0] if lines else message
            recommendation = lines[1] if len(lines) > 1 else "Contact property owners with market intelligence"

        except Exception as e:
            logger.warning(f"Error generating AI alert: {e}")
            alert_message = f"{primary_trigger.replace('_', ' ').title()} detected in {location} - seller motivation at {profile.seller_motivation_index:.0f}/100"
            recommendation = "Target property owners with market timing consultation"

        # Generate target audience profile
        target_audience = self._generate_target_audience(primary_trigger, profile)

        return SentimentAlert(
            alert_id=f"alert_{location}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            priority=priority,
            location=location,
            trigger_type=SentimentTriggerType(primary_trigger),
            message=alert_message,
            recommended_action=recommendation,
            target_audience=target_audience,
            timing_window=profile.optimal_outreach_window,
            expected_lead_quality=min(100, profile.seller_motivation_index * 1.1),
            generated_at=datetime.now(),
        )

    def _generate_target_audience(self, trigger_type: str, profile: MarketSentimentProfile) -> str:
        """Generate target audience description based on sentiment triggers."""

        if trigger_type == "economic_stress":
            return "Property owners facing increased carrying costs (taxes, HOA, insurance)"
        elif trigger_type == "permit_disruption":
            return "Long-term residents concerned about neighborhood development changes"
        elif trigger_type == "infrastructure_concern":
            return "Commuters and families affected by traffic/infrastructure issues"
        elif trigger_type == "investment_pressure":
            return "Investment property owners considering portfolio optimization"
        else:
            return "Property owners in area experiencing market uncertainty"

    async def get_location_recommendations(
        self, agent_territory: List[str], max_locations: int = 10
    ) -> List[Dict[str, Any]]:
        """Get prioritized location recommendations for prospecting."""

        location_scores = []

        for location in agent_territory:
            try:
                profile = await self.analyze_market_sentiment(location)

                # Calculate prospecting score
                prospecting_score = (
                    profile.seller_motivation_index * 0.6
                    + min(50, abs(profile.velocity) * 10) * 0.3  # Velocity indicates change/urgency
                    + profile.confidence_score * 50 * 0.1
                )

                location_scores.append(
                    {
                        "location": location,
                        "prospecting_score": prospecting_score,
                        "motivation_index": profile.seller_motivation_index,
                        "trend": profile.trend_direction,
                        "optimal_window": profile.optimal_outreach_window,
                        "key_triggers": [s.signal_type.value for s in profile.key_signals[:2]],
                        "confidence": profile.confidence_score,
                    }
                )

            except Exception as e:
                logger.error(f"Error analyzing {location}: {e}")

        # Sort by prospecting score and return top locations
        location_scores.sort(key=lambda x: x["prospecting_score"], reverse=True)
        return location_scores[:max_locations]


# Singleton instance
_sentiment_radar = None


async def get_market_sentiment_radar() -> MarketSentimentRadar:
    """Get singleton market sentiment radar instance."""
    global _sentiment_radar
    if _sentiment_radar is None:
        _sentiment_radar = MarketSentimentRadar()
    return _sentiment_radar
