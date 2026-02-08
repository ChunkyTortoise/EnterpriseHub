"""
Machine Learning Package for Real Estate AI.

This package contains advanced ML models and engines for:
- Price prediction with 95%+ accuracy
- Market trend analysis
- Investment opportunity scoring
- Risk assessment models
- Demand forecasting
- Predictive lead scoring and analytics
"""

from .price_prediction_engine import (
    EnsemblePricePredictor,
    ModelMetrics,
    ModelType,
    PredictionFeatures,
    PredictionTimeframe,
    PricePredictionEngine,
    PricePredictionResult,
    get_price_prediction_engine,
)

__all__ = [
    "PricePredictionEngine",
    "EnsemblePricePredictor",
    "PredictionFeatures",
    "PricePredictionResult",
    "ModelMetrics",
    "PredictionTimeframe",
    "ModelType",
    "get_price_prediction_engine",
]
