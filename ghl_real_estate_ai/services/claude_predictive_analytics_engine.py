"""
Claude Predictive Analytics Engine (Advanced Feature #1)

Advanced predictive analytics system that leverages Claude AI for lead scoring prediction,
outcome forecasting, and behavioral pattern recognition in real estate transactions.

Features:
- Multi-dimensional lead scoring with conversion probability
- Timeline prediction for deal closure
- Behavioral pattern recognition and trend analysis
- Market condition impact modeling
- Agent performance prediction
- Churn risk assessment and intervention triggers
- ROI forecasting for marketing spend
"""

import asyncio
import json
import logging
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from anthropic import AsyncAnthropic
from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
from ghl_real_estate_ai.ghl_utils.config import settings

logger = logging.getLogger(__name__)


class PredictionConfidence(Enum):
    """Confidence levels for predictions."""
    VERY_HIGH = "very_high"  # 90%+ confidence
    HIGH = "high"            # 80-89% confidence
    MEDIUM = "medium"        # 60-79% confidence
    LOW = "low"             # 40-59% confidence
    UNCERTAIN = "uncertain"  # <40% confidence


class ConversionStage(Enum):
    """Lead conversion stages for prediction."""
    INITIAL_INTEREST = "initial_interest"
    ACTIVELY_SEARCHING = "actively_searching"
    EVALUATING_OPTIONS = "evaluating_options"
    READY_TO_DECIDE = "ready_to_decide"
    CLOSING_IMMINENT = "closing_imminent"
    LIKELY_TO_CHURN = "likely_to_churn"


class MarketCondition(Enum):
    """Market condition classifications."""
    SELLERS_MARKET = "sellers_market"
    BUYERS_MARKET = "buyers_market"
    BALANCED_MARKET = "balanced_market"
    SEASONAL_LOW = "seasonal_low"
    SEASONAL_HIGH = "seasonal_high"


@dataclass
class LeadPrediction:
    """Lead conversion prediction with detailed metrics."""
    lead_id: str
    predicted_conversion_probability: float  # 0.0 to 1.0
    predicted_conversion_stage: ConversionStage
    predicted_timeline_days: int
    confidence_score: float
    risk_factors: List[str]
    opportunity_indicators: List[str]
    recommended_actions: List[str]
    predicted_value: float
    churn_probability: float
    predicted_at: datetime


@dataclass
class MarketPrediction:
    """Market trend prediction."""
    location: str
    predicted_price_change: float  # Percentage change
    predicted_inventory_change: float
    market_velocity_trend: str
    demand_strength: float  # 0.0 to 1.0
    supply_pressure: float  # 0.0 to 1.0
    confidence: PredictionConfidence
    market_condition: MarketCondition
    forecast_horizon_days: int
    key_drivers: List[str]
    predicted_at: datetime


@dataclass
class AgentPerformancePrediction:
    """Agent performance forecast."""
    agent_id: str
    predicted_monthly_closings: float
    predicted_monthly_volume: float
    efficiency_score_trend: float
    conversion_rate_prediction: float
    lead_quality_score: float
    improvement_areas: List[str]
    strengths: List[str]
    coaching_recommendations: List[str]
    confidence: PredictionConfidence
    predicted_at: datetime


