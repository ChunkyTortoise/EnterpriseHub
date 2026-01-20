"""
Advanced Machine Learning Analytics Module

Enhanced ML capabilities for competitive intelligence including neural network forecasting,
real-time streaming analytics, and advanced pattern recognition.

Features:
- Deep learning models for competitive pattern prediction
- Neural network-based market forecasting  
- Real-time competitive behavior modeling
- Advanced NLP for competitor signal detection
- Ensemble models for prediction accuracy
- Streaming analytics for live competitive monitoring

Author: Claude
Date: January 2026
"""

from .neural_forecasting import (
    NeuralForecaster, ForecastModel, CompetitorBehaviorPredictor
)
from .pattern_recognition import (
    AdvancedPatternRecognizer, CompetitiveSignalDetector, NLPAnalyzer
)
from .ensemble_models import (
    EnsemblePredictor, ModelPerformanceTracker, PredictionConfidenceAnalyzer
)
from .streaming_analytics import (
    StreamingProcessor, RealTimeCompetitorMonitor, LiveMarketAnalyzer
)

# Export public API
__all__ = [
    # Neural forecasting
    "NeuralForecaster",
    "ForecastModel", 
    "CompetitorBehaviorPredictor",
    
    # Pattern recognition
    "AdvancedPatternRecognizer",
    "CompetitiveSignalDetector",
    "NLPAnalyzer",
    
    # Ensemble models
    "EnsemblePredictor",
    "ModelPerformanceTracker",
    "PredictionConfidenceAnalyzer",
    
    # Streaming analytics
    "StreamingProcessor",
    "RealTimeCompetitorMonitor", 
    "LiveMarketAnalyzer"
]

# Version info
__version__ = "1.0.0"
__author__ = "Claude"
__description__ = "Advanced ML Analytics for Competitive Intelligence"