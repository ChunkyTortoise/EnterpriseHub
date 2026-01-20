"""
Base CRM Connector Interface

This module defines the abstract base class and data models for CRM integrations,
providing a unified interface across all supported CRM platforms.

Author: Claude  
Date: January 2026
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union, AsyncIterator
from uuid import uuid4

logger = logging.getLogger(__name__)


class CRMPlatform(Enum):
    """Supported CRM platforms."""
    GOHIGHLEVEL = "gohighlevel"
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"


class ContactStatus(Enum):
    """Contact status in CRM."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LEAD = "lead"
    CUSTOMER = "customer"
    CHURNED = "churned"


class OpportunityStage(Enum):
    """Opportunity stages across CRM platforms."""
    PROSPECT = "prospect"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class SynchronizationStatus(Enum):
    """Data synchronization status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CRMConnection:
    """CRM connection configuration and status."""
    connection_id: str
    platform: CRMPlatform
    instance_url: Optional[str]
    api_version: str
    authenticated: bool
    auth_expires_at: Optional[datetime]
    rate_limit_remaining: int
    rate_limit_reset_at: Optional[datetime]
    last_sync_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CRMContact:
    """Standardized contact representation across CRM platforms."""
    contact_id: str
    external_id: str  # ID in the CRM platform
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    phone: Optional[str]
    status: ContactStatus
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    competitive_intelligence_score: Optional[float] = None
    last_competitive_insight: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def full_name(self) -> str:
        """Get full name of the contact."""
        parts = [self.first_name, self.last_name]
        return " ".join(filter(None, parts))


@dataclass
class CRMOpportunity:
    """Standardized opportunity representation across CRM platforms."""
    opportunity_id: str
    external_id: str  # ID in the CRM platform
    contact_id: str
    name: str
    stage: OpportunityStage
    amount: Optional[float]
    currency: str = "USD"
    close_date: Optional[datetime] = None
    probability: Optional[float] = None
    competitive_threats: List[str] = field(default_factory=list)
    competitive_advantages: List[str] = field(default_factory=list)
    intelligence_insights: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WebhookEvent:
    """Webhook event data structure."""
    event_id: str
    platform: CRMPlatform
    event_type: str
    object_type: str  # contact, opportunity, etc.
    object_id: str
    action: str  # created, updated, deleted
    data: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None
    processed: bool = False
    processed_at: Optional[datetime] = None


@dataclass
class SyncOperation:
    """Data synchronization operation tracking."""
    operation_id: str
    platform: CRMPlatform
    operation_type: str  # full_sync, incremental_sync, single_object
    status: SynchronizationStatus
    objects_processed: int = 0
    objects_total: int = 0
    objects_failed: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCRMConnector(ABC):
    """
    Abstract base class for all CRM platform integrations.
    
    This class defines the unified interface that all CRM connectors must implement,
    ensuring consistent behavior across different platforms while allowing for
    platform-specific optimizations.
    """
    
    def __init__(
        self,
        platform: CRMPlatform,
        connection_config: Dict[str, Any],
        rate_limit_per_minute: int = 100,
        max_retries: int = 3,
        timeout_seconds: int = 30
    ):
        """
        Initialize the CRM connector.
        
        Args:
            platform: CRM platform type
            connection_config: Platform-specific connection configuration
            rate_limit_per_minute: API rate limit
            max_retries: Maximum retry attempts for failed requests
            timeout_seconds: Request timeout
        """
        self.platform = platform
        self.connection_config = connection_config
        self.rate_limit_per_minute = rate_limit_per_minute
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        # Connection state
        self.connection: Optional[CRMConnection] = None
        self.is_connected = False
        
        # Rate limiting
        self._request_times: List[datetime] = []
        
        # Metrics
        self.requests_made = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.last_request_at: Optional[datetime] = None
        
        logger.info(f"Initialized {platform.value} CRM connector")
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with the CRM platform.
        
        Args:
            credentials: Platform-specific authentication credentials
            
        Returns:
            True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test the connection to the CRM platform.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_contacts(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        updated_since: Optional[datetime] = None
    ) -> List[CRMContact]:
        """
        Retrieve contacts from the CRM platform.
        
        Args:
            limit: Maximum number of contacts to retrieve
            offset: Number of contacts to skip
            filters: Platform-specific filters
            updated_since: Only return contacts updated since this datetime
            
        Returns:
            List of CRM contacts
        """
        pass
    
    @abstractmethod
    async def get_contact(self, contact_id: str) -> Optional[CRMContact]:
        """
        Retrieve a specific contact by ID.
        
        Args:
            contact_id: External CRM contact ID
            
        Returns:
            Contact if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def create_contact(self, contact: CRMContact) -> str:
        """
        Create a new contact in the CRM platform.
        
        Args:
            contact: Contact data to create
            
        Returns:
            External CRM contact ID of the created contact
        """
        pass
    
    @abstractmethod
    async def update_contact(self, contact: CRMContact) -> bool:
        """
        Update an existing contact in the CRM platform.
        
        Args:
            contact: Updated contact data
            
        Returns:
            True if update successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_opportunities(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        updated_since: Optional[datetime] = None
    ) -> List[CRMOpportunity]:
        """
        Retrieve opportunities from the CRM platform.
        
        Args:
            limit: Maximum number of opportunities to retrieve
            offset: Number of opportunities to skip
            filters: Platform-specific filters
            updated_since: Only return opportunities updated since this datetime
            
        Returns:
            List of CRM opportunities
        """
        pass
    
    @abstractmethod
    async def get_opportunity(self, opportunity_id: str) -> Optional[CRMOpportunity]:
        """
        Retrieve a specific opportunity by ID.
        
        Args:
            opportunity_id: External CRM opportunity ID
            
        Returns:
            Opportunity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def create_opportunity(self, opportunity: CRMOpportunity) -> str:
        """
        Create a new opportunity in the CRM platform.
        
        Args:
            opportunity: Opportunity data to create
            
        Returns:
            External CRM opportunity ID of the created opportunity
        """
        pass
    
    @abstractmethod
    async def update_opportunity(self, opportunity: CRMOpportunity) -> bool:
        """
        Update an existing opportunity in the CRM platform.
        
        Args:
            opportunity: Updated opportunity data
            
        Returns:
            True if update successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def add_note(
        self,
        object_type: str,  # contact, opportunity
        object_id: str,
        content: str,
        note_type: str = "intelligence_insight"
    ) -> str:
        """
        Add a note to a CRM object (contact, opportunity).
        
        Args:
            object_type: Type of object (contact, opportunity)
            object_id: External CRM object ID
            content: Note content
            note_type: Type of note for categorization
            
        Returns:
            External CRM note ID
        """
        pass
    
    @abstractmethod
    async def add_tags(
        self,
        object_type: str,
        object_id: str,
        tags: List[str]
    ) -> bool:
        """
        Add tags to a CRM object.
        
        Args:
            object_type: Type of object (contact, opportunity)
            object_id: External CRM object ID
            tags: List of tags to add
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def setup_webhook(
        self,
        webhook_url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> str:
        """
        Setup webhook for real-time event notifications.
        
        Args:
            webhook_url: URL to receive webhook notifications
            events: List of events to subscribe to
            secret: Optional webhook secret for signature verification
            
        Returns:
            Webhook ID for management
        """
        pass
    
    @abstractmethod
    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature for security.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            secret: Webhook secret
            
        Returns:
            True if signature is valid, False otherwise
        """
        pass
    
    # Common utility methods (implemented in base class)
    
    async def _rate_limit_check(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.now(timezone.utc)
        
        # Remove requests older than 1 minute
        cutoff = now - timedelta(minutes=1)
        self._request_times = [t for t in self._request_times if t > cutoff]
        
        # Check if we're at the rate limit
        if len(self._request_times) >= self.rate_limit_per_minute:
            return False
        
        # Add current request time
        self._request_times.append(now)
        return True
    
    async def _wait_for_rate_limit(self) -> None:
        """Wait until we can make another request."""
        while not await self._rate_limit_check():
            await asyncio.sleep(1)
    
    def _update_metrics(self, success: bool):
        """Update request metrics."""
        self.requests_made += 1
        self.last_request_at = datetime.now(timezone.utc)
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def get_connection_status(self) -> CRMConnection:
        """Get current connection status."""
        if not self.connection:
            raise ValueError("Not connected to CRM platform")
        
        return self.connection
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connector performance metrics."""
        success_rate = 0.0
        if self.requests_made > 0:
            success_rate = (self.successful_requests / self.requests_made) * 100
        
        return {
            "platform": self.platform.value,
            "is_connected": self.is_connected,
            "requests_made": self.requests_made,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "last_request_at": self.last_request_at.isoformat() if self.last_request_at else None,
            "rate_limit_remaining": len(self._request_times),
            "rate_limit_per_minute": self.rate_limit_per_minute
        }


# Export data models and base class
__all__ = [
    "BaseCRMConnector",
    "CRMPlatform", 
    "ContactStatus",
    "OpportunityStage",
    "SynchronizationStatus",
    "CRMConnection",
    "CRMContact",
    "CRMOpportunity", 
    "WebhookEvent",
    "SyncOperation"
]