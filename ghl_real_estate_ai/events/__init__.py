"""
Events Package - Jorge AI Lead Scoring System

ML event models and publishers that extend Jorge's existing event infrastructure
"""

from .ml_event_models import (
    MLEventType,
    LeadMLScoredEvent,
    LeadMLEscalatedEvent,
    LeadMLCacheHitEvent,
    MLEventPublisher,
    create_ml_event,
    ExtendedEventType
)

__all__ = [
    'MLEventType',
    'LeadMLScoredEvent',
    'LeadMLEscalatedEvent',
    'LeadMLCacheHitEvent',
    'MLEventPublisher',
    'create_ml_event',
    'ExtendedEventType'
]