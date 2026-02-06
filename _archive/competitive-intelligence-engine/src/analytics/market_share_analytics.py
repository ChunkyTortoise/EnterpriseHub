"""
Enhanced Competitive Intelligence Engine - Market Share Analytics

This module implements advanced time series analysis for market share forecasting,
competitive dynamics modeling, and market expansion opportunity identification.

Features:
- Advanced time series market share analysis
- Market share trend prediction with confidence intervals
- Competitive dynamics modeling and interaction effects
- Share-of-voice correlation analysis
- Market expansion opportunity identification
- Seasonal and cyclical pattern detection

Author: Claude
Date: January 2026
"""

import asyncio
import json
import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
from statsmodels.tsa.vector_ar.var_model import VAR

from ..core.event_bus import (
    EventBus, EventType, EventPriority, get_event_bus
)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure logging
logger = logging.getLogger(__name__)


class TrendType(Enum):
    """Types of market share trends."""
    GROWING = "growing"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"
    SEASONAL = "seasonal"
    CYCLICAL = "cyclical"


class ForecastHorizon(Enum):
    """Forecast time horizons."""
    SHORT_TERM = "1_month"
    MEDIUM_TERM = "3_months"
    LONG_TERM = "12_months"
    STRATEGIC = "24_months"


class ModelType(Enum):
    """Time series model types."""
    ARIMA = "arima"
    VAR = "vector_autoregression"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"
    ENSEMBLE = "ensemble"


@dataclass
class MarketShareDataPoint:
    """Single market share observation."""
    competitor_id: str
    market_segment: str
    timestamp: datetime
    market_share: float  # 0.0 to 1.0
    revenue: Optional[float] = None
    customer_count: Optional[int] = None
    share_of_voice: Optional[float] = None
    marketing_spend: Optional[float] = None
    product_launches: int = 0
    pricing_changes: int = 0


@dataclass
class TimeSeriesForecast:
    """Time series forecast result."""
    forecast_id: str
    competitor_id: str
    market_segment: str
    model_type: ModelType
    forecast_horizon: ForecastHorizon
    prediction_dates: List[datetime]
    predicted_values: List[float]
    confidence_intervals: List[Tuple[float, float]]
    trend_type: TrendType
    seasonality_detected: bool
    model_accuracy_score: float
    created_at: datetime


@dataclass
class CompetitiveDynamics:
    """Competitive interaction analysis."""
    analysis_id: str
    market_segment: str
    time_period: Tuple[datetime, datetime]
    competitor_interactions: Dict[str, Dict[str, float]]  # Correlation matrix
    market_elasticity: Dict[str, float]
    granger_causality: Dict[str, List[str]]  # Who influences whom
    competitive_pressure_index: float
    market_concentration: float
    volatility_score: float


@dataclass
class MarketExpansionOpportunity:
    """Market expansion opportunity identification."""
    opportunity_id: str
    target_segment: str
    current_leaders: List[str]
    growth_potential: float  # Expected growth rate
    entry_difficulty: float  # 0.0 to 1.0
    time_to_market: int  # Months
    required_market_share: float  # To be viable
    competitive_response_risk: float
    opportunity_value: float  # Dollar amount
    confidence_score: float


@dataclass
class MarketShareAnalysis:
    """Comprehensive market share analysis result."""
    analysis_id: str
    created_at: datetime
    market_segments: List[str]
    forecasts: List[TimeSeriesForecast]
    competitive_dynamics: List[CompetitiveDynamics]
    expansion_opportunities: List[MarketExpansionOpportunity]
    market_trends: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    correlation_id: Optional[str] = None


