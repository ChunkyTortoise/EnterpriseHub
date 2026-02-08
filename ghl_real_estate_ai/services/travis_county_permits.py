"""
Travis County Permit Data Integration
====================================

Real permit data integration for Market Sentiment Radar.
Replaces mock permit data with actual Travis County permit information.

Author: Data Integration Phase - January 2026
"""

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import aiohttp

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.market_sentiment_radar import (
    DataSourceInterface,
    SentimentSignal,
    SentimentTriggerType,
)

logger = get_logger(__name__)


@dataclass
class PermitData:
    """Structured permit data from Travis County."""

    permit_id: str
    permit_type: str
    status: str
    description: str
    address: str
    zip_code: Optional[str]
    filing_date: datetime
    approval_date: Optional[datetime]
    value: Optional[float]
    project_type: str


class TravisCountyPermitService(DataSourceInterface):
    """
    Travis County permit data integration.

    Provides real permit data for market sentiment analysis including:
    - Building permits and their status
    - Zoning applications and decisions
    - Development projects and approvals
    - Infrastructure projects affecting neighborhoods
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.session = None

        # Travis County data sources
        self.permit_api_base = "https://data.austintexas.gov/resource/3syk-w9eu.json"
        self.development_api_base = "https://data.austintexas.gov/resource/74ds-b4fc.json"

        # Cache TTL
        self.cache_ttl = 3600  # 1 hour for permit data

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def fetch_sentiment_data(self, location: str, timeframe_days: int = 30) -> List[SentimentSignal]:
        """Fetch permit-based sentiment signals for a location."""

        signals = []

        try:
            # Extract ZIP code from location
            zip_code = self._extract_zip_code(location)
            if not zip_code:
                logger.warning(f"Could not extract ZIP code from location: {location}")
                return signals

            # Get permit data for the area
            permits = await self._get_permits_for_area(zip_code, timeframe_days)

            # Analyze permit patterns for sentiment signals
            signals.extend(await self._analyze_building_permits(permits, location))
            signals.extend(await self._analyze_development_pressure(permits, location))
            signals.extend(await self._analyze_infrastructure_projects(permits, location))

            logger.info(f"Generated {len(signals)} permit-based sentiment signals for {location}")

        except Exception as e:
            logger.error(f"Error fetching permit data for {location}: {e}")

        return signals

    async def _get_permits_for_area(self, zip_code: str, timeframe_days: int) -> List[PermitData]:
        """Get permit data for a specific ZIP code area."""

        cache_key = f"permits:{zip_code}:{timeframe_days}"
        cached_permits = await self.cache.get(cache_key)

        if cached_permits:
            return [self._dict_to_permit(p) for p in json.loads(cached_permits)]

        permits = []
        cutoff_date = datetime.now() - timedelta(days=timeframe_days)

        try:
            session = await self.get_session()

            # Query building permits
            building_permits = await self._fetch_building_permits(session, zip_code, cutoff_date)
            permits.extend(building_permits)

            # Query development/zoning permits
            development_permits = await self._fetch_development_permits(session, zip_code, cutoff_date)
            permits.extend(development_permits)

            # Cache results
            permit_dicts = [self._permit_to_dict(p) for p in permits]
            await self.cache.set(cache_key, json.dumps(permit_dicts, default=str), expire=self.cache_ttl)

        except Exception as e:
            logger.error(f"Error fetching permits for {zip_code}: {e}")

        return permits

    async def _fetch_building_permits(
        self, session: aiohttp.ClientSession, zip_code: str, cutoff_date: datetime
    ) -> List[PermitData]:
        """Fetch building permits from Austin/Travis County data portal."""

        permits = []

        try:
            # Format date for API query
            date_filter = cutoff_date.strftime("%Y-%m-%dT00:00:00.000")

            # Build API query for permits in ZIP code
            query_params = {
                "$where": f"issued_date >= '{date_filter}' AND zip_code = '{zip_code}'",
                "$limit": 1000,
                "$order": "issued_date DESC",
            }

            url = f"{self.permit_api_base}?{self._build_query_string(query_params)}"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    for item in data:
                        try:
                            permit = self._parse_building_permit(item)
                            if permit:
                                permits.append(permit)
                        except Exception as e:
                            logger.warning(f"Error parsing building permit: {e}")

        except Exception as e:
            logger.error(f"Error fetching building permits: {e}")

        return permits

    async def _fetch_development_permits(
        self, session: aiohttp.ClientSession, zip_code: str, cutoff_date: datetime
    ) -> List[PermitData]:
        """Fetch development/zoning permits."""

        permits = []

        try:
            # Format date for API query
            date_filter = cutoff_date.strftime("%Y-%m-%dT00:00:00.000")

            # Build API query
            query_params = {
                "$where": f"case_created >= '{date_filter}' AND zip_code = '{zip_code}'",
                "$limit": 500,
                "$order": "case_created DESC",
            }

            url = f"{self.development_api_base}?{self._build_query_string(query_params)}"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    for item in data:
                        try:
                            permit = self._parse_development_permit(item)
                            if permit:
                                permits.append(permit)
                        except Exception as e:
                            logger.warning(f"Error parsing development permit: {e}")

        except Exception as e:
            logger.error(f"Error fetching development permits: {e}")

        return permits

    def _parse_building_permit(self, data: Dict[str, Any]) -> Optional[PermitData]:
        """Parse building permit from API data."""

        try:
            permit_id = data.get("permit_number", "")
            permit_type = data.get("permit_type_desc", "building")
            status = data.get("status_current", "unknown")
            description = data.get("description", "")
            address = data.get("original_address1", "")
            zip_code = data.get("zip_code", "")

            # Parse dates
            filing_date = self._parse_date(data.get("issued_date"))
            approval_date = self._parse_date(data.get("final_date"))

            # Parse value
            value_str = data.get("total_valuation", "0")
            value = float(value_str) if value_str and value_str != "0" else None

            # Classify project type
            project_type = self._classify_project_type(permit_type, description)

            return PermitData(
                permit_id=permit_id,
                permit_type=permit_type,
                status=status,
                description=description,
                address=address,
                zip_code=zip_code,
                filing_date=filing_date,
                approval_date=approval_date,
                value=value,
                project_type=project_type,
            )

        except Exception as e:
            logger.warning(f"Error parsing building permit data: {e}")
            return None

    def _parse_development_permit(self, data: Dict[str, Any]) -> Optional[PermitData]:
        """Parse development/zoning permit from API data."""

        try:
            permit_id = data.get("case_number", "")
            permit_type = data.get("case_type", "zoning")
            status = data.get("case_status", "unknown")
            description = data.get("case_description", "")
            address = data.get("case_address", "")
            zip_code = data.get("zip_code", "")

            # Parse dates
            filing_date = self._parse_date(data.get("case_created"))
            approval_date = self._parse_date(data.get("case_closed"))

            # Development permits typically don't have direct values
            value = None

            project_type = "development"

            return PermitData(
                permit_id=permit_id,
                permit_type=permit_type,
                status=status,
                description=description,
                address=address,
                zip_code=zip_code,
                filing_date=filing_date,
                approval_date=approval_date,
                value=value,
                project_type=project_type,
            )

        except Exception as e:
            logger.warning(f"Error parsing development permit data: {e}")
            return None

    async def _analyze_building_permits(self, permits: List[PermitData], location: str) -> List[SentimentSignal]:
        """Analyze building permit patterns for sentiment signals."""

        signals = []

        # Count permits by type and status
        total_permits = len(permits)
        denied_permits = [p for p in permits if "denied" in p.status.lower() or "rejected" in p.status.lower()]
        delayed_permits = [p for p in permits if "review" in p.status.lower() or "pending" in p.status.lower()]

        # High denial rate indicates regulatory resistance
        if total_permits > 0:
            denial_rate = len(denied_permits) / total_permits

            if denial_rate > 0.3:  # 30%+ denial rate
                signals.append(
                    SentimentSignal(
                        source="travis_county_permits",
                        signal_type=SentimentTriggerType.PERMIT_DISRUPTION,
                        location=location,
                        sentiment_score=-60 - (denial_rate * 40),  # -60 to -100
                        confidence=0.85,
                        raw_content=f"{denial_rate:.1%} permit denial rate ({len(denied_permits)} of {total_permits} permits denied)",
                        detected_at=datetime.now(),
                        urgency_multiplier=2.5,
                    )
                )

        # High number of multifamily permits suggests development pressure
        multifamily_permits = [
            p for p in permits if "multi" in p.description.lower() or "apartment" in p.description.lower()
        ]

        if len(multifamily_permits) > 5:  # 5+ multifamily permits in timeframe
            signals.append(
                SentimentSignal(
                    source="travis_county_permits",
                    signal_type=SentimentTriggerType.NEIGHBORHOOD_DECLINE,
                    location=location,
                    sentiment_score=-45,
                    confidence=0.75,
                    raw_content=f"{len(multifamily_permits)} multifamily development permits filed - neighborhood character changing",
                    detected_at=datetime.now(),
                    urgency_multiplier=1.8,
                )
            )

        return signals

    async def _analyze_development_pressure(self, permits: List[PermitData], location: str) -> List[SentimentSignal]:
        """Analyze development pressure indicators."""

        signals = []

        # Look for large commercial/retail developments
        commercial_permits = [
            p
            for p in permits
            if any(
                term in p.description.lower() for term in ["commercial", "retail", "shopping", "store", "restaurant"]
            )
        ]

        if len(commercial_permits) > 3:  # 3+ commercial permits
            signals.append(
                SentimentSignal(
                    source="travis_county_permits",
                    signal_type=SentimentTriggerType.INFRASTRUCTURE_CONCERN,
                    location=location,
                    sentiment_score=-30,
                    confidence=0.70,
                    raw_content=f"{len(commercial_permits)} commercial development permits - increased traffic and congestion expected",
                    detected_at=datetime.now(),
                    urgency_multiplier=1.5,
                )
            )

        # Look for zoning variance requests (often contentious)
        variance_permits = [
            p
            for p in permits
            if any(term in p.description.lower() for term in ["variance", "zoning", "setback", "height"])
        ]

        if len(variance_permits) > 2:  # 2+ variance requests
            signals.append(
                SentimentSignal(
                    source="travis_county_permits",
                    signal_type=SentimentTriggerType.PERMIT_DISRUPTION,
                    location=location,
                    sentiment_score=-35,
                    confidence=0.80,
                    raw_content=f"{len(variance_permits)} zoning variance requests - neighborhood opposition and delays likely",
                    detected_at=datetime.now(),
                    urgency_multiplier=2.0,
                )
            )

        return signals

    async def _analyze_infrastructure_projects(self, permits: List[PermitData], location: str) -> List[SentimentSignal]:
        """Analyze infrastructure project impacts."""

        signals = []

        # Look for utility and infrastructure permits
        infrastructure_permits = [
            p
            for p in permits
            if any(term in p.description.lower() for term in ["water", "sewer", "utility", "road", "street", "traffic"])
        ]

        if len(infrastructure_permits) > 5:  # 5+ infrastructure permits
            # Could be positive (improvements) or negative (disruption)
            # Err on negative side for sentiment analysis
            signals.append(
                SentimentSignal(
                    source="travis_county_permits",
                    signal_type=SentimentTriggerType.INFRASTRUCTURE_CONCERN,
                    location=location,
                    sentiment_score=-25,
                    confidence=0.65,
                    raw_content=f"{len(infrastructure_permits)} infrastructure permits filed - construction disruption expected",
                    detected_at=datetime.now(),
                    urgency_multiplier=1.3,
                )
            )

        return signals

    def _extract_zip_code(self, location: str) -> Optional[str]:
        """Extract ZIP code from location string."""

        # Look for 5-digit ZIP codes starting with 78 (Austin area)
        zip_match = re.search(r"\b(78\d{3})\b", location)
        if zip_match:
            return zip_match.group(1)

        # Handle common Austin area names
        area_to_zip = {
            "downtown": "78701",
            "west lake hills": "78746",
            "cedar park": "78613",
            "round rock": "78664",
            "pflugerville": "78660",
            "bee cave": "78738",
            "lakeway": "78734",
        }

        location_lower = location.lower()
        for area, zip_code in area_to_zip.items():
            if area in location_lower:
                return zip_code

        return None

    def _classify_project_type(self, permit_type: str, description: str) -> str:
        """Classify permit into project type categories."""

        combined = f"{permit_type} {description}".lower()

        if any(term in combined for term in ["single", "family", "residence", "house"]):
            return "single_family"
        elif any(term in combined for term in ["multi", "apartment", "condo", "duplex"]):
            return "multifamily"
        elif any(term in combined for term in ["commercial", "retail", "office", "business"]):
            return "commercial"
        elif any(term in combined for term in ["utility", "water", "sewer", "electric"]):
            return "utility"
        elif any(term in combined for term in ["road", "street", "sidewalk", "traffic"]):
            return "transportation"
        else:
            return "other"

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string from API."""

        if not date_str:
            return None

        try:
            # Try common formats
            formats = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]

            for fmt in formats:
                try:
                    return datetime.strptime(date_str[: len(fmt) - 2], fmt[:-2] if fmt.endswith(".%f") else fmt)
                except ValueError:
                    continue

            # Try ISO format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return None

    def _build_query_string(self, params: Dict[str, str]) -> str:
        """Build URL query string from parameters."""

        parts = []
        for key, value in params.items():
            parts.append(f"{quote(key)}={quote(str(value))}")
        return "&".join(parts)

    def _permit_to_dict(self, permit: PermitData) -> Dict[str, Any]:
        """Convert permit to dictionary for caching."""

        return {
            "permit_id": permit.permit_id,
            "permit_type": permit.permit_type,
            "status": permit.status,
            "description": permit.description,
            "address": permit.address,
            "zip_code": permit.zip_code,
            "filing_date": permit.filing_date.isoformat() if permit.filing_date else None,
            "approval_date": permit.approval_date.isoformat() if permit.approval_date else None,
            "value": permit.value,
            "project_type": permit.project_type,
        }

    def _dict_to_permit(self, data: Dict[str, Any]) -> PermitData:
        """Convert dictionary back to permit object."""

        return PermitData(
            permit_id=data["permit_id"],
            permit_type=data["permit_type"],
            status=data["status"],
            description=data["description"],
            address=data["address"],
            zip_code=data["zip_code"],
            filing_date=self._parse_date(data["filing_date"]),
            approval_date=self._parse_date(data["approval_date"]),
            value=data["value"],
            project_type=data["project_type"],
        )

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()


# Singleton instance
_travis_permit_service = None


async def get_travis_county_permit_service() -> TravisCountyPermitService:
    """Get singleton Travis County permit service."""
    global _travis_permit_service
    if _travis_permit_service is None:
        _travis_permit_service = TravisCountyPermitService()
    return _travis_permit_service
