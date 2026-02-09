"""
Property Alert System - Automated notifications for Austin real estate opportunities.

Provides intelligent property alerts including:
- New listing notifications matching lead preferences
- Price drop alerts for tracked properties
- Market opportunity alerts (underpriced properties, hot neighborhoods)
- Inventory alerts for competitive market conditions
- Corporate relocation timing alerts
"""

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.austin_market_service import (
    PropertyListing,
    PropertyType,
    get_austin_market_service,
)
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class AlertType(Enum):
    NEW_LISTING = "new_listing"
    PRICE_DROP = "price_drop"
    MARKET_OPPORTUNITY = "market_opportunity"
    INVENTORY_ALERT = "inventory_alert"
    CORPORATE_RELOCATION = "corporate_relocation"
    NEIGHBORHOOD_TREND = "neighborhood_trend"
    SCHOOL_DISTRICT = "school_district"


class AlertPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AlertCriteria:
    """Lead-specific alert criteria for property notifications."""

    lead_id: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_beds: Optional[int] = None
    max_beds: Optional[int] = None
    min_baths: Optional[float] = None
    property_types: List[PropertyType] = None
    neighborhoods: List[str] = None
    school_districts: List[str] = None
    max_commute_time: Optional[int] = None  # Minutes to work location
    work_location: Optional[str] = None
    lifestyle_preferences: List[str] = None  # walkable, family-friendly, etc.
    exclude_hoa: bool = False
    min_lot_size: Optional[float] = None
    max_year_built: Optional[int] = None
    must_have_features: List[str] = None
    deal_threshold: float = 0.1  # Percentage below market for opportunity alerts
    active: bool = True
    created_at: datetime = None
    last_updated: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()
        if self.property_types is None:
            self.property_types = [PropertyType.SINGLE_FAMILY]
        if self.neighborhoods is None:
            self.neighborhoods = []
        if self.school_districts is None:
            self.school_districts = []
        if self.lifestyle_preferences is None:
            self.lifestyle_preferences = []
        if self.must_have_features is None:
            self.must_have_features = []


