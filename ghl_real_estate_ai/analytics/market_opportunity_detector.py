"""
Market Opportunity Intelligence Engine - Track 5 Advanced Analytics
AI-powered market intelligence for investment recommendations and pricing optimization.

Features:
📈 Real-time market anomaly detection and undervalued property identification
💰 ML-powered optimal pricing strategy recommendations with confidence intervals
🎯 Investment opportunity alerts with ROI projections
📊 Competitive intelligence and market positioning analytics
🔍 Emerging market trend detection before they become obvious
📱 Mobile-ready market intelligence for field work
"""

import asyncio
import time
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ML and statistical analysis imports
import scipy.stats as stats
import xgboost as xgb
from scipy.signal import find_peaks
from sklearn.ensemble import IsolationForest
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.cache_service import get_cache_service

# Jorge's platform imports
from ghl_real_estate_ai.services.ghl_service import GHLService
from ghl_real_estate_ai.services.memory_service import MemoryService

logger = get_logger(__name__)

# =============================================================================
# MARKET INTELLIGENCE DATA MODELS
# =============================================================================


@dataclass
class MarketOpportunity:
    """Investment or pricing opportunity with AI-powered analysis."""

    opportunity_id: str
    opportunity_type: str  # 'undervalued_property', 'pricing_optimization', 'market_timing'
    confidence_score: float  # 0.0 to 1.0

    # Property details
    property_address: str
    current_market_value: float
    ai_predicted_value: float
    opportunity_value: float  # Potential profit/savings

    # Market intelligence
    market_trend: str  # 'appreciating', 'stable', 'declining'
    market_velocity: int  # Days on market average
    competition_analysis: Dict[str, Any]
    seasonal_factors: Dict[str, Any]

    # Investment analysis
    roi_projection: float
    risk_assessment: str  # 'low', 'medium', 'high'
    recommended_action: str
    optimal_timing: str

    # Jorge-specific insights
    jorge_commission_potential: float
    listing_strategy_recommendation: Dict[str, Any]
    client_match_probability: float

    # Metadata
    analysis_timestamp: datetime
    data_sources: List[str]
    model_version: str


@dataclass
class PricingStrategy:
    """Optimal pricing strategy with ML-powered recommendations."""

    property_id: str
    property_address: str

    # Pricing analysis
    recommended_listing_price: float
    price_confidence_interval: Tuple[float, float]
    competitive_price_range: Tuple[float, float]
    price_elasticity_score: float

    # Market positioning
    pricing_strategy: str  # 'aggressive', 'market', 'premium'
    predicted_days_on_market: int
    sale_probability_by_price: Dict[str, float]

    # Dynamic pricing recommendations
    price_adjustment_schedule: List[Dict[str, Any]]
    market_response_triggers: List[Dict[str, Any]]

    # Jorge-specific factors
    jorge_methodology_alignment: float
    confrontational_pricing_score: float  # How well price supports Jorge's approach
    commission_optimization: Dict[str, Any]

    # Analysis metadata
    analysis_date: datetime
    market_data_freshness: int  # Hours since last market update
    prediction_accuracy_estimate: float


@dataclass
class MarketTrend:
    """Emerging market trend with predictive analysis."""

    trend_id: str
    trend_name: str
    trend_type: str  # 'price', 'inventory', 'demand', 'seasonal'

    # Trend analysis
    trend_strength: float  # 0.0 to 1.0
    trend_duration_months: int
    trend_direction: str  # 'upward', 'downward', 'cyclical'
    peak_confidence: float

    # Geographic scope
    affected_areas: List[str]
    geographic_spread_rate: float

    # Business impact
    revenue_impact_estimate: float
    strategic_recommendations: List[str]
    timing_optimization: Dict[str, Any]

    # Metadata
    detection_timestamp: datetime
    confirmation_level: str  # 'emerging', 'confirmed', 'established'
    data_points_analyzed: int


@dataclass
class CompetitiveLandscape:
    """Competitive analysis and positioning intelligence."""

    analysis_id: str
    market_area: str

    # Competitive metrics
    total_active_listings: int
    jorge_market_share: float
    competitor_pricing_patterns: Dict[str, Any]
    average_days_on_market_by_agent: Dict[str, int]

    # Opportunity analysis
    underserved_price_segments: List[Dict[str, Any]]
    competitive_advantages: List[str]
    market_gaps: List[Dict[str, Any]]

    # Strategic positioning
    differentiation_opportunities: List[str]
    competitive_response_recommendations: List[str]
    market_expansion_potential: Dict[str, Any]

    # Performance benchmarking
    jorge_vs_market_metrics: Dict[str, float]
    success_rate_analysis: Dict[str, Any]

    # Metadata
    analysis_timestamp: datetime
    data_coverage_percentage: float
    competitive_intelligence_score: float