class MarketShareAnalytics:
    """
    Market Share Analytics - Time Series Forecasting and Competitive Dynamics
    
    This analytics engine provides advanced time series analysis for market share
    prediction, competitive dynamics modeling, and strategic opportunity identification
    using statistical forecasting methods and machine learning techniques.
    
    Features:
    - ARIMA and VAR models for time series forecasting
    - Seasonal decomposition and trend analysis
    - Granger causality testing for competitive interactions
    - Share-of-voice correlation analysis
    - Market expansion opportunity scoring
    """
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        min_data_points: int = 12,
        forecast_confidence: float = 0.95,
        seasonality_threshold: float = 0.3,
        volatility_threshold: float = 0.2
    ):
        """
        Initialize Market Share Analytics engine.
        
        Args:
            event_bus: Event bus for coordination
            min_data_points: Minimum data points for forecasting
            forecast_confidence: Confidence level for intervals
            seasonality_threshold: Threshold for seasonality detection
            volatility_threshold: Threshold for volatility classification
        """
        self.event_bus = event_bus or get_event_bus()
        self.min_data_points = min_data_points
        self.forecast_confidence = forecast_confidence
        self.seasonality_threshold = seasonality_threshold
        self.volatility_threshold = volatility_threshold
        
        # Model cache and state
        self._model_cache: Dict[str, Any] = {}
        self._forecast_cache: Dict[str, Tuple[TimeSeriesForecast, datetime]] = {}
        
        # Performance metrics
        self.forecasts_generated = 0
        self.analyses_completed = 0
        self.average_model_accuracy = 0.0
        self.cache_hit_rate = 0.0
        
        # Scaler for normalization
        self.scaler = StandardScaler()
        
        logger.info("Market Share Analytics engine initialized")
    
    async def forecast_market_shares(
        self,
        historical_data: List[MarketShareDataPoint],
        forecast_horizon: ForecastHorizon = ForecastHorizon.MEDIUM_TERM,
        model_type: ModelType = ModelType.ENSEMBLE,
        correlation_id: Optional[str] = None
    ) -> List[TimeSeriesForecast]:
        """
        Generate market share forecasts for all competitors and segments.
        
        Args:
            historical_data: Historical market share data
            forecast_horizon: Forecasting time horizon
            model_type: Type of forecasting model to use
            correlation_id: Event correlation tracking
            
        Returns:
            List of forecasts for each competitor-segment combination
        """
        start_time = datetime.now()
        
        try:
            # Organize data by competitor and segment
            data_groups = self._group_data_by_competitor_segment(historical_data)
            
            forecasts = []
            
            for (competitor_id, segment), data_points in data_groups.items():
                if len(data_points) < self.min_data_points:
                    logger.warning(
                        f"Insufficient data for {competitor_id} in {segment}: "
                        f"{len(data_points)} points (minimum: {self.min_data_points})"
                    )
                    continue
                
                # Generate forecast for this competitor-segment combination
                forecast = await self._generate_single_forecast(
                    competitor_id, segment, data_points, 
                    forecast_horizon, model_type
                )
                
                if forecast:
                    forecasts.append(forecast)
            
            # Update performance metrics
            self.forecasts_generated += len(forecasts)
            
            # Publish forecasting event
            await self._publish_forecast_event(forecasts, correlation_id)
            
            generation_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Generated {len(forecasts)} market share forecasts "
                f"in {generation_time:.2f} seconds"
            )
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Failed to generate market share forecasts: {e}")
            raise
    
    async def analyze_competitive_dynamics(
        self,
        historical_data: List[MarketShareDataPoint],
        analysis_period_months: int = 12,
        min_correlation: float = 0.3
    ) -> List[CompetitiveDynamics]:
        """
        Analyze competitive dynamics and interactions using time series analysis.
        
        Args:
            historical_data: Historical market share data
            analysis_period_months: Period for dynamics analysis
            min_correlation: Minimum correlation threshold
            
        Returns:
            Competitive dynamics analysis for each market segment
        """
        try:
            # Filter data to analysis period
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=analysis_period_months * 30)
            recent_data = [
                dp for dp in historical_data 
                if dp.timestamp >= cutoff_date
            ]
            
            # Group by market segment
            segment_groups = self._group_data_by_segment(recent_data)
            
            dynamics_list = []
            
            for segment, segment_data in segment_groups.items():
                dynamics = await self._analyze_segment_dynamics(
                    segment, segment_data, min_correlation
                )
                if dynamics:
                    dynamics_list.append(dynamics)
            
            logger.info(f"Analyzed dynamics for {len(dynamics_list)} market segments")
            return dynamics_list
            
        except Exception as e:
            logger.error(f"Failed to analyze competitive dynamics: {e}")
            raise
    
    async def identify_expansion_opportunities(
        self,
        historical_data: List[MarketShareDataPoint],
        growth_threshold: float = 0.1,
        min_opportunity_value: float = 1000000.0
    ) -> List[MarketExpansionOpportunity]:
        """
        Identify market expansion opportunities using growth and gap analysis.
        
        Args:
            historical_data: Historical market share data
            growth_threshold: Minimum growth rate for opportunity
            min_opportunity_value: Minimum opportunity value in dollars
            
        Returns:
            List of identified market expansion opportunities
        """
        try:
            opportunities = []
            
            # Analyze each market segment
            segment_groups = self._group_data_by_segment(historical_data)
            
            for segment, segment_data in segment_groups.items():
                segment_opportunities = await self._identify_segment_opportunities(
                    segment, segment_data, growth_threshold, min_opportunity_value
                )
                opportunities.extend(segment_opportunities)
            
            # Sort by opportunity value
            opportunities.sort(key=lambda o: o.opportunity_value, reverse=True)
            
            logger.info(f"Identified {len(opportunities)} expansion opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Failed to identify expansion opportunities: {e}")
            raise
    
    async def generate_comprehensive_analysis(
        self,
        historical_data: List[MarketShareDataPoint],
        forecast_horizon: ForecastHorizon = ForecastHorizon.MEDIUM_TERM,
        correlation_id: Optional[str] = None
    ) -> MarketShareAnalysis:
        """
        Generate comprehensive market share analysis combining all analytics.
        
        Args:
            historical_data: Historical market share data
            forecast_horizon: Forecasting horizon
            correlation_id: Event correlation tracking
            
        Returns:
            Complete market share analysis
        """
        start_time = datetime.now()
        
        try:
            # Run all analyses in parallel for efficiency
            forecasts_task = self.forecast_market_shares(
                historical_data, forecast_horizon, ModelType.ENSEMBLE, correlation_id
            )
            
            dynamics_task = self.analyze_competitive_dynamics(historical_data)
            
            opportunities_task = self.identify_expansion_opportunities(historical_data)
            
            # Wait for all analyses to complete
            forecasts, dynamics, opportunities = await asyncio.gather(
                forecasts_task, dynamics_task, opportunities_task
            )
            
            # Generate market trends summary
            market_trends = self._analyze_market_trends(
                historical_data, forecasts, dynamics
            )
            
            # Generate strategic recommendations
            recommendations = self._generate_market_recommendations(
                forecasts, dynamics, opportunities, market_trends
            )
            
            # Create comprehensive analysis
            analysis = MarketShareAnalysis(
                analysis_id=str(uuid4()),
                created_at=datetime.now(timezone.utc),
                market_segments=list(set(dp.market_segment for dp in historical_data)),
                forecasts=forecasts,
                competitive_dynamics=dynamics,
                expansion_opportunities=opportunities,
                market_trends=market_trends,
                recommendations=recommendations,
                correlation_id=correlation_id
            )
            
            self.analyses_completed += 1
            
            # Publish comprehensive analysis event
            await self._publish_analysis_event(analysis)
            
            analysis_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Generated comprehensive market analysis in {analysis_time:.2f} seconds"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive analysis: {e}")
            raise
    
    def _group_data_by_competitor_segment(
        self, 
        data: List[MarketShareDataPoint]
    ) -> Dict[Tuple[str, str], List[MarketShareDataPoint]]:
        """Group data points by competitor and market segment."""
        groups = {}
        
        for data_point in data:
            key = (data_point.competitor_id, data_point.market_segment)
            if key not in groups:
                groups[key] = []
            groups[key].append(data_point)
        
        # Sort each group by timestamp
        for key in groups:
            groups[key].sort(key=lambda dp: dp.timestamp)
        
        return groups
    
    def _group_data_by_segment(
        self, 
        data: List[MarketShareDataPoint]
    ) -> Dict[str, List[MarketShareDataPoint]]:
        """Group data points by market segment."""
        groups = {}
        
        for data_point in data:
            segment = data_point.market_segment
            if segment not in groups:
                groups[segment] = []
            groups[segment].append(data_point)
        
        return groups
    
    async def _generate_single_forecast(
        self,
        competitor_id: str,
        segment: str,
        data_points: List[MarketShareDataPoint],
        forecast_horizon: ForecastHorizon,
        model_type: ModelType
    ) -> Optional[TimeSeriesForecast]:
        """Generate forecast for single competitor-segment combination."""
        try:
            # Prepare time series data
            ts_data = pd.DataFrame([
                {
                    'timestamp': dp.timestamp,
                    'market_share': dp.market_share,
                    'share_of_voice': dp.share_of_voice or 0.0,
                    'marketing_spend': dp.marketing_spend or 0.0
                }
                for dp in data_points
            ])
            
            ts_data = ts_data.set_index('timestamp').sort_index()
            
            # Check data quality
            if ts_data['market_share'].isnull().sum() > len(ts_data) * 0.3:
                logger.warning(f"Too many null values for {competitor_id} in {segment}")
                return None
            
            # Fill missing values
            ts_data = ts_data.fillna(method='ffill').fillna(method='bfill')
            
            # Detect trends and seasonality
            trend_type, seasonality_detected = self._analyze_trend_seasonality(
                ts_data['market_share']
            )
            
            # Generate forecast based on model type
            if model_type == ModelType.ENSEMBLE:
                forecast_result = await self._ensemble_forecast(
                    ts_data, forecast_horizon
                )
            elif model_type == ModelType.ARIMA:
                forecast_result = self._arima_forecast(
                    ts_data['market_share'], forecast_horizon
                )
            elif model_type == ModelType.VAR:
                forecast_result = self._var_forecast(ts_data, forecast_horizon)
            else:
                # Default to ARIMA
                forecast_result = self._arima_forecast(
                    ts_data['market_share'], forecast_horizon
                )
            
            if not forecast_result:
                return None
            
            predicted_values, confidence_intervals, accuracy_score = forecast_result
            
            # Generate prediction dates
            last_date = ts_data.index[-1]
            prediction_dates = self._generate_prediction_dates(last_date, forecast_horizon)
            
            forecast = TimeSeriesForecast(
                forecast_id=str(uuid4()),
                competitor_id=competitor_id,
                market_segment=segment,
                model_type=model_type,
                forecast_horizon=forecast_horizon,
                prediction_dates=prediction_dates,
                predicted_values=predicted_values,
                confidence_intervals=confidence_intervals,
                trend_type=trend_type,
                seasonality_detected=seasonality_detected,
                model_accuracy_score=accuracy_score,
                created_at=datetime.now(timezone.utc)
            )
            
            return forecast
            
        except Exception as e:
            logger.error(f"Failed to generate forecast for {competitor_id} in {segment}: {e}")
            return None
    
    def _analyze_trend_seasonality(
        self, 
        time_series: pd.Series
    ) -> Tuple[TrendType, bool]:
        """Analyze trend and seasonality in time series."""
        try:
            # Check if series has enough data for seasonal decomposition
            if len(time_series) < 24:  # Need at least 2 years of monthly data
                # Simple trend analysis
                trend_slope = np.polyfit(range(len(time_series)), time_series.values, 1)[0]
                
                if abs(trend_slope) < 0.001:
                    trend_type = TrendType.STABLE
                elif trend_slope > 0:
                    trend_type = TrendType.GROWING
                else:
                    trend_type = TrendType.DECLINING
                
                # Check volatility
                volatility = time_series.std() / time_series.mean()
                if volatility > self.volatility_threshold:
                    trend_type = TrendType.VOLATILE
                
                return trend_type, False
            
            # Seasonal decomposition
            try:
                decomposition = seasonal_decompose(
                    time_series, model='additive', period=12
                )
                
                # Check seasonality strength
                seasonal_strength = decomposition.seasonal.std() / time_series.std()
                seasonality_detected = seasonal_strength > self.seasonality_threshold
                
                # Analyze trend component
                trend = decomposition.trend.dropna()
                if len(trend) > 2:
                    trend_slope = np.polyfit(range(len(trend)), trend.values, 1)[0]
                    
                    if seasonality_detected:
                        trend_type = TrendType.SEASONAL
                    elif abs(trend_slope) < 0.001:
                        trend_type = TrendType.STABLE
                    elif trend_slope > 0:
                        trend_type = TrendType.GROWING
                    else:
                        trend_type = TrendType.DECLINING
                else:
                    trend_type = TrendType.STABLE
                
                return trend_type, seasonality_detected
                
            except Exception:
                # Fallback to simple analysis
                return self._simple_trend_analysis(time_series), False
            
        except Exception as e:
            logger.error(f"Failed to analyze trend and seasonality: {e}")
            return TrendType.STABLE, False
    
    def _simple_trend_analysis(self, time_series: pd.Series) -> TrendType:
        """Simple trend analysis fallback."""
        # Calculate moving averages
        if len(time_series) >= 6:
            ma_short = time_series.rolling(3).mean()
            ma_long = time_series.rolling(6).mean()
            
            # Compare recent short vs long term averages
            if ma_short.iloc[-1] > ma_long.iloc[-1] * 1.05:
                return TrendType.GROWING
            elif ma_short.iloc[-1] < ma_long.iloc[-1] * 0.95:
                return TrendType.DECLINING
            else:
                return TrendType.STABLE
        else:
            return TrendType.STABLE
    
    def _arima_forecast(
        self, 
        time_series: pd.Series, 
        forecast_horizon: ForecastHorizon
    ) -> Optional[Tuple[List[float], List[Tuple[float, float]], float]]:
        """Generate ARIMA forecast."""
        try:
            # Determine forecast steps
            steps = self._get_forecast_steps(forecast_horizon)
            
            # Check stationarity
            adf_result = adfuller(time_series.dropna())
            is_stationary = adf_result[1] < 0.05
            
            # Auto ARIMA model selection (simplified)
            best_aic = float('inf')
            best_order = None
            best_model = None
            
            # Try different ARIMA orders
            for p in range(3):
                for d in range(2 if not is_stationary else 1):
                    for q in range(3):
                        try:
                            model = ARIMA(time_series, order=(p, d, q))
                            fitted_model = model.fit()
                            
                            if fitted_model.aic < best_aic:
                                best_aic = fitted_model.aic
                                best_order = (p, d, q)
                                best_model = fitted_model
                                
                        except Exception:
                            continue
            
            if best_model is None:
                logger.warning("Failed to fit ARIMA model")
                return None
            
            # Generate forecast
            forecast_result = best_model.forecast(steps=steps)
            confidence_int = best_model.get_forecast(steps=steps).conf_int()
            
            predicted_values = forecast_result.tolist()
            confidence_intervals = [
                (float(confidence_int.iloc[i, 0]), float(confidence_int.iloc[i, 1]))
                for i in range(len(confidence_int))
            ]
            
            # Calculate accuracy (using in-sample fit)
            fitted_values = best_model.fittedvalues
            actual_values = time_series.iloc[1:]  # Skip first value due to differencing
            
            if len(fitted_values) == len(actual_values):
                accuracy_score = 1.0 - mean_absolute_error(actual_values, fitted_values) / actual_values.mean()
            else:
                accuracy_score = 0.8  # Default moderate accuracy
            
            return predicted_values, confidence_intervals, max(0.0, min(1.0, accuracy_score))
            
        except Exception as e:
            logger.error(f"ARIMA forecasting failed: {e}")
            return None
    
    def _var_forecast(
        self, 
        time_series_data: pd.DataFrame, 
        forecast_horizon: ForecastHorizon
    ) -> Optional[Tuple[List[float], List[Tuple[float, float]], float]]:
        """Generate VAR (Vector Autoregression) forecast."""
        try:
            # Ensure we have multiple variables for VAR
            if time_series_data.shape[1] < 2:
                return None
            
            steps = self._get_forecast_steps(forecast_horizon)
            
            # Prepare data for VAR
            var_data = time_series_data.dropna()
            
            if len(var_data) < 10:  # Need sufficient data for VAR
                return None
            
            # Fit VAR model
            model = VAR(var_data)
            
            # Select optimal lag order
            lag_order_results = model.select_order(maxlags=min(8, len(var_data) // 3))
            optimal_lag = lag_order_results.aic
            
            fitted_model = model.fit(optimal_lag)
            
            # Generate forecast
            forecast_result = fitted_model.forecast(var_data.values[-optimal_lag:], steps)
            
            # Extract market share forecasts (assuming it's the first column)
            predicted_values = forecast_result[:, 0].tolist()
            
            # Simple confidence intervals (VAR doesn't provide them directly)
            forecast_errors = fitted_model.resid[:, 0]
            error_std = np.std(forecast_errors)
            
            confidence_intervals = [
                (pred - 1.96 * error_std, pred + 1.96 * error_std)
                for pred in predicted_values
            ]
            
            # Calculate accuracy
            fitted_values = fitted_model.fittedvalues[:, 0]
            actual_values = var_data.iloc[optimal_lag:, 0]
            
            if len(fitted_values) == len(actual_values):
                accuracy_score = 1.0 - mean_absolute_error(actual_values, fitted_values) / actual_values.mean()
            else:
                accuracy_score = 0.75  # Default accuracy for VAR
            
            return predicted_values, confidence_intervals, max(0.0, min(1.0, accuracy_score))
            
        except Exception as e:
            logger.error(f"VAR forecasting failed: {e}")
            return None
    
    async def _ensemble_forecast(
        self, 
        time_series_data: pd.DataFrame, 
        forecast_horizon: ForecastHorizon
    ) -> Optional[Tuple[List[float], List[Tuple[float, float]], float]]:
        """Generate ensemble forecast combining multiple methods."""
        try:
            forecasts = []
            accuracies = []
            
            # ARIMA forecast
            arima_result = self._arima_forecast(
                time_series_data['market_share'], forecast_horizon
            )
            if arima_result:
                forecasts.append(arima_result)
                accuracies.append(arima_result[2])
            
            # VAR forecast (if multiple variables available)
            if time_series_data.shape[1] > 1:
                var_result = self._var_forecast(time_series_data, forecast_horizon)
                if var_result:
                    forecasts.append(var_result)
                    accuracies.append(var_result[2])
            
            # Exponential smoothing forecast
            exp_smooth_result = self._exponential_smoothing_forecast(
                time_series_data['market_share'], forecast_horizon
            )
            if exp_smooth_result:
                forecasts.append(exp_smooth_result)
                accuracies.append(exp_smooth_result[2])
            
            if not forecasts:
                return None
            
            # Weighted ensemble based on accuracy
            weights = np.array(accuracies) / sum(accuracies)
            
            # Combine predictions
            ensemble_predictions = []
            ensemble_confidence = []
            
            for i in range(len(forecasts[0][0])):  # For each forecast step
                weighted_pred = sum(
                    weight * forecast[0][i] 
                    for weight, forecast in zip(weights, forecasts)
                )
                ensemble_predictions.append(weighted_pred)
                
                # Combine confidence intervals (simplified)
                lower_bounds = [forecast[1][i][0] for forecast in forecasts]
                upper_bounds = [forecast[1][i][1] for forecast in forecasts]
                
                ensemble_lower = sum(w * lb for w, lb in zip(weights, lower_bounds))
                ensemble_upper = sum(w * ub for w, ub in zip(weights, upper_bounds))
                
                ensemble_confidence.append((ensemble_lower, ensemble_upper))
            
            # Ensemble accuracy is weighted average
            ensemble_accuracy = sum(w * acc for w, acc in zip(weights, accuracies))
            
            return ensemble_predictions, ensemble_confidence, ensemble_accuracy
            
        except Exception as e:
            logger.error(f"Ensemble forecasting failed: {e}")
            return None
    
    def _exponential_smoothing_forecast(
        self, 
        time_series: pd.Series, 
        forecast_horizon: ForecastHorizon
    ) -> Optional[Tuple[List[float], List[Tuple[float, float]], float]]:
        """Generate exponential smoothing forecast."""
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            
            steps = self._get_forecast_steps(forecast_horizon)
            
            # Try different exponential smoothing models
            models_to_try = [
                {'trend': None, 'seasonal': None},  # Simple exponential smoothing
                {'trend': 'add', 'seasonal': None},  # Holt's method
            ]
            
            if len(time_series) >= 24:  # Need enough data for seasonal models
                models_to_try.append({'trend': 'add', 'seasonal': 'add'})
                models_to_try.append({'trend': 'add', 'seasonal': 'mul'})
            
            best_aic = float('inf')
            best_model = None
            
            for model_config in models_to_try:
                try:
                    model = ExponentialSmoothing(
                        time_series,
                        trend=model_config['trend'],
                        seasonal=model_config['seasonal'],
                        seasonal_periods=12 if model_config['seasonal'] else None
                    )
                    
                    fitted_model = model.fit()
                    
                    if fitted_model.aic < best_aic:
                        best_aic = fitted_model.aic
                        best_model = fitted_model
                        
                except Exception:
                    continue
            
            if best_model is None:
                return None
            
            # Generate forecast
            forecast_result = best_model.forecast(steps)
            
            # Simple confidence intervals based on residuals
            residuals = best_model.resid
            error_std = np.std(residuals)
            
            predicted_values = forecast_result.tolist()
            confidence_intervals = [
                (pred - 1.96 * error_std, pred + 1.96 * error_std)
                for pred in predicted_values
            ]
            
            # Calculate accuracy
            fitted_values = best_model.fittedvalues
            actual_values = time_series
            
            accuracy_score = 1.0 - mean_absolute_error(actual_values, fitted_values) / actual_values.mean()
            
            return predicted_values, confidence_intervals, max(0.0, min(1.0, accuracy_score))
            
        except Exception as e:
            logger.error(f"Exponential smoothing failed: {e}")
            return None
    
    def _get_forecast_steps(self, forecast_horizon: ForecastHorizon) -> int:
        """Get number of forecast steps for given horizon."""
        horizon_map = {
            ForecastHorizon.SHORT_TERM: 1,
            ForecastHorizon.MEDIUM_TERM: 3,
            ForecastHorizon.LONG_TERM: 12,
            ForecastHorizon.STRATEGIC: 24
        }
        return horizon_map.get(forecast_horizon, 3)
    
    def _generate_prediction_dates(
        self, 
        last_date: datetime, 
        forecast_horizon: ForecastHorizon
    ) -> List[datetime]:
        """Generate prediction dates for forecast."""
        steps = self._get_forecast_steps(forecast_horizon)
        dates = []
        
        current_date = last_date
        for _ in range(steps):
            current_date += timedelta(days=30)  # Monthly predictions
            dates.append(current_date)
        
        return dates
    
    async def _analyze_segment_dynamics(
        self,
        segment: str,
        segment_data: List[MarketShareDataPoint],
        min_correlation: float
    ) -> Optional[CompetitiveDynamics]:
        """Analyze competitive dynamics within a market segment."""
        try:
            # Create time series matrix for all competitors
            competitor_series = self._create_competitor_time_series_matrix(segment_data)
            
            if competitor_series.empty or len(competitor_series.columns) < 2:
                return None
            
            # Calculate correlation matrix
            correlation_matrix = competitor_series.corr()
            
            # Extract significant correlations
            interactions = {}
            for comp1 in correlation_matrix.index:
                interactions[comp1] = {}
                for comp2 in correlation_matrix.columns:
                    if comp1 != comp2:
                        corr = correlation_matrix.loc[comp1, comp2]
                        if abs(corr) >= min_correlation:
                            interactions[comp1][comp2] = corr
            
            # Granger causality analysis
            granger_causality = {}
            for comp1 in competitor_series.columns:
                granger_causality[comp1] = []
                for comp2 in competitor_series.columns:
                    if comp1 != comp2:
                        try:
                            # Test if comp1 Granger-causes comp2
                            test_result = grangercausalitytests(
                                competitor_series[[comp2, comp1]].dropna(),
                                maxlag=4,
                                verbose=False
                            )
                            
                            # Check if any lag is significant (p < 0.05)
                            for lag in test_result:
                                if test_result[lag][0]['ssr_ftest'][1] < 0.05:
                                    granger_causality[comp1].append(comp2)
                                    break
                                    
                        except Exception:
                            continue
            
            # Calculate market metrics
            market_shares = competitor_series.iloc[-1]  # Latest shares
            market_concentration = sum(share ** 2 for share in market_shares)  # HHI
            
            volatility_scores = competitor_series.std()
            avg_volatility = volatility_scores.mean()
            
            competitive_pressure = 1.0 - market_concentration  # Inverse of concentration
            
            # Analyze time period
            timestamps = [dp.timestamp for dp in segment_data]
            time_period = (min(timestamps), max(timestamps))
            
            dynamics = CompetitiveDynamics(
                analysis_id=str(uuid4()),
                market_segment=segment,
                time_period=time_period,
                competitor_interactions=interactions,
                market_elasticity={},  # Would need demand data for proper elasticity
                granger_causality=granger_causality,
                competitive_pressure_index=competitive_pressure,
                market_concentration=market_concentration,
                volatility_score=avg_volatility
            )
            
            return dynamics
            
        except Exception as e:
            logger.error(f"Failed to analyze segment dynamics for {segment}: {e}")
            return None
    
    def _create_competitor_time_series_matrix(
        self, 
        segment_data: List[MarketShareDataPoint]
    ) -> pd.DataFrame:
        """Create time series matrix with competitors as columns."""
        # Organize data by competitor and timestamp
        data_dict = {}
        
        for data_point in segment_data:
            timestamp = data_point.timestamp.strftime('%Y-%m')  # Monthly aggregation
            competitor = data_point.competitor_id
            
            if timestamp not in data_dict:
                data_dict[timestamp] = {}
            
            data_dict[timestamp][competitor] = data_point.market_share
        
        # Create DataFrame
        df = pd.DataFrame.from_dict(data_dict, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        return df.fillna(method='ffill').fillna(0.0)
    
    async def _identify_segment_opportunities(
        self,
        segment: str,
        segment_data: List[MarketShareDataPoint],
        growth_threshold: float,
        min_opportunity_value: float
    ) -> List[MarketExpansionOpportunity]:
        """Identify expansion opportunities within a market segment."""
        try:
            opportunities = []
            
            # Analyze market growth trends
            time_series = self._create_competitor_time_series_matrix(segment_data)
            
            if time_series.empty:
                return opportunities
            
            # Calculate total market growth
            total_market = time_series.sum(axis=1)
            
            if len(total_market) < 6:  # Need sufficient data
                return opportunities
            
            # Simple growth calculation
            early_period = total_market.head(len(total_market) // 3).mean()
            recent_period = total_market.tail(len(total_market) // 3).mean()
            
            growth_rate = (recent_period - early_period) / early_period if early_period > 0 else 0
            
            if growth_rate < growth_threshold:
                return opportunities  # Not growing fast enough
            
            # Identify market leaders
            latest_shares = time_series.iloc[-1]
            current_leaders = latest_shares.nlargest(3).index.tolist()
            
            # Calculate opportunity metrics
            market_size = sum(
                dp.revenue for dp in segment_data 
                if dp.revenue and dp.timestamp >= (datetime.now(timezone.utc) - timedelta(days=90))
            ) or 10000000.0  # Default $10M if no revenue data
            
            opportunity_value = market_size * growth_rate * 0.1  # 10% capture assumption
            
            if opportunity_value >= min_opportunity_value:
                # Calculate entry difficulty based on market concentration
                concentration = sum(share ** 2 for share in latest_shares)
                entry_difficulty = min(1.0, concentration)  # Higher concentration = harder entry
                
                opportunity = MarketExpansionOpportunity(
                    opportunity_id=str(uuid4()),
                    target_segment=segment,
                    current_leaders=current_leaders,
                    growth_potential=growth_rate,
                    entry_difficulty=entry_difficulty,
                    time_to_market=max(6, int(12 * entry_difficulty)),  # Months
                    required_market_share=0.05,  # 5% minimum viable share
                    competitive_response_risk=min(0.9, entry_difficulty + 0.2),
                    opportunity_value=opportunity_value,
                    confidence_score=0.7  # Default confidence
                )
                
                opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Failed to identify opportunities for {segment}: {e}")
            return []
    
    def _analyze_market_trends(
        self,
        historical_data: List[MarketShareDataPoint],
        forecasts: List[TimeSeriesForecast],
        dynamics: List[CompetitiveDynamics]
    ) -> Dict[str, Any]:
        """Analyze overall market trends across all data."""
        trends = {
            "growth_trends": {},
            "competitive_trends": {},
            "seasonal_patterns": {},
            "volatility_analysis": {},
            "forecast_summary": {}
        }
        
        # Analyze growth trends
        segments = list(set(dp.market_segment for dp in historical_data))
        for segment in segments:
            segment_data = [dp for dp in historical_data if dp.market_segment == segment]
            
            if len(segment_data) > 6:
                # Simple trend analysis
                monthly_totals = {}
                for dp in segment_data:
                    month = dp.timestamp.strftime('%Y-%m')
                    if month not in monthly_totals:
                        monthly_totals[month] = 0.0
                    monthly_totals[month] += dp.market_share
                
                if len(monthly_totals) > 3:
                    values = list(monthly_totals.values())
                    trend_slope = np.polyfit(range(len(values)), values, 1)[0]
                    
                    trends["growth_trends"][segment] = {
                        "slope": trend_slope,
                        "direction": "growing" if trend_slope > 0 else "declining",
                        "strength": abs(trend_slope)
                    }
        
        # Analyze competitive trends from dynamics
        for dynamic in dynamics:
            trends["competitive_trends"][dynamic.market_segment] = {
                "concentration": dynamic.market_concentration,
                "pressure": dynamic.competitive_pressure_index,
                "volatility": dynamic.volatility_score
            }
        
        # Analyze forecast trends
        forecast_accuracy = [f.model_accuracy_score for f in forecasts]
        
        trends["forecast_summary"] = {
            "total_forecasts": len(forecasts),
            "average_accuracy": sum(forecast_accuracy) / len(forecast_accuracy) if forecast_accuracy else 0,
            "seasonal_forecasts": len([f for f in forecasts if f.seasonality_detected]),
            "growing_forecasts": len([f for f in forecasts if f.trend_type == TrendType.GROWING])
        }
        
        return trends
    
    def _generate_market_recommendations(
        self,
        forecasts: List[TimeSeriesForecast],
        dynamics: List[CompetitiveDynamics],
        opportunities: List[MarketExpansionOpportunity],
        trends: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate strategic recommendations based on analysis."""
        recommendations = []
        
        # Opportunity recommendations
        top_opportunities = sorted(opportunities, key=lambda o: o.opportunity_value, reverse=True)[:3]
        if top_opportunities:
            recommendations.append({
                "type": "expansion",
                "title": "Top Market Expansion Opportunities",
                "description": f"Focus on {len(top_opportunities)} highest-value expansion opportunities",
                "opportunities": [o.opportunity_id for o in top_opportunities],
                "total_value": sum(o.opportunity_value for o in top_opportunities),
                "priority": "high"
            })
        
        # Growth trend recommendations
        growing_segments = [
            segment for segment, data in trends["growth_trends"].items()
            if data["direction"] == "growing" and data["strength"] > 0.01
        ]
        
        if growing_segments:
            recommendations.append({
                "type": "growth",
                "title": "Capitalize on Growing Segments", 
                "description": f"Focus investment on {len(growing_segments)} growing market segments",
                "segments": growing_segments,
                "priority": "medium"
            })
        
        # Competitive pressure recommendations
        high_pressure_segments = [
            dynamic.market_segment for dynamic in dynamics
            if dynamic.competitive_pressure_index > 0.7
        ]
        
        if high_pressure_segments:
            recommendations.append({
                "type": "competitive",
                "title": "Address High Competitive Pressure",
                "description": f"Strengthen position in {len(high_pressure_segments)} highly competitive segments",
                "segments": high_pressure_segments,
                "priority": "medium"
            })
        
        # Forecasting accuracy recommendations  
        low_accuracy_forecasts = [f for f in forecasts if f.model_accuracy_score < 0.6]
        if low_accuracy_forecasts:
            recommendations.append({
                "type": "data_quality",
                "title": "Improve Data Quality for Forecasting",
                "description": f"Address {len(low_accuracy_forecasts)} low-accuracy forecasts",
                "affected_forecasts": len(low_accuracy_forecasts),
                "priority": "low"
            })
        
        return recommendations
    
    async def _publish_forecast_event(
        self, 
        forecasts: List[TimeSeriesForecast], 
        correlation_id: Optional[str]
    ):
        """Publish forecast generation event."""
        try:
            await self.event_bus.publish(
                event_type=EventType.MARKET_SHARE_CALCULATED,
                data={
                    "forecasts_generated": len(forecasts),
                    "segments_analyzed": len(set(f.market_segment for f in forecasts)),
                    "competitors_analyzed": len(set(f.competitor_id for f in forecasts)),
                    "average_accuracy": sum(f.model_accuracy_score for f in forecasts) / len(forecasts) if forecasts else 0,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                source_system="market_share_analytics",
                priority=EventPriority.MEDIUM,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            logger.error(f"Failed to publish forecast event: {e}")
    
    async def _publish_analysis_event(self, analysis: MarketShareAnalysis):
        """Publish comprehensive analysis event."""
        try:
            await self.event_bus.publish(
                event_type=EventType.STRATEGIC_PATTERN_IDENTIFIED,
                data={
                    "analysis_id": analysis.analysis_id,
                    "segments_analyzed": len(analysis.market_segments),
                    "forecasts_count": len(analysis.forecasts),
                    "dynamics_analyzed": len(analysis.competitive_dynamics),
                    "opportunities_identified": len(analysis.expansion_opportunities),
                    "total_opportunity_value": sum(o.opportunity_value for o in analysis.expansion_opportunities),
                    "recommendations_count": len(analysis.recommendations),
                    "created_at": analysis.created_at.isoformat()
                },
                source_system="market_share_analytics",
                priority=EventPriority.HIGH,
                correlation_id=analysis.correlation_id
            )
            
        except Exception as e:
            logger.error(f"Failed to publish analysis event: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get analytics performance metrics."""
        return {
            "forecasts_generated": self.forecasts_generated,
            "analyses_completed": self.analyses_completed,
            "average_model_accuracy": self.average_model_accuracy,
            "cache_hit_rate": self.cache_hit_rate,
            "cached_forecasts": len(self._forecast_cache),
            "cached_models": len(self._model_cache)
        }


# Export public API
__all__ = [
    "MarketShareAnalytics",
    "MarketShareDataPoint",
    "TimeSeriesForecast", 
    "CompetitiveDynamics",
    "MarketExpansionOpportunity",
    "MarketShareAnalysis",
    "TrendType",
    "ForecastHorizon",
    "ModelType"
]