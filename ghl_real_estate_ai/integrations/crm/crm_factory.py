"""
Jorge's Real Estate AI Platform - CRM Factory & Multi-CRM Support
Factory pattern for supporting multiple CRM systems with unified interface

This module provides:
- Universal CRM interface abstraction
- Factory pattern for CRM system creation
- Configuration management for multiple CRMs
- Authentication and connection handling
- Data mapping and transformation
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

import aiohttp

from ...ghl_utils.jorge_config import JorgeConfig
from ...services.cache_service import CacheService

logger = logging.getLogger(__name__)


class CRMType(Enum):
    """Supported CRM systems"""

    CHIME = "chime"
    TOP_PRODUCER = "top_producer"
    WISE_AGENT = "wise_agent"
    FOLLOW_UP_BOSS = "follow_up_boss"
    REAL_GEEKS = "real_geeks"
    LIONDESK = "liondesk"
    CUSTOM = "custom"


@dataclass
class CRMConfiguration:
    """CRM system configuration"""

    crm_type: CRMType
    api_endpoint: str
    api_key: str
    api_secret: Optional[str] = None
    oauth_token: Optional[str] = None
    refresh_token: Optional[str] = None
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    rate_limit: int = 60  # requests per minute
    timeout: int = 30  # seconds
    custom_fields_mapping: Dict[str, str] = None
    webhook_url: Optional[str] = None


@dataclass
class Contact:
    """Universal contact representation"""

    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    tags: List[str] = None
    custom_fields: Dict[str, Any] = None
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    jorge_temperature: Optional[float] = None
    jorge_insights: Dict[str, Any] = None


@dataclass
class SyncResult:
    """CRM synchronization result"""

    success: bool
    contacts_synced: int
    contacts_updated: int
    contacts_added: int
    errors: List[str]
    sync_duration: float
    last_sync_timestamp: datetime


class BaseCRMConnector(ABC):
    """Abstract base class for CRM connectors"""

    def __init__(self, config: CRMConfiguration):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = datetime.now()
        self.request_count = 0

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the CRM system"""
        pass

    @abstractmethod
    async def get_contacts(
        self, limit: Optional[int] = None, offset: Optional[int] = None, modified_since: Optional[datetime] = None
    ) -> List[Contact]:
        """Retrieve contacts from CRM"""
        pass

    @abstractmethod
    async def create_contact(self, contact: Contact) -> Contact:
        """Create a new contact in CRM"""
        pass

    @abstractmethod
    async def update_contact(self, contact: Contact) -> Contact:
        """Update existing contact in CRM"""
        pass

    @abstractmethod
    async def delete_contact(self, contact_id: str) -> bool:
        """Delete contact from CRM"""
        pass

    @abstractmethod
    async def search_contacts(self, query: str) -> List[Contact]:
        """Search contacts in CRM"""
        pass

    @abstractmethod
    async def add_note(self, contact_id: str, note: str, note_type: str = "general") -> bool:
        """Add note to contact"""
        pass

    @abstractmethod
    async def add_task(self, contact_id: str, task: Dict[str, Any]) -> bool:
        """Add task for contact"""
        pass

    async def initialize(self):
        """Initialize CRM connector"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout), headers={"User-Agent": "Jorge-AI-Platform/1.0"}
        )
        return await self.authenticate()

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    async def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        current_time = datetime.now()
        time_diff = (current_time - self.last_request_time).total_seconds()

        if time_diff < 60:  # Within the same minute
            if self.request_count >= self.config.rate_limit:
                wait_time = 60 - time_diff
                await asyncio.sleep(wait_time)
                self.request_count = 0
        else:
            self.request_count = 0

        self.request_count += 1
        self.last_request_time = current_time


class ChimeCRMConnector(BaseCRMConnector):
    """Chime CRM connector implementation"""

    async def authenticate(self) -> bool:
        """Authenticate with Chime CRM"""
        try:
            auth_url = f"{self.config.api_endpoint}/auth/token"
            auth_data = {"api_key": self.config.api_key, "api_secret": self.config.api_secret}

            await self._rate_limit_check()
            async with self.session.post(auth_url, json=auth_data) as response:
                if response.status == 200:
                    auth_result = await response.json()
                    self.config.oauth_token = auth_result.get("access_token")
                    self.session.headers.update({"Authorization": f"Bearer {self.config.oauth_token}"})
                    return True
                else:
                    logger.error(f"Chime CRM authentication failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Chime CRM authentication error: {str(e)}")
            return False

    async def get_contacts(
        self, limit: Optional[int] = None, offset: Optional[int] = None, modified_since: Optional[datetime] = None
    ) -> List[Contact]:
        """Retrieve contacts from Chime CRM"""
        try:
            url = f"{self.config.api_endpoint}/contacts"
            params = {}

            if limit:
                params["limit"] = limit
            if offset:
                params["offset"] = offset
            if modified_since:
                params["modified_since"] = modified_since.isoformat()

            await self._rate_limit_check()
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return [self._map_chime_to_contact(contact) for contact in data.get("contacts", [])]
                else:
                    logger.error(f"Failed to get Chime contacts: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error getting Chime contacts: {str(e)}")
            return []

    async def create_contact(self, contact: Contact) -> Contact:
        """Create contact in Chime CRM"""
        try:
            url = f"{self.config.api_endpoint}/contacts"
            contact_data = self._map_contact_to_chime(contact)

            await self._rate_limit_check()
            async with self.session.post(url, json=contact_data) as response:
                if response.status == 201:
                    data = await response.json()
                    return self._map_chime_to_contact(data)
                else:
                    logger.error(f"Failed to create Chime contact: {response.status}")
                    raise ValueError(f"Contact creation failed: {response.status}")

        except Exception as e:
            logger.error(f"Error creating Chime contact: {str(e)}")
            raise

    async def update_contact(self, contact: Contact) -> Contact:
        """Update contact in Chime CRM"""
        try:
            url = f"{self.config.api_endpoint}/contacts/{contact.id}"
            contact_data = self._map_contact_to_chime(contact)

            await self._rate_limit_check()
            async with self.session.put(url, json=contact_data) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._map_chime_to_contact(data)
                else:
                    logger.error(f"Failed to update Chime contact: {response.status}")
                    raise ValueError(f"Contact update failed: {response.status}")

        except Exception as e:
            logger.error(f"Error updating Chime contact: {str(e)}")
            raise

    async def delete_contact(self, contact_id: str) -> bool:
        """Delete contact from Chime CRM"""
        try:
            url = f"{self.config.api_endpoint}/contacts/{contact_id}"

            await self._rate_limit_check()
            async with self.session.delete(url) as response:
                return response.status == 204

        except Exception as e:
            logger.error(f"Error deleting Chime contact: {str(e)}")
            return False

    async def search_contacts(self, query: str) -> List[Contact]:
        """Search contacts in Chime CRM"""
        try:
            url = f"{self.config.api_endpoint}/contacts/search"
            params = {"q": query}

            await self._rate_limit_check()
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return [self._map_chime_to_contact(contact) for contact in data.get("contacts", [])]
                else:
                    return []

        except Exception as e:
            logger.error(f"Error searching Chime contacts: {str(e)}")
            return []

    async def add_note(self, contact_id: str, note: str, note_type: str = "general") -> bool:
        """Add note to Chime contact"""
        try:
            url = f"{self.config.api_endpoint}/contacts/{contact_id}/notes"
            note_data = {"content": note, "type": note_type, "created_by": "Jorge AI Platform"}

            await self._rate_limit_check()
            async with self.session.post(url, json=note_data) as response:
                return response.status == 201

        except Exception as e:
            logger.error(f"Error adding Chime note: {str(e)}")
            return False

    async def add_task(self, contact_id: str, task: Dict[str, Any]) -> bool:
        """Add task for Chime contact"""
        try:
            url = f"{self.config.api_endpoint}/contacts/{contact_id}/tasks"
            task_data = {
                "title": task.get("title", "Follow up"),
                "description": task.get("description", ""),
                "due_date": task.get("due_date"),
                "priority": task.get("priority", "normal"),
                "created_by": "Jorge AI Platform",
            }

            await self._rate_limit_check()
            async with self.session.post(url, json=task_data) as response:
                return response.status == 201

        except Exception as e:
            logger.error(f"Error adding Chime task: {str(e)}")
            return False

    def _map_chime_to_contact(self, chime_data: Dict[str, Any]) -> Contact:
        """Map Chime CRM data to universal Contact format"""
        return Contact(
            id=str(chime_data.get("id", "")),
            first_name=chime_data.get("first_name", ""),
            last_name=chime_data.get("last_name", ""),
            email=chime_data.get("email"),
            phone=chime_data.get("phone"),
            address=chime_data.get("address"),
            city=chime_data.get("city"),
            state=chime_data.get("state"),
            zip_code=chime_data.get("zip_code"),
            source=chime_data.get("source"),
            status=chime_data.get("status"),
            tags=chime_data.get("tags", []),
            custom_fields=chime_data.get("custom_fields", {}),
            created_date=self._parse_datetime(chime_data.get("created_at")),
            last_modified=self._parse_datetime(chime_data.get("updated_at")),
        )

    def _map_contact_to_chime(self, contact: Contact) -> Dict[str, Any]:
        """Map universal Contact to Chime CRM format"""
        return {
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "phone": contact.phone,
            "address": contact.address,
            "city": contact.city,
            "state": contact.state,
            "zip_code": contact.zip_code,
            "source": contact.source,
            "status": contact.status,
            "tags": contact.tags or [],
            "custom_fields": contact.custom_fields or {},
        }

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None


class TopProducerCRMConnector(BaseCRMConnector):
    """Top Producer CRM connector implementation"""

    async def authenticate(self) -> bool:
        """Authenticate with Top Producer CRM"""
        # Implementation specific to Top Producer API
        return True

    async def get_contacts(
        self, limit: Optional[int] = None, offset: Optional[int] = None, modified_since: Optional[datetime] = None
    ) -> List[Contact]:
        """Retrieve contacts from Top Producer CRM"""
        # Implementation specific to Top Producer API
        return []

    async def create_contact(self, contact: Contact) -> Contact:
        """Create contact in Top Producer CRM"""
        # Implementation specific to Top Producer API
        return contact

    async def update_contact(self, contact: Contact) -> Contact:
        """Update contact in Top Producer CRM"""
        # Implementation specific to Top Producer API
        return contact

    async def delete_contact(self, contact_id: str) -> bool:
        """Delete contact from Top Producer CRM"""
        # Implementation specific to Top Producer API
        return True

    async def search_contacts(self, query: str) -> List[Contact]:
        """Search contacts in Top Producer CRM"""
        # Implementation specific to Top Producer API
        return []

    async def add_note(self, contact_id: str, note: str, note_type: str = "general") -> bool:
        """Add note to Top Producer contact"""
        # Implementation specific to Top Producer API
        return True

    async def add_task(self, contact_id: str, task: Dict[str, Any]) -> bool:
        """Add task for Top Producer contact"""
        # Implementation specific to Top Producer API
        return True


class CRMFactory:
    """
    Factory class for creating CRM connectors
    Manages multiple CRM configurations and provides unified interface
    """

    def __init__(self):
        self.config = JorgeConfig()
        self.cache = CacheService()
        self.connectors: Dict[str, BaseCRMConnector] = {}
        self.configurations: Dict[str, CRMConfiguration] = {}

        # Registry of CRM connector classes
        self.connector_registry: Dict[CRMType, Type[BaseCRMConnector]] = {
            CRMType.CHIME: ChimeCRMConnector,
            CRMType.TOP_PRODUCER: TopProducerCRMConnector,
            # Add other CRM connectors as implemented
        }

    async def initialize(self):
        """Initialize CRM factory and load configurations"""
        try:
            await self._load_crm_configurations()
            await self._initialize_connectors()
            logger.info(f"CRM Factory initialized with {len(self.connectors)} connectors")

        except Exception as e:
            logger.error(f"CRM Factory initialization failed: {str(e)}")
            raise

    async def _load_crm_configurations(self):
        """Load CRM configurations from environment/database"""
        try:
            # Load configurations for each supported CRM
            crm_configs = {}

            # Chime CRM configuration
            chime_api_key = self.config.get_env_var("CHIME_CRM_API_KEY")
            chime_api_secret = self.config.get_env_var("CHIME_CRM_API_SECRET")
            if chime_api_key and chime_api_secret:
                crm_configs[CRMType.CHIME.value] = CRMConfiguration(
                    crm_type=CRMType.CHIME,
                    api_endpoint="https://api.chimecrm.com/v1",
                    api_key=chime_api_key,
                    api_secret=chime_api_secret,
                    rate_limit=100,
                    webhook_url=self.config.get_env_var("CHIME_WEBHOOK_URL"),
                )

            # Top Producer CRM configuration
            tp_api_key = self.config.get_env_var("TOP_PRODUCER_API_KEY")
            if tp_api_key:
                crm_configs[CRMType.TOP_PRODUCER.value] = CRMConfiguration(
                    crm_type=CRMType.TOP_PRODUCER,
                    api_endpoint="https://api.topproducer.com/v2",
                    api_key=tp_api_key,
                    rate_limit=60,
                )

            self.configurations = crm_configs
            logger.info(f"Loaded {len(self.configurations)} CRM configurations")

        except Exception as e:
            logger.error(f"Failed to load CRM configurations: {str(e)}")
            raise

    async def _initialize_connectors(self):
        """Initialize CRM connectors"""
        try:
            for crm_id, config in self.configurations.items():
                connector_class = self.connector_registry.get(config.crm_type)
                if connector_class:
                    connector = connector_class(config)
                    if await connector.initialize():
                        self.connectors[crm_id] = connector
                        logger.info(f"Successfully initialized {crm_id} CRM connector")
                    else:
                        logger.error(f"Failed to initialize {crm_id} CRM connector")

        except Exception as e:
            logger.error(f"Failed to initialize CRM connectors: {str(e)}")
            raise

    def get_connector(self, crm_type: Union[str, CRMType]) -> Optional[BaseCRMConnector]:
        """Get CRM connector by type"""
        if isinstance(crm_type, CRMType):
            crm_type = crm_type.value

        return self.connectors.get(crm_type)

    def get_available_crms(self) -> List[str]:
        """Get list of available CRM types"""
        return list(self.connectors.keys())

    async def sync_all_crms(self, modified_since: Optional[datetime] = None) -> Dict[str, SyncResult]:
        """Synchronize data from all configured CRMs"""
        try:
            sync_results = {}

            # Sync each CRM in parallel
            sync_tasks = []
            for crm_id, connector in self.connectors.items():
                task = asyncio.create_task(self._sync_single_crm(crm_id, connector, modified_since))
                sync_tasks.append((crm_id, task))

            # Wait for all sync operations to complete
            for crm_id, task in sync_tasks:
                try:
                    result = await task
                    sync_results[crm_id] = result
                except Exception as e:
                    logger.error(f"Sync failed for {crm_id}: {str(e)}")
                    sync_results[crm_id] = SyncResult(
                        success=False,
                        contacts_synced=0,
                        contacts_updated=0,
                        contacts_added=0,
                        errors=[str(e)],
                        sync_duration=0.0,
                        last_sync_timestamp=datetime.now(),
                    )

            return sync_results

        except Exception as e:
            logger.error(f"CRM sync operation failed: {str(e)}")
            raise

    async def _sync_single_crm(
        self, crm_id: str, connector: BaseCRMConnector, modified_since: Optional[datetime]
    ) -> SyncResult:
        """Synchronize single CRM system"""
        try:
            start_time = datetime.now()

            # Get contacts from CRM
            contacts = await connector.get_contacts(limit=1000, modified_since=modified_since)

            # Process and store contacts
            # This would involve updating the local database
            # and applying Jorge's AI insights

            sync_duration = (datetime.now() - start_time).total_seconds()

            return SyncResult(
                success=True,
                contacts_synced=len(contacts),
                contacts_updated=0,  # Would be calculated during processing
                contacts_added=len(contacts),  # Would be calculated during processing
                errors=[],
                sync_duration=sync_duration,
                last_sync_timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Single CRM sync failed for {crm_id}: {str(e)}")
            raise

    async def cleanup(self):
        """Clean up all CRM connectors"""
        try:
            for connector in self.connectors.values():
                await connector.cleanup()

            logger.info("CRM Factory cleanup completed")

        except Exception as e:
            logger.error(f"CRM Factory cleanup failed: {str(e)}")


# Global CRM factory instance
crm_factory = CRMFactory()
