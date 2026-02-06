"""
Integration Coordination Layer

Unified integration layer that coordinates CRM, Advanced Analytics, and Real-Time Dashboard
components for seamless enterprise-grade competitive intelligence workflows.

Features:
- Cross-track event coordination
- Unified data pipeline management
- Intelligence-to-action workflow automation
- Real-time dashboard data streaming
- CRM intelligence synchronization
- ML model integration with dashboards

Author: Claude
Date: January 2026
"""

from .event_bridge import EventBridge, CrossTrackEvent, IntegrationEventType
from .data_pipeline import DataPipeline, PipelineStage, DataFlow
from .workflow_coordinator import (
    WorkflowCoordinator, IntelligenceWorkflow, WorkflowTrigger, ActionChain
)

# Export public API
__all__ = [
    # Event coordination
    "EventBridge",
    "CrossTrackEvent", 
    "IntegrationEventType",
    
    # Data pipeline
    "DataPipeline",
    "PipelineStage",
    "DataFlow",
    
    # Workflow coordination
    "WorkflowCoordinator",
    "IntelligenceWorkflow", 
    "WorkflowTrigger",
    "ActionChain"
]

# Version info
__version__ = "1.0.0"
__author__ = "Claude"
__description__ = "Integration Coordination Layer for Competitive Intelligence"