@dataclass
class PropertyAlert:
    """Property alert notification."""

    alert_id: str
    lead_id: str
    alert_type: AlertType
    priority: AlertPriority
    property_data: Dict[str, Any]
    message: str
    detailed_analysis: Dict[str, Any]
    action_items: List[str]
    expiry_time: datetime
    created_at: datetime = None
    sent: bool = False

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class MarketAlert:
    """General market condition alert."""

    alert_id: str
    alert_type: AlertType
    priority: AlertPriority
    neighborhood: Optional[str]
    message: str
    market_data: Dict[str, Any]
    recommendations: List[str]
    affects_leads: List[str]  # Lead IDs that should be notified
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class PropertyAlertSystem:
    """
    Comprehensive property alert system for Austin real estate.

    Monitors MLS data, market conditions, and lead preferences to deliver
    intelligent property and market notifications.
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.market_service = get_austin_market_service()
        self.active_criteria: Dict[str, AlertCriteria] = {}
        self.sent_alerts: Set[str] = set()

    async def setup_lead_alerts(self, criteria: AlertCriteria) -> bool:
        """Set up property alerts for a specific lead."""
        try:
            # Store criteria
            self.active_criteria[criteria.lead_id] = criteria

            # Cache criteria for persistence
            cache_key = f"alert_criteria:{criteria.lead_id}"
            await self.cache.set(cache_key, asdict(criteria), ttl=86400 * 30)  # 30 days

            logger.info(f"Set up alerts for lead {criteria.lead_id}")
            return True

        except Exception as e:
            logger.error(f"Error setting up alerts for lead {criteria.lead_id}: {e}")
            return False

    async def update_lead_alerts(self, lead_id: str, criteria: AlertCriteria) -> bool:
        """Update existing alert criteria for a lead."""
        try:
            criteria.last_updated = datetime.now()
            self.active_criteria[lead_id] = criteria

            cache_key = f"alert_criteria:{lead_id}"
            await self.cache.set(cache_key, asdict(criteria), ttl=86400 * 30)

            logger.info(f"Updated alerts for lead {lead_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating alerts for lead {lead_id}: {e}")
            return False

    async def disable_lead_alerts(self, lead_id: str) -> bool:
        """Disable alerts for a specific lead."""
        try:
            if lead_id in self.active_criteria:
                self.active_criteria[lead_id].active = False

                cache_key = f"alert_criteria:{lead_id}"
                await self.cache.set(cache_key, asdict(self.active_criteria[lead_id]), ttl=86400 * 30)

            logger.info(f"Disabled alerts for lead {lead_id}")
            return True

        except Exception as e:
            logger.error(f"Error disabling alerts for lead {lead_id}: {e}")
            return False

    async def check_new_listings(self) -> List[PropertyAlert]:
        """Check for new listings matching active alert criteria."""
        alerts = []

        try:
            # Get recent listings (last 24 hours)
            recent_listings = await self._get_recent_listings()

            for listing in recent_listings:
                # Check against all active criteria
                for lead_id, criteria in self.active_criteria.items():
                    if not criteria.active:
                        continue

                    if await self._property_matches_criteria(listing, criteria):
                        alert = await self._create_new_listing_alert(listing, criteria)
                        alerts.append(alert)

            logger.info(f"Generated {len(alerts)} new listing alerts")
            return alerts

        except Exception as e:
            logger.error(f"Error checking new listings: {e}")
            return []

    async def check_price_drops(self) -> List[PropertyAlert]:
        """Check for price drops on tracked properties."""
        alerts = []

        try:
            # Get properties with recent price changes
            price_changed_properties = await self._get_price_changed_properties()

            for listing in price_changed_properties:
                price_changes = listing.price_changes
                if not price_changes:
                    continue

                # Check if latest change is a drop
                latest_change = price_changes[-1]
                if latest_change["type"] == "decrease":
                    # Find leads interested in this property
                    interested_leads = await self._find_interested_leads(listing)

                    for lead_id in interested_leads:
                        criteria = self.active_criteria.get(lead_id)
                        if criteria and criteria.active:
                            alert = await self._create_price_drop_alert(listing, latest_change, criteria)
                            alerts.append(alert)

            logger.info(f"Generated {len(alerts)} price drop alerts")
            return alerts

        except Exception as e:
            logger.error(f"Error checking price drops: {e}")
            return []

    async def check_market_opportunities(self) -> List[PropertyAlert]:
        """Check for underpriced properties and market opportunities."""
        alerts = []

        try:
            # Analyze recent listings for opportunities
            recent_listings = await self._get_recent_listings()

            for listing in recent_listings:
                opportunity_score = await self._calculate_opportunity_score(listing)

                if opportunity_score > 75:  # High opportunity threshold
                    # Find leads who might be interested
                    interested_leads = await self._find_leads_for_opportunity(listing)

                    for lead_id in interested_leads:
                        criteria = self.active_criteria.get(lead_id)
                        if criteria and criteria.active:
                            alert = await self._create_opportunity_alert(listing, opportunity_score, criteria)
                            alerts.append(alert)

            logger.info(f"Generated {len(alerts)} opportunity alerts")
            return alerts

        except Exception as e:
            logger.error(f"Error checking market opportunities: {e}")
            return []

    async def check_inventory_alerts(self) -> List[MarketAlert]:
        """Check for significant inventory changes in key neighborhoods."""
        alerts = []

        try:
            for neighborhood in ["Round Rock", "Domain", "South Lamar", "Downtown", "Mueller"]:
                metrics = await self.market_service.get_market_metrics(neighborhood)

                # Check for low inventory alerts
                if metrics.months_supply < 1.5:
                    affected_leads = await self._find_leads_in_neighborhood(neighborhood)
                    if affected_leads:
                        alert = MarketAlert(
                            alert_id=f"inventory_low_{neighborhood}_{int(datetime.now().timestamp())}",
                            alert_type=AlertType.INVENTORY_ALERT,
                            priority=AlertPriority.HIGH,
                            neighborhood=neighborhood,
                            message=f"Critical inventory shortage in {neighborhood}",
                            market_data={
                                "months_supply": metrics.months_supply,
                                "inventory_count": metrics.inventory_count,
                                "market_condition": metrics.market_condition.value,
                            },
                            recommendations=[
                                "Act quickly on suitable properties",
                                "Be prepared for competitive offers",
                                "Consider expanding search criteria",
                                "Pre-approval letter essential",
                            ],
                            affects_leads=affected_leads,
                        )
                        alerts.append(alert)

            logger.info(f"Generated {len(alerts)} inventory alerts")
            return alerts

        except Exception as e:
            logger.error(f"Error checking inventory alerts: {e}")
            return []

    async def check_corporate_relocation_alerts(self) -> List[PropertyAlert]:
        """Check for corporate relocation opportunities and timing."""
        alerts = []

        try:
            # Check for corporate announcement impacts
            corporate_events = await self._get_corporate_events()

            for event in corporate_events:
                if event["type"] == "expansion" or event["type"] == "new_campus":
                    # Find leads who might be affected
                    affected_leads = await self._find_corporate_affected_leads(event)

                    for lead_id in affected_leads:
                        criteria = self.active_criteria.get(lead_id)
                        if criteria and criteria.active:
                            alert = await self._create_corporate_alert(event, criteria)
                            alerts.append(alert)

            logger.info(f"Generated {len(alerts)} corporate relocation alerts")
            return alerts

        except Exception as e:
            logger.error(f"Error checking corporate relocation alerts: {e}")
            return []

    async def process_all_alerts(self) -> Dict[str, List[Any]]:
        """Process all alert types and return categorized results."""
        try:
            # Load active criteria from cache
            await self._load_active_criteria()

            # Run all alert checks in parallel
            results = await asyncio.gather(
                self.check_new_listings(),
                self.check_price_drops(),
                self.check_market_opportunities(),
                self.check_inventory_alerts(),
                self.check_corporate_relocation_alerts(),
                return_exceptions=True,
            )

            return {
                "new_listings": results[0] if not isinstance(results[0], Exception) else [],
                "price_drops": results[1] if not isinstance(results[1], Exception) else [],
                "opportunities": results[2] if not isinstance(results[2], Exception) else [],
                "inventory": results[3] if not isinstance(results[3], Exception) else [],
                "corporate": results[4] if not isinstance(results[4], Exception) else [],
            }

        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
            return {}

    async def get_alert_summary(self, lead_id: str) -> Dict[str, Any]:
        """Get alert summary for a specific lead."""
        try:
            cache_key = f"alert_summary:{lead_id}"
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

            criteria = self.active_criteria.get(lead_id)
            if not criteria or not criteria.active:
                return {"active": False, "message": "No active alerts configured"}

            # Get recent alerts for this lead
            recent_alerts = await self._get_recent_alerts_for_lead(lead_id)

            summary = {
                "active": True,
                "criteria": asdict(criteria),
                "recent_alerts_count": len(recent_alerts),
                "alerts_last_24h": len(
                    [a for a in recent_alerts if a.created_at > datetime.now() - timedelta(hours=24)]
                ),
                "high_priority_alerts": len(
                    [a for a in recent_alerts if a.priority in [AlertPriority.HIGH, AlertPriority.URGENT]]
                ),
                "last_alert": recent_alerts[0].created_at.isoformat() if recent_alerts else None,
                "alert_types_active": [alert_type.value for alert_type in AlertType],
            }

            # Cache for 10 minutes
            await self.cache.set(cache_key, summary, ttl=600)
            return summary

        except Exception as e:
            logger.error(f"Error getting alert summary for {lead_id}: {e}")
            return {"error": str(e)}

    # Private helper methods

    async def _load_active_criteria(self):
        """Load active criteria from cache."""
        try:
            # In production, this would load from database
            # For now, maintain in-memory state
            pass
        except Exception as e:
            logger.error(f"Error loading active criteria: {e}")

    async def _get_recent_listings(self) -> List[PropertyListing]:
        """Get recent property listings."""
        # In production, this would query MLS for properties listed in last 24 hours
        criteria = {"listed_since": datetime.now() - timedelta(hours=24)}
        return await self.market_service.search_properties(criteria, limit=100)

    async def _get_price_changed_properties(self) -> List[PropertyListing]:
        """Get properties with recent price changes."""
        # In production, track price changes in database
        # For demo, simulate some price changes
        return await self.market_service.search_properties({}, limit=20)

    async def _property_matches_criteria(self, listing: PropertyListing, criteria: AlertCriteria) -> bool:
        """Check if property matches lead's alert criteria."""
        # Price range
        if criteria.min_price and listing.price < criteria.min_price:
            return False
        if criteria.max_price and listing.price > criteria.max_price:
            return False

        # Bedrooms
        if criteria.min_beds and listing.beds < criteria.min_beds:
            return False
        if criteria.max_beds and listing.beds > criteria.max_beds:
            return False

        # Bathrooms
        if criteria.min_baths and listing.baths < criteria.min_baths:
            return False

        # Property type
        if criteria.property_types and listing.property_type not in criteria.property_types:
            return False

        # Neighborhood
        if criteria.neighborhoods and listing.neighborhood not in criteria.neighborhoods:
            return False

        # School district
        if criteria.school_districts and listing.school_district not in criteria.school_districts:
            return False

        # Commute time
        if criteria.work_location and criteria.max_commute_time:
            commute_data = await self.market_service.get_commute_analysis(listing.coordinates, criteria.work_location)
            # Parse commute time and check
            if (
                commute_data.get("driving", {}).get("time_rush_hour", "60 minutes")
                > f"{criteria.max_commute_time} minutes"
            ):
                return False

        return True

    async def _create_new_listing_alert(self, listing: PropertyListing, criteria: AlertCriteria) -> PropertyAlert:
        """Create alert for new listing."""
        # Calculate why this is a good match
        match_reasons = []
        if criteria.neighborhoods and listing.neighborhood in criteria.neighborhoods:
            match_reasons.append(f"In preferred neighborhood: {listing.neighborhood}")
        if criteria.work_location:
            match_reasons.append(f"Good commute to {criteria.work_location}")

        return PropertyAlert(
            alert_id=f"new_{listing.mls_id}_{criteria.lead_id}_{int(datetime.now().timestamp())}",
            lead_id=criteria.lead_id,
            alert_type=AlertType.NEW_LISTING,
            priority=AlertPriority.MEDIUM,
            property_data=asdict(listing),
            message=f"New listing matches your criteria: {listing.address}",
            detailed_analysis={
                "match_score": 85,
                "match_reasons": match_reasons,
                "market_position": "Well-priced for neighborhood",
                "urgency": "Moderate - good neighborhood, expect interest",
            },
            action_items=[
                "Schedule showing within 48 hours",
                "Research comparable sales",
                "Prepare pre-approval letter",
                "Contact Jorge for neighborhood insights",
            ],
            expiry_time=datetime.now() + timedelta(hours=48),
        )

    async def _create_price_drop_alert(
        self, listing: PropertyListing, price_change: Dict[str, Any], criteria: AlertCriteria
    ) -> PropertyAlert:
        """Create alert for price drop."""
        drop_amount = price_change["amount"]
        drop_percentage = (drop_amount / listing.price) * 100

        return PropertyAlert(
            alert_id=f"price_drop_{listing.mls_id}_{criteria.lead_id}_{int(datetime.now().timestamp())}",
            lead_id=criteria.lead_id,
            alert_type=AlertType.PRICE_DROP,
            priority=AlertPriority.HIGH if drop_percentage > 5 else AlertPriority.MEDIUM,
            property_data=asdict(listing),
            message=f"Price drop: {listing.address} reduced by ${drop_amount:,.0f} ({drop_percentage:.1f}%)",
            detailed_analysis={
                "drop_amount": drop_amount,
                "drop_percentage": drop_percentage,
                "new_price": listing.price,
                "market_impact": "Increased competitiveness",
                "seller_motivation": "High" if drop_percentage > 5 else "Moderate",
            },
            action_items=[
                "Contact listing agent immediately",
                "Schedule showing ASAP",
                "Prepare competitive offer",
                "Investigate reason for price drop",
            ],
            expiry_time=datetime.now() + timedelta(hours=24),
        )

    async def _calculate_opportunity_score(self, listing: PropertyListing) -> float:
        """Calculate opportunity score for a property."""
        # Get neighborhood metrics
        neighborhood_data = await self.market_service.get_neighborhood_analysis(listing.neighborhood)
        if not neighborhood_data:
            return 0

        score = 50  # Base score

        # Compare to neighborhood median
        if listing.price < neighborhood_data.median_price * 0.9:
            score += 20

        # Days on market factor
        if listing.days_on_market > 30:
            score += 10

        # School rating factor
        if neighborhood_data.school_rating > 8.5:
            score += 15

        # Tech worker appeal
        if neighborhood_data.tech_worker_appeal > 80:
            score += 10

        return min(100, score)

    async def _create_opportunity_alert(
        self, listing: PropertyListing, opportunity_score: float, criteria: AlertCriteria
    ) -> PropertyAlert:
        """Create market opportunity alert."""
        return PropertyAlert(
            alert_id=f"opportunity_{listing.mls_id}_{criteria.lead_id}_{int(datetime.now().timestamp())}",
            lead_id=criteria.lead_id,
            alert_type=AlertType.MARKET_OPPORTUNITY,
            priority=AlertPriority.HIGH,
            property_data=asdict(listing),
            message=f"Market opportunity: {listing.address} (Score: {opportunity_score:.0f}/100)",
            detailed_analysis={
                "opportunity_score": opportunity_score,
                "below_market": True,
                "reasons": ["Below neighborhood median", "Good school district", "High tech appeal"],
                "estimated_equity": "$45,000 immediate equity potential",
            },
            action_items=[
                "Schedule immediate showing",
                "Prepare strong offer",
                "Research property history",
                "Consider quick close to strengthen offer",
            ],
            expiry_time=datetime.now() + timedelta(hours=12),
        )

    async def _find_interested_leads(self, listing: PropertyListing) -> List[str]:
        """Find leads who would be interested in this specific property."""
        interested = []
        for lead_id, criteria in self.active_criteria.items():
            if criteria.active and await self._property_matches_criteria(listing, criteria):
                interested.append(lead_id)
        return interested

    async def _find_leads_for_opportunity(self, listing: PropertyListing) -> List[str]:
        """Find leads who might be interested in this opportunity."""
        return await self._find_interested_leads(listing)

    async def _find_leads_in_neighborhood(self, neighborhood: str) -> List[str]:
        """Find leads interested in a specific neighborhood."""
        interested = []
        for lead_id, criteria in self.active_criteria.items():
            if criteria.active and neighborhood in criteria.neighborhoods:
                interested.append(lead_id)
        return interested

    async def _get_corporate_events(self) -> List[Dict[str, Any]]:
        """Get recent corporate events affecting Austin market."""
        # In production, integrate with news APIs, corporate announcements
        return [
            {
                "type": "expansion",
                "company": "Apple",
                "announcement_date": datetime.now() - timedelta(days=3),
                "impact": "Additional 5,000 jobs by 2025",
                "location": "Round Rock campus",
            }
        ]

    async def _find_corporate_affected_leads(self, event: Dict[str, Any]) -> List[str]:
        """Find leads affected by corporate events."""
        affected = []
        company = event["company"].lower()
        for lead_id, criteria in self.active_criteria.items():
            if criteria.active and criteria.work_location and company in criteria.work_location.lower():
                affected.append(lead_id)
        return affected

    async def _create_corporate_alert(self, event: Dict[str, Any], criteria: AlertCriteria) -> PropertyAlert:
        """Create corporate relocation alert."""
        return PropertyAlert(
            alert_id=f"corporate_{event['company']}_{criteria.lead_id}_{int(datetime.now().timestamp())}",
            lead_id=criteria.lead_id,
            alert_type=AlertType.CORPORATE_RELOCATION,
            priority=AlertPriority.HIGH,
            property_data={},
            message=f"{event['company']} expansion may impact your home search timeline",
            detailed_analysis={
                "event": event,
                "market_impact": "Increased demand in preferred neighborhoods",
                "timing_recommendation": "Consider acting sooner to avoid increased competition",
            },
            action_items=[
                "Accelerate home search timeline",
                "Consider pre-approval for higher amount",
                "Expand search to adjacent neighborhoods",
                "Monitor inventory levels closely",
            ],
            expiry_time=datetime.now() + timedelta(days=7),
        )

    async def _get_recent_alerts_for_lead(self, lead_id: str) -> List[PropertyAlert]:
        """Get recent alerts for a specific lead."""
        # In production, query database for recent alerts
        return []


# Global service instance
_property_alert_system = None


def get_property_alert_system() -> PropertyAlertSystem:
    """Get singleton instance of Property Alert System."""
    global _property_alert_system
    if _property_alert_system is None:
        _property_alert_system = PropertyAlertSystem()
    return _property_alert_system
