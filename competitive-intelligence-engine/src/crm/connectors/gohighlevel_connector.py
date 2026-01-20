"""
GoHighLevel CRM Connector

Enterprise-grade integration with GoHighLevel CRM platform, providing comprehensive
contact management, opportunity tracking, and real-time webhook capabilities.

Features:
- OAuth 2.0 authentication with refresh token management
- Full CRUD operations for contacts and opportunities
- Real-time webhook event processing
- Rate limiting and retry logic
- Competitive intelligence integration

Author: Claude
Date: January 2026
"""

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from uuid import uuid4
import aiohttp

from ..base_crm_connector import (
    BaseCRMConnector, CRMPlatform, ContactStatus, OpportunityStage,
    CRMConnection, CRMContact, CRMOpportunity, WebhookEvent
)

logger = logging.getLogger(__name__)


class GoHighLevelConnector(BaseCRMConnector):
    """
    GoHighLevel CRM Connector Implementation
    
    Provides full integration with GoHighLevel's API v2, including:
    - Contact and opportunity management
    - Custom field mapping for competitive intelligence
    - Webhook notifications for real-time updates
    - OAuth 2.0 authentication flow
    """
    
    # GHL API configuration
    BASE_URL = "https://services.leadconnectorhq.com"
    API_VERSION = "v2"
    
    # Custom field mappings for competitive intelligence
    GHL_CUSTOM_FIELDS = {
        "competitive_score": "custom.competitive_intelligence_score",
        "last_insight": "custom.last_competitive_insight",
        "threat_level": "custom.competitive_threat_level",
        "opportunity_value": "custom.competitive_opportunity_value"
    }
    
    # Status mappings
    GHL_CONTACT_STATUS_MAP = {
        "active": ContactStatus.ACTIVE,
        "inactive": ContactStatus.INACTIVE, 
        "lead": ContactStatus.LEAD,
        "customer": ContactStatus.CUSTOMER,
        "lost": ContactStatus.CHURNED
    }
    
    GHL_OPPORTUNITY_STAGE_MAP = {
        "new": OpportunityStage.PROSPECT,
        "qualification": OpportunityStage.QUALIFICATION,
        "proposal": OpportunityStage.PROPOSAL,
        "negotiation": OpportunityStage.NEGOTIATION,
        "closed-won": OpportunityStage.CLOSED_WON,
        "closed-lost": OpportunityStage.CLOSED_LOST
    }
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        webhook_secret: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize GoHighLevel connector.
        
        Args:
            client_id: GHL OAuth app client ID
            client_secret: GHL OAuth app client secret  
            redirect_uri: OAuth redirect URI
            webhook_secret: Secret for webhook signature verification
            **kwargs: Additional connector configuration
        """
        connection_config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "webhook_secret": webhook_secret
        }
        
        super().__init__(
            platform=CRMPlatform.GOHIGHLEVEL,
            connection_config=connection_config,
            rate_limit_per_minute=kwargs.get("rate_limit", 100),
            **kwargs
        )
        
        # OAuth tokens
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate using OAuth 2.0 authorization code or refresh token.
        
        Args:
            credentials: Must contain either:
                - 'authorization_code': OAuth authorization code from GHL
                OR
                - 'access_token' and 'refresh_token': Existing tokens
                - 'expires_at': Token expiration timestamp (ISO format)
        
        Returns:
            True if authentication successful
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)
                )
            
            if "authorization_code" in credentials:
                # Exchange authorization code for tokens
                success = await self._exchange_authorization_code(
                    credentials["authorization_code"]
                )
            elif "access_token" in credentials and "refresh_token" in credentials:
                # Use existing tokens
                self.access_token = credentials["access_token"]
                self.refresh_token = credentials["refresh_token"]
                
                if "expires_at" in credentials:
                    self.token_expires_at = datetime.fromisoformat(
                        credentials["expires_at"]
                    )
                
                success = await self._refresh_access_token()
            else:
                logger.error("Invalid credentials provided")
                return False
            
            if success:
                # Test connection and get account info
                connection_test = await self.test_connection()
                if connection_test:
                    self.is_connected = True
                    
                    # Create connection object
                    self.connection = CRMConnection(
                        connection_id=f"ghl_{self.connection_config['client_id']}",
                        platform=self.platform,
                        instance_url=self.BASE_URL,
                        api_version=self.API_VERSION,
                        authenticated=True,
                        auth_expires_at=self.token_expires_at,
                        rate_limit_remaining=self.rate_limit_per_minute,
                        rate_limit_reset_at=None,
                        last_sync_at=None,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    
                    logger.info("Successfully authenticated with GoHighLevel")
                    return True
                else:
                    logger.error("Authentication successful but connection test failed")
                    return False
            else:
                logger.error("Failed to authenticate with GoHighLevel")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def _exchange_authorization_code(self, auth_code: str) -> bool:
        """Exchange authorization code for access and refresh tokens."""
        try:
            data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": self.connection_config["client_id"],
                "client_secret": self.connection_config["client_secret"],
                "redirect_uri": self.connection_config["redirect_uri"]
            }
            
            async with self.session.post(
                f"{self.BASE_URL}/oauth/token",
                data=data
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    self.access_token = token_data["access_token"]
                    self.refresh_token = token_data["refresh_token"]
                    
                    # Calculate expiration time
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = (
                        datetime.now(timezone.utc) + 
                        timedelta(seconds=expires_in)
                    )
                    
                    return True
                else:
                    logger.error(f"Token exchange failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return False
    
    async def _refresh_access_token(self) -> bool:
        """Refresh access token using refresh token."""
        try:
            if not self.refresh_token:
                logger.error("No refresh token available")
                return False
            
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.connection_config["client_id"],
                "client_secret": self.connection_config["client_secret"]
            }
            
            async with self.session.post(
                f"{self.BASE_URL}/oauth/token",
                data=data
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    self.access_token = token_data["access_token"]
                    if "refresh_token" in token_data:
                        self.refresh_token = token_data["refresh_token"]
                    
                    # Update expiration time
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = (
                        datetime.now(timezone.utc) + 
                        timedelta(seconds=expires_in)
                    )
                    
                    return True
                else:
                    logger.error(f"Token refresh failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False
    
    async def _ensure_valid_token(self) -> bool:
        """Ensure access token is valid, refresh if needed."""
        if not self.access_token:
            return False
        
        # Check if token is about to expire (within 5 minutes)
        if self.token_expires_at:
            time_until_expiry = self.token_expires_at - datetime.now(timezone.utc)
            if time_until_expiry < timedelta(minutes=5):
                logger.info("Access token expiring soon, refreshing...")
                return await self._refresh_access_token()
        
        return True
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Make authenticated API request to GoHighLevel."""
        try:
            # Rate limiting
            await self._wait_for_rate_limit()
            
            # Ensure valid token
            if not await self._ensure_valid_token():
                logger.error("Invalid or expired access token")
                self._update_metrics(False)
                return None
            
            # Prepare request
            url = f"{self.BASE_URL}/{endpoint}"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Make request
            async with self.session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=data if data else None
            ) as response:
                
                # Handle rate limiting
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if retry_count < self.max_retries:
                        logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        return await self._make_request(
                            method, endpoint, params, data, retry_count + 1
                        )
                    else:
                        logger.error("Max retries exceeded for rate limiting")
                        self._update_metrics(False)
                        return None
                
                # Handle token expiration
                if response.status == 401:
                    logger.warning("Access token expired, attempting refresh")
                    if await self._refresh_access_token() and retry_count < 1:
                        return await self._make_request(
                            method, endpoint, params, data, retry_count + 1
                        )
                    else:
                        logger.error("Token refresh failed")
                        self._update_metrics(False)
                        return None
                
                # Handle successful responses
                if 200 <= response.status < 300:
                    self._update_metrics(True)
                    if response.headers.get("content-type", "").startswith("application/json"):
                        return await response.json()
                    else:
                        return {"status": "success"}
                else:
                    logger.error(f"API request failed: {response.status}")
                    self._update_metrics(False)
                    return None
                    
        except Exception as e:
            logger.error(f"API request error: {e}")
            self._update_metrics(False)
            return None
    
    async def test_connection(self) -> bool:
        """Test connection to GoHighLevel API."""
        try:
            # Try to get account information
            result = await self._make_request("GET", "oauth/installedLocations")
            return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_contacts(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        updated_since: Optional[datetime] = None
    ) -> List[CRMContact]:
        """
        Retrieve contacts from GoHighLevel.
        
        Args:
            limit: Maximum contacts to retrieve (max 100)
            offset: Number of contacts to skip
            filters: Additional filters (email, phone, tags, etc.)
            updated_since: Only contacts updated since this datetime
            
        Returns:
            List of CRM contacts
        """
        try:
            params = {
                "limit": min(limit, 100),  # GHL max limit is 100
                "offset": offset
            }
            
            # Add filters
            if filters:
                if "email" in filters:
                    params["email"] = filters["email"]
                if "phone" in filters:
                    params["phone"] = filters["phone"]
                if "tags" in filters:
                    params["tags"] = ",".join(filters["tags"])
            
            # Add date filter
            if updated_since:
                params["dateUpdated"] = updated_since.isoformat()
            
            # Make request
            result = await self._make_request("GET", "contacts", params=params)
            
            if not result or "contacts" not in result:
                return []
            
            # Convert to standard format
            contacts = []
            for ghl_contact in result["contacts"]:
                contact = self._convert_ghl_contact_to_standard(ghl_contact)
                if contact:
                    contacts.append(contact)
            
            return contacts
            
        except Exception as e:
            logger.error(f"Failed to retrieve contacts: {e}")
            return []
    
    async def get_contact(self, contact_id: str) -> Optional[CRMContact]:
        """Get a specific contact by ID."""
        try:
            result = await self._make_request("GET", f"contacts/{contact_id}")
            
            if result and "contact" in result:
                return self._convert_ghl_contact_to_standard(result["contact"])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve contact {contact_id}: {e}")
            return None
    
    async def create_contact(self, contact: CRMContact) -> str:
        """Create a new contact in GoHighLevel."""
        try:
            ghl_data = self._convert_standard_contact_to_ghl(contact)
            
            result = await self._make_request("POST", "contacts", data=ghl_data)
            
            if result and "contact" in result:
                return result["contact"]["id"]
            else:
                raise ValueError("Contact creation failed")
                
        except Exception as e:
            logger.error(f"Failed to create contact: {e}")
            raise
    
    async def update_contact(self, contact: CRMContact) -> bool:
        """Update an existing contact in GoHighLevel."""
        try:
            ghl_data = self._convert_standard_contact_to_ghl(contact, is_update=True)
            
            result = await self._make_request(
                "PUT", 
                f"contacts/{contact.external_id}", 
                data=ghl_data
            )
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to update contact {contact.external_id}: {e}")
            return False
    
    async def get_opportunities(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        updated_since: Optional[datetime] = None
    ) -> List[CRMOpportunity]:
        """Retrieve opportunities from GoHighLevel."""
        try:
            params = {
                "limit": min(limit, 100),
                "offset": offset
            }
            
            # Add filters
            if filters:
                if "stage" in filters:
                    params["status"] = filters["stage"]
                if "contact_id" in filters:
                    params["contactId"] = filters["contact_id"]
            
            if updated_since:
                params["dateUpdated"] = updated_since.isoformat()
            
            result = await self._make_request("GET", "opportunities", params=params)
            
            if not result or "opportunities" not in result:
                return []
            
            opportunities = []
            for ghl_opp in result["opportunities"]:
                opportunity = self._convert_ghl_opportunity_to_standard(ghl_opp)
                if opportunity:
                    opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Failed to retrieve opportunities: {e}")
            return []
    
    async def get_opportunity(self, opportunity_id: str) -> Optional[CRMOpportunity]:
        """Get a specific opportunity by ID."""
        try:
            result = await self._make_request("GET", f"opportunities/{opportunity_id}")
            
            if result and "opportunity" in result:
                return self._convert_ghl_opportunity_to_standard(result["opportunity"])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve opportunity {opportunity_id}: {e}")
            return None
    
    async def create_opportunity(self, opportunity: CRMOpportunity) -> str:
        """Create a new opportunity in GoHighLevel."""
        try:
            ghl_data = self._convert_standard_opportunity_to_ghl(opportunity)
            
            result = await self._make_request("POST", "opportunities", data=ghl_data)
            
            if result and "opportunity" in result:
                return result["opportunity"]["id"]
            else:
                raise ValueError("Opportunity creation failed")
                
        except Exception as e:
            logger.error(f"Failed to create opportunity: {e}")
            raise
    
    async def update_opportunity(self, opportunity: CRMOpportunity) -> bool:
        """Update an existing opportunity in GoHighLevel."""
        try:
            ghl_data = self._convert_standard_opportunity_to_ghl(
                opportunity, is_update=True
            )
            
            result = await self._make_request(
                "PUT",
                f"opportunities/{opportunity.external_id}",
                data=ghl_data
            )
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to update opportunity {opportunity.external_id}: {e}")
            return False
    
    async def add_note(
        self,
        object_type: str,
        object_id: str,
        content: str,
        note_type: str = "intelligence_insight"
    ) -> str:
        """Add a note to a contact or opportunity."""
        try:
            # Map object type to GHL endpoint
            if object_type == "contact":
                endpoint = f"contacts/{object_id}/notes"
            elif object_type == "opportunity":
                endpoint = f"opportunities/{object_id}/notes"
            else:
                raise ValueError(f"Unsupported object type: {object_type}")
            
            data = {
                "body": content,
                "type": note_type,
                "userId": "system"  # System-generated note
            }
            
            result = await self._make_request("POST", endpoint, data=data)
            
            if result and "note" in result:
                return result["note"]["id"]
            else:
                raise ValueError("Note creation failed")
                
        except Exception as e:
            logger.error(f"Failed to add note: {e}")
            raise
    
    async def add_tags(
        self,
        object_type: str,
        object_id: str,
        tags: List[str]
    ) -> bool:
        """Add tags to a contact or opportunity."""
        try:
            if object_type == "contact":
                # Get current contact data
                contact = await self.get_contact(object_id)
                if not contact:
                    return False
                
                # Add new tags to existing ones
                existing_tags = set(contact.tags)
                new_tags = existing_tags.union(set(tags))
                
                # Update contact with new tags
                data = {"tags": list(new_tags)}
                result = await self._make_request(
                    "PUT", 
                    f"contacts/{object_id}",
                    data=data
                )
                
                return result is not None
            else:
                logger.warning(f"Tags not supported for {object_type} in GoHighLevel")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add tags: {e}")
            return False
    
    async def setup_webhook(
        self,
        webhook_url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> str:
        """Setup webhook for real-time notifications."""
        try:
            # GoHighLevel webhook configuration
            data = {
                "url": webhook_url,
                "events": events,
                "status": "active"
            }
            
            if secret:
                data["secret"] = secret
            
            result = await self._make_request("POST", "webhooks", data=data)
            
            if result and "webhook" in result:
                webhook_id = result["webhook"]["id"]
                logger.info(f"Webhook created: {webhook_id}")
                return webhook_id
            else:
                raise ValueError("Webhook creation failed")
                
        except Exception as e:
            logger.error(f"Failed to setup webhook: {e}")
            raise
    
    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """Verify GoHighLevel webhook signature."""
        try:
            # GoHighLevel uses HMAC-SHA256 for webhook signatures
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    def _convert_ghl_contact_to_standard(self, ghl_contact: Dict[str, Any]) -> Optional[CRMContact]:
        """Convert GoHighLevel contact to standard format."""
        try:
            # Extract custom fields for competitive intelligence
            custom_fields = ghl_contact.get("customFields", {})
            competitive_score = None
            last_insight = None
            
            # Look for competitive intelligence fields
            for field in custom_fields:
                if field.get("key") == self.GHL_CUSTOM_FIELDS["competitive_score"]:
                    try:
                        competitive_score = float(field.get("value", 0))
                    except (ValueError, TypeError):
                        pass
                elif field.get("key") == self.GHL_CUSTOM_FIELDS["last_insight"]:
                    try:
                        last_insight = datetime.fromisoformat(field.get("value"))
                    except (ValueError, TypeError):
                        pass
            
            # Map status
            ghl_status = ghl_contact.get("type", "lead").lower()
            status = self.GHL_CONTACT_STATUS_MAP.get(ghl_status, ContactStatus.LEAD)
            
            # Extract tags
            tags = ghl_contact.get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            
            return CRMContact(
                contact_id=str(uuid4()),
                external_id=ghl_contact["id"],
                email=ghl_contact.get("email", ""),
                first_name=ghl_contact.get("firstName"),
                last_name=ghl_contact.get("lastName"),
                company=ghl_contact.get("companyName"),
                phone=ghl_contact.get("phone"),
                status=status,
                tags=tags,
                custom_fields=custom_fields,
                competitive_intelligence_score=competitive_score,
                last_competitive_insight=last_insight,
                created_at=datetime.fromisoformat(ghl_contact.get("dateAdded", datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(ghl_contact.get("dateUpdated", datetime.now().isoformat()))
            )
            
        except Exception as e:
            logger.error(f"Failed to convert GHL contact: {e}")
            return None
    
    def _convert_standard_contact_to_ghl(
        self, 
        contact: CRMContact, 
        is_update: bool = False
    ) -> Dict[str, Any]:
        """Convert standard contact to GoHighLevel format."""
        data = {}
        
        if contact.email:
            data["email"] = contact.email
        if contact.first_name:
            data["firstName"] = contact.first_name
        if contact.last_name:
            data["lastName"] = contact.last_name
        if contact.company:
            data["companyName"] = contact.company
        if contact.phone:
            data["phone"] = contact.phone
        
        # Map status back to GHL
        ghl_status_map = {v: k for k, v in self.GHL_CONTACT_STATUS_MAP.items()}
        if contact.status in ghl_status_map:
            data["type"] = ghl_status_map[contact.status]
        
        # Add tags
        if contact.tags:
            data["tags"] = contact.tags
        
        # Add competitive intelligence custom fields
        custom_fields = []
        
        if contact.competitive_intelligence_score is not None:
            custom_fields.append({
                "key": self.GHL_CUSTOM_FIELDS["competitive_score"],
                "value": str(contact.competitive_intelligence_score)
            })
        
        if contact.last_competitive_insight:
            custom_fields.append({
                "key": self.GHL_CUSTOM_FIELDS["last_insight"],
                "value": contact.last_competitive_insight.isoformat()
            })
        
        if custom_fields:
            data["customFields"] = custom_fields
        
        return data
    
    def _convert_ghl_opportunity_to_standard(
        self, 
        ghl_opp: Dict[str, Any]
    ) -> Optional[CRMOpportunity]:
        """Convert GoHighLevel opportunity to standard format."""
        try:
            # Map stage
            ghl_stage = ghl_opp.get("status", "new").lower()
            stage = self.GHL_OPPORTUNITY_STAGE_MAP.get(ghl_stage, OpportunityStage.PROSPECT)
            
            # Parse amount
            amount = None
            if "monetaryValue" in ghl_opp:
                try:
                    amount = float(ghl_opp["monetaryValue"])
                except (ValueError, TypeError):
                    pass
            
            # Parse dates
            close_date = None
            if "closeDate" in ghl_opp and ghl_opp["closeDate"]:
                try:
                    close_date = datetime.fromisoformat(ghl_opp["closeDate"])
                except ValueError:
                    pass
            
            return CRMOpportunity(
                opportunity_id=str(uuid4()),
                external_id=ghl_opp["id"],
                contact_id=ghl_opp.get("contactId", ""),
                name=ghl_opp.get("name", "Unnamed Opportunity"),
                stage=stage,
                amount=amount,
                currency="USD",  # GHL default
                close_date=close_date,
                probability=ghl_opp.get("probability"),
                competitive_threats=[],  # Would be populated from custom fields
                competitive_advantages=[],  # Would be populated from custom fields
                intelligence_insights=[],  # Would be populated from notes/custom fields
                created_at=datetime.fromisoformat(ghl_opp.get("dateCreated", datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(ghl_opp.get("dateUpdated", datetime.now().isoformat()))
            )
            
        except Exception as e:
            logger.error(f"Failed to convert GHL opportunity: {e}")
            return None
    
    def _convert_standard_opportunity_to_ghl(
        self,
        opportunity: CRMOpportunity,
        is_update: bool = False
    ) -> Dict[str, Any]:
        """Convert standard opportunity to GoHighLevel format."""
        data = {
            "name": opportunity.name,
            "contactId": opportunity.contact_id
        }
        
        # Map stage back to GHL
        ghl_stage_map = {v: k for k, v in self.GHL_OPPORTUNITY_STAGE_MAP.items()}
        if opportunity.stage in ghl_stage_map:
            data["status"] = ghl_stage_map[opportunity.stage]
        
        if opportunity.amount is not None:
            data["monetaryValue"] = opportunity.amount
        
        if opportunity.close_date:
            data["closeDate"] = opportunity.close_date.isoformat()
        
        if opportunity.probability is not None:
            data["probability"] = opportunity.probability
        
        return data
    
    async def close(self):
        """Close the connector and cleanup resources."""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.is_connected = False
        logger.info("GoHighLevel connector closed")


# Export the connector
__all__ = ["GoHighLevelConnector"]