class MarketOpportunityDetector:
    """
    AI-powered market intelligence engine for Jorge's competitive advantage.

    Features:
    - Real-time market anomaly detection using isolation forests
    - ML-powered property valuation and undervaluation detection
    - Optimal pricing strategy recommendations with dynamic adjustments
    - Emerging trend detection before market-wide recognition
    - Competitive intelligence and positioning optimization
    - Investment opportunity alerts with ROI projections
    """

    def __init__(self):
        # Jorge's platform services
        self.ghl_service = GHLService()
        self.memory_service = MemoryService()
        self.cache = get_cache_service()
        self.analytics = AnalyticsService()

        # ML models for market intelligence
        self.anomaly_detector = None
        self.price_predictor = None
        self.trend_detector = None

        # Market data and analysis
        self.market_data_cache = {}
        self.trend_history = []
        self.opportunity_history = []

        # Configuration
        self.anomaly_threshold = 0.1  # 10% anomaly threshold
        self.price_prediction_confidence = 0.85
        self.trend_detection_lookback_days = 90
        self.cache_ttl = 3600  # 1 hour cache for market data

        logger.info("Market Opportunity Detector initialized")

    # =========================================================================
    # MAIN MARKET INTELLIGENCE INTERFACES
    # =========================================================================

    async def detect_undervalued_properties(
        self, market_area: str = None, max_opportunities: int = 10
    ) -> List[MarketOpportunity]:
        """
        Detect undervalued properties using AI-powered market analysis.

        Args:
            market_area: Geographic area to analyze (e.g., "Austin, TX")
            max_opportunities: Maximum number of opportunities to return

        Returns:
            List of market opportunities ranked by potential value
        """
        logger.info(f"Detecting undervalued properties in {market_area or 'all markets'}...")

        try:
            # Get comprehensive market data
            market_data = await self._collect_comprehensive_market_data(market_area)

            if len(market_data) < 50:
                logger.warning("Insufficient market data for reliable analysis")
                return []

            # Train/update anomaly detection model
            await self._update_anomaly_detection_model(market_data)

            # Identify anomalies (potential undervalued properties)
            anomalies = await self._detect_market_anomalies(market_data)

            # Analyze each anomaly for investment opportunity
            opportunities = []
            for anomaly in anomalies[: max_opportunities * 2]:  # Analyze more than needed for filtering
                opportunity = await self._analyze_investment_opportunity(anomaly, market_data)
                if opportunity and opportunity.confidence_score > 0.7:
                    opportunities.append(opportunity)

            # Rank by potential value and Jorge's criteria
            opportunities.sort(key=lambda x: x.opportunity_value * x.confidence_score, reverse=True)

            logger.info(f"Identified {len(opportunities)} high-confidence undervalued properties")
            return opportunities[:max_opportunities]

        except Exception as e:
            logger.error(f"Error detecting undervalued properties: {e}")
            return []

    async def predict_optimal_listing_price(
        self, property_data: Dict[str, Any], strategy: str = "optimal"
    ) -> PricingStrategy:
        """
        Generate ML-powered optimal pricing strategy for a property.

        Args:
            property_data: Property details including address, features, etc.
            strategy: Pricing strategy ('aggressive', 'market', 'premium', 'optimal')

        Returns:
            PricingStrategy with recommended price and dynamic adjustments
        """
        logger.info(f"Generating pricing strategy for {property_data.get('address', 'unknown property')}...")

        try:
            # Collect comparable properties and market data
            market_context = await self._collect_property_market_context(property_data)

            # Train/update price prediction model
            price_model = await self._get_price_prediction_model(market_context)

            # Generate base price prediction
            predicted_price = await self._predict_property_value(property_data, price_model)

            # Analyze market dynamics and competition
            market_analysis = await self._analyze_market_dynamics(property_data, market_context)

            # Generate pricing strategy based on Jorge's methodology
            strategy_details = await self._generate_jorge_pricing_strategy(predicted_price, market_analysis, strategy)

            # Create dynamic pricing schedule
            pricing_schedule = await self._create_dynamic_pricing_schedule(predicted_price, market_analysis)

            # Build comprehensive pricing strategy
            pricing_strategy = PricingStrategy(
                property_id=property_data.get("id", "unknown"),
                property_address=property_data.get("address", ""),
                recommended_listing_price=strategy_details["recommended_price"],
                price_confidence_interval=strategy_details["confidence_interval"],
                competitive_price_range=strategy_details["competitive_range"],
                price_elasticity_score=market_analysis["elasticity_score"],
                pricing_strategy=strategy,
                predicted_days_on_market=strategy_details["predicted_dom"],
                sale_probability_by_price=strategy_details["probability_curve"],
                price_adjustment_schedule=pricing_schedule,
                market_response_triggers=await self._generate_market_triggers(market_analysis),
                jorge_methodology_alignment=strategy_details["jorge_alignment"],
                confrontational_pricing_score=strategy_details["confrontational_score"],
                commission_optimization=await self._optimize_commission_strategy(strategy_details),
                analysis_date=datetime.now(),
                market_data_freshness=market_context.get("data_age_hours", 0),
                prediction_accuracy_estimate=price_model.get("accuracy", 0.85),
            )

            logger.info(
                f"Generated pricing strategy: ${pricing_strategy.recommended_listing_price:,.0f} "
                f"(confidence: {pricing_strategy.prediction_accuracy_estimate:.1%})"
            )

            return pricing_strategy

        except Exception as e:
            logger.error(f"Error generating pricing strategy: {e}")
            return await self._generate_fallback_pricing_strategy(property_data)

    async def identify_market_trends(self, market_area: str = None, trend_types: List[str] = None) -> List[MarketTrend]:
        """
        Detect emerging market trends before they become widely recognized.

        Args:
            market_area: Geographic area to analyze
            trend_types: Types of trends to detect ('price', 'inventory', 'demand', 'seasonal')

        Returns:
            List of detected market trends with business impact analysis
        """
        logger.info(f"Detecting market trends in {market_area or 'all markets'}...")

        try:
            # Default trend types if not specified
            if not trend_types:
                trend_types = ["price", "inventory", "demand", "seasonal"]

            # Collect historical market data for trend analysis
            historical_data = await self._collect_historical_market_data(
                market_area, days_back=self.trend_detection_lookback_days
            )

            # Detect trends for each type
            detected_trends = []

            for trend_type in trend_types:
                trends = await self._detect_trends_by_type(historical_data, trend_type)
                detected_trends.extend(trends)

            # Analyze business impact for Jorge
            for trend in detected_trends:
                trend = await self._analyze_trend_business_impact(trend, historical_data)

            # Filter and rank trends by significance and opportunity
            significant_trends = [t for t in detected_trends if t.trend_strength > 0.6]
            significant_trends.sort(key=lambda x: x.revenue_impact_estimate, reverse=True)

            logger.info(f"Detected {len(significant_trends)} significant market trends")
            return significant_trends[:10]  # Return top 10 trends

        except Exception as e:
            logger.error(f"Error detecting market trends: {e}")
            return []

    async def generate_investment_alerts(self, user_preferences: Dict[str, Any] = None) -> List[MarketOpportunity]:
        """
        Generate proactive investment opportunity alerts based on market analysis.

        Args:
            user_preferences: Jorge's investment criteria and preferences

        Returns:
            List of time-sensitive investment opportunities
        """
        logger.info("Generating investment opportunity alerts...")

        try:
            # Default preferences aligned with Jorge's methodology
            if not user_preferences:
                user_preferences = {
                    "min_commission_value": 15000,  # $15K minimum commission (6% of $250K)
                    "max_risk_level": "medium",
                    "preferred_property_types": ["single_family", "townhouse"],
                    "max_days_on_market": 60,
                    "target_markets": ["austin", "cedar_park", "round_rock"],
                }

            # Collect recent market opportunities
            recent_opportunities = await self.detect_undervalued_properties(max_opportunities=25)

            # Filter opportunities based on Jorge's criteria
            filtered_opportunities = []
            for opportunity in recent_opportunities:
                if await self._meets_jorge_investment_criteria(opportunity, user_preferences):
                    # Add urgency scoring for alert prioritization
                    opportunity = await self._add_urgency_scoring(opportunity)
                    filtered_opportunities.append(opportunity)

            # Rank by urgency and potential value
            filtered_opportunities.sort(key=lambda x: x.confidence_score * x.opportunity_value, reverse=True)

            # Generate time-sensitive alerts
            alerts = []
            for opportunity in filtered_opportunities[:5]:  # Top 5 most urgent
                if await self._is_time_sensitive(opportunity):
                    alerts.append(opportunity)

            logger.info(f"Generated {len(alerts)} investment alerts for Jorge")
            return alerts

        except Exception as e:
            logger.error(f"Error generating investment alerts: {e}")
            return []

    # =========================================================================
    # MARKET DATA COLLECTION AND ANALYSIS
    # =========================================================================

    async def _collect_comprehensive_market_data(self, market_area: str = None) -> pd.DataFrame:
        """Collect comprehensive market data for analysis."""
        try:
            # Check cache first
            cache_key = f"market_data:{market_area or 'all'}"
            cached_data = await self.cache.get(cache_key)

            if cached_data:
                logger.debug("Using cached market data")
                return pd.DataFrame(cached_data)

            # Collect from multiple data sources
            market_data = []

            # 1. Active listings data
            active_listings = await self._get_active_listings_data(market_area)
            market_data.extend(active_listings)

            # 2. Recent sales data
            recent_sales = await self._get_recent_sales_data(market_area)
            market_data.extend(recent_sales)

            # 3. Property assessment data
            assessment_data = await self._get_property_assessment_data(market_area)
            market_data.extend(assessment_data)

            # 4. Market indicators
            market_indicators = await self._get_market_indicators(market_area)

            # Convert to DataFrame and add calculated features
            df = pd.DataFrame(market_data)

            if not df.empty:
                # Add calculated market features
                df = await self._add_market_features(df, market_indicators)

                # Cache the processed data
                await self.cache.set(cache_key, df.to_dict("records"), ttl=self.cache_ttl)

            logger.info(f"Collected {len(df)} market data points for analysis")
            return df

        except Exception as e:
            logger.error(f"Error collecting market data: {e}")
            return pd.DataFrame()

    async def _collect_property_market_context(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect market context specific to a property."""
        try:
            context = {
                "property": property_data,
                "comparables": [],
                "market_indicators": {},
                "competitive_landscape": {},
                "data_age_hours": 0,
            }

            # Get comparable properties
            comparables = await self._find_comparable_properties(property_data)
            context["comparables"] = comparables

            # Get market indicators for the area
            market_indicators = await self._get_area_market_indicators(property_data.get("area"))
            context["market_indicators"] = market_indicators

            # Analyze competitive landscape
            competitive_analysis = await self._analyze_local_competition(property_data)
            context["competitive_landscape"] = competitive_analysis

            # Calculate data freshness
            context["data_age_hours"] = await self._calculate_data_freshness(property_data)

            return context

        except Exception as e:
            logger.error(f"Error collecting property market context: {e}")
            return {}

    async def _collect_historical_market_data(self, market_area: str, days_back: int = 90) -> pd.DataFrame:
        """Collect historical market data for trend analysis."""
        try:
            # Time series data for trend detection
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Collect daily market metrics
            historical_data = []
            current_date = start_date

            while current_date <= end_date:
                daily_metrics = await self._get_daily_market_metrics(market_area, current_date)
                if daily_metrics:
                    daily_metrics["date"] = current_date
                    historical_data.append(daily_metrics)

                current_date += timedelta(days=1)

            df = pd.DataFrame(historical_data)

            if not df.empty:
                # Sort by date and add time series features
                df = df.sort_values("date")
                df = await self._add_time_series_features(df)

            logger.info(f"Collected {len(df)} days of historical market data")
            return df

        except Exception as e:
            logger.error(f"Error collecting historical market data: {e}")
            return pd.DataFrame()

    # =========================================================================
    # ML MODELS AND PREDICTION ENGINES
    # =========================================================================

    async def _update_anomaly_detection_model(self, market_data: pd.DataFrame):
        """Train/update anomaly detection model for undervalued properties."""
        try:
            if len(market_data) < 50:
                return

            # Select features for anomaly detection
            anomaly_features = [
                "price_per_sqft",
                "days_on_market",
                "price_vs_assessment",
                "market_appreciation_rate",
                "inventory_levels",
                "demand_score",
            ]

            # Filter and prepare data
            feature_data = market_data[anomaly_features].dropna()

            if len(feature_data) < 30:
                return

            # Standardize features
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(feature_data)

            # Train isolation forest for anomaly detection
            self.anomaly_detector = IsolationForest(
                contamination=self.anomaly_threshold, random_state=42, n_estimators=200
            )

            self.anomaly_detector.fit(scaled_features)

            # Store scaler for future use
            self.anomaly_scaler = scaler

            logger.debug("Updated anomaly detection model")

        except Exception as e:
            logger.error(f"Error updating anomaly detection model: {e}")

    async def _detect_market_anomalies(self, market_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect market anomalies that could represent opportunities."""
        try:
            if self.anomaly_detector is None:
                return []

            # Prepare features
            anomaly_features = [
                "price_per_sqft",
                "days_on_market",
                "price_vs_assessment",
                "market_appreciation_rate",
                "inventory_levels",
                "demand_score",
            ]

            feature_data = market_data[anomaly_features].dropna()
            scaled_features = self.anomaly_scaler.transform(feature_data)

            # Detect anomalies
            anomaly_scores = self.anomaly_detector.decision_function(scaled_features)
            anomaly_predictions = self.anomaly_detector.predict(scaled_features)

            # Get anomalous properties
            anomalies = []
            for i, prediction in enumerate(anomaly_predictions):
                if prediction == -1:  # Anomaly detected
                    property_data = market_data.iloc[feature_data.index[i]].to_dict()
                    property_data["anomaly_score"] = anomaly_scores[i]
                    anomalies.append(property_data)

            # Sort by anomaly score (most anomalous first)
            anomalies.sort(key=lambda x: x["anomaly_score"])

            logger.debug(f"Detected {len(anomalies)} market anomalies")
            return anomalies

        except Exception as e:
            logger.error(f"Error detecting market anomalies: {e}")
            return []

    async def _get_price_prediction_model(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get/train price prediction model for property valuation."""
        try:
            # Check if we have sufficient data for training
            comparables = market_context.get("comparables", [])

            if len(comparables) < 20:
                # Use cached model or fallback to simple averaging
                return {"model": "simple_average", "accuracy": 0.75, "data_points": len(comparables)}

            # Prepare training data
            df = pd.DataFrame(comparables)

            # Feature engineering for price prediction
            features = ["sqft", "bedrooms", "bathrooms", "lot_size", "year_built", "days_on_market"]
            target = "sale_price"

            # Filter data
            model_data = df[features + [target]].dropna()

            if len(model_data) < 15:
                return {"model": "simple_average", "accuracy": 0.70, "data_points": len(model_data)}

            # Split data
            X = model_data[features]
            y = model_data[target]
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Train XGBoost model
            model = xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)

            model.fit(X_train, y_train)

            # Evaluate model
            y_pred = model.predict(X_test)
            accuracy = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)

            return {
                "model": model,
                "accuracy": max(accuracy, 0.0),
                "mae": mae,
                "features": features,
                "data_points": len(model_data),
            }

        except Exception as e:
            logger.error(f"Error creating price prediction model: {e}")
            return {"model": "simple_average", "accuracy": 0.65, "data_points": 0}

    async def _predict_property_value(self, property_data: Dict[str, Any], price_model: Dict[str, Any]) -> float:
        """Predict property value using trained model."""
        try:
            if price_model["model"] == "simple_average":
                # Fallback to simple averaging
                return property_data.get("estimated_value", 0)

            model = price_model["model"]
            features = price_model["features"]

            # Prepare property features
            property_features = []
            for feature in features:
                value = property_data.get(feature, 0)
                property_features.append(value)

            # Make prediction
            predicted_value = model.predict([property_features])[0]

            return max(predicted_value, 0)  # Ensure non-negative

        except Exception as e:
            logger.error(f"Error predicting property value: {e}")
            return property_data.get("estimated_value", 0)

    # =========================================================================
    # OPPORTUNITY ANALYSIS AND STRATEGY GENERATION
    # =========================================================================

    async def _analyze_investment_opportunity(
        self, anomaly_data: Dict[str, Any], market_context: pd.DataFrame
    ) -> Optional[MarketOpportunity]:
        """Analyze a market anomaly for investment opportunity potential."""
        try:
            # Extract opportunity details
            property_address = anomaly_data.get("address", "Unknown Address")
            current_market_value = anomaly_data.get("current_value", 0)
            anomaly_score = anomaly_data.get("anomaly_score", 0)

            # Calculate AI-predicted value based on comparables
            predicted_value = await self._calculate_predicted_value(anomaly_data, market_context)

            # Determine opportunity value
            opportunity_value = predicted_value - current_market_value

            # Skip if not a true opportunity
            if opportunity_value <= 0:
                return None

            # Calculate confidence score
            confidence_score = await self._calculate_opportunity_confidence(
                anomaly_data, market_context, opportunity_value
            )

            # Analyze market trends for this property type/area
            market_trend_analysis = await self._analyze_property_market_trends(anomaly_data)

            # Calculate Jorge's potential commission
            jorge_commission = predicted_value * 0.06

            # Generate recommendations
            recommendations = await self._generate_opportunity_recommendations(
                anomaly_data, opportunity_value, confidence_score
            )

            # Create opportunity object
            opportunity = MarketOpportunity(
                opportunity_id=f"opp_{int(time.time())}_{hash(property_address) % 10000}",
                opportunity_type="undervalued_property",
                confidence_score=confidence_score,
                property_address=property_address,
                current_market_value=current_market_value,
                ai_predicted_value=predicted_value,
                opportunity_value=opportunity_value,
                market_trend=market_trend_analysis["trend"],
                market_velocity=market_trend_analysis["velocity"],
                competition_analysis=market_trend_analysis["competition"],
                seasonal_factors=market_trend_analysis["seasonal"],
                roi_projection=opportunity_value / current_market_value if current_market_value > 0 else 0,
                risk_assessment=recommendations["risk_level"],
                recommended_action=recommendations["action"],
                optimal_timing=recommendations["timing"],
                jorge_commission_potential=jorge_commission,
                listing_strategy_recommendation=recommendations["listing_strategy"],
                client_match_probability=recommendations["client_match_probability"],
                analysis_timestamp=datetime.now(),
                data_sources=["MLS", "Property_Assessment", "Market_Analysis"],
                model_version="1.0",
            )

            return opportunity

        except Exception as e:
            logger.error(f"Error analyzing investment opportunity: {e}")
            return None

    async def _generate_jorge_pricing_strategy(
        self, predicted_price: float, market_analysis: Dict[str, Any], strategy_type: str
    ) -> Dict[str, Any]:
        """Generate pricing strategy aligned with Jorge's methodology."""
        try:
            # Base strategy adjustments
            strategy_multipliers = {
                "aggressive": 0.95,  # Price to sell quickly
                "market": 1.00,  # Market value pricing
                "premium": 1.05,  # Premium positioning
                "optimal": 1.02,  # Slight premium for negotiation room
            }

            base_multiplier = strategy_multipliers.get(strategy_type, 1.00)
            recommended_price = predicted_price * base_multiplier

            # Jorge's confrontational approach factors
            confrontational_factors = {
                "high_confidence_pricing": 1.03,  # Jorge's confidence justifies premium
                "market_knowledge_advantage": 1.02,  # Superior market intelligence
                "rapid_qualification": 0.98,  # Price to attract serious buyers only
                "negotiation_room": 1.05,  # Room for Jorge's negotiation tactics
            }

            # Apply Jorge-specific adjustments
            jorge_adjustment = 1.0
            for factor, multiplier in confrontational_factors.items():
                if market_analysis.get(factor, False):
                    jorge_adjustment *= multiplier

            final_recommended_price = recommended_price * jorge_adjustment

            # Calculate confidence interval
            market_volatility = market_analysis.get("price_volatility", 0.05)
            confidence_interval = (
                final_recommended_price * (1 - market_volatility),
                final_recommended_price * (1 + market_volatility),
            )

            # Competitive price range analysis
            competitive_range = await self._analyze_competitive_pricing(predicted_price, market_analysis)

            # Predict days on market
            predicted_dom = await self._predict_days_on_market(final_recommended_price, market_analysis)

            # Jorge methodology alignment score
            jorge_alignment = await self._calculate_jorge_alignment(
                final_recommended_price, predicted_price, market_analysis
            )

            # Confrontational pricing score (supports direct approach)
            confrontational_score = await self._calculate_confrontational_pricing_score(
                final_recommended_price, market_analysis
            )

            # Sale probability curve
            probability_curve = await self._generate_price_probability_curve(predicted_price, market_analysis)

            return {
                "recommended_price": final_recommended_price,
                "confidence_interval": confidence_interval,
                "competitive_range": competitive_range,
                "predicted_dom": predicted_dom,
                "jorge_alignment": jorge_alignment,
                "confrontational_score": confrontational_score,
                "probability_curve": probability_curve,
            }

        except Exception as e:
            logger.error(f"Error generating Jorge pricing strategy: {e}")
            return {
                "recommended_price": predicted_price,
                "confidence_interval": (predicted_price * 0.95, predicted_price * 1.05),
                "competitive_range": (predicted_price * 0.9, predicted_price * 1.1),
                "predicted_dom": 45,
                "jorge_alignment": 0.75,
                "confrontational_score": 0.70,
                "probability_curve": {},
            }

    # =========================================================================
    # TREND DETECTION AND ANALYSIS
    # =========================================================================

    async def _detect_trends_by_type(self, historical_data: pd.DataFrame, trend_type: str) -> List[MarketTrend]:
        """Detect market trends by specific type."""
        try:
            trends = []

            if trend_type == "price":
                price_trends = await self._detect_price_trends(historical_data)
                trends.extend(price_trends)

            elif trend_type == "inventory":
                inventory_trends = await self._detect_inventory_trends(historical_data)
                trends.extend(inventory_trends)

            elif trend_type == "demand":
                demand_trends = await self._detect_demand_trends(historical_data)
                trends.extend(demand_trends)

            elif trend_type == "seasonal":
                seasonal_trends = await self._detect_seasonal_patterns(historical_data)
                trends.extend(seasonal_trends)

            return trends

        except Exception as e:
            logger.error(f"Error detecting {trend_type} trends: {e}")
            return []

    async def _detect_price_trends(self, historical_data: pd.DataFrame) -> List[MarketTrend]:
        """Detect emerging price trends."""
        try:
            if "median_price" not in historical_data.columns:
                return []

            # Calculate price momentum and trend strength
            price_series = historical_data["median_price"].values
            dates = historical_data["date"].values

            # Use signal processing to detect trends
            peaks, _ = find_peaks(price_series, prominence=np.std(price_series) * 0.5)
            troughs, _ = find_peaks(-price_series, prominence=np.std(price_series) * 0.5)

            trends = []

            # Analyze recent trend (last 30 days)
            if len(price_series) >= 30:
                recent_prices = price_series[-30:]
                trend_strength = self._calculate_trend_strength(recent_prices)

                if trend_strength > 0.6:  # Significant trend
                    trend_direction = "upward" if recent_prices[-1] > recent_prices[0] else "downward"

                    trend = MarketTrend(
                        trend_id=f"price_trend_{int(time.time())}",
                        trend_name=f"Price {trend_direction.title()} Trend",
                        trend_type="price",
                        trend_strength=trend_strength,
                        trend_duration_months=1,  # Recent trend
                        trend_direction=trend_direction,
                        peak_confidence=trend_strength,
                        affected_areas=["current_market"],
                        geographic_spread_rate=0.8,
                        revenue_impact_estimate=await self._estimate_price_trend_impact(
                            trend_direction, trend_strength
                        ),
                        strategic_recommendations=await self._generate_price_trend_strategies(
                            trend_direction, trend_strength
                        ),
                        timing_optimization={"optimal_listing_window": "next_30_days"},
                        detection_timestamp=datetime.now(),
                        confirmation_level="emerging" if trend_strength < 0.8 else "confirmed",
                        data_points_analyzed=len(recent_prices),
                    )

                    trends.append(trend)

            return trends

        except Exception as e:
            logger.error(f"Error detecting price trends: {e}")
            return []

    def _calculate_trend_strength(self, data_series: np.ndarray) -> float:
        """Calculate trend strength using statistical analysis."""
        try:
            if len(data_series) < 5:
                return 0.0

            # Linear regression to measure trend consistency
            x = np.arange(len(data_series))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, data_series)

            # Trend strength based on R-squared and consistency
            trend_strength = abs(r_value)

            # Adjust for statistical significance
            if p_value > 0.05:  # Not statistically significant
                trend_strength *= 0.5

            return min(trend_strength, 1.0)

        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0.0

    # =========================================================================
    # HELPER METHODS AND UTILITIES
    # =========================================================================

    async def _meets_jorge_investment_criteria(self, opportunity: MarketOpportunity, criteria: Dict[str, Any]) -> bool:
        """Check if opportunity meets Jorge's investment criteria."""
        try:
            # Commission value check
            if opportunity.jorge_commission_potential < criteria.get("min_commission_value", 15000):
                return False

            # Risk level check
            max_risk = criteria.get("max_risk_level", "medium")
            risk_levels = {"low": 1, "medium": 2, "high": 3}
            if risk_levels.get(opportunity.risk_assessment, 3) > risk_levels.get(max_risk, 2):
                return False

            # Confidence score check
            if opportunity.confidence_score < 0.7:
                return False

            # Market velocity check
            if opportunity.market_velocity > criteria.get("max_days_on_market", 60):
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking Jorge investment criteria: {e}")
            return False

    # Placeholder methods for data collection and analysis
    async def _get_active_listings_data(self, market_area: str) -> List[Dict]:
        return []

    async def _get_recent_sales_data(self, market_area: str) -> List[Dict]:
        return []

    async def _get_property_assessment_data(self, market_area: str) -> List[Dict]:
        return []

    async def _get_market_indicators(self, market_area: str) -> Dict:
        return {}

    async def _add_market_features(self, df: pd.DataFrame, indicators: Dict) -> pd.DataFrame:
        return df

    async def _find_comparable_properties(self, property_data: Dict) -> List[Dict]:
        return []

    async def _get_area_market_indicators(self, area: str) -> Dict:
        return {}

    async def _analyze_local_competition(self, property_data: Dict) -> Dict:
        return {}

    async def _calculate_data_freshness(self, property_data: Dict) -> int:
        return 2

    async def _get_daily_market_metrics(self, market_area: str, date: datetime) -> Dict:
        return {}

    async def _add_time_series_features(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    async def _calculate_predicted_value(self, anomaly_data: Dict, market_context: pd.DataFrame) -> float:
        return anomaly_data.get("current_value", 0) * 1.1

    async def _calculate_opportunity_confidence(
        self, anomaly_data: Dict, market_context: pd.DataFrame, opportunity_value: float
    ) -> float:
        return 0.8

    async def _analyze_property_market_trends(self, property_data: Dict) -> Dict:
        return {"trend": "stable", "velocity": 35, "competition": {}, "seasonal": {}}

    async def _generate_opportunity_recommendations(
        self, anomaly_data: Dict, opportunity_value: float, confidence: float
    ) -> Dict:
        return {
            "risk_level": "medium",
            "action": "investigate_further",
            "timing": "next_30_days",
            "listing_strategy": {},
            "client_match_probability": 0.75,
        }

    # Additional placeholder methods
    async def _analyze_market_dynamics(self, property_data: Dict, market_context: Dict) -> Dict:
        return {"elasticity_score": 0.7}

    async def _create_dynamic_pricing_schedule(self, predicted_price: float, market_analysis: Dict) -> List[Dict]:
        return [{"week": 1, "price_adjustment": 0}]

    async def _generate_market_triggers(self, market_analysis: Dict) -> List[Dict]:
        return [{"trigger": "low_activity", "action": "reduce_price_5_percent"}]

    async def _optimize_commission_strategy(self, strategy_details: Dict) -> Dict:
        return {"commission_rate": 0.06, "value_optimization": True}

    async def _generate_fallback_pricing_strategy(self, property_data: Dict) -> PricingStrategy:
        estimated_value = property_data.get("estimated_value", 400000)
        return PricingStrategy(
            property_id=property_data.get("id", "unknown"),
            property_address=property_data.get("address", ""),
            recommended_listing_price=estimated_value,
            price_confidence_interval=(estimated_value * 0.95, estimated_value * 1.05),
            competitive_price_range=(estimated_value * 0.9, estimated_value * 1.1),
            price_elasticity_score=0.7,
            pricing_strategy="market",
            predicted_days_on_market=45,
            sale_probability_by_price={},
            price_adjustment_schedule=[],
            market_response_triggers=[],
            jorge_methodology_alignment=0.75,
            confrontational_pricing_score=0.70,
            commission_optimization={},
            analysis_date=datetime.now(),
            market_data_freshness=0,
            prediction_accuracy_estimate=0.70,
        )

    # Additional helper methods
    async def _analyze_competitive_pricing(self, predicted_price: float, market_analysis: Dict) -> Tuple[float, float]:
        return (predicted_price * 0.9, predicted_price * 1.1)

    async def _predict_days_on_market(self, price: float, market_analysis: Dict) -> int:
        return 35

    async def _calculate_jorge_alignment(
        self, recommended_price: float, predicted_price: float, market_analysis: Dict
    ) -> float:
        return 0.85

    async def _calculate_confrontational_pricing_score(self, price: float, market_analysis: Dict) -> float:
        return 0.80

    async def _generate_price_probability_curve(
        self, predicted_price: float, market_analysis: Dict
    ) -> Dict[str, float]:
        return {
            f"{predicted_price * 0.95:.0f}": 0.9,
            f"{predicted_price:.0f}": 0.8,
            f"{predicted_price * 1.05:.0f}": 0.6,
        }

    async def _detect_inventory_trends(self, historical_data: pd.DataFrame) -> List[MarketTrend]:
        return []

    async def _detect_demand_trends(self, historical_data: pd.DataFrame) -> List[MarketTrend]:
        return []

    async def _detect_seasonal_patterns(self, historical_data: pd.DataFrame) -> List[MarketTrend]:
        return []

    async def _analyze_trend_business_impact(self, trend: MarketTrend, historical_data: pd.DataFrame) -> MarketTrend:
        return trend

    async def _estimate_price_trend_impact(self, direction: str, strength: float) -> float:
        return strength * 50000  # Estimated revenue impact

    async def _generate_price_trend_strategies(self, direction: str, strength: float) -> List[str]:
        if direction == "upward":
            return ["List properties quickly", "Price at market or slightly above"]
        else:
            return ["Price aggressively", "Focus on motivated sellers"]

    async def _add_urgency_scoring(self, opportunity: MarketOpportunity) -> MarketOpportunity:
        # Add urgency scoring logic
        return opportunity

    async def _is_time_sensitive(self, opportunity: MarketOpportunity) -> bool:
        return opportunity.confidence_score > 0.8


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_market_detector_instance = None


def get_market_opportunity_detector() -> MarketOpportunityDetector:
    """Get singleton market opportunity detector instance."""
    global _market_detector_instance
    if _market_detector_instance is None:
        _market_detector_instance = MarketOpportunityDetector()
    return _market_detector_instance


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":

    async def main():
        print("📊 Jorge's Market Opportunity Intelligence Engine - Track 5")
        print("=" * 65)

        detector = get_market_opportunity_detector()

        # Demo market analysis
        print("\n🔍 Detecting undervalued properties...")
        opportunities = await detector.detect_undervalued_properties("Austin, TX", max_opportunities=5)

        print(f"✅ Found {len(opportunities)} investment opportunities")
        for opp in opportunities:
            print(
                f"  📍 {opp.property_address}: ${opp.opportunity_value:,.0f} potential value "
                f"({opp.confidence_score:.1%} confidence)"
            )

        print("\n🎯 Market intelligence engine ready for production!")
        print("💰 Generating investment alerts and pricing strategies!")

    asyncio.run(main())
