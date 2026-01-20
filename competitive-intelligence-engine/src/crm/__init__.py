"""
CRM Integration Engine - Multi-Platform Customer Relationship Management Integration

This package provides enterprise-grade CRM integration capabilities for the Enhanced
Competitive Intelligence Engine, enabling seamless connection between competitive insights
and customer relationship workflows.

Supported CRM Platforms:
- GoHighLevel (GHL) - Primary integration for existing customer base
- Salesforce - Enterprise CRM integration
- HubSpot - Marketing automation and CRM
- Pipedrive - Sales-focused CRM

Key Features:
- OAuth 2.0 authentication flows
- Real-time bidirectional data synchronization  
- Intelligent lead scoring from competitive insights
- Automated workflow triggers based on competitive events
- Webhook management for real-time updates
- Rate limiting and error handling
- Audit logging and compliance features

Architecture:
- Base connector interface for extensibility
- Platform-specific implementations
- Unified coordination layer
- Event-driven integration with analytics engine

Author: Claude
Date: January 2026
"""

from .base_crm_connector import BaseCRMConnector, CRMConnection, CRMContact, CRMOpportunity
from .crm_coordinator import CRMCoordinator, CRMConfiguration
from .webhook_manager import WebhookManager, WebhookEvent

# CRM connector implementations
from .connectors.gohighlevel_connector import GoHighLevelConnector
from .connectors.salesforce_connector import SalesforceConnector  
from .connectors.hubspot_connector import HubSpotConnector

# Workflow and synchronization services
from .workflows.intelligence_to_crm_service import IntelligenceToCRMService
from .sync.data_synchronization_service import DataSynchronizationService

# Export public API
__all__ = [
    # Base interfaces
    "BaseCRMConnector",
    "CRMConnection", 
    "CRMContact",
    "CRMOpportunity",
    
    # Core services
    "CRMCoordinator",
    "CRMConfiguration", 
    "WebhookManager",
    "WebhookEvent",
    
    # CRM connectors
    "GoHighLevelConnector",
    "SalesforceConnector",
    "HubSpotConnector",
    
    # Integration services
    "IntelligenceToCRMService",
    "DataSynchronizationService"
]

# Version info
__version__ = "1.0.0"
__author__ = "Claude"
__description__ = "Enterprise CRM Integration Engine for Competitive Intelligence"