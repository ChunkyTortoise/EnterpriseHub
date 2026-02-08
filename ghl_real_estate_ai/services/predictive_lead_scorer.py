"""
Predictive Lead Scoring (Legacy Redirect)
=========================================

This file is a compatibility redirect.
The canonical implementation is now in `ai_predictive_lead_scoring.py`.
"""

from .ai_predictive_lead_scoring import PredictiveLeadScorer

# Re-export for backward compatibility
__all__ = ["PredictiveLeadScorer"]
