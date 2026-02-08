"""
Behavioral Event Tracking System

Provides event collection, storage, and retrieval for the learning engine.
Supports multiple storage backends with consistent interface.
"""

from .behavior_tracker import InMemoryBehaviorTracker
from .event_collector import EventCollector

__all__ = ["InMemoryBehaviorTracker", "EventCollector"]
