"""
Advanced Market Prediction Analytics Engine for Jorge's Rancho Cucamonga Real Estate Platform

Provides ML-powered market intelligence and forecasting including:
- Rancho Cucamonga neighborhood appreciation predictions
- Optimal listing timing recommendations for sellers
- Market opportunity detection (undervalued properties, emerging areas)
- Interest rate impact analysis on Jorge's pipeline
- Seasonal pattern analysis for Inland Empire market
- Investment property ROI predictions

This system transforms Jorge's market analysis from reactive to predictive,
providing insights no competitor in the Inland Empire can match.
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
import uuid
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.rancho_cucamonga_ai_assistant import get_rancho_cucamonga_ai_assistant
from ghl_real_estate_ai.data.rancho_cucamonga_market_data import get_rancho_cucamonga_market_intelligence
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class PredictionType(Enum):
    """Types of market predictions"""
    PRICE_APPRECIATION = "price_appreciation"
    OPTIMAL_TIMING = "optimal_timing"
    MARKET_OPPORTUNITY = "market_opportunity"
    INVESTMENT_ROI = "investment_roi"
    SEASONAL_PATTERN = "seasonal_pattern"
    INTEREST_RATE_IMPACT = "interest_rate_impact"


class MarketConfidence(Enum):
    """Confidence levels for predictions"""
    HIGH = "high"          # >80% confidence
    MEDIUM = "medium"      # 60-80% confidence
    LOW = "low"            # 40-60% confidence
    UNCERTAIN = "uncertain"  # <40% confidence


class TimeHorizon(Enum):
    """Prediction time horizons"""
    SHORT_TERM = "short_term"    # 1-3 months
    MEDIUM_TERM = "medium_term"  # 3-12 months
    LONG_TERM = "long_term"      # 1-3 years


@dataclass
class MarketDataPoint:
    """Single market data point for ML training"""
    date: datetime
    neighborhood: str
    median_price: float
    days_on_market: int
    inventory_months: float
    price_per_sqft: float

    # Economic indicators
    interest_rate: float
    employment_rate: float
    population_growth: float
    new_construction: int

    # Seasonal factors
    month: int
    quarter: int
    is_spring_market: bool
    is_holiday_season: bool

    # External factors
    gas_prices: float
    mortgage_applications: int
    consumer_confidence: float


@dataclass
class PredictionResult:
    """Market prediction result"""
    prediction_id: str
    prediction_type: PredictionType
    target: str  # neighborhood, property, market segment
    time_horizon: TimeHorizon

    # Prediction details
    predicted_value: float
    current_value: float
    change_percentage: float
    confidence_level: MarketConfidence
    confidence_score: float  # 0-1

    # Supporting data
    key_factors: List[str]
    risk_factors: List[str]
    opportunities: List[str]

    # Timing information
    prediction_date: datetime
    target_date: datetime
    update_frequency: str  # daily, weekly, monthly

    # Model information
    model_accuracy: float
    data_points_used: int
    last_training_date: datetime

    def __post_init__(self):
        if self.prediction_date is None:
            self.prediction_date = datetime.now()


@dataclass
class MarketOpportunity:
    """Identified market opportunity"""
    opportunity_id: str
    opportunity_type: str  # undervalued, emerging, timing
    neighborhood: str
    description: str

    # Opportunity metrics
    potential_return: float
    confidence_score: float
    timeline: str
    investment_required: float

    # Risk assessment
    risk_level: str  # low, medium, high
    risk_factors: List[str]
    mitigation_strategies: List[str]

    # Action items
    recommended_actions: List[str]
    ideal_client_profile: str

    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class MarketPredictionEngine:
    """
    Advanced Market Prediction Analytics Engine

    Features:
    - ML-powered price appreciation forecasting
    - Optimal timing analysis for buying/selling
    - Market opportunity detection and scoring
    - Investment ROI predictions with risk analysis
    - Seasonal pattern recognition and forecasting
    - Interest rate impact modeling
    """

    def __init__(self):
        self.llm_client = LLMClient(provider="claude")
        self.rc_assistant = get_rancho_cucamonga_ai_assistant()
        self.cache = get_cache_service()
        self.market_intelligence = get_rancho_cucamonga_market_intelligence()

        # ML Models (stored in memory, in production would persist to disk)
        self.models = {}
        self.scalers = {}
        self.model_metadata = {}

        # Historical data and features
        self.market_data = []
        self.feature_names = []

        # Prediction cache
        self.predictions_cache = {}
        self.opportunities_cache = {}

        # Initialize with mock data and train models
        asyncio.create_task(self._initialize_models())

    async def _initialize_models(self):
        """Initialize and train ML models with historical data"""
        try:
            # Load historical market data
            await self._load_historical_data()

            # Train prediction models
            await self._train_models()

            logger.info("Market prediction models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing prediction models: {e}")

    async def _load_historical_data(self):
        """Load historical market data for training"""
        # In production, this would load from database or external APIs
        # For demo, we'll generate synthetic historical data

        start_date = datetime.now() - timedelta(days=365 * 3)  # 3 years of data
        current_date = start_date

        neighborhoods = ["etiwanda", "alta_loma", "central_rc", "north_rc", "south_rc"]
        base_prices = {
            "etiwanda": 650000,
            "alta_loma": 850000,
            "central_rc": 720000,
            "north_rc": 680000,
            "south_rc": 590000
        }

        while current_date < datetime.now():
            for neighborhood in neighborhoods:
                # Generate synthetic but realistic market data
                data_point = self._generate_synthetic_data_point(
                    current_date, neighborhood, base_prices[neighborhood]
                )
                self.market_data.append(data_point)

            current_date += timedelta(days=7)  # Weekly data points

        logger.info(f"Loaded {len(self.market_data)} historical market data points")

    def _generate_synthetic_data_point(self, date: datetime, neighborhood: str, base_price: float) -> MarketDataPoint:
        """Generate realistic synthetic market data point"""

        # Add seasonal and trend variations
        days_since_start = (date - datetime(2021, 1, 1)).days
        trend_factor = 1 + (days_since_start / 365) * 0.05  # 5% annual appreciation

        seasonal_factor = 1.0
        month = date.month
        if month in [3, 4, 5]:  # Spring market
            seasonal_factor = 1.1
        elif month in [6, 7, 8]:  # Summer
            seasonal_factor = 1.05
        elif month in [11, 12]:  # Winter slowdown
            seasonal_factor = 0.95

        # Neighborhood-specific factors
        neighborhood_factors = {
            "etiwanda": 1.02,  # Strong schools drive demand
            "alta_loma": 1.01,  # Luxury market stability
            "central_rc": 1.03,  # Development growth
            "north_rc": 1.02,   # Family demand
            "south_rc": 1.04    # Affordability growth
        }

        adjusted_price = base_price * trend_factor * seasonal_factor * neighborhood_factors[neighborhood]

        # Add some randomness
        import random
        price_variation = random.uniform(0.95, 1.05)
        adjusted_price *= price_variation

        return MarketDataPoint(
            date=date,
            neighborhood=neighborhood,
            median_price=adjusted_price,
            days_on_market=random.randint(15, 45),
            inventory_months=random.uniform(1.5, 4.0),
            price_per_sqft=adjusted_price / random.uniform(1800, 2500),
            interest_rate=random.uniform(3.0, 7.0),
            employment_rate=random.uniform(0.92, 0.97),
            population_growth=random.uniform(0.01, 0.04),
            new_construction=random.randint(50, 200),
            month=month,
            quarter=(month - 1) // 3 + 1,
            is_spring_market=month in [3, 4, 5],
            is_holiday_season=month in [11, 12],
            gas_prices=random.uniform(3.5, 5.5),
            mortgage_applications=random.randint(8000, 15000),
            consumer_confidence=random.uniform(85, 115)
        )

    async def _train_models(self):
        """Train ML models for different prediction types"""

        if not self.market_data:
            logger.warning("No market data available for training")
            return

        # Convert data to DataFrame
        df = pd.DataFrame([asdict(point) for point in self.market_data])
        df['date'] = pd.to_datetime(df['date'])

        # Train price appreciation model
        await self._train_price_appreciation_model(df)

        # Train optimal timing model
        await self._train_timing_model(df)

        # Train investment ROI model
        await self._train_roi_model(df)

        logger.info("ML models trained successfully")

    async def _train_price_appreciation_model(self, df: pd.DataFrame):
        """Train price appreciation prediction model"""

        # Prepare features for price appreciation
        features = [
            'days_on_market', 'inventory_months', 'interest_rate', 'employment_rate',
            'population_growth', 'new_construction', 'month', 'quarter',
            'is_spring_market', 'is_holiday_season', 'gas_prices',
            'mortgage_applications', 'consumer_confidence'
        ]

        # Create target variable (3-month price change)
        df = df.sort_values(['neighborhood', 'date'])
        df['future_price'] = df.groupby('neighborhood')['median_price'].shift(-12)  # 12 weeks = ~3 months
        df['price_change_pct'] = (df['future_price'] - df['median_price']) / df['median_price']

        # Remove rows without future price data
        train_df = df.dropna(subset=['price_change_pct'])

        if len(train_df) < 50:
            logger.warning("Insufficient data for price appreciation model")
            return

        X = train_df[features]
        y = train_df['price_change_pct']

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)

        # Evaluate model
        y_pred = model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Store model
        self.models['price_appreciation'] = model
        self.scalers['price_appreciation'] = scaler
        self.model_metadata['price_appreciation'] = {
            'features': features,
            'mae': mae,
            'r2': r2,
            'training_date': datetime.now(),
            'data_points': len(train_df)
        }

        logger.info(f"Price appreciation model trained: R² = {r2:.3f}, MAE = {mae:.4f}")

    async def _train_timing_model(self, df: pd.DataFrame):
        """Train optimal timing prediction model"""

        # Simplified timing model based on seasonal patterns and market indicators
        features = [
            'inventory_months', 'interest_rate', 'month', 'quarter',
            'is_spring_market', 'consumer_confidence'
        ]

        # Create timing score (0-1, where 1 is optimal time to sell)
        df['timing_score'] = 0.5  # Base score

        # Seasonal adjustments
        df.loc[df['is_spring_market'], 'timing_score'] += 0.3
        df.loc[df['month'].isin([11, 12]), 'timing_score'] -= 0.2

        # Market condition adjustments
        df.loc[df['inventory_months'] < 2, 'timing_score'] += 0.2  # Low inventory favors sellers
        df.loc[df['inventory_months'] > 4, 'timing_score'] -= 0.2  # High inventory favors buyers

        # Interest rate adjustments
        df.loc[df['interest_rate'] < 4, 'timing_score'] += 0.1  # Low rates increase demand
        df.loc[df['interest_rate'] > 6, 'timing_score'] -= 0.1  # High rates decrease demand

        # Clip scores to 0-1 range
        df['timing_score'] = df['timing_score'].clip(0, 1)

        X = df[features]
        y = df['timing_score']

        # Train model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Store model
        self.models['timing'] = model
        self.scalers['timing'] = scaler
        self.model_metadata['timing'] = {
            'features': features,
            'mae': mae,
            'r2': r2,
            'training_date': datetime.now(),
            'data_points': len(df)
        }

        logger.info(f"Timing model trained: R² = {r2:.3f}, MAE = {mae:.4f}")

    async def _train_roi_model(self, df: pd.DataFrame):
        """Train investment ROI prediction model"""

        features = [
            'median_price', 'price_per_sqft', 'population_growth', 'new_construction',
            'employment_rate', 'month'
        ]

        # Calculate historical ROI (simplified)
        df = df.sort_values(['neighborhood', 'date'])
        df['price_1yr_ago'] = df.groupby('neighborhood')['median_price'].shift(52)  # 52 weeks ago
        df['annual_roi'] = (df['median_price'] - df['price_1yr_ago']) / df['price_1yr_ago']

        # Remove rows without historical data
        train_df = df.dropna(subset=['annual_roi'])

        if len(train_df) < 50:
            logger.warning("Insufficient data for ROI model")
            return

        X = train_df[features]
        y = train_df['annual_roi']

        # Train model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Store model
        self.models['roi'] = model
        self.scalers['roi'] = scaler
        self.model_metadata['roi'] = {
            'features': features,
            'mae': mae,
            'r2': r2,
            'training_date': datetime.now(),
            'data_points': len(train_df)
        }

        logger.info(f"ROI model trained: R² = {r2:.3f}, MAE = {mae:.4f}")

    async def predict_price_appreciation(
        self,
        neighborhood: str,
        time_horizon: TimeHorizon,
        current_conditions: Optional[Dict[str, Any]] = None
    ) -> PredictionResult:
        """Predict price appreciation for neighborhood"""

        if 'price_appreciation' not in self.models:
            raise ValueError("Price appreciation model not trained")

        # Get current market conditions
        conditions = current_conditions or await self._get_current_market_conditions(neighborhood)

        # Prepare features
        features = self._prepare_prediction_features(conditions, 'price_appreciation')

        # Make prediction
        model = self.models['price_appreciation']
        scaler = self.scalers['price_appreciation']
        features_scaled = scaler.transform([features])

        predicted_change = model.predict(features_scaled)[0]

        # Adjust for time horizon
        horizon_multipliers = {
            TimeHorizon.SHORT_TERM: 0.25,   # 3 months
            TimeHorizon.MEDIUM_TERM: 1.0,   # 12 months
            TimeHorizon.LONG_TERM: 3.0      # 3 years
        }

        adjusted_prediction = predicted_change * horizon_multipliers[time_horizon]

        # Calculate confidence based on model performance and data recency
        confidence_score = self._calculate_confidence(
            model_accuracy=self.model_metadata['price_appreciation']['r2'],
            data_recency=0.9,  # High for synthetic data
            market_volatility=abs(predicted_change) * 2
        )

        # Get current value
        current_value = conditions.get('median_price', 700000)
        predicted_value = current_value * (1 + adjusted_prediction)

        # Generate supporting insights using AI
        insights = await self._generate_prediction_insights(
            neighborhood, 'price_appreciation', adjusted_prediction, conditions
        )

        prediction_id = str(uuid.uuid4())
        target_date = datetime.now() + self._get_horizon_timedelta(time_horizon)

        result = PredictionResult(
            prediction_id=prediction_id,
            prediction_type=PredictionType.PRICE_APPRECIATION,
            target=neighborhood,
            time_horizon=time_horizon,
            predicted_value=predicted_value,
            current_value=current_value,
            change_percentage=adjusted_prediction * 100,
            confidence_level=self._score_to_confidence_level(confidence_score),
            confidence_score=confidence_score,
            key_factors=insights['key_factors'],
            risk_factors=insights['risk_factors'],
            opportunities=insights['opportunities'],
            target_date=target_date,
            update_frequency="weekly",
            model_accuracy=self.model_metadata['price_appreciation']['r2'],
            data_points_used=self.model_metadata['price_appreciation']['data_points'],
            last_training_date=self.model_metadata['price_appreciation']['training_date']
        )

        # Cache result
        await self._cache_prediction_result(result)

        return result

    async def predict_optimal_timing(
        self,
        action_type: str,  # "buy" or "sell"
        neighborhood: str,
        property_details: Optional[Dict[str, Any]] = None
    ) -> PredictionResult:
        """Predict optimal timing for buying or selling"""

        if 'timing' not in self.models:
            raise ValueError("Timing model not trained")

        # Get current market conditions
        conditions = await self._get_current_market_conditions(neighborhood)

        # Prepare features
        features = self._prepare_prediction_features(conditions, 'timing')

        # Make prediction
        model = self.models['timing']
        scaler = self.scalers['timing']
        features_scaled = scaler.transform([features])

        timing_score = model.predict(features_scaled)[0]

        # Adjust score based on action type
        if action_type == "buy":
            # For buyers, invert the score (low seller timing = good buyer timing)
            adjusted_score = 1 - timing_score
        else:
            adjusted_score = timing_score

        # Generate timing recommendations
        timing_insights = await self._generate_timing_insights(
            action_type, neighborhood, adjusted_score, conditions
        )

        confidence_score = self._calculate_confidence(
            model_accuracy=self.model_metadata['timing']['r2'],
            data_recency=0.9,
            market_volatility=0.2
        )

        prediction_id = str(uuid.uuid4())

        result = PredictionResult(
            prediction_id=prediction_id,
            prediction_type=PredictionType.OPTIMAL_TIMING,
            target=f"{action_type}_{neighborhood}",
            time_horizon=TimeHorizon.SHORT_TERM,
            predicted_value=adjusted_score * 100,  # Convert to percentage score
            current_value=50.0,  # Baseline timing score
            change_percentage=(adjusted_score - 0.5) * 100,
            confidence_level=self._score_to_confidence_level(confidence_score),
            confidence_score=confidence_score,
            key_factors=timing_insights['key_factors'],
            risk_factors=timing_insights['risk_factors'],
            opportunities=timing_insights['opportunities'],
            target_date=datetime.now() + timedelta(weeks=4),
            update_frequency="weekly",
            model_accuracy=self.model_metadata['timing']['r2'],
            data_points_used=self.model_metadata['timing']['data_points'],
            last_training_date=self.model_metadata['timing']['training_date']
        )

        await self._cache_prediction_result(result)
        return result

    async def predict_investment_roi(
        self,
        property_data: Dict[str, Any],
        investment_horizon: int = 5  # years
    ) -> PredictionResult:
        """Predict investment ROI for a specific property"""

        if 'roi' not in self.models:
            raise ValueError("ROI model not trained")

        neighborhood = property_data.get('neighborhood', 'central_rc')
        property_price = property_data.get('price', 700000)

        # Get market conditions
        conditions = await self._get_current_market_conditions(neighborhood)
        conditions.update({
            'median_price': property_price,
            'price_per_sqft': property_price / property_data.get('sqft', 2000)
        })

        # Prepare features
        features = self._prepare_prediction_features(conditions, 'roi')

        # Make prediction
        model = self.models['roi']
        scaler = self.scalers['roi']
        features_scaled = scaler.transform([features])

        annual_roi = model.predict(features_scaled)[0]

        # Calculate compound ROI over investment horizon
        total_roi = ((1 + annual_roi) ** investment_horizon - 1)

        # Generate investment insights
        investment_insights = await self._generate_investment_insights(
            property_data, annual_roi, total_roi, conditions
        )

        confidence_score = self._calculate_confidence(
            model_accuracy=self.model_metadata['roi']['r2'],
            data_recency=0.9,
            market_volatility=abs(annual_roi) * 1.5
        )

        prediction_id = str(uuid.uuid4())
        target_date = datetime.now() + timedelta(days=365 * investment_horizon)

        result = PredictionResult(
            prediction_id=prediction_id,
            prediction_type=PredictionType.INVESTMENT_ROI,
            target=f"{neighborhood}_investment",
            time_horizon=TimeHorizon.LONG_TERM,
            predicted_value=total_roi * 100,  # Convert to percentage
            current_value=0.0,  # Starting ROI
            change_percentage=total_roi * 100,
            confidence_level=self._score_to_confidence_level(confidence_score),
            confidence_score=confidence_score,
            key_factors=investment_insights['key_factors'],
            risk_factors=investment_insights['risk_factors'],
            opportunities=investment_insights['opportunities'],
            target_date=target_date,
            update_frequency="monthly",
            model_accuracy=self.model_metadata['roi']['r2'],
            data_points_used=self.model_metadata['roi']['data_points'],
            last_training_date=self.model_metadata['roi']['training_date']
        )

        await self._cache_prediction_result(result)
        return result

    async def detect_market_opportunities(self) -> List[MarketOpportunity]:
        """Detect and score market opportunities across all neighborhoods"""

        opportunities = []

        neighborhoods = ["etiwanda", "alta_loma", "central_rc", "north_rc", "south_rc"]

        for neighborhood in neighborhoods:
            # Get price appreciation prediction
            price_prediction = await self.predict_price_appreciation(
                neighborhood, TimeHorizon.MEDIUM_TERM
            )

            # Analyze for different opportunity types
            if price_prediction.change_percentage > 8:  # Strong appreciation expected
                opportunity = await self._create_appreciation_opportunity(neighborhood, price_prediction)
                opportunities.append(opportunity)

            # Check for undervalued properties
            undervalued_opportunity = await self._detect_undervalued_opportunity(neighborhood)
            if undervalued_opportunity:
                opportunities.append(undervalued_opportunity)

            # Check for emerging area patterns
            emerging_opportunity = await self._detect_emerging_area_opportunity(neighborhood)
            if emerging_opportunity:
                opportunities.append(emerging_opportunity)

        # Sort by potential return and confidence
        opportunities.sort(key=lambda x: x.potential_return * x.confidence_score, reverse=True)

        # Cache opportunities
        for opp in opportunities:
            self.opportunities_cache[opp.opportunity_id] = opp

        logger.info(f"Detected {len(opportunities)} market opportunities")
        return opportunities

    async def analyze_seasonal_patterns(self, neighborhood: str) -> Dict[str, Any]:
        """Analyze seasonal market patterns for neighborhood"""

        # Get historical data for the neighborhood
        neighborhood_data = [
            point for point in self.market_data
            if point.neighborhood == neighborhood
        ]

        if not neighborhood_data:
            return {"error": "No data available for neighborhood"}

        # Group by month and calculate averages
        monthly_stats = {}
        for month in range(1, 13):
            month_data = [point for point in neighborhood_data if point.month == month]
            if month_data:
                monthly_stats[month] = {
                    "avg_price": np.mean([point.median_price for point in month_data]),
                    "avg_dom": np.mean([point.days_on_market for point in month_data]),
                    "avg_inventory": np.mean([point.inventory_months for point in month_data]),
                    "data_points": len(month_data)
                }

        # Analyze patterns using AI
        pattern_analysis = await self._analyze_seasonal_patterns_ai(monthly_stats, neighborhood)

        return {
            "neighborhood": neighborhood,
            "monthly_statistics": monthly_stats,
            "patterns": pattern_analysis,
            "recommendations": await self._generate_seasonal_recommendations(monthly_stats, neighborhood)
        }

    async def analyze_interest_rate_impact(
        self,
        rate_change: float,  # Predicted rate change (e.g., +0.5 for 0.5% increase)
        neighborhood: str = None
    ) -> Dict[str, Any]:
        """Analyze impact of interest rate changes on market"""

        # Get current conditions
        neighborhoods = [neighborhood] if neighborhood else ["etiwanda", "alta_loma", "central_rc", "north_rc", "south_rc"]

        impact_analysis = {}

        for nbhd in neighborhoods:
            conditions = await self._get_current_market_conditions(nbhd)
            current_rate = conditions.get('interest_rate', 5.5)
            new_rate = current_rate + rate_change

            # Calculate demand impact (simplified model)
            # Each 1% rate increase typically reduces demand by 8-12%
            demand_impact = -rate_change * 10  # Percentage change in demand

            # Price impact (demand affects prices with lag)
            price_impact = demand_impact * 0.3  # 30% of demand change flows to prices

            # Time on market impact
            dom_impact = -demand_impact * 0.5  # Lower demand = higher DOM

            impact_analysis[nbhd] = {
                "current_rate": current_rate,
                "new_rate": new_rate,
                "rate_change": rate_change,
                "demand_impact_pct": demand_impact,
                "price_impact_pct": price_impact,
                "dom_impact_days": dom_impact,
                "buyer_affordability": self._calculate_affordability_impact(
                    conditions.get('median_price', 700000), current_rate, new_rate
                )
            }

        # Generate strategic insights
        strategic_insights = await self._generate_rate_impact_insights(impact_analysis, rate_change)

        return {
            "rate_change": rate_change,
            "neighborhood_impacts": impact_analysis,
            "strategic_insights": strategic_insights,
            "timing_recommendations": await self._generate_rate_timing_recommendations(rate_change)
        }

    async def _get_current_market_conditions(self, neighborhood: str) -> Dict[str, Any]:
        """Get current market conditions for neighborhood"""

        # In production, this would pull from real data sources
        # For demo, we'll use recent synthetic data
        recent_data = [
            point for point in self.market_data
            if point.neighborhood == neighborhood and
            (datetime.now() - point.date).days <= 30
        ]

        if recent_data:
            latest = max(recent_data, key=lambda x: x.date)
            return asdict(latest)
        else:
            # Return default conditions
            return {
                'median_price': 700000,
                'days_on_market': 25,
                'inventory_months': 2.5,
                'interest_rate': 5.5,
                'employment_rate': 0.94,
                'population_growth': 0.02,
                'new_construction': 120,
                'month': datetime.now().month,
                'quarter': (datetime.now().month - 1) // 3 + 1,
                'is_spring_market': datetime.now().month in [3, 4, 5],
                'is_holiday_season': datetime.now().month in [11, 12],
                'consumer_confidence': 95.0
            }

    def _prepare_prediction_features(self, conditions: Dict[str, Any], model_type: str) -> List[float]:
        """Prepare feature vector for prediction"""

        feature_names = self.model_metadata[model_type]['features']
        features = []

        for feature in feature_names:
            value = conditions.get(feature, 0)
            # Convert boolean to int
            if isinstance(value, bool):
                value = int(value)
            features.append(value)

        return features

    async def _generate_prediction_insights(
        self,
        neighborhood: str,
        prediction_type: str,
        prediction_value: float,
        conditions: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Generate AI-powered insights for predictions"""

        prompt = f"""
Analyze this {prediction_type} prediction for {neighborhood} in Rancho Cucamonga:

Predicted Change: {prediction_value:.1%}
Current Conditions: {json.dumps(conditions, indent=2, default=str)}

As Jorge Martinez, provide insights in these categories:

1. Key Factors driving this prediction (3-4 factors)
2. Risk Factors that could affect the prediction (2-3 risks)
3. Opportunities this creates for clients (2-3 opportunities)

Focus on Inland Empire market dynamics, logistics/healthcare employment, and neighborhood-specific factors.

Return as JSON:
{
  "key_factors": ["factor1", "factor2", "factor3"],
  "risk_factors": ["risk1", "risk2"],
  "opportunities": ["opp1", "opp2", "opp3"]
}
"""

        try:
            response = await self.llm_client.agenerate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )

            insights = json.loads(response.content)
            return insights

        except Exception as e:
            logger.warning(f"AI insight generation failed: {e}")
            return {
                "key_factors": ["Market momentum", "Economic indicators", "Seasonal patterns"],
                "risk_factors": ["Interest rate changes", "Economic uncertainty"],
                "opportunities": ["Investment potential", "Timing advantages"]
            }

    async def _generate_timing_insights(
        self,
        action_type: str,
        neighborhood: str,
        timing_score: float,
        conditions: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Generate timing-specific insights"""

        score_description = "excellent" if timing_score > 0.8 else "good" if timing_score > 0.6 else "fair" if timing_score > 0.4 else "poor"

        prompt = f"""
Analyze this {action_type} timing for {neighborhood} in Rancho Cucamonga:

Timing Score: {timing_score:.2f} ({score_description})
Market Conditions: {json.dumps(conditions, indent=2, default=str)}

As Jorge Martinez, provide timing insights:

1. Key Factors supporting this timing (3-4 factors)
2. Risk Factors to consider (2-3 risks)
3. Opportunities to maximize success (2-3 opportunities)

Focus on market timing, seasonal factors, and IE-specific conditions.

Return as JSON with key_factors, risk_factors, opportunities arrays.
"""

        try:
            response = await self.llm_client.agenerate(prompt=prompt, max_tokens=500, temperature=0.7)
            return json.loads(response.content)
        except:
            return {
                "key_factors": [f"Market conditions favor {action_type}ers", "Seasonal timing alignment"],
                "risk_factors": ["Market volatility", "Interest rate uncertainty"],
                "opportunities": ["Negotiation leverage", "Selection advantages"]
            }

    async def _generate_investment_insights(
        self,
        property_data: Dict[str, Any],
        annual_roi: float,
        total_roi: float,
        conditions: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Generate investment-specific insights"""

        prompt = f"""
Analyze this investment opportunity in Rancho Cucamonga:

Property: {property_data.get('neighborhood', 'RC')} - ${property_data.get('price', 700000):,}
Predicted Annual ROI: {annual_roi:.1%}
Total ROI Projection: {total_roi:.1%}
Market Conditions: {json.dumps(conditions, indent=2, default=str)}

As Jorge Martinez, provide investment insights:

1. Key Factors supporting this investment (3-4 factors)
2. Risk Factors to evaluate (2-3 risks)
3. Opportunities to enhance returns (2-3 opportunities)

Focus on IE investment potential, rental markets, and appreciation drivers.

Return as JSON with key_factors, risk_factors, opportunities arrays.
"""

        try:
            response = await self.llm_client.agenerate(prompt=prompt, max_tokens=500, temperature=0.7)
            return json.loads(response.content)
        except:
            return {
                "key_factors": ["Strong IE growth", "Logistics employment", "Population trends"],
                "risk_factors": ["Market cycles", "Interest rate sensitivity"],
                "opportunities": ["Rental demand", "Long-term appreciation", "Tax benefits"]
            }

    def _calculate_confidence(self, model_accuracy: float, data_recency: float, market_volatility: float) -> float:
        """Calculate prediction confidence score"""

        # Weight factors
        accuracy_weight = 0.5
        recency_weight = 0.3
        volatility_weight = 0.2

        # Volatility reduces confidence (invert it)
        stability_score = max(0, 1 - min(market_volatility, 1))

        confidence = (
            model_accuracy * accuracy_weight +
            data_recency * recency_weight +
            stability_score * volatility_weight
        )

        return max(0, min(confidence, 1))

    def _score_to_confidence_level(self, score: float) -> MarketConfidence:
        """Convert numeric confidence to categorical level"""
        if score >= 0.8:
            return MarketConfidence.HIGH
        elif score >= 0.6:
            return MarketConfidence.MEDIUM
        elif score >= 0.4:
            return MarketConfidence.LOW
        else:
            return MarketConfidence.UNCERTAIN

    def _get_horizon_timedelta(self, horizon: TimeHorizon) -> timedelta:
        """Convert time horizon to timedelta"""
        if horizon == TimeHorizon.SHORT_TERM:
            return timedelta(days=90)
        elif horizon == TimeHorizon.MEDIUM_TERM:
            return timedelta(days=365)
        else:  # LONG_TERM
            return timedelta(days=1095)  # 3 years

    async def _create_appreciation_opportunity(
        self,
        neighborhood: str,
        prediction: PredictionResult
    ) -> MarketOpportunity:
        """Create opportunity from strong appreciation prediction"""

        return MarketOpportunity(
            opportunity_id=str(uuid.uuid4()),
            opportunity_type="appreciation",
            neighborhood=neighborhood,
            description=f"Strong {prediction.change_percentage:.1f}% appreciation predicted for {neighborhood}",
            potential_return=prediction.change_percentage,
            confidence_score=prediction.confidence_score,
            timeline=prediction.time_horizon.value,
            investment_required=prediction.current_value,
            risk_level="medium",
            risk_factors=prediction.risk_factors,
            mitigation_strategies=[
                "Monitor interest rate trends",
                "Diversify neighborhood exposure",
                "Time entry carefully"
            ],
            recommended_actions=[
                "Identify undervalued properties in the neighborhood",
                "Target investors and upgraders",
                "Create urgency around market timing"
            ],
            ideal_client_profile="Investors and move-up buyers"
        )

    async def _detect_undervalued_opportunity(self, neighborhood: str) -> Optional[MarketOpportunity]:
        """Detect undervalued property opportunities"""

        # Simplified undervaluation detection
        # In production, would compare to detailed comps and market models

        conditions = await self._get_current_market_conditions(neighborhood)
        median_price = conditions.get('median_price', 700000)

        # Mock undervaluation scoring
        import random
        undervaluation_score = random.uniform(0, 1)

        if undervaluation_score > 0.7:  # 30% chance of undervaluation
            return MarketOpportunity(
                opportunity_id=str(uuid.uuid4()),
                opportunity_type="undervalued",
                neighborhood=neighborhood,
                description=f"Properties in {neighborhood} showing 5-15% undervaluation vs market",
                potential_return=12.0,
                confidence_score=0.75,
                timeline="3-6 months",
                investment_required=median_price,
                risk_level="low",
                risk_factors=["Market correction risk"],
                mitigation_strategies=["Thorough comp analysis", "Quick closing capability"],
                recommended_actions=[
                    "Identify specific undervalued listings",
                    "Target cash buyers for speed",
                    "Create compelling value proposition"
                ],
                ideal_client_profile="Investors and savvy owner-occupants"
            )

        return None

    async def _detect_emerging_area_opportunity(self, neighborhood: str) -> Optional[MarketOpportunity]:
        """Detect emerging area opportunities"""

        # Simplified emerging area detection
        emerging_indicators = {
            "north_rc": 0.8,  # Strong emerging score
            "south_rc": 0.9,  # Highest emerging potential
            "central_rc": 0.6,
            "etiwanda": 0.4,
            "alta_loma": 0.3   # Already established
        }

        emerging_score = emerging_indicators.get(neighborhood, 0.3)

        if emerging_score > 0.7:
            return MarketOpportunity(
                opportunity_id=str(uuid.uuid4()),
                opportunity_type="emerging",
                neighborhood=neighborhood,
                description=f"{neighborhood} showing early signs of rapid development and appreciation",
                potential_return=18.0,
                confidence_score=emerging_score,
                timeline="1-2 years",
                investment_required=600000,  # Lower entry point
                risk_level="medium",
                risk_factors=["Development delays", "Infrastructure limitations"],
                mitigation_strategies=["Monitor development progress", "Diversified entry strategy"],
                recommended_actions=[
                    "Position as area expert before competition",
                    "Educate clients on emerging area benefits",
                    "Build relationships with local developers"
                ],
                ideal_client_profile="Forward-thinking investors and young families"
            )

        return None

    async def _analyze_seasonal_patterns_ai(self, monthly_stats: Dict, neighborhood: str) -> Dict[str, Any]:
        """Use AI to analyze seasonal patterns"""

        prompt = f"""
Analyze seasonal patterns for {neighborhood} in Rancho Cucamonga:

Monthly Statistics: {json.dumps(monthly_stats, indent=2, default=str)}

Identify:
1. Peak months for prices, sales volume, and buyer activity
2. Seasonal trends and patterns
3. Best timing recommendations for buyers and sellers
4. Unique IE/RC seasonal factors

Return as JSON with: peak_months, seasonal_trends, buyer_timing, seller_timing
"""

        try:
            response = await self.llm_client.agenerate(prompt=prompt, max_tokens=400, temperature=0.5)
            return json.loads(response.content)
        except:
            return {
                "peak_months": [4, 5, 6],
                "seasonal_trends": "Spring peak with winter slowdown",
                "buyer_timing": "Fall/winter for better prices",
                "seller_timing": "Spring for maximum exposure"
            }

    async def _generate_seasonal_recommendations(self, monthly_stats: Dict, neighborhood: str) -> List[str]:
        """Generate seasonal recommendations"""

        recommendations = [
            f"List properties in {neighborhood} during March-May for optimal exposure",
            "Buyers should focus on November-February for best negotiating power",
            "Investment purchases work well in winter months with less competition"
        ]

        return recommendations

    def _calculate_affordability_impact(self, price: float, old_rate: float, new_rate: float) -> Dict[str, float]:
        """Calculate affordability impact of rate change"""

        # Simplified mortgage payment calculation
        loan_amount = price * 0.8  # 20% down

        old_payment = loan_amount * (old_rate / 100 / 12) / (1 - (1 + old_rate / 100 / 12) ** -360)
        new_payment = loan_amount * (new_rate / 100 / 12) / (1 - (1 + new_rate / 100 / 12) ** -360)

        payment_change = new_payment - old_payment
        change_percentage = (payment_change / old_payment) * 100

        return {
            "old_payment": old_payment,
            "new_payment": new_payment,
            "payment_change": payment_change,
            "change_percentage": change_percentage
        }

    async def _generate_rate_impact_insights(self, impact_analysis: Dict, rate_change: float) -> List[str]:
        """Generate insights on interest rate impact"""

        insights = []

        if rate_change > 0:
            insights.extend([
                "Rising rates will reduce buyer purchasing power and demand",
                "Sellers should consider pricing adjustments to maintain competitiveness",
                "Investors may find better deals as competition decreases"
            ])
        else:
            insights.extend([
                "Lower rates will increase buyer demand and competition",
                "Sellers can expect faster sales and potentially higher prices",
                "Investment opportunities may become more expensive quickly"
            ])

        return insights

    async def _generate_rate_timing_recommendations(self, rate_change: float) -> List[str]:
        """Generate timing recommendations based on rate changes"""

        if rate_change > 0.25:  # Significant rate increase
            return [
                "Buyers should act quickly before rates rise further",
                "Sellers should adjust expectations for longer marketing times",
                "Refinancing opportunities may disappear - advise current homeowners"
            ]
        elif rate_change < -0.25:  # Significant rate decrease
            return [
                "Expect increased buyer competition - prepare for multiple offers",
                "Sellers can maximize pricing due to improved affordability",
                "Investment demand will increase - identify opportunities early"
            ]
        else:
            return [
                "Modest rate changes - monitor for trend continuation",
                "Maintain current market strategies with close monitoring"
            ]

    async def _cache_prediction_result(self, result: PredictionResult):
        """Cache prediction result"""
        cache_key = f"prediction:{result.prediction_id}"
        await self.cache.set(cache_key, asdict(result), ttl=7*24*3600)  # 7 days

    async def get_prediction_analytics(self) -> Dict[str, Any]:
        """Get analytics on prediction performance and trends"""

        analytics = {
            "model_performance": {},
            "prediction_trends": {},
            "confidence_distribution": {},
            "accuracy_tracking": {}
        }

        # Model performance metrics
        for model_name, metadata in self.model_metadata.items():
            analytics["model_performance"][model_name] = {
                "accuracy": metadata.get("r2", 0),
                "mae": metadata.get("mae", 0),
                "training_date": metadata.get("training_date"),
                "data_points": metadata.get("data_points", 0)
            }

        # Add prediction trend analysis
        analytics["prediction_trends"] = {
            "total_predictions": len(self.predictions_cache),
            "opportunities_identified": len(self.opportunities_cache),
            "avg_confidence": 0.75,  # Placeholder
            "high_confidence_predictions": 0
        }

        return analytics


# Singleton instance
_market_prediction_engine = None

def get_market_prediction_engine() -> MarketPredictionEngine:
    """Get singleton Market Prediction Engine instance"""
    global _market_prediction_engine
    if _market_prediction_engine is None:
        _market_prediction_engine = MarketPredictionEngine()
    return _market_prediction_engine