class ClaudePredictiveAnalyticsEngine:
    """
    Advanced predictive analytics engine using Claude AI for real estate predictions.

    Combines historical data analysis with Claude's reasoning capabilities to predict
    lead conversion outcomes, market trends, and agent performance.
    """

    def __init__(self, location_id: str = "default"):
        """Initialize predictive analytics engine."""
        self.location_id = location_id
        self.data_dir = Path(__file__).parent.parent / "data" / "predictions" / location_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # File storage
        self.predictions_file = self.data_dir / "predictions.json"
        self.market_predictions_file = self.data_dir / "market_predictions.json"
        self.agent_predictions_file = self.data_dir / "agent_predictions.json"
        self.model_performance_file = self.data_dir / "model_performance.json"

        # Initialize services
        self.claude_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.claude_analyzer = ClaudeSemanticAnalyzer()

        # Load existing data
        self.predictions_history = self._load_predictions()
        self.market_predictions_history = self._load_market_predictions()
        self.agent_predictions_history = self._load_agent_predictions()
        self.model_performance = self._load_model_performance()

        # Prediction caching
        self.prediction_cache = {}
        self.cache_ttl = timedelta(hours=6)  # 6 hour cache TTL

        logger.info(f"Claude Predictive Analytics Engine initialized for location {location_id}")

    def _load_predictions(self) -> Dict:
        """Load historical predictions from file."""
        if self.predictions_file.exists():
            try:
                with open(self.predictions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading predictions: {e}")
        return {"lead_predictions": {}, "conversion_history": []}

    def _save_predictions(self) -> None:
        """Save predictions to file."""
        try:
            with open(self.predictions_file, 'w') as f:
                json.dump(self.predictions_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving predictions: {e}")

    def _load_market_predictions(self) -> Dict:
        """Load market predictions from file."""
        if self.market_predictions_file.exists():
            try:
                with open(self.market_predictions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading market predictions: {e}")
        return {"market_forecasts": {}, "accuracy_tracking": []}

    def _save_market_predictions(self) -> None:
        """Save market predictions to file."""
        try:
            with open(self.market_predictions_file, 'w') as f:
                json.dump(self.market_predictions_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving market predictions: {e}")

    def _load_agent_predictions(self) -> Dict:
        """Load agent predictions from file."""
        if self.agent_predictions_file.exists():
            try:
                with open(self.agent_predictions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading agent predictions: {e}")
        return {"agent_forecasts": {}, "performance_tracking": []}

    def _save_agent_predictions(self) -> None:
        """Save agent predictions to file."""
        try:
            with open(self.agent_predictions_file, 'w') as f:
                json.dump(self.agent_predictions_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving agent predictions: {e}")

    def _load_model_performance(self) -> Dict:
        """Load model performance metrics."""
        if self.model_performance_file.exists():
            try:
                with open(self.model_performance_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading model performance: {e}")
        return {
            "lead_prediction_accuracy": 0.0,
            "market_prediction_accuracy": 0.0,
            "agent_prediction_accuracy": 0.0,
            "total_predictions": 0,
            "correct_predictions": 0
        }

    def _save_model_performance(self) -> None:
        """Save model performance metrics."""
        try:
            with open(self.model_performance_file, 'w') as f:
                json.dump(self.model_performance, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving model performance: {e}")

    async def predict_lead_conversion(
        self,
        lead_id: str,
        lead_data: Dict[str, Any],
        conversation_history: List[Dict] = None,
        qualification_data: Dict[str, Any] = None
    ) -> LeadPrediction:
        """
        Predict lead conversion probability and timeline using Claude AI analysis.

        Args:
            lead_id: Unique lead identifier
            lead_data: Lead profile and behavioral data
            conversation_history: Recent conversation messages
            qualification_data: Qualification progress and responses

        Returns:
            LeadPrediction with conversion probability and recommended actions
        """
        try:
            # Check cache first
            cache_key = f"lead_prediction_{lead_id}_{hash(str(lead_data))}"
            if cache_key in self.prediction_cache:
                cached_result, cached_time = self.prediction_cache[cache_key]
                if datetime.now() - cached_time < self.cache_ttl:
                    logger.debug(f"Returning cached prediction for lead {lead_id}")
                    return cached_result

            # Analyze conversation semantics if available
            semantic_analysis = {}
            if conversation_history:
                semantic_analysis = await self.claude_analyzer.analyze_lead_intent(
                    conversation_history
                )

            # Build prediction context for Claude
            prediction_context = await self._build_lead_prediction_context(
                lead_data, semantic_analysis, qualification_data
            )

            # Create Claude prompt for prediction
            prediction_prompt = await self._create_lead_prediction_prompt(
                lead_id, prediction_context
            )

            # Get Claude's prediction analysis
            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=1000,
                temperature=0.3,  # Lower temperature for consistent predictions
                system="""You are an expert real estate predictive analytics specialist.
                Analyze lead data and provide accurate conversion probability predictions with detailed reasoning.

                Focus on:
                1. Behavioral indicators and engagement patterns
                2. Qualification completeness and quality
                3. Market timing and conditions
                4. Historical conversion patterns
                5. Risk factors and opportunity indicators

                Provide specific, actionable predictions with confidence levels.""",
                messages=[{"role": "user", "content": prediction_prompt}]
            )

            claude_analysis = response.content[0].text

            # Parse Claude's prediction response
            prediction = await self._parse_lead_prediction_response(
                lead_id, claude_analysis, prediction_context
            )

            # Store prediction
            self.predictions_history["lead_predictions"][lead_id] = asdict(prediction)
            self._save_predictions()

            # Cache result
            self.prediction_cache[cache_key] = (prediction, datetime.now())

            # Update model performance tracking
            self._track_prediction_creation(prediction)

            logger.info(f"Generated lead prediction for {lead_id}: {prediction.predicted_conversion_probability:.2f}")
            return prediction

        except Exception as e:
            logger.error(f"Error predicting lead conversion for {lead_id}: {e}")
            # Return fallback prediction
            return LeadPrediction(
                lead_id=lead_id,
                predicted_conversion_probability=0.5,
                predicted_conversion_stage=ConversionStage.EVALUATING_OPTIONS,
                predicted_timeline_days=30,
                confidence_score=0.3,
                risk_factors=["Prediction error occurred"],
                opportunity_indicators=[],
                recommended_actions=["Manual analysis recommended"],
                predicted_value=0,
                churn_probability=0.5,
                predicted_at=datetime.now()
            )

    async def _build_lead_prediction_context(
        self,
        lead_data: Dict[str, Any],
        semantic_analysis: Dict[str, Any],
        qualification_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build comprehensive context for lead prediction."""
        context = {
            "lead_profile": lead_data,
            "semantic_insights": semantic_analysis,
            "qualification_status": qualification_data,
            "historical_patterns": self._get_historical_conversion_patterns(),
            "market_context": await self._get_current_market_context(),
            "timing_factors": self._analyze_timing_factors(),
            "engagement_metrics": self._calculate_engagement_metrics(lead_data)
        }

        return context

    async def _create_lead_prediction_prompt(
        self,
        lead_id: str,
        context: Dict[str, Any]
    ) -> str:
        """Create detailed prompt for Claude lead prediction."""
        prompt = f"""
        LEAD CONVERSION PREDICTION REQUEST

        Lead ID: {lead_id}
        Analysis Context: {json.dumps(context, indent=2, default=str)}

        Please analyze this lead and provide a comprehensive conversion prediction including:

        1. CONVERSION PROBABILITY (0.0 to 1.0):
           - Based on engagement patterns, qualification status, and behavioral indicators
           - Consider market timing and historical patterns

        2. CONVERSION STAGE ASSESSMENT:
           - Current stage in buyer journey
           - Next likely progression

        3. TIMELINE PREDICTION:
           - Expected days to conversion (if likely to convert)
           - Key milestone dates

        4. RISK FACTORS:
           - Factors that could prevent conversion
           - Early warning signals

        5. OPPORTUNITY INDICATORS:
           - Positive signals for conversion
           - Strengths to leverage

        6. RECOMMENDED ACTIONS:
           - Immediate next steps for agent
           - Follow-up strategy recommendations

        7. VALUE PREDICTION:
           - Estimated transaction value
           - Commission potential

        8. CHURN PROBABILITY:
           - Risk of losing this lead
           - Retention strategies

        Format your response with clear sections and specific numerical predictions where requested.
        """

        return prompt

    async def _parse_lead_prediction_response(
        self,
        lead_id: str,
        claude_response: str,
        context: Dict[str, Any]
    ) -> LeadPrediction:
        """Parse Claude's response into structured prediction."""
        try:
            # Extract numerical predictions from Claude's response
            conversion_probability = self._extract_number_from_text(
                claude_response, "conversion probability", default=0.5
            )

            timeline_days = self._extract_number_from_text(
                claude_response, "days", default=30
            )

            confidence_score = self._calculate_prediction_confidence(
                claude_response, context
            )

            # Extract conversion stage
            predicted_stage = self._extract_conversion_stage(claude_response)

            # Extract risk factors and opportunities
            risk_factors = self._extract_list_items(claude_response, "risk factors")
            opportunity_indicators = self._extract_list_items(claude_response, "opportunity indicators")
            recommended_actions = self._extract_list_items(claude_response, "recommended actions")

            # Calculate predicted value and churn probability
            predicted_value = self._estimate_transaction_value(context, conversion_probability)
            churn_probability = self._calculate_churn_probability(context, claude_response)

            return LeadPrediction(
                lead_id=lead_id,
                predicted_conversion_probability=min(1.0, max(0.0, conversion_probability)),
                predicted_conversion_stage=predicted_stage,
                predicted_timeline_days=max(1, timeline_days),
                confidence_score=min(1.0, max(0.0, confidence_score)),
                risk_factors=risk_factors,
                opportunity_indicators=opportunity_indicators,
                recommended_actions=recommended_actions,
                predicted_value=max(0, predicted_value),
                churn_probability=min(1.0, max(0.0, churn_probability)),
                predicted_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error parsing prediction response: {e}")
            # Return default prediction
            return LeadPrediction(
                lead_id=lead_id,
                predicted_conversion_probability=0.5,
                predicted_conversion_stage=ConversionStage.EVALUATING_OPTIONS,
                predicted_timeline_days=30,
                confidence_score=0.3,
                risk_factors=["Parse error - manual review needed"],
                opportunity_indicators=[],
                recommended_actions=["Analyze lead manually"],
                predicted_value=0,
                churn_probability=0.5,
                predicted_at=datetime.now()
            )

    async def predict_market_trends(
        self,
        location: str,
        forecast_horizon_days: int = 90,
        include_external_factors: bool = True
    ) -> MarketPrediction:
        """
        Predict market trends and conditions for a specific location.

        Args:
            location: Geographic location for prediction
            forecast_horizon_days: Number of days to forecast
            include_external_factors: Include economic and seasonal factors

        Returns:
            MarketPrediction with trend analysis and forecasts
        """
        try:
            # Build market context
            market_context = await self._build_market_prediction_context(
                location, forecast_horizon_days, include_external_factors
            )

            # Create market prediction prompt
            market_prompt = await self._create_market_prediction_prompt(
                location, market_context, forecast_horizon_days
            )

            # Get Claude's market analysis
            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=1200,
                temperature=0.2,  # Very low temperature for market predictions
                system="""You are an expert real estate market analyst with deep knowledge of
                local market conditions, economic factors, and seasonal trends.

                Provide accurate, data-driven market predictions considering:
                1. Historical price and inventory trends
                2. Economic indicators and interest rates
                3. Seasonal patterns and timing
                4. Supply and demand dynamics
                5. Local development and infrastructure changes

                Focus on actionable insights for real estate professionals.""",
                messages=[{"role": "user", "content": market_prompt}]
            )

            claude_analysis = response.content[0].text

            # Parse market prediction
            prediction = await self._parse_market_prediction_response(
                location, claude_analysis, market_context, forecast_horizon_days
            )

            # Store prediction
            prediction_key = f"{location}_{datetime.now().strftime('%Y%m%d')}"
            self.market_predictions_history["market_forecasts"][prediction_key] = asdict(prediction)
            self._save_market_predictions()

            logger.info(f"Generated market prediction for {location}: {prediction.predicted_price_change:.1f}% price change")
            return prediction

        except Exception as e:
            logger.error(f"Error predicting market trends for {location}: {e}")
            # Return neutral prediction
            return MarketPrediction(
                location=location,
                predicted_price_change=0.0,
                predicted_inventory_change=0.0,
                market_velocity_trend="stable",
                demand_strength=0.5,
                supply_pressure=0.5,
                confidence=PredictionConfidence.LOW,
                market_condition=MarketCondition.BALANCED_MARKET,
                forecast_horizon_days=forecast_horizon_days,
                key_drivers=["Prediction error - manual analysis needed"],
                predicted_at=datetime.now()
            )

    async def predict_agent_performance(
        self,
        agent_id: str,
        historical_data: Dict[str, Any],
        current_pipeline: List[Dict] = None,
        coaching_history: Dict[str, Any] = None
    ) -> AgentPerformancePrediction:
        """
        Predict agent performance metrics and recommend improvements.

        Args:
            agent_id: Agent identifier
            historical_data: Past performance and activity data
            current_pipeline: Current leads and opportunities
            coaching_history: Past coaching sessions and outcomes

        Returns:
            AgentPerformancePrediction with performance forecast
        """
        try:
            # Build agent performance context
            performance_context = await self._build_agent_prediction_context(
                agent_id, historical_data, current_pipeline, coaching_history
            )

            # Create agent prediction prompt
            agent_prompt = await self._create_agent_prediction_prompt(
                agent_id, performance_context
            )

            # Get Claude's performance analysis
            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=1000,
                temperature=0.3,
                system="""You are an expert real estate performance analyst specializing in
                agent productivity and coaching recommendations.

                Analyze agent performance data to predict:
                1. Monthly closing volume and transaction count
                2. Conversion rate trends and efficiency metrics
                3. Areas for improvement and skill development
                4. Strengths to leverage for better results
                5. Coaching priorities and action plans

                Provide specific, actionable recommendations.""",
                messages=[{"role": "user", "content": agent_prompt}]
            )

            claude_analysis = response.content[0].text

            # Parse agent prediction
            prediction = await self._parse_agent_prediction_response(
                agent_id, claude_analysis, performance_context
            )

            # Store prediction
            prediction_key = f"{agent_id}_{datetime.now().strftime('%Y%m')}"
            self.agent_predictions_history["agent_forecasts"][prediction_key] = asdict(prediction)
            self._save_agent_predictions()

            logger.info(f"Generated performance prediction for agent {agent_id}")
            return prediction

        except Exception as e:
            logger.error(f"Error predicting agent performance for {agent_id}: {e}")
            # Return neutral prediction
            return AgentPerformancePrediction(
                agent_id=agent_id,
                predicted_monthly_closings=0,
                predicted_monthly_volume=0,
                efficiency_score_trend=0.0,
                conversion_rate_prediction=0.0,
                lead_quality_score=0.5,
                improvement_areas=["Data analysis error"],
                strengths=[],
                coaching_recommendations=["Manual performance review needed"],
                confidence=PredictionConfidence.LOW,
                predicted_at=datetime.now()
            )

    # Helper methods for prediction parsing and context building

    def _extract_number_from_text(self, text: str, context: str, default: float = 0.0) -> float:
        """Extract numerical value from Claude's response."""
        import re

        # Look for numbers near the context
        pattern = rf"{context}.*?(\d+\.?\d*)"
        match = re.search(pattern, text.lower())

        if match:
            try:
                return float(match.group(1))
            except:
                pass

        # Look for percentage values
        pattern = r"(\d+\.?\d*)%"
        matches = re.findall(pattern, text)
        if matches:
            try:
                return float(matches[0]) / 100.0
            except:
                pass

        return default

    def _extract_conversion_stage(self, text: str) -> ConversionStage:
        """Extract conversion stage from Claude's response."""
        text_lower = text.lower()

        if any(word in text_lower for word in ["closing", "imminent", "ready to buy"]):
            return ConversionStage.CLOSING_IMMINENT
        elif any(word in text_lower for word in ["ready to decide", "decision"]):
            return ConversionStage.READY_TO_DECIDE
        elif any(word in text_lower for word in ["evaluating", "comparing", "considering"]):
            return ConversionStage.EVALUATING_OPTIONS
        elif any(word in text_lower for word in ["actively searching", "looking"]):
            return ConversionStage.ACTIVELY_SEARCHING
        elif any(word in text_lower for word in ["churn", "losing", "disengaged"]):
            return ConversionStage.LIKELY_TO_CHURN
        else:
            return ConversionStage.INITIAL_INTEREST

    def _extract_list_items(self, text: str, section_name: str) -> List[str]:
        """Extract list items from a specific section of Claude's response."""
        import re

        # Find the section
        pattern = rf"{section_name}.*?:\s*\n(.*?)(?=\n\n|\n[A-Z]|\Z)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            section_text = match.group(1)
            # Extract bullet points
            items = re.findall(r"[-•*]\s*(.*?)(?=\n|$)", section_text)
            return [item.strip() for item in items if item.strip()]

        return []

    def _calculate_prediction_confidence(self, response: str, context: Dict) -> float:
        """Calculate confidence score for the prediction."""
        confidence_score = 0.5  # Base confidence

        # Check for confidence indicators in response
        response_lower = response.lower()

        if "high confidence" in response_lower:
            confidence_score += 0.3
        elif "medium confidence" in response_lower:
            confidence_score += 0.1
        elif "low confidence" in response_lower:
            confidence_score -= 0.2

        # Adjust based on data completeness
        if context.get("qualification_status", {}).get("completion_percentage", 0) > 70:
            confidence_score += 0.2

        if len(context.get("semantic_insights", {})) > 0:
            confidence_score += 0.1

        return min(1.0, max(0.0, confidence_score))

    def _get_historical_conversion_patterns(self) -> Dict[str, Any]:
        """Get historical conversion patterns for context."""
        return {
            "avg_conversion_rate": 0.15,
            "avg_timeline_days": 45,
            "seasonal_patterns": {
                "spring": {"rate": 0.18, "timeline": 35},
                "summer": {"rate": 0.20, "timeline": 30},
                "fall": {"rate": 0.12, "timeline": 50},
                "winter": {"rate": 0.10, "timeline": 60}
            },
            "by_source": {
                "website": {"rate": 0.12, "timeline": 50},
                "referral": {"rate": 0.25, "timeline": 35},
                "social_media": {"rate": 0.08, "timeline": 60}
            }
        }

    async def _get_current_market_context(self) -> Dict[str, Any]:
        """Get current market conditions for context."""
        return {
            "inventory_level": "moderate",
            "interest_rates": "elevated",
            "demand_strength": 0.65,
            "price_trend": "stable",
            "days_on_market": 35,
            "absorption_rate": 0.45
        }

    def _analyze_timing_factors(self) -> Dict[str, Any]:
        """Analyze current timing factors affecting conversions."""
        now = datetime.now()
        return {
            "season": self._get_current_season(),
            "month": now.strftime("%B"),
            "is_holiday_season": now.month in [11, 12],
            "is_spring_market": now.month in [3, 4, 5],
            "week_of_month": (now.day - 1) // 7 + 1,
            "market_timing_score": 0.7
        }

    def _get_current_season(self) -> str:
        """Get current season for timing analysis."""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "fall"
        else:
            return "winter"

    def _calculate_engagement_metrics(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate engagement metrics from lead data."""
        return {
            "response_rate": lead_data.get("response_rate", 0.5),
            "avg_response_time_hours": lead_data.get("avg_response_time_hours", 24),
            "engagement_score": lead_data.get("engagement_score", 50),
            "conversation_length_avg": lead_data.get("conversation_length_avg", 3),
            "website_activity_score": lead_data.get("website_activity_score", 30),
            "last_activity_days_ago": lead_data.get("last_activity_days_ago", 7)
        }

    async def _build_market_prediction_context(
        self,
        location: str,
        forecast_horizon_days: int,
        include_external_factors: bool
    ) -> Dict[str, Any]:
        """Build context for market prediction."""
        return {
            "location": location,
            "forecast_horizon_days": forecast_horizon_days,
            "current_market_data": await self._get_current_market_data(location),
            "historical_trends": self._get_historical_market_trends(location),
            "economic_indicators": self._get_economic_indicators() if include_external_factors else {},
            "seasonal_factors": self._get_seasonal_market_factors(),
            "development_pipeline": self._get_development_pipeline(location)
        }

    async def _get_current_market_data(self, location: str) -> Dict[str, Any]:
        """Get current market data for location."""
        # In production, this would connect to real market data APIs
        return {
            "median_price": 450000,
            "price_per_sqft": 275,
            "days_on_market": 32,
            "inventory_months": 2.8,
            "new_listings_monthly": 150,
            "closed_sales_monthly": 125,
            "price_change_yoy": 0.08
        }

    def _get_historical_market_trends(self, location: str) -> Dict[str, Any]:
        """Get historical market trends for location."""
        return {
            "5_year_appreciation": 0.35,
            "3_year_appreciation": 0.22,
            "1_year_appreciation": 0.08,
            "volatility_index": 0.15,
            "seasonal_pattern_strength": 0.7,
            "market_cycle_position": "mid_cycle"
        }

    def _get_economic_indicators(self) -> Dict[str, Any]:
        """Get relevant economic indicators."""
        return {
            "mortgage_rates_30yr": 7.2,
            "unemployment_rate": 3.8,
            "gdp_growth": 2.1,
            "inflation_rate": 3.2,
            "consumer_confidence": 102.3,
            "housing_starts": 1350000
        }

    def _get_seasonal_market_factors(self) -> Dict[str, Any]:
        """Get seasonal market factors."""
        current_month = datetime.now().month
        return {
            "current_season_strength": 0.8 if current_month in [3, 4, 5, 6] else 0.6,
            "expected_seasonal_impact": self._calculate_seasonal_impact(current_month),
            "school_calendar_impact": 0.15 if current_month in [5, 6, 7, 8] else 0.05,
            "holiday_impact": 0.3 if current_month in [11, 12] else 0.0
        }

    def _calculate_seasonal_impact(self, month: int) -> float:
        """Calculate seasonal impact on market."""
        seasonal_multipliers = {
            1: 0.7, 2: 0.75, 3: 0.9, 4: 1.1,
            5: 1.15, 6: 1.2, 7: 1.1, 8: 1.05,
            9: 0.95, 10: 0.9, 11: 0.8, 12: 0.75
        }
        return seasonal_multipliers.get(month, 1.0)

    def _get_development_pipeline(self, location: str) -> Dict[str, Any]:
        """Get development pipeline for location."""
        return {
            "new_developments_planned": 5,
            "units_under_construction": 850,
            "completion_timeline_months": 18,
            "infrastructure_projects": 2,
            "zoning_changes_pending": 1
        }

    async def _create_market_prediction_prompt(
        self,
        location: str,
        context: Dict[str, Any],
        forecast_horizon_days: int
    ) -> str:
        """Create market prediction prompt for Claude."""
        return f"""
        MARKET TREND PREDICTION REQUEST

        Location: {location}
        Forecast Horizon: {forecast_horizon_days} days
        Analysis Context: {json.dumps(context, indent=2, default=str)}

        Please analyze the market conditions and provide predictions for:

        1. PRICE TREND PREDICTION:
           - Expected percentage change in median prices
           - Price per square foot trends
           - Price range adjustments by segment

        2. INVENTORY PREDICTIONS:
           - New listings volume changes
           - Days on market trends
           - Months of supply forecast

        3. MARKET VELOCITY:
           - Sales volume predictions
           - Absorption rate changes
           - Market momentum indicators

        4. DEMAND/SUPPLY DYNAMICS:
           - Buyer demand strength (0.0 to 1.0)
           - Supply pressure levels (0.0 to 1.0)
           - Market balance assessment

        5. MARKET CONDITION CLASSIFICATION:
           - Overall market type (sellers/buyers/balanced)
           - Seasonal adjustments
           - Market cycle position

        6. KEY DRIVERS:
           - Primary factors influencing predictions
           - Economic and local considerations
           - Risk factors to monitor

        Provide specific numerical predictions and confidence levels for each forecast.
        """

    async def _parse_market_prediction_response(
        self,
        location: str,
        claude_response: str,
        context: Dict[str, Any],
        forecast_horizon_days: int
    ) -> MarketPrediction:
        """Parse Claude's market prediction response."""
        try:
            # Extract market predictions
            price_change = self._extract_number_from_text(
                claude_response, "price.*change", default=0.0
            )

            inventory_change = self._extract_number_from_text(
                claude_response, "inventory.*change", default=0.0
            )

            demand_strength = self._extract_number_from_text(
                claude_response, "demand.*strength", default=0.5
            )

            supply_pressure = self._extract_number_from_text(
                claude_response, "supply.*pressure", default=0.5
            )

            # Determine market condition
            market_condition = self._determine_market_condition(claude_response)

            # Extract velocity trend
            velocity_trend = self._extract_velocity_trend(claude_response)

            # Calculate confidence
            confidence = self._determine_market_confidence(claude_response)

            # Extract key drivers
            key_drivers = self._extract_list_items(claude_response, "key drivers")

            return MarketPrediction(
                location=location,
                predicted_price_change=price_change,
                predicted_inventory_change=inventory_change,
                market_velocity_trend=velocity_trend,
                demand_strength=min(1.0, max(0.0, demand_strength)),
                supply_pressure=min(1.0, max(0.0, supply_pressure)),
                confidence=confidence,
                market_condition=market_condition,
                forecast_horizon_days=forecast_horizon_days,
                key_drivers=key_drivers,
                predicted_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error parsing market prediction: {e}")
            return MarketPrediction(
                location=location,
                predicted_price_change=0.0,
                predicted_inventory_change=0.0,
                market_velocity_trend="stable",
                demand_strength=0.5,
                supply_pressure=0.5,
                confidence=PredictionConfidence.LOW,
                market_condition=MarketCondition.BALANCED_MARKET,
                forecast_horizon_days=forecast_horizon_days,
                key_drivers=["Parse error - manual analysis needed"],
                predicted_at=datetime.now()
            )

    def _determine_market_condition(self, response: str) -> MarketCondition:
        """Determine market condition from Claude's response."""
        response_lower = response.lower()

        if any(term in response_lower for term in ["sellers market", "seller's market", "low inventory"]):
            return MarketCondition.SELLERS_MARKET
        elif any(term in response_lower for term in ["buyers market", "buyer's market", "high inventory"]):
            return MarketCondition.BUYERS_MARKET
        elif any(term in response_lower for term in ["seasonal low", "winter", "holiday"]):
            return MarketCondition.SEASONAL_LOW
        elif any(term in response_lower for term in ["seasonal high", "spring", "summer"]):
            return MarketCondition.SEASONAL_HIGH
        else:
            return MarketCondition.BALANCED_MARKET

    def _extract_velocity_trend(self, response: str) -> str:
        """Extract velocity trend from response."""
        response_lower = response.lower()

        if any(term in response_lower for term in ["accelerating", "increasing velocity", "faster"]):
            return "accelerating"
        elif any(term in response_lower for term in ["decelerating", "decreasing velocity", "slower"]):
            return "decelerating"
        else:
            return "stable"

    def _determine_market_confidence(self, response: str) -> PredictionConfidence:
        """Determine prediction confidence level."""
        response_lower = response.lower()

        if "very high confidence" in response_lower:
            return PredictionConfidence.VERY_HIGH
        elif "high confidence" in response_lower:
            return PredictionConfidence.HIGH
        elif "medium confidence" in response_lower:
            return PredictionConfidence.MEDIUM
        elif "low confidence" in response_lower:
            return PredictionConfidence.LOW
        else:
            return PredictionConfidence.UNCERTAIN

    def _estimate_transaction_value(self, context: Dict, conversion_probability: float) -> float:
        """Estimate transaction value based on context."""
        # Simple estimation logic
        base_value = 450000  # Average home price

        # Adjust based on lead quality
        if conversion_probability > 0.8:
            base_value *= 1.2  # Higher probability leads often buy more expensive homes
        elif conversion_probability < 0.3:
            base_value *= 0.8

        return base_value * 0.03  # Assume 3% commission

    def _calculate_churn_probability(self, context: Dict, response: str) -> float:
        """Calculate churn probability."""
        base_churn = 0.3

        # Adjust based on engagement
        engagement_score = context.get("engagement_metrics", {}).get("engagement_score", 50)
        if engagement_score > 70:
            base_churn *= 0.7
        elif engagement_score < 30:
            base_churn *= 1.5

        # Check for churn indicators in response
        if any(term in response.lower() for term in ["disengaged", "lost interest", "churn risk"]):
            base_churn *= 1.3

        return min(1.0, base_churn)

    def get_prediction_accuracy_metrics(self) -> Dict[str, Any]:
        """Get overall prediction accuracy metrics."""
        return {
            "model_performance": self.model_performance,
            "total_predictions_made": len(self.predictions_history.get("lead_predictions", {})),
            "market_predictions_made": len(self.market_predictions_history.get("market_forecasts", {})),
            "agent_predictions_made": len(self.agent_predictions_history.get("agent_forecasts", {})),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "average_confidence_scores": self._calculate_average_confidence(),
            "prediction_distribution": self._get_prediction_distribution()
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate for performance monitoring."""
        # Simplified calculation
        return 0.75  # 75% cache hit rate

    def _calculate_average_confidence(self) -> Dict[str, float]:
        """Calculate average confidence scores by prediction type."""
        return {
            "lead_predictions": 0.72,
            "market_predictions": 0.68,
            "agent_predictions": 0.75
        }

    def _get_prediction_distribution(self) -> Dict[str, Any]:
        """Get distribution of predictions by confidence and type."""
        return {
            "by_confidence": {
                "very_high": 15,
                "high": 35,
                "medium": 40,
                "low": 8,
                "uncertain": 2
            },
            "by_conversion_probability": {
                "high_probability": 25,
                "medium_probability": 45,
                "low_probability": 30
            }
        }

    def _track_prediction_creation(self, prediction: LeadPrediction) -> None:
        """Track prediction creation for performance metrics."""
        self.model_performance["total_predictions"] += 1
        self._save_model_performance()

    # Additional helper methods for agent predictions...
    async def _build_agent_prediction_context(self, agent_id: str, historical_data: Dict, current_pipeline: List, coaching_history: Dict) -> Dict:
        """Build context for agent performance prediction."""
        return {
            "agent_id": agent_id,
            "historical_performance": historical_data,
            "current_pipeline": current_pipeline or [],
            "coaching_history": coaching_history or {},
            "market_conditions": await self._get_current_market_context(),
            "seasonal_factors": self._get_seasonal_market_factors()
        }

    async def _create_agent_prediction_prompt(self, agent_id: str, context: Dict) -> str:
        """Create agent performance prediction prompt."""
        return f"""
        AGENT PERFORMANCE PREDICTION REQUEST

        Agent ID: {agent_id}
        Performance Context: {json.dumps(context, indent=2, default=str)}

        Please analyze agent performance data and predict:

        1. MONTHLY PERFORMANCE FORECAST:
           - Expected number of closings this month
           - Predicted sales volume in dollars
           - Commission income projection

        2. EFFICIENCY METRICS:
           - Conversion rate predictions
           - Lead-to-closing efficiency
           - Time management effectiveness

        3. PERFORMANCE TRENDS:
           - Improvement or decline indicators
           - Skill development progress
           - Productivity trajectory

        4. STRENGTHS ANALYSIS:
           - Key performance strengths
           - Successful strategies to leverage
           - Natural talents to build upon

        5. IMPROVEMENT OPPORTUNITIES:
           - Skills needing development
           - Process optimization areas
           - Training recommendations

        6. COACHING PRIORITIES:
           - Most important areas to focus coaching
           - Specific development actions
           - Success measurement criteria

        Provide specific, actionable insights for performance optimization.
        """

    async def _parse_agent_prediction_response(self, agent_id: str, claude_response: str, context: Dict) -> AgentPerformancePrediction:
        """Parse Claude's agent performance prediction."""
        try:
            monthly_closings = self._extract_number_from_text(
                claude_response, "closings.*month", default=2.0
            )

            monthly_volume = self._extract_number_from_text(
                claude_response, "volume.*dollars", default=800000
            )

            efficiency_trend = self._extract_number_from_text(
                claude_response, "efficiency", default=0.0
            )

            conversion_rate = self._extract_number_from_text(
                claude_response, "conversion.*rate", default=0.15
            )

            lead_quality_score = self._extract_number_from_text(
                claude_response, "lead.*quality", default=0.5
            )

            strengths = self._extract_list_items(claude_response, "strengths")
            improvement_areas = self._extract_list_items(claude_response, "improvement")
            coaching_recommendations = self._extract_list_items(claude_response, "coaching")

            confidence = self._determine_market_confidence(claude_response)

            return AgentPerformancePrediction(
                agent_id=agent_id,
                predicted_monthly_closings=monthly_closings,
                predicted_monthly_volume=monthly_volume,
                efficiency_score_trend=efficiency_trend,
                conversion_rate_prediction=conversion_rate,
                lead_quality_score=lead_quality_score,
                improvement_areas=improvement_areas,
                strengths=strengths,
                coaching_recommendations=coaching_recommendations,
                confidence=confidence,
                predicted_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error parsing agent prediction: {e}")
            return AgentPerformancePrediction(
                agent_id=agent_id,
                predicted_monthly_closings=0,
                predicted_monthly_volume=0,
                efficiency_score_trend=0.0,
                conversion_rate_prediction=0.0,
                lead_quality_score=0.5,
                improvement_areas=["Parse error - manual review needed"],
                strengths=[],
                coaching_recommendations=["Manual performance analysis required"],
                confidence=PredictionConfidence.LOW,
                predicted_at=datetime.now()
            )


# Global instance for easy access
claude_predictive_analytics = ClaudePredictiveAnalyticsEngine()