"""
Enterprise Integrations for Customer Intelligence Platform.

Provides CRM connectors, SSO authentication, and audit trail capabilities
for enterprise-grade integrations and compliance.
"""

import asyncio
import json
import uuid
import hashlib
import hmac
from typing import Dict, List, Optional, Any, Union, Type
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from urllib.parse import urlencode, parse_qs
import base64
import secrets

import httpx
from pydantic import BaseModel, Field, EmailStr
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..core.event_bus import EventBus, EventType
from ..database.service import DatabaseService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class IntegrationType(Enum):
    """Types of enterprise integrations."""
    CRM_SALESFORCE = "crm_salesforce"
    CRM_HUBSPOT = "crm_hubspot" 
    CRM_PIPEDRIVE = "crm_pipedrive"
    SSO_SAML = "sso_saml"
    SSO_AZURE_AD = "sso_azure_ad"
    SSO_GOOGLE_WORKSPACE = "sso_google_workspace"
    AUDIT_SPLUNK = "audit_splunk"
    AUDIT_DATADOG = "audit_datadog"
    WEBHOOK_GENERIC = "webhook_generic"


class ConnectionStatus(Enum):
    """Integration connection statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"
    EXPIRED = "expired"


@dataclass
class IntegrationCredentials:
    """Secure credentials for external integrations."""
    integration_type: IntegrationType
    tenant_id: str
    encrypted_credentials: str
    metadata: Dict[str, Any]
    expires_at: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass 
class AuditEvent:
    """Audit trail event for compliance logging."""
    event_id: str
    tenant_id: str
    user_id: str
    event_type: str
    resource_type: str
    resource_id: str
    action: str
    outcome: str  # success, failure, unauthorized
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    timestamp: datetime
    session_id: Optional[str] = None
    

class CredentialsManager:
    """Secure credentials management for enterprise integrations."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        if encryption_key:
            self.fernet = Fernet(encryption_key.encode())
        else:
            # Generate key from environment-specific salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'customer_intelligence_salt',  # In production, use env-specific salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(b'default_key'))  # Use env password
            self.fernet = Fernet(key)
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials for secure storage."""
        credentials_json = json.dumps(credentials)
        encrypted = self.fernet.encrypt(credentials_json.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt credentials for use."""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_credentials.encode())
        decrypted = self.fernet.decrypt(encrypted_bytes)
        return json.loads(decrypted.decode())
    
    def rotate_encryption_key(self):
        """Rotate encryption key for enhanced security."""
        # Implementation for key rotation
        pass


class CRMConnector(ABC):
    """Abstract base class for CRM integrations."""
    
    def __init__(self, credentials: Dict[str, Any], tenant_id: str):
        self.credentials = credentials
        self.tenant_id = tenant_id
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the CRM connection."""
        pass
    
    @abstractmethod
    async def sync_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync contact data to CRM."""
        pass
    
    @abstractmethod
    async def create_lead(self, lead_data: Dict[str, Any]) -> str:
        """Create a new lead in CRM."""
        pass
    
    @abstractmethod
    async def update_opportunity(self, opportunity_id: str, data: Dict[str, Any]) -> bool:
        """Update opportunity in CRM."""
        pass
    
    async def cleanup(self):
        """Clean up resources."""
        await self.client.aclose()


class SalesforceConnector(CRMConnector):
    """Salesforce CRM integration."""
    
    def __init__(self, credentials: Dict[str, Any], tenant_id: str):
        super().__init__(credentials, tenant_id)
        self.instance_url = credentials.get("instance_url")
        self.access_token = credentials.get("access_token")
    
    async def test_connection(self) -> bool:
        """Test Salesforce connection."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await self.client.get(
                f"{self.instance_url}/services/data/v57.0/sobjects/Account/describe",
                headers=headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Salesforce connection test failed: {e}")
            return False
    
    async def sync_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync contact to Salesforce."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Map platform data to Salesforce Contact fields
            sf_contact = {
                "FirstName": contact_data.get("first_name", ""),
                "LastName": contact_data.get("last_name", "Unknown"),
                "Email": contact_data.get("email"),
                "Phone": contact_data.get("phone"),
                "Company": contact_data.get("company", "Unknown"),
                "LeadSource": "Customer Intelligence Platform"
            }
            
            response = await self.client.post(
                f"{self.instance_url}/services/data/v57.0/sobjects/Contact",
                headers=headers,
                json=sf_contact
            )
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "crm_id": result.get("id"),
                    "crm_url": f"{self.instance_url}/lightning/r/Contact/{result.get('id')}/view"
                }
            else:
                logger.error(f"Salesforce contact sync failed: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"Error syncing contact to Salesforce: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_lead(self, lead_data: Dict[str, Any]) -> str:
        """Create lead in Salesforce."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            sf_lead = {
                "FirstName": lead_data.get("first_name", ""),
                "LastName": lead_data.get("last_name", "Unknown"),
                "Email": lead_data.get("email"),
                "Phone": lead_data.get("phone"),
                "Company": lead_data.get("company", "Unknown"),
                "Status": "Open - Not Contacted",
                "LeadSource": "Customer Intelligence Platform",
                "Rating": lead_data.get("lead_score_tier", "Cold")
            }
            
            response = await self.client.post(
                f"{self.instance_url}/services/data/v57.0/sobjects/Lead",
                headers=headers,
                json=sf_lead
            )
            
            if response.status_code == 201:
                result = response.json()
                return result.get("id")
            else:
                raise Exception(f"Failed to create lead: {response.text}")
                
        except Exception as e:
            logger.error(f"Error creating Salesforce lead: {e}")
            raise
    
    async def update_opportunity(self, opportunity_id: str, data: Dict[str, Any]) -> bool:
        """Update Salesforce opportunity."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await self.client.patch(
                f"{self.instance_url}/services/data/v57.0/sobjects/Opportunity/{opportunity_id}",
                headers=headers,
                json=data
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logger.error(f"Error updating Salesforce opportunity: {e}")
            return False


class HubSpotConnector(CRMConnector):
    """HubSpot CRM integration."""
    
    def __init__(self, credentials: Dict[str, Any], tenant_id: str):
        super().__init__(credentials, tenant_id)
        self.api_key = credentials.get("api_key")
        self.access_token = credentials.get("access_token")  # OAuth
        self.base_url = "https://api.hubapi.com"
    
    async def test_connection(self) -> bool:
        """Test HubSpot connection."""
        try:
            headers = self._get_auth_headers()
            
            response = await self.client.get(
                f"{self.base_url}/crm/v3/objects/contacts",
                headers=headers,
                params={"limit": 1}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"HubSpot connection test failed: {e}")
            return False
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for HubSpot API."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        elif self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        else:
            raise ValueError("No valid HubSpot authentication credentials")
    
    async def sync_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync contact to HubSpot."""
        try:
            headers = self._get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            # Map platform data to HubSpot properties
            hs_contact = {
                "properties": {
                    "firstname": contact_data.get("first_name", ""),
                    "lastname": contact_data.get("last_name", "Unknown"),
                    "email": contact_data.get("email"),
                    "phone": contact_data.get("phone"),
                    "company": contact_data.get("company"),
                    "hs_lead_status": "NEW",
                    "lifecyclestage": "lead"
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/crm/v3/objects/contacts",
                headers=headers,
                json=hs_contact
            )
            
            if response.status_code == 201:
                result = response.json()
                contact_id = result.get("id")
                return {
                    "success": True,
                    "crm_id": contact_id,
                    "crm_url": f"https://app.hubspot.com/contacts/{contact_id}"
                }
            else:
                logger.error(f"HubSpot contact sync failed: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"Error syncing contact to HubSpot: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_lead(self, lead_data: Dict[str, Any]) -> str:
        """Create lead in HubSpot (as Contact with Lead lifecycle stage)."""
        result = await self.sync_contact(lead_data)
        if result.get("success"):
            return result.get("crm_id")
        else:
            raise Exception(f"Failed to create HubSpot lead: {result.get('error')}")
    
    async def update_opportunity(self, opportunity_id: str, data: Dict[str, Any]) -> bool:
        """Update HubSpot deal."""
        try:
            headers = self._get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            # Map data to HubSpot deal properties
            hs_deal = {"properties": data}
            
            response = await self.client.patch(
                f"{self.base_url}/crm/v3/objects/deals/{opportunity_id}",
                headers=headers,
                json=hs_deal
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error updating HubSpot deal: {e}")
            return False


class SSOProvider(ABC):
    """Abstract base class for SSO integrations."""
    
    def __init__(self, config: Dict[str, Any], tenant_id: str):
        self.config = config
        self.tenant_id = tenant_id
    
    @abstractmethod
    async def get_authorization_url(self, state: str) -> str:
        """Get SSO authorization URL."""
        pass
    
    @abstractmethod
    async def handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SSO callback and extract user info."""
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate SSO token and return user info."""
        pass


class AzureADProvider(SSOProvider):
    """Azure AD SSO integration."""
    
    def __init__(self, config: Dict[str, Any], tenant_id: str):
        super().__init__(config, tenant_id)
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.azure_tenant_id = config.get("azure_tenant_id")
        self.redirect_uri = config.get("redirect_uri")
    
    async def get_authorization_url(self, state: str) -> str:
        """Get Azure AD authorization URL."""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email",
            "state": state,
            "response_mode": "query"
        }
        
        base_url = f"https://login.microsoftonline.com/{self.azure_tenant_id}/oauth2/v2.0/authorize"
        return f"{base_url}?{urlencode(params)}"
    
    async def handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Azure AD OAuth callback."""
        code = callback_data.get("code")
        if not code:
            raise ValueError("No authorization code in callback")
        
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            }
            
            response = await client.post(
                f"https://login.microsoftonline.com/{self.azure_tenant_id}/oauth2/v2.0/token",
                data=token_data
            )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            tokens = response.json()
            
            # Get user info from token
            user_info = await self.validate_token(tokens.get("access_token"))
            
            return {
                "user_info": user_info,
                "tokens": tokens
            }
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate Azure AD token and get user info."""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            
            response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Token validation failed: {response.text}")


class AuditLogger:
    """Enterprise audit logging for compliance."""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.event_bus = EventBus()
    
    async def log_event(self, event: AuditEvent):
        """Log an audit event for compliance tracking."""
        try:
            # Store in database
            await self.db_service.create_audit_log(asdict(event))
            
            # Publish to event bus for real-time monitoring
            await self.event_bus.publish(
                EventType.AUDIT_EVENT_LOGGED,
                {
                    "event_id": event.event_id,
                    "tenant_id": event.tenant_id,
                    "user_id": event.user_id,
                    "event_type": event.event_type,
                    "action": event.action,
                    "outcome": event.outcome,
                    "timestamp": event.timestamp.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to log audit event {event.event_id}: {e}")
            # Critical: audit logging failures should be escalated
            raise
    
    async def log_user_action(
        self,
        user_id: str,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: str,
        details: Dict[str, Any],
        ip_address: str,
        user_agent: str,
        session_id: Optional[str] = None
    ):
        """Log a user action for audit trail."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="user_action",
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            session_id=session_id
        )
        
        await self.log_event(event)
    
    async def log_system_event(
        self,
        tenant_id: str,
        event_type: str,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: str,
        details: Dict[str, Any]
    ):
        """Log a system event for audit trail."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id="system",
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            details=details,
            ip_address="127.0.0.1",
            user_agent="system",
            timestamp=datetime.utcnow()
        )
        
        await self.log_event(event)


class EnterpriseIntegrationManager:
    """
    Main manager for enterprise integrations.
    
    Handles CRM connectors, SSO providers, and audit logging
    for comprehensive enterprise integration capabilities.
    """
    
    def __init__(self):
        self.credentials_manager = CredentialsManager()
        self.audit_logger = AuditLogger()
        self.db_service = DatabaseService()
        self.event_bus = EventBus()
        self.active_connections: Dict[str, Union[CRMConnector, SSOProvider]] = {}
    
    async def register_integration(
        self,
        tenant_id: str,
        integration_type: IntegrationType,
        credentials: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> str:
        """Register a new enterprise integration."""
        try:
            # Encrypt credentials
            encrypted_creds = self.credentials_manager.encrypt_credentials(credentials)
            
            # Store integration config
            integration_config = IntegrationCredentials(
                integration_type=integration_type,
                tenant_id=tenant_id,
                encrypted_credentials=encrypted_creds,
                metadata=metadata or {}
            )
            
            integration_id = str(uuid.uuid4())
            
            # Store in database
            await self.db_service.create_integration(
                integration_id,
                asdict(integration_config)
            )
            
            # Test connection
            connection_status = await self._test_integration(integration_id, integration_config)
            
            # Log audit event
            await self.audit_logger.log_system_event(
                tenant_id=tenant_id,
                event_type="integration_management",
                action="register_integration",
                resource_type="integration",
                resource_id=integration_id,
                outcome="success" if connection_status == ConnectionStatus.ACTIVE else "failure",
                details={
                    "integration_type": integration_type.value,
                    "connection_status": connection_status.value
                }
            )
            
            return integration_id
            
        except Exception as e:
            logger.error(f"Failed to register integration: {e}")
            
            await self.audit_logger.log_system_event(
                tenant_id=tenant_id,
                event_type="integration_management", 
                action="register_integration",
                resource_type="integration",
                resource_id="unknown",
                outcome="failure",
                details={"error": str(e), "integration_type": integration_type.value}
            )
            
            raise
    
    async def get_crm_connector(
        self,
        tenant_id: str,
        integration_type: IntegrationType
    ) -> CRMConnector:
        """Get an active CRM connector for the tenant."""
        
        # Check for existing active connection
        connection_key = f"{tenant_id}:{integration_type.value}"
        if connection_key in self.active_connections:
            return self.active_connections[connection_key]
        
        # Load integration config from database
        integration_config = await self.db_service.get_integration_by_type(
            tenant_id, 
            integration_type
        )
        
        if not integration_config:
            raise ValueError(f"No {integration_type.value} integration found for tenant")
        
        # Decrypt credentials
        credentials = self.credentials_manager.decrypt_credentials(
            integration_config["encrypted_credentials"]
        )
        
        # Create connector
        if integration_type == IntegrationType.CRM_SALESFORCE:
            connector = SalesforceConnector(credentials, tenant_id)
        elif integration_type == IntegrationType.CRM_HUBSPOT:
            connector = HubSpotConnector(credentials, tenant_id)
        else:
            raise ValueError(f"Unsupported CRM type: {integration_type}")
        
        # Test connection
        if await connector.test_connection():
            self.active_connections[connection_key] = connector
            return connector
        else:
            raise Exception(f"Failed to connect to {integration_type.value}")
    
    async def get_sso_provider(
        self,
        tenant_id: str,
        provider_type: IntegrationType
    ) -> SSOProvider:
        """Get SSO provider for tenant."""
        
        # Load integration config
        integration_config = await self.db_service.get_integration_by_type(
            tenant_id,
            provider_type
        )
        
        if not integration_config:
            raise ValueError(f"No {provider_type.value} integration found for tenant")
        
        # Decrypt credentials
        credentials = self.credentials_manager.decrypt_credentials(
            integration_config["encrypted_credentials"]
        )
        
        # Create provider
        if provider_type == IntegrationType.SSO_AZURE_AD:
            return AzureADProvider(credentials, tenant_id)
        else:
            raise ValueError(f"Unsupported SSO provider: {provider_type}")
    
    async def sync_customer_to_crm(
        self,
        tenant_id: str,
        customer_data: Dict[str, Any],
        crm_type: IntegrationType
    ) -> Dict[str, Any]:
        """Sync customer data to CRM system."""
        try:
            # Get CRM connector
            connector = await self.get_crm_connector(tenant_id, crm_type)
            
            # Sync contact
            result = await connector.sync_contact(customer_data)
            
            # Log audit event
            await self.audit_logger.log_system_event(
                tenant_id=tenant_id,
                event_type="crm_sync",
                action="sync_customer",
                resource_type="customer",
                resource_id=customer_data.get("customer_id", "unknown"),
                outcome="success" if result.get("success") else "failure",
                details={
                    "crm_type": crm_type.value,
                    "crm_id": result.get("crm_id"),
                    "result": result
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to sync customer to CRM: {e}")
            
            await self.audit_logger.log_system_event(
                tenant_id=tenant_id,
                event_type="crm_sync",
                action="sync_customer", 
                resource_type="customer",
                resource_id=customer_data.get("customer_id", "unknown"),
                outcome="failure",
                details={"error": str(e), "crm_type": crm_type.value}
            )
            
            raise
    
    async def _test_integration(
        self,
        integration_id: str,
        config: IntegrationCredentials
    ) -> ConnectionStatus:
        """Test integration connection."""
        try:
            credentials = self.credentials_manager.decrypt_credentials(
                config.encrypted_credentials
            )
            
            if config.integration_type in [
                IntegrationType.CRM_SALESFORCE,
                IntegrationType.CRM_HUBSPOT
            ]:
                # Test CRM connection
                if config.integration_type == IntegrationType.CRM_SALESFORCE:
                    connector = SalesforceConnector(credentials, config.tenant_id)
                elif config.integration_type == IntegrationType.CRM_HUBSPOT:
                    connector = HubSpotConnector(credentials, config.tenant_id)
                
                is_connected = await connector.test_connection()
                await connector.cleanup()
                
                return ConnectionStatus.ACTIVE if is_connected else ConnectionStatus.ERROR
            
            else:
                # For SSO and other integrations, return pending for manual verification
                return ConnectionStatus.PENDING
                
        except Exception as e:
            logger.error(f"Integration test failed for {integration_id}: {e}")
            return ConnectionStatus.ERROR
    
    async def health_check(self, tenant_id: str) -> Dict[str, Any]:
        """Check health of all integrations for a tenant."""
        try:
            integrations = await self.db_service.get_tenant_integrations(tenant_id)
            
            health_status = {
                "tenant_id": tenant_id,
                "total_integrations": len(integrations),
                "integrations": [],
                "overall_status": "healthy"
            }
            
            for integration in integrations:
                config = IntegrationCredentials(**integration)
                status = await self._test_integration(integration["id"], config)
                
                integration_health = {
                    "integration_id": integration["id"],
                    "type": config.integration_type.value,
                    "status": status.value,
                    "last_tested": datetime.utcnow().isoformat()
                }
                
                health_status["integrations"].append(integration_health)
                
                if status != ConnectionStatus.ACTIVE:
                    health_status["overall_status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Integration health check failed for tenant {tenant_id}: {e}")
            return {
                "tenant_id": tenant_id,
                "overall_status": "error",
                "error": str(e)
            }


# Singleton instance
_integration_manager = None

def get_integration_manager() -> EnterpriseIntegrationManager:
    """Get the global enterprise integration manager."""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = EnterpriseIntegrationManager()
    return _integration_manager