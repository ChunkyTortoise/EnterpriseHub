"""
Property Scoring Strategy Pattern Interfaces
Enterprise-grade interfaces for flexible property scoring algorithms
"""

from .property_scorer import PropertyScorer, ScoringResult
from .scoring_context import ScoringContext, LeadPreferences

__all__ = [
    'PropertyScorer',
    'ScoringResult',
    'ScoringContext',
    'LeadPreferences'
]