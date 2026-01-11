"""
Advanced Predictive Analytics Engine for Real Estate

Provides sophisticated predictions for:
- Deal closure probability and timeline
- Market trend analysis and pricing predictions
- Agent performance forecasting
- Lead conversion optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
from enum import Enum
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, mean_squared_error
import plotly.graph_objects as go
import plotly.express as px

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    DEAL_CLOSURE = "deal_closure"
    MARKET_TREND = "market_trend"
    AGENT_PERFORMANCE = "agent_performance"
    LEAD_CONVERSION = "lead_conversion"
    PRICE_OPTIMIZATION = "price_optimization"


@dataclass
class PredictionResult:
    """Comprehensive prediction result with confidence intervals"""
    prediction_type: PredictionType
    primary_prediction: float
    confidence: float
    confidence_interval: Tuple[float, float]
    contributing_factors: Dict[str, float]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            'prediction_type': self.prediction_type.value,
            'primary_prediction': round(self.primary_prediction, 4),
            'confidence': round(self.confidence, 3),
            'confidence_interval': [round(ci, 4) for ci in self.confidence_interval],
            'contributing_factors': {k: round(v, 3) for k, v in self.contributing_factors.items()},
            'recommendations': self.recommendations,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class MarketInsight:
    """Market trend and insight data"""
    region: str
    property_type: str
    trend_direction: str  # 'rising', 'falling', 'stable'
    price_change_percent: float
    volume_change_percent: float
    days_on_market_trend: float
    demand_supply_ratio: float
    seasonal_factor: float
    economic_indicators: Dict[str, float] = field(default_factory=dict)


class PredictiveAnalyticsEngine:
    """
    Advanced predictive analytics engine for real estate intelligence
    Combines multiple ML models with market data and behavioral signals
    """

    def __init__(self):
        # ML Models for different prediction types
        self.deal_closure_model: Optional[RandomForestClassifier] = None
        self.price_prediction_model: Optional[GradientBoostingRegressor] = None
        self.conversion_model: Optional[MLPRegressor] = None
        self.market_trend_model: Optional[GradientBoostingRegressor] = None

        # Data preprocessing
        self.scalers = {}
        self.label_encoders = {}

        # Historical data cache
        self.historical_deals = []
        self.market_data_cache = {}
        self.agent_performance_history = {}

        # Model performance tracking
        self.model_accuracy = {}
        self.prediction_history = []

        # Market intelligence
        self.current_market_insights = {}

    async def initialize(self) -> None:
        """Initialize the predictive analytics engine"""
        try:
            # Load historical data
            await self._load_historical_data()

            # Train prediction models
            await self._train_models()

            # Initialize market intelligence
            await self._initialize_market_intelligence()

            logger.info("✅ Predictive Analytics Engine initialized successfully")

        except Exception as e:
            logger.error(f"❌ Predictive Analytics initialization failed: {e}")

    async def predict_deal_closure(
        self,
        lead_id: str,
        deal_data: Dict,
        agent_id: str,
        tenant_id: str
    ) -> PredictionResult:
        """
        Predict deal closure probability and timeline

        Args:
            lead_id: Lead identifier
            deal_data: Current deal information
            agent_id: Agent handling the deal
            tenant_id: Tenant identifier

        Returns:
            PredictionResult with closure probability and timeline
        """

        try:
            # 1. Extract features for prediction
            features = await self._extract_deal_features(deal_data, agent_id, tenant_id)

            # 2. Get base closure probability
            closure_probability = 0.5  # Default

            if self.deal_closure_model and len(features) > 0:
                feature_vector = self._create_feature_vector(features, 'deal_closure')
                closure_probability = self.deal_closure_model.predict_proba([feature_vector])[0][1]

            # 3. Calculate contributing factors
            contributing_factors = await self._analyze_deal_factors(deal_data, agent_id)

            # 4. Predict timeline to closure
            estimated_days = await self._predict_closure_timeline(deal_data, closure_probability)

            # 5. Generate confidence interval
            confidence = self._calculate_prediction_confidence('deal_closure', features)
            lower_bound = max(0, closure_probability - (0.2 * (1 - confidence)))
            upper_bound = min(1, closure_probability + (0.2 * (1 - confidence)))

            # 6. Generate recommendations
            recommendations = await self._generate_deal_recommendations(
                closure_probability, contributing_factors, deal_data
            )

            return PredictionResult(
                prediction_type=PredictionType.DEAL_CLOSURE,
                primary_prediction=closure_probability,
                confidence=confidence,
                confidence_interval=(lower_bound, upper_bound),
                contributing_factors=contributing_factors,
                recommendations=recommendations,
                metadata={
                    'estimated_days_to_close': estimated_days,
                    'lead_id': lead_id,
                    'agent_id': agent_id,
                    'deal_stage': deal_data.get('stage', 'unknown')
                }
            )

        except Exception as e:
            logger.error(f"Deal closure prediction failed: {e}")
            return self._create_fallback_prediction(PredictionType.DEAL_CLOSURE)

    async def predict_market_trends(
        self,
        region: str,
        property_type: str,
        forecast_days: int = 90
    ) -> PredictionResult:
        """
        Predict market trends for a specific region and property type

        Args:
            region: Geographic region
            property_type: Type of property
            forecast_days: Number of days to forecast

        Returns:
            PredictionResult with market trend predictions
        """

        try:
            # 1. Get current market data
            current_market = await self._get_market_data(region, property_type)

            # 2. Extract market trend features
            trend_features = await self._extract_market_features(region, property_type)

            # 3. Predict price trend
            price_trend = 0.0  # Default no change

            if self.market_trend_model and len(trend_features) > 0:
                feature_vector = self._create_feature_vector(trend_features, 'market_trend')
                price_trend = self.market_trend_model.predict([feature_vector])[0]

            # 4. Analyze market factors
            market_factors = await self._analyze_market_factors(region, property_type)

            # 5. Calculate confidence based on data quality
            confidence = self._calculate_market_prediction_confidence(region, property_type)

            # 6. Generate market recommendations
            recommendations = await self._generate_market_recommendations(
                price_trend, market_factors, region, property_type
            )

            # 7. Create confidence interval
            volatility = market_factors.get('market_volatility', 0.1)
            lower_bound = price_trend - (2 * volatility)
            upper_bound = price_trend + (2 * volatility)

            return PredictionResult(
                prediction_type=PredictionType.MARKET_TREND,
                primary_prediction=price_trend,
                confidence=confidence,
                confidence_interval=(lower_bound, upper_bound),
                contributing_factors=market_factors,
                recommendations=recommendations,
                metadata={
                    'region': region,
                    'property_type': property_type,
                    'forecast_days': forecast_days,
                    'current_median_price': current_market.get('median_price', 0),
                    'volume_trend': current_market.get('volume_trend', 'stable')
                }
            )

        except Exception as e:
            logger.error(f"Market trend prediction failed: {e}")
            return self._create_fallback_prediction(PredictionType.MARKET_TREND)

    async def predict_agent_performance(
        self,
        agent_id: str,
        tenant_id: str,
        forecast_period: str = "monthly"
    ) -> PredictionResult:
        """
        Predict agent performance metrics

        Args:
            agent_id: Agent identifier
            tenant_id: Tenant identifier
            forecast_period: 'weekly', 'monthly', 'quarterly'

        Returns:
            PredictionResult with performance predictions
        """

        try:
            # 1. Get agent historical performance
            agent_history = await self._get_agent_performance_history(agent_id, tenant_id)

            # 2. Extract agent performance features
            perf_features = await self._extract_agent_features(agent_id, tenant_id)

            # 3. Predict future performance metrics
            predicted_metrics = await self._predict_agent_metrics(perf_features, forecast_period)

            # 4. Analyze performance factors
            performance_factors = await self._analyze_agent_factors(agent_history, perf_features)

            # 5. Calculate prediction confidence
            confidence = self._calculate_agent_prediction_confidence(agent_history)

            # 6. Generate performance improvement recommendations
            recommendations = await self._generate_agent_recommendations(
                predicted_metrics, performance_factors, agent_history
            )

            # 7. Calculate confidence interval for primary metric (conversion rate)
            conversion_rate = predicted_metrics.get('predicted_conversion_rate', 0.2)
            performance_variance = performance_factors.get('performance_consistency', 0.1)

            lower_bound = max(0, conversion_rate - performance_variance)
            upper_bound = min(1, conversion_rate + performance_variance)

            return PredictionResult(
                prediction_type=PredictionType.AGENT_PERFORMANCE,
                primary_prediction=conversion_rate,
                confidence=confidence,
                confidence_interval=(lower_bound, upper_bound),
                contributing_factors=performance_factors,
                recommendations=recommendations,
                metadata={
                    'agent_id': agent_id,
                    'forecast_period': forecast_period,
                    'predicted_deals': predicted_metrics.get('predicted_deals', 0),
                    'predicted_revenue': predicted_metrics.get('predicted_revenue', 0),
                    'current_pipeline_value': predicted_metrics.get('pipeline_value', 0)
                }
            )

        except Exception as e:
            logger.error(f"Agent performance prediction failed: {e}")
            return self._create_fallback_prediction(PredictionType.AGENT_PERFORMANCE)

    async def optimize_pricing_strategy(
        self,
        property_data: Dict,
        market_conditions: Dict,
        urgency_level: float = 0.5
    ) -> PredictionResult:
        """
        Optimize pricing strategy for a property

        Args:
            property_data: Property information
            market_conditions: Current market conditions
            urgency_level: Urgency to sell (0-1)

        Returns:
            PredictionResult with optimal pricing recommendations
        """

        try:
            # 1. Extract property and market features
            pricing_features = await self._extract_pricing_features(property_data, market_conditions)

            # 2. Predict optimal price
            optimal_price = await self._predict_optimal_price(pricing_features, urgency_level)

            # 3. Calculate pricing factors
            pricing_factors = await self._analyze_pricing_factors(
                property_data, market_conditions, optimal_price
            )

            # 4. Calculate confidence in pricing prediction
            confidence = self._calculate_pricing_confidence(property_data, market_conditions)

            # 5. Generate pricing recommendations
            recommendations = await self._generate_pricing_recommendations(
                optimal_price, pricing_factors, urgency_level
            )

            # 6. Calculate price range (confidence interval)
            market_volatility = market_conditions.get('volatility', 0.05)
            price_range = optimal_price * market_volatility
            lower_bound = optimal_price - price_range
            upper_bound = optimal_price + price_range

            return PredictionResult(
                prediction_type=PredictionType.PRICE_OPTIMIZATION,
                primary_prediction=optimal_price,
                confidence=confidence,
                confidence_interval=(lower_bound, upper_bound),
                contributing_factors=pricing_factors,
                recommendations=recommendations,
                metadata={
                    'property_id': property_data.get('id', 'unknown'),
                    'current_list_price': property_data.get('list_price', 0),
                    'price_adjustment': optimal_price - property_data.get('list_price', 0),
                    'urgency_level': urgency_level,
                    'expected_days_on_market': pricing_factors.get('expected_dom', 30)
                }
            )

        except Exception as e:
            logger.error(f"Pricing optimization failed: {e}")
            return self._create_fallback_prediction(PredictionType.PRICE_OPTIMIZATION)

    # Feature extraction methods

    async def _extract_deal_features(self, deal_data: Dict, agent_id: str, tenant_id: str) -> Dict:
        """Extract features for deal closure prediction"""
        features = {}

        # Deal characteristics
        features['deal_value'] = deal_data.get('value', 0)
        features['deal_stage'] = deal_data.get('stage', 'initial')
        features['days_in_pipeline'] = deal_data.get('days_in_pipeline', 0)
        features['lead_score'] = deal_data.get('lead_score', 50)

        # Property characteristics
        property_data = deal_data.get('property', {})
        features['property_price'] = property_data.get('price', 0)
        features['property_type'] = property_data.get('type', 'single-family')
        features['property_bedrooms'] = property_data.get('bedrooms', 3)
        features['days_on_market'] = property_data.get('days_on_market', 30)

        # Agent performance
        agent_perf = await self._get_agent_performance_history(agent_id, tenant_id)
        features['agent_conversion_rate'] = agent_perf.get('conversion_rate', 0.2)
        features['agent_avg_deal_time'] = agent_perf.get('avg_deal_time', 45)

        # Market conditions
        market_data = await self._get_market_data(
            property_data.get('region', 'general'),
            property_data.get('type', 'general')
        )
        features['market_trend'] = market_data.get('price_trend', 0)
        features['market_volume'] = market_data.get('volume_trend', 0)

        # Financing factors
        features['financing_approved'] = 1 if deal_data.get('financing_approved') else 0
        features['cash_buyer'] = 1 if deal_data.get('cash_buyer') else 0

        # Lead engagement
        features['property_views'] = deal_data.get('property_views', 1)
        features['agent_interactions'] = deal_data.get('agent_interactions', 1)
        features['showing_requests'] = deal_data.get('showing_requests', 0)

        return features

    async def _extract_market_features(self, region: str, property_type: str) -> Dict:
        """Extract features for market trend prediction"""
        features = {}

        # Historical price trends
        historical_data = self.market_data_cache.get(f"{region}_{property_type}", {})
        features['price_trend_30d'] = historical_data.get('price_trend_30d', 0)
        features['price_trend_90d'] = historical_data.get('price_trend_90d', 0)
        features['price_trend_365d'] = historical_data.get('price_trend_365d', 0)

        # Volume trends
        features['volume_trend_30d'] = historical_data.get('volume_trend_30d', 0)
        features['inventory_levels'] = historical_data.get('inventory_months', 3)

        # Economic indicators
        features['interest_rates'] = historical_data.get('current_interest_rate', 6.5)
        features['employment_rate'] = historical_data.get('employment_rate', 95)
        features['income_growth'] = historical_data.get('income_growth', 2)

        # Seasonal factors
        current_month = datetime.now().month
        features['seasonal_factor'] = self._get_seasonal_factor(current_month, region)

        # Supply and demand
        features['new_listings'] = historical_data.get('new_listings_trend', 0)
        features['pending_sales'] = historical_data.get('pending_sales_trend', 0)

        return features

    async def _extract_agent_features(self, agent_id: str, tenant_id: str) -> Dict:
        """Extract features for agent performance prediction"""
        features = {}

        # Historical performance
        history = await self._get_agent_performance_history(agent_id, tenant_id)
        features['historical_conversion_rate'] = history.get('conversion_rate', 0.2)
        features['avg_deal_size'] = history.get('avg_deal_size', 350000)
        features['avg_deal_time'] = history.get('avg_deal_time', 45)

        # Recent activity
        features['current_pipeline_size'] = history.get('current_pipeline_size', 5)
        features['recent_activity_score'] = history.get('activity_score', 0.5)

        # Skills and training
        features['experience_years'] = history.get('experience_years', 2)
        features['training_score'] = history.get('training_score', 0.7)
        features['certification_level'] = history.get('certification_level', 1)

        # Market specialization
        features['market_expertise'] = history.get('market_expertise_score', 0.6)
        features['property_type_expertise'] = history.get('property_expertise_score', 0.6)

        return features

    async def _extract_pricing_features(self, property_data: Dict, market_conditions: Dict) -> Dict:
        """Extract features for pricing optimization"""
        features = {}

        # Property characteristics
        features['bedrooms'] = property_data.get('bedrooms', 3)
        features['bathrooms'] = property_data.get('bathrooms', 2)
        features['square_feet'] = property_data.get('square_feet', 2000)
        features['year_built'] = property_data.get('year_built', 1990)
        features['lot_size'] = property_data.get('lot_size', 0.25)

        # Location factors
        features['school_rating'] = property_data.get('school_rating', 5)
        features['walkability_score'] = property_data.get('walkability_score', 50)
        features['crime_score'] = property_data.get('crime_score', 50)

        # Market conditions
        features['median_price_psf'] = market_conditions.get('median_price_psf', 200)
        features['days_on_market_avg'] = market_conditions.get('avg_days_on_market', 30)
        features['absorption_rate'] = market_conditions.get('absorption_rate', 0.5)

        # Comparable sales
        features['comp_price_avg'] = market_conditions.get('recent_comp_avg', 0)
        features['comp_count'] = market_conditions.get('comp_count', 0)

        return features

    # Prediction helper methods

    async def _predict_closure_timeline(self, deal_data: Dict, closure_probability: float) -> int:
        """Predict days to closure based on deal characteristics"""
        base_timeline = 45  # Average days to close

        # Adjust based on deal characteristics
        if deal_data.get('cash_buyer'):
            base_timeline *= 0.7  # Faster for cash buyers
        if deal_data.get('financing_approved'):
            base_timeline *= 0.8  # Faster if pre-approved

        # Adjust based on closure probability
        urgency_factor = 1 - (closure_probability * 0.3)
        base_timeline *= urgency_factor

        return int(base_timeline)

    async def _predict_optimal_price(self, features: Dict, urgency_level: float) -> float:
        """Predict optimal price for a property"""
        if self.price_prediction_model:
            try:
                feature_vector = self._create_feature_vector(features, 'pricing')
                base_price = self.price_prediction_model.predict([feature_vector])[0]

                # Adjust for urgency
                urgency_discount = urgency_level * 0.05  # Up to 5% discount for urgent sales
                optimal_price = base_price * (1 - urgency_discount)

                return optimal_price
            except Exception as e:
                logger.warning(f"ML pricing prediction failed: {e}")

        # Fallback: rule-based pricing
        comp_price = features.get('comp_price_avg', 400000)
        sqft = features.get('square_feet', 2000)

        price_per_sqft = comp_price / sqft if sqft > 0 else 200
        property_sqft = features.get('square_feet', 2000)

        return price_per_sqft * property_sqft

    # Analysis methods

    async def _analyze_deal_factors(self, deal_data: Dict, agent_id: str) -> Dict[str, float]:
        """Analyze factors contributing to deal closure probability"""
        factors = {}

        # Lead qualification strength
        lead_score = deal_data.get('lead_score', 50)
        factors['lead_qualification'] = lead_score / 100

        # Financial readiness
        financing_ready = deal_data.get('financing_approved', False)
        cash_buyer = deal_data.get('cash_buyer', False)
        factors['financial_readiness'] = 0.9 if cash_buyer else (0.7 if financing_ready else 0.3)

        # Property attractiveness
        days_on_market = deal_data.get('property', {}).get('days_on_market', 30)
        factors['property_attractiveness'] = max(0.1, 1.0 - (days_on_market / 180))

        # Agent effectiveness
        agent_perf = self.agent_performance_history.get(agent_id, {})
        factors['agent_effectiveness'] = agent_perf.get('conversion_rate', 0.2) / 0.4  # Normalize to 0-1

        # Market conditions
        market_favorability = 0.6  # Mock value - in production, calculate from real market data
        factors['market_conditions'] = market_favorability

        # Deal momentum
        interactions = deal_data.get('agent_interactions', 1)
        views = deal_data.get('property_views', 1)
        factors['deal_momentum'] = min(1.0, (interactions + views) / 10)

        return factors

    async def _analyze_market_factors(self, region: str, property_type: str) -> Dict[str, float]:
        """Analyze market factors for trend prediction"""
        factors = {}

        # Supply and demand balance
        factors['supply_demand_ratio'] = 0.8  # Mock - in production, calculate from inventory data

        # Price momentum
        factors['price_momentum'] = 0.05  # Mock 5% annual appreciation

        # Economic indicators
        factors['economic_strength'] = 0.7  # Mock economic health score

        # Seasonal influence
        current_month = datetime.now().month
        factors['seasonal_factor'] = self._get_seasonal_factor(current_month, region)

        # Market volatility
        factors['market_volatility'] = 0.1  # Mock 10% typical volatility

        # Interest rate impact
        factors['interest_rate_impact'] = 0.6  # Mock impact score

        return factors

    async def _analyze_agent_factors(self, agent_history: Dict, features: Dict) -> Dict[str, float]:
        """Analyze agent performance factors"""
        factors = {}

        # Experience level
        years = features.get('experience_years', 2)
        factors['experience_factor'] = min(1.0, years / 10)  # Normalize to max 10 years

        # Market knowledge
        factors['market_expertise'] = features.get('market_expertise', 0.6)

        # Recent performance trend
        recent_rate = features.get('recent_conversion_rate', 0.2)
        historical_rate = features.get('historical_conversion_rate', 0.2)
        factors['performance_trend'] = recent_rate / max(historical_rate, 0.1)

        # Pipeline management
        pipeline_size = features.get('current_pipeline_size', 5)
        factors['pipeline_efficiency'] = min(1.0, pipeline_size / 15)  # Normalize

        # Training and development
        factors['skill_development'] = features.get('training_score', 0.7)

        # Performance consistency
        factors['performance_consistency'] = 1.0 - agent_history.get('performance_variance', 0.2)

        return factors

    async def _analyze_pricing_factors(
        self,
        property_data: Dict,
        market_conditions: Dict,
        optimal_price: float
    ) -> Dict[str, float]:
        """Analyze factors affecting optimal pricing"""
        factors = {}

        # Market positioning
        current_price = property_data.get('list_price', optimal_price)
        factors['market_positioning'] = optimal_price / current_price if current_price > 0 else 1.0

        # Competitive landscape
        factors['competition_level'] = market_conditions.get('inventory_months', 3) / 6  # Normalize

        # Property condition
        year_built = property_data.get('year_built', 1990)
        current_year = datetime.now().year
        property_age = current_year - year_built
        factors['property_condition'] = max(0.3, 1.0 - (property_age / 100))

        # Location desirability
        factors['location_premium'] = property_data.get('location_score', 0.7)

        # Market timing
        factors['market_timing'] = market_conditions.get('market_timing_score', 0.6)

        # Pricing strategy effectiveness
        factors['pricing_strategy'] = 0.8  # Mock - based on pricing model confidence

        return factors

    # Recommendation generation

    async def _generate_deal_recommendations(
        self,
        closure_probability: float,
        factors: Dict[str, float],
        deal_data: Dict
    ) -> List[str]:
        """Generate actionable recommendations for deal closure"""
        recommendations = []

        if closure_probability < 0.4:
            recommendations.append("🔴 HIGH RISK: Consider re-qualifying lead or adjusting approach")

            if factors.get('financial_readiness', 0) < 0.5:
                recommendations.append("💰 Focus on financial pre-qualification and lending options")

            if factors.get('agent_effectiveness', 0) < 0.5:
                recommendations.append("👤 Consider agent coaching or lead reassignment")

        elif closure_probability < 0.7:
            recommendations.append("🟡 MODERATE RISK: Increase engagement and address concerns")

            if factors.get('deal_momentum', 0) < 0.5:
                recommendations.append("⚡ Schedule additional property viewings or virtual tours")

        else:
            recommendations.append("🟢 HIGH PROBABILITY: Focus on closing logistics")
            recommendations.append("📋 Prepare closing documents and coordinate inspections")

        # Specific factor-based recommendations
        if factors.get('property_attractiveness', 0) < 0.5:
            recommendations.append("🏠 Consider property improvements or pricing adjustments")

        if factors.get('market_conditions', 0) > 0.7:
            recommendations.append("📈 Leverage strong market conditions in negotiations")

        return recommendations

    async def _generate_market_recommendations(
        self,
        price_trend: float,
        factors: Dict[str, float],
        region: str,
        property_type: str
    ) -> List[str]:
        """Generate market strategy recommendations"""
        recommendations = []

        if price_trend > 0.05:  # Rising market
            recommendations.append("📈 RISING MARKET: Aggressive pricing strategy recommended")
            recommendations.append("⏰ Encourage buyers to act quickly before further increases")

        elif price_trend < -0.05:  # Falling market
            recommendations.append("📉 DECLINING MARKET: Conservative pricing and flexible terms")
            recommendations.append("💡 Focus on value propositions and unique property features")

        else:  # Stable market
            recommendations.append("📊 STABLE MARKET: Competitive pricing with strong marketing")

        # Factor-specific recommendations
        if factors.get('supply_demand_ratio', 0.5) > 0.7:
            recommendations.append("🏠 High inventory levels - emphasize unique selling points")

        if factors.get('seasonal_factor', 0.5) > 0.7:
            recommendations.append("🌟 Favorable seasonal timing - maximize marketing exposure")

        return recommendations

    async def _generate_agent_recommendations(
        self,
        predicted_metrics: Dict,
        factors: Dict[str, float],
        history: Dict
    ) -> List[str]:
        """Generate agent performance improvement recommendations"""
        recommendations = []

        predicted_conversion = predicted_metrics.get('predicted_conversion_rate', 0.2)

        if predicted_conversion < 0.15:
            recommendations.append("🎯 FOCUS: Improve lead qualification and follow-up processes")

            if factors.get('pipeline_efficiency', 0) < 0.5:
                recommendations.append("📋 Optimize pipeline management - reduce lead volume, increase quality")

        elif predicted_conversion < 0.25:
            recommendations.append("📈 DEVELOP: Sales skills training and market knowledge")

        else:
            recommendations.append("🌟 OPTIMIZE: Focus on high-value opportunities and referrals")

        # Specific factor recommendations
        if factors.get('experience_factor', 0) < 0.5:
            recommendations.append("📚 Recommended: Advanced real estate training and certification")

        if factors.get('market_expertise', 0) < 0.6:
            recommendations.append("🗺️ Improve: Local market knowledge and neighborhood expertise")

        if factors.get('performance_consistency', 0) < 0.7:
            recommendations.append("⚖️ Focus: Consistent follow-up and systematic sales process")

        return recommendations

    async def _generate_pricing_recommendations(
        self,
        optimal_price: float,
        factors: Dict[str, float],
        urgency_level: float
    ) -> List[str]:
        """Generate pricing strategy recommendations"""
        recommendations = []

        positioning = factors.get('market_positioning', 1.0)

        if positioning > 1.1:  # Overpriced
            price_reduction = (positioning - 1.0) * 100
            recommendations.append(f"📉 REDUCE PRICE: Consider {price_reduction:.1f}% reduction to ${optimal_price:,.0f}")

        elif positioning < 0.9:  # Underpriced
            price_increase = (1.0 - positioning) * 100
            recommendations.append(f"📈 INCREASE PRICE: Consider {price_increase:.1f}% increase to ${optimal_price:,.0f}")

        else:  # Well-priced
            recommendations.append(f"✅ OPTIMAL PRICING: Current price near optimal (${optimal_price:,.0f})")

        # Urgency-based recommendations
        if urgency_level > 0.7:
            recommendations.append("⚡ HIGH URGENCY: Consider competitive pricing and incentives")

        # Factor-specific recommendations
        if factors.get('competition_level', 0.5) > 0.7:
            recommendations.append("🏃 HIGH COMPETITION: Price aggressively or enhance value proposition")

        if factors.get('location_premium', 0.5) > 0.8:
            recommendations.append("🌟 PREMIUM LOCATION: Leverage location in pricing and marketing")

        return recommendations

    # Utility methods

    def _create_feature_vector(self, features: Dict, prediction_type: str) -> np.ndarray:
        """Create standardized feature vector for ML models"""
        # This would be implemented based on the trained model requirements
        # For now, return a placeholder vector

        feature_list = list(features.values())
        numeric_features = [float(f) if isinstance(f, (int, float)) else 0.0 for f in feature_list]

        # Pad or truncate to expected size
        expected_size = 20  # Mock expected feature count
        if len(numeric_features) < expected_size:
            numeric_features.extend([0.0] * (expected_size - len(numeric_features)))

        return np.array(numeric_features[:expected_size])

    def _calculate_prediction_confidence(self, prediction_type: str, features: Dict) -> float:
        """Calculate confidence in prediction based on data quality"""
        # Data completeness
        total_features = len(features)
        non_zero_features = sum(1 for v in features.values() if v != 0)
        completeness = non_zero_features / max(total_features, 1)

        # Model accuracy (if available)
        model_accuracy = self.model_accuracy.get(prediction_type, 0.7)

        # Historical prediction accuracy
        recent_predictions = [p for p in self.prediction_history[-50:]
                            if p.get('type') == prediction_type]

        historical_accuracy = 0.7  # Default
        if recent_predictions:
            accuracies = [p.get('accuracy', 0.7) for p in recent_predictions]
            historical_accuracy = np.mean(accuracies)

        # Combine factors
        confidence = 0.4 * completeness + 0.3 * model_accuracy + 0.3 * historical_accuracy
        return min(max(confidence, 0.1), 0.95)

    def _calculate_market_prediction_confidence(self, region: str, property_type: str) -> float:
        """Calculate confidence in market predictions"""
        # Data availability
        data_key = f"{region}_{property_type}"
        market_data = self.market_data_cache.get(data_key, {})
        data_completeness = len(market_data) / 15  # Expected number of market indicators

        # Historical accuracy for this market
        regional_accuracy = 0.65  # Mock regional model accuracy

        return min(max(0.4 * data_completeness + 0.6 * regional_accuracy, 0.2), 0.9)

    def _calculate_agent_prediction_confidence(self, agent_history: Dict) -> float:
        """Calculate confidence in agent performance predictions"""
        # Historical data depth
        data_points = agent_history.get('data_points', 10)
        data_depth = min(data_points / 50, 1.0)  # Normalize to 50 data points max

        # Performance consistency
        consistency = 1.0 - agent_history.get('performance_variance', 0.3)

        # Recent activity level
        activity = min(agent_history.get('recent_activity', 0.5), 1.0)

        return 0.4 * data_depth + 0.4 * consistency + 0.2 * activity

    def _calculate_pricing_confidence(self, property_data: Dict, market_conditions: Dict) -> float:
        """Calculate confidence in pricing predictions"""
        # Comparable sales count
        comp_count = market_conditions.get('comp_count', 0)
        comp_confidence = min(comp_count / 10, 1.0)  # Normalize to 10 comps

        # Property data completeness
        required_fields = ['bedrooms', 'bathrooms', 'square_feet', 'year_built']
        available_fields = sum(1 for field in required_fields if property_data.get(field))
        data_completeness = available_fields / len(required_fields)

        # Market data freshness
        market_freshness = 0.8  # Mock freshness score

        return 0.4 * comp_confidence + 0.3 * data_completeness + 0.3 * market_freshness

    def _get_seasonal_factor(self, month: int, region: str) -> float:
        """Get seasonal factor for real estate activity"""
        # Mock seasonal factors (spring/summer higher activity)
        seasonal_map = {
            1: 0.7, 2: 0.6, 3: 0.8, 4: 0.9, 5: 1.0, 6: 1.0,
            7: 0.9, 8: 0.8, 9: 0.8, 10: 0.7, 11: 0.6, 12: 0.5
        }

        return seasonal_map.get(month, 0.7)

    def _create_fallback_prediction(self, prediction_type: PredictionType) -> PredictionResult:
        """Create fallback prediction when models fail"""
        defaults = {
            PredictionType.DEAL_CLOSURE: 0.5,
            PredictionType.MARKET_TREND: 0.02,  # 2% appreciation
            PredictionType.AGENT_PERFORMANCE: 0.2,  # 20% conversion
            PredictionType.PRICE_OPTIMIZATION: 400000  # Default price
        }

        return PredictionResult(
            prediction_type=prediction_type,
            primary_prediction=defaults.get(prediction_type, 0.5),
            confidence=0.3,  # Low confidence for fallback
            confidence_interval=(0.1, 0.9),
            contributing_factors={'model_unavailable': 1.0},
            recommendations=['⚠️ Limited prediction data - manual review recommended']
        )

    # Data loading and model training (mock implementations)

    async def _load_historical_data(self) -> None:
        """Load historical data for model training"""
        # Mock implementation - in production, load from database
        self.historical_deals = []
        self.market_data_cache = {}
        self.agent_performance_history = {}

    async def _train_models(self) -> None:
        """Train ML models from historical data"""
        # Mock implementation - in production, implement full ML pipeline
        try:
            # Initialize models with default parameters
            self.deal_closure_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.price_prediction_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            self.conversion_model = MLPRegressor(hidden_layer_sizes=(50, 25), random_state=42)
            self.market_trend_model = GradientBoostingRegressor(n_estimators=100, random_state=42)

            # Set mock accuracy scores
            self.model_accuracy = {
                'deal_closure': 0.82,
                'market_trend': 0.75,
                'agent_performance': 0.78,
                'pricing': 0.85
            }

            logger.info("✅ Predictive models initialized (training data needed for full functionality)")

        except Exception as e:
            logger.error(f"Model training failed: {e}")

    async def _initialize_market_intelligence(self) -> None:
        """Initialize market intelligence system"""
        # Mock market insights
        self.current_market_insights = {
            'austin_single_family': MarketInsight(
                region='austin',
                property_type='single_family',
                trend_direction='rising',
                price_change_percent=8.5,
                volume_change_percent=-12.0,
                days_on_market_trend=-5.0,
                demand_supply_ratio=1.3,
                seasonal_factor=0.9
            ),
            'austin_condo': MarketInsight(
                region='austin',
                property_type='condo',
                trend_direction='stable',
                price_change_percent=2.1,
                volume_change_percent=3.0,
                days_on_market_trend=2.0,
                demand_supply_ratio=0.8,
                seasonal_factor=0.8
            )
        }

    async def _get_market_data(self, region: str, property_type: str) -> Dict:
        """Get current market data for region and property type"""
        # Mock implementation
        return {
            'median_price': 450000,
            'price_trend': 0.05,
            'volume_trend': 0.02,
            'avg_days_on_market': 28,
            'inventory_months': 2.5,
            'absorption_rate': 0.6
        }

    async def _get_agent_performance_history(self, agent_id: str, tenant_id: str) -> Dict:
        """Get agent performance history"""
        # Mock implementation
        return {
            'conversion_rate': 0.22,
            'avg_deal_size': 385000,
            'avg_deal_time': 42,
            'current_pipeline_size': 8,
            'activity_score': 0.7,
            'experience_years': 3,
            'training_score': 0.8,
            'market_expertise': 0.75,
            'performance_variance': 0.15,
            'data_points': 45,
            'recent_activity': 0.8
        }

    async def _predict_agent_metrics(self, features: Dict, forecast_period: str) -> Dict:
        """Predict agent performance metrics"""
        base_conversion = features.get('historical_conversion_rate', 0.2)

        # Adjust based on trends and features
        trend_adjustment = features.get('performance_trend', 1.0)
        predicted_conversion = base_conversion * trend_adjustment

        pipeline_size = features.get('current_pipeline_size', 5)
        avg_deal_size = features.get('avg_deal_size', 350000)

        period_multiplier = {'weekly': 0.25, 'monthly': 1.0, 'quarterly': 3.0}.get(forecast_period, 1.0)

        return {
            'predicted_conversion_rate': predicted_conversion,
            'predicted_deals': int(pipeline_size * predicted_conversion * period_multiplier),
            'predicted_revenue': pipeline_size * predicted_conversion * avg_deal_size * period_multiplier,
            'pipeline_value': pipeline_size * avg_deal_size
        }


# Global instance
predictive_analytics = PredictiveAnalyticsEngine()


# Convenience functions
async def predict_deal_closure_probability(
    lead_id: str, deal_data: Dict, agent_id: str, tenant_id: str
) -> PredictionResult:
    """Predict deal closure probability"""
    return await predictive_analytics.predict_deal_closure(lead_id, deal_data, agent_id, tenant_id)


async def predict_market_trends(region: str, property_type: str, forecast_days: int = 90) -> PredictionResult:
    """Predict market trends"""
    return await predictive_analytics.predict_market_trends(region, property_type, forecast_days)


async def predict_agent_performance(agent_id: str, tenant_id: str, forecast_period: str = "monthly") -> PredictionResult:
    """Predict agent performance"""
    return await predictive_analytics.predict_agent_performance(agent_id, tenant_id, forecast_period)


async def optimize_property_pricing(property_data: Dict, market_conditions: Dict, urgency_level: float = 0.5) -> PredictionResult:
    """Optimize property pricing strategy"""
    return await predictive_analytics.optimize_pricing_strategy(property_data, market_conditions, urgency_level)