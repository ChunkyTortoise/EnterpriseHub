"""
GHL Deal Intelligence Service - Real CRM Data Integration
========================================================

Replaces mock deal data with real GoHighLevel CRM integration for Emergency Deal Rescue.
Provides live deal risk monitoring and conversation intelligence.

Author: Data Integration Phase - January 2026
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.ghl_api_client import GHLAPIClient

logger = get_logger(__name__)


@dataclass
class GHLDealData:
    """Structured deal data from GHL opportunities."""

    deal_id: str
    contact_id: str
    opportunity_id: str

    # Basic deal info
    deal_value: float
    commission_value: float
    deal_stage: str
    pipeline_id: str

    # Timeline info
    created_date: datetime
    updated_date: datetime
    expected_close_date: Optional[datetime]
    days_since_creation: int

    # Contact info
    contact_name: str
    contact_email: Optional[str]
    contact_phone: Optional[str]

    # Property details
    property_address: Optional[str]
    property_type: Optional[str]
    property_value: Optional[float]

    # Additional context
    deal_source: Optional[str]
    assigned_user: Optional[str]
    tags: List[str]
    custom_fields: Dict[str, Any]

    # Conversation context
    last_contact_date: Optional[datetime]
    conversation_count: int
    recent_messages: List[Dict]


class GHLDealIntelligenceService:
    """
    Real-time deal intelligence from GoHighLevel CRM.

    Replaces mock data in Emergency Deal Rescue system with live CRM data.
    Provides comprehensive deal context for churn prediction and intervention.
    """

    def __init__(self):
        self.ghl_client = GHLAPIClient()
        self.cache = get_cache_service()

        # Configuration
        self.cache_ttl = 1800  # 30 minutes for deal data
        self.conversation_cache_ttl = 300  # 5 minutes for conversations

        # Deal value thresholds for prioritization
        self.high_value_threshold = 500000
        self.critical_value_threshold = 750000

    async def get_active_deals(
        self, limit: int = 50, min_value: Optional[float] = None, pipeline_ids: Optional[List[str]] = None
    ) -> List[GHLDealData]:
        """
        Get active deals from GHL CRM.

        Args:
            limit: Maximum number of deals to return
            min_value: Minimum deal value filter
            pipeline_ids: Specific pipeline IDs to include

        Returns:
            List of active deals with comprehensive data
        """
        cache_key = f"ghl_active_deals:{limit}:{min_value}:{pipeline_ids}"

        # Check cache first
        cached_deals = await self.cache.get(cache_key)
        if cached_deals:
            deals_data = json.loads(cached_deals)
            return [self._dict_to_deal_data(deal) for deal in deals_data]

        try:
            # Get opportunities from GHL
            all_deals = []

            if pipeline_ids:
                # Get deals from specific pipelines
                for pipeline_id in pipeline_ids:
                    response = await self.ghl_client.get_opportunities(limit=limit, pipeline_id=pipeline_id)
                    opportunities = response.get("opportunities", [])
                    all_deals.extend(opportunities)
            else:
                # Get all opportunities
                response = await self.ghl_client.get_opportunities(limit=limit)
                all_deals = response.get("opportunities", [])

            # Process and enrich deal data
            enriched_deals = []

            for opportunity in all_deals:
                try:
                    deal_data = await self._process_opportunity(opportunity)

                    # Apply filters
                    if min_value and deal_data.deal_value < min_value:
                        continue

                    # Only include active deals (not closed/lost)
                    if self._is_active_deal(deal_data):
                        enriched_deals.append(deal_data)

                except Exception as e:
                    logger.warning(f"Error processing opportunity {opportunity.get('id', 'unknown')}: {e}")

            # Sort by deal value descending
            enriched_deals.sort(key=lambda d: d.deal_value, reverse=True)

            # Cache results
            deals_dict = [self._deal_data_to_dict(deal) for deal in enriched_deals]
            await self.cache.set(cache_key, json.dumps(deals_dict, default=str), expire=self.cache_ttl)

            logger.info(f"Retrieved {len(enriched_deals)} active deals from GHL")
            return enriched_deals

        except Exception as e:
            logger.error(f"Error retrieving deals from GHL: {e}")
            return []

    async def get_deal_by_id(self, deal_id: str) -> Optional[GHLDealData]:
        """Get specific deal by ID with full context."""
        cache_key = f"ghl_deal:{deal_id}"

        # Check cache
        cached_deal = await self.cache.get(cache_key)
        if cached_deal:
            return self._dict_to_deal_data(json.loads(cached_deal))

        try:
            # Get opportunity from GHL
            opportunity = await self.ghl_client.get_opportunity(deal_id)
            deal_data = await self._process_opportunity(opportunity)

            # Cache result
            deal_dict = self._deal_data_to_dict(deal_data)
            await self.cache.set(cache_key, json.dumps(deal_dict, default=str), expire=self.cache_ttl)

            return deal_data

        except Exception as e:
            logger.error(f"Error retrieving deal {deal_id} from GHL: {e}")
            return None

    async def get_deal_conversations(self, deal_id: str, contact_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a deal."""
        cache_key = f"ghl_conversations:{contact_id}"

        # Check cache
        cached_conversations = await self.cache.get(cache_key)
        if cached_conversations:
            return json.loads(cached_conversations)

        try:
            # Get conversations from GHL
            conversations_response = await self.ghl_client.get_conversations(contact_id=contact_id)
            conversations = conversations_response.get("conversations", [])

            # Get messages from recent conversations
            recent_messages = []

            for conversation in conversations[:3]:  # Last 3 conversations
                conv_id = conversation.get("id")
                if conv_id:
                    messages_response = await self.ghl_client.get_messages(conv_id, limit=10)
                    messages = messages_response.get("messages", [])

                    for message in messages:
                        recent_messages.append(
                            {
                                "content": message.get("body", ""),
                                "timestamp": message.get("dateAdded"),
                                "direction": message.get("direction"),  # inbound/outbound
                                "type": message.get("type"),
                                "conversation_id": conv_id,
                            }
                        )

            # Sort by timestamp, most recent first
            recent_messages.sort(key=lambda m: m.get("timestamp", ""), reverse=True)

            # Cache result
            await self.cache.set(
                cache_key, json.dumps(recent_messages, default=str), expire=self.conversation_cache_ttl
            )

            return recent_messages[:20]  # Return last 20 messages

        except Exception as e:
            logger.error(f"Error retrieving conversations for deal {deal_id}: {e}")
            return []

    async def get_high_risk_deals(self, risk_threshold: float = 0.5) -> List[GHLDealData]:
        """Get deals that may be at risk based on activity patterns."""

        # Get all high-value active deals
        deals = await self.get_active_deals(limit=100, min_value=self.high_value_threshold)

        high_risk_deals = []

        for deal in deals:
            risk_score = await self._calculate_basic_risk_score(deal)

            if risk_score >= risk_threshold:
                # Add risk score to deal data for sorting
                deal.custom_fields["calculated_risk_score"] = risk_score
                high_risk_deals.append(deal)

        # Sort by risk score descending
        high_risk_deals.sort(key=lambda d: d.custom_fields.get("calculated_risk_score", 0), reverse=True)

        logger.info(f"Identified {len(high_risk_deals)} high-risk deals")
        return high_risk_deals

    async def _process_opportunity(self, opportunity: Dict[str, Any]) -> GHLDealData:
        """Convert GHL opportunity to structured deal data."""

        # Extract basic opportunity data
        opportunity_id = opportunity.get("id", "")
        contact_id = opportunity.get("contactId", "")

        # Calculate deal value and commission
        monetary_value = opportunity.get("monetaryValue", 0)
        deal_value = float(monetary_value) if monetary_value else 0.0
        commission_rate = 0.06  # Default 6% commission
        commission_value = deal_value * commission_rate

        # Parse dates
        created_date = self._parse_ghl_date(opportunity.get("dateAdded"))
        updated_date = self._parse_ghl_date(opportunity.get("lastStatusChangeDate", opportunity.get("dateAdded")))
        expected_close_date = self._parse_ghl_date(opportunity.get("expectedCloseDate"))

        # Calculate days since creation
        days_since_creation = (datetime.now() - created_date).days if created_date else 0

        # Get contact information
        contact_info = await self._get_contact_info(contact_id)

        # Get conversation context
        recent_messages = await self.get_deal_conversations(opportunity_id, contact_id)
        conversation_count = len(recent_messages)

        # Find last contact date
        last_contact_date = None
        if recent_messages:
            last_message_timestamp = recent_messages[0].get("timestamp")
            if last_message_timestamp:
                last_contact_date = self._parse_ghl_date(last_message_timestamp)

        # Extract custom fields and property details
        custom_fields = opportunity.get("customFields", {})
        property_details = self._extract_property_details(custom_fields)

        return GHLDealData(
            deal_id=opportunity_id,
            contact_id=contact_id,
            opportunity_id=opportunity_id,
            deal_value=deal_value,
            commission_value=commission_value,
            deal_stage=opportunity.get("status", "unknown"),
            pipeline_id=opportunity.get("pipelineId", ""),
            created_date=created_date,
            updated_date=updated_date,
            expected_close_date=expected_close_date,
            days_since_creation=days_since_creation,
            contact_name=contact_info.get("name", "Unknown"),
            contact_email=contact_info.get("email"),
            contact_phone=contact_info.get("phone"),
            property_address=property_details.get("address"),
            property_type=property_details.get("type", "single_family"),
            property_value=property_details.get("value", deal_value),
            deal_source=opportunity.get("source", "unknown"),
            assigned_user=opportunity.get("assignedUserId"),
            tags=opportunity.get("tags", []),
            custom_fields=custom_fields,
            last_contact_date=last_contact_date,
            conversation_count=conversation_count,
            recent_messages=recent_messages,
        )

    async def _get_contact_info(self, contact_id: str) -> Dict[str, Any]:
        """Get contact information from GHL."""
        if not contact_id:
            return {}

        try:
            contact = await self.ghl_client.get_contact(contact_id)
            return {
                "name": f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                "email": contact.get("email"),
                "phone": contact.get("phone"),
                "tags": contact.get("tags", []),
                "source": contact.get("source"),
            }
        except Exception as e:
            logger.warning(f"Error getting contact info for {contact_id}: {e}")
            return {}

    def _extract_property_details(self, custom_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Extract property details from custom fields."""
        return {
            "address": custom_fields.get("property_address"),
            "type": custom_fields.get("property_type", "single_family"),
            "value": custom_fields.get("property_value"),
            "bedrooms": custom_fields.get("bedrooms"),
            "bathrooms": custom_fields.get("bathrooms"),
            "sqft": custom_fields.get("square_feet"),
            "lot_size": custom_fields.get("lot_size"),
        }

    async def _calculate_basic_risk_score(self, deal: GHLDealData) -> float:
        """Calculate basic risk score based on activity patterns."""
        risk_score = 0.0

        # Communication silence risk
        if deal.last_contact_date:
            days_since_contact = (datetime.now() - deal.last_contact_date).days
            if days_since_contact > 7:
                risk_score += 0.3  # 30% risk for week+ silence
            elif days_since_contact > 3:
                risk_score += 0.15  # 15% risk for 3+ days silence

        # Deal age risk
        if deal.days_since_creation > 45:
            risk_score += 0.25  # 25% risk for deals over 45 days old
        elif deal.days_since_creation > 30:
            risk_score += 0.1  # 10% risk for deals over 30 days old

        # Low conversation activity risk
        if deal.conversation_count < 5 and deal.days_since_creation > 14:
            risk_score += 0.2  # 20% risk for low communication

        # Stage-based risk (if deal has been in same stage too long)
        if deal.expected_close_date and deal.expected_close_date < datetime.now():
            risk_score += 0.4  # 40% risk for overdue deals

        return min(1.0, risk_score)  # Cap at 100%

    def _is_active_deal(self, deal: GHLDealData) -> bool:
        """Determine if deal is active (not closed/lost)."""
        inactive_stages = ["closed", "lost", "cancelled", "archived", "won"]
        return deal.deal_stage.lower() not in inactive_stages

    def _parse_ghl_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse GHL date string to datetime object."""
        if not date_str:
            return None

        try:
            # Try different date formats that GHL might use
            formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]

            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            # If none work, try ISO format parsing
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return None

    def _deal_data_to_dict(self, deal: GHLDealData) -> Dict[str, Any]:
        """Convert deal data to dictionary for caching."""
        return {
            "deal_id": deal.deal_id,
            "contact_id": deal.contact_id,
            "opportunity_id": deal.opportunity_id,
            "deal_value": deal.deal_value,
            "commission_value": deal.commission_value,
            "deal_stage": deal.deal_stage,
            "pipeline_id": deal.pipeline_id,
            "created_date": deal.created_date.isoformat() if deal.created_date else None,
            "updated_date": deal.updated_date.isoformat() if deal.updated_date else None,
            "expected_close_date": deal.expected_close_date.isoformat() if deal.expected_close_date else None,
            "days_since_creation": deal.days_since_creation,
            "contact_name": deal.contact_name,
            "contact_email": deal.contact_email,
            "contact_phone": deal.contact_phone,
            "property_address": deal.property_address,
            "property_type": deal.property_type,
            "property_value": deal.property_value,
            "deal_source": deal.deal_source,
            "assigned_user": deal.assigned_user,
            "tags": deal.tags,
            "custom_fields": deal.custom_fields,
            "last_contact_date": deal.last_contact_date.isoformat() if deal.last_contact_date else None,
            "conversation_count": deal.conversation_count,
            "recent_messages": deal.recent_messages,
        }

    def _dict_to_deal_data(self, deal_dict: Dict[str, Any]) -> GHLDealData:
        """Convert dictionary back to deal data object."""
        return GHLDealData(
            deal_id=deal_dict["deal_id"],
            contact_id=deal_dict["contact_id"],
            opportunity_id=deal_dict["opportunity_id"],
            deal_value=deal_dict["deal_value"],
            commission_value=deal_dict["commission_value"],
            deal_stage=deal_dict["deal_stage"],
            pipeline_id=deal_dict["pipeline_id"],
            created_date=self._parse_ghl_date(deal_dict["created_date"]),
            updated_date=self._parse_ghl_date(deal_dict["updated_date"]),
            expected_close_date=self._parse_ghl_date(deal_dict["expected_close_date"]),
            days_since_creation=deal_dict["days_since_creation"],
            contact_name=deal_dict["contact_name"],
            contact_email=deal_dict["contact_email"],
            contact_phone=deal_dict["contact_phone"],
            property_address=deal_dict["property_address"],
            property_type=deal_dict["property_type"],
            property_value=deal_dict["property_value"],
            deal_source=deal_dict["deal_source"],
            assigned_user=deal_dict["assigned_user"],
            tags=deal_dict["tags"],
            custom_fields=deal_dict["custom_fields"],
            last_contact_date=self._parse_ghl_date(deal_dict["last_contact_date"]),
            conversation_count=deal_dict["conversation_count"],
            recent_messages=deal_dict["recent_messages"],
        )


# Singleton instance
_ghl_deal_service = None


async def get_ghl_deal_intelligence_service() -> GHLDealIntelligenceService:
    """Get singleton GHL deal intelligence service."""
    global _ghl_deal_service
    if _ghl_deal_service is None:
        _ghl_deal_service = GHLDealIntelligenceService()
    return _ghl_deal_service
