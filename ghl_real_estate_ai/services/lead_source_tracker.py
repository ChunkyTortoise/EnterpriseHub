"""
Lead Source Tracker - Comprehensive Attribution System for Jorge's Lead Bot.

Detects, tracks, and analyzes lead origination sources across all channels:
- UTM parameter parsing for digital marketing campaigns
- Referrer detection for organic and social traffic
- Lead source classification and performance tracking
- ROI calculation by marketing channel
- Integration with GHL custom fields for persistence

Key Features:
- Support for all major lead sources (Zillow, Facebook, Google, referrals)
- Historical performance tracking and trend analysis
- Automated alerts for source performance changes
- Custom field updates for source tracking in GHL
"""

import re
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass, asdict
from enum import Enum

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.services.cache_service import CacheService

logger = get_logger(__name__)


class LeadSource(str, Enum):
    """Standardized lead source classifications."""

    # Digital Marketing Sources
    FACEBOOK_ORGANIC = "facebook_organic"
    FACEBOOK_ADS = "facebook_ads"
    GOOGLE_ORGANIC = "google_organic"
    GOOGLE_ADS = "google_ads"
    INSTAGRAM_ORGANIC = "instagram_organic"
    INSTAGRAM_ADS = "instagram_ads"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"

    # Real Estate Platforms
    ZILLOW = "zillow"
    REALTOR_COM = "realtor_com"
    TRULIA = "trulia"
    REDFIN = "redfin"
    HOMES_COM = "homes_com"
    MLS = "mls"

    # Referral Sources
    AGENT_REFERRAL = "agent_referral"
    CLIENT_REFERRAL = "client_referral"
    VENDOR_REFERRAL = "vendor_referral"

    # Direct Sources
    DIRECT = "direct"
    WEBSITE = "website"
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    TEXT_MESSAGE = "text_message"

    # Traditional Marketing
    PRINT_AD = "print_ad"
    RADIO = "radio"
    TV = "tv"
    BILLBOARD = "billboard"
    DIRECT_MAIL = "direct_mail"

    # Events & Networking
    OPEN_HOUSE = "open_house"
    NETWORKING_EVENT = "networking_event"
    TRADE_SHOW = "trade_show"

    # Other
    UNKNOWN = "unknown"
    OTHER = "other"


class SourceQuality(str, Enum):
    """Lead source quality classifications."""

    PREMIUM = "premium"      # High conversion, high value
    STANDARD = "standard"    # Average performance
    BUDGET = "budget"        # Low cost, volume focused
    EXPERIMENTAL = "experimental"  # Testing phase


@dataclass
class SourceAttribution:
    """Complete source attribution data for a lead."""

    # Primary Source Information
    source: LeadSource
    source_detail: Optional[str] = None  # e.g., specific campaign name
    medium: Optional[str] = None         # e.g., cpc, organic, referral
    campaign: Optional[str] = None       # Campaign identifier

    # UTM Parameters
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None

    # Technical Data
    referrer: Optional[str] = None
    landing_page: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    # Attribution Metadata
    quality_score: float = 0.0
    source_quality: SourceQuality = SourceQuality.STANDARD
    confidence_score: float = 1.0  # How confident we are in this attribution

    # Timestamps
    first_touch: Optional[datetime] = None
    last_touch: Optional[datetime] = None

    # Performance Data (will be populated over time)
    historical_conversion_rate: float = 0.0
    historical_avg_deal_size: float = 0.0
    historical_time_to_close: Optional[int] = None  # days


@dataclass
class SourcePerformance:
    """Performance metrics for a lead source."""

    source: LeadSource
    period_start: datetime
    period_end: datetime

    # Volume Metrics
    total_leads: int = 0
    qualified_leads: int = 0
    hot_leads: int = 0

    # Conversion Metrics
    conversion_rate: float = 0.0
    qualification_rate: float = 0.0
    hot_lead_rate: float = 0.0

    # Financial Metrics
    total_revenue: float = 0.0
    avg_deal_size: float = 0.0
    cost_per_lead: float = 0.0
    cost_per_qualified_lead: float = 0.0
    roi: float = 0.0

    # Timing Metrics
    avg_response_time: Optional[float] = None  # minutes
    avg_time_to_qualify: Optional[float] = None  # hours
    avg_time_to_close: Optional[float] = None  # days

    # Quality Metrics
    avg_lead_score: float = 0.0
    avg_budget: float = 0.0
    urgent_timeline_percentage: float = 0.0


class LeadSourceTracker:
    """
    Comprehensive lead source attribution and tracking system.

    Analyzes incoming leads to determine their origin, tracks performance
    over time, and provides actionable insights for marketing optimization.
    """

    def __init__(self):
        self.cache = CacheService()

        # Source patterns for detection
        self.source_patterns = self._build_source_patterns()

        # Default quality scores by source
        self.source_quality_scores = self._build_quality_scores()

        logger.info("LeadSourceTracker initialized with comprehensive attribution system")

    def _build_source_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for source detection."""
        return {
            LeadSource.FACEBOOK_ORGANIC: [
                r"facebook\.com",
                r"fb\.com",
                r"m\.facebook\.com"
            ],
            LeadSource.FACEBOOK_ADS: [
                r"facebook.*ads",
                r"fb.*ads",
                r"utm_source=facebook.*utm_medium=cpc"
            ],
            LeadSource.GOOGLE_ORGANIC: [
                r"google\.com.*q=",
                r"utm_source=google.*utm_medium=organic"
            ],
            LeadSource.GOOGLE_ADS: [
                r"googleadservices\.com",
                r"utm_source=google.*utm_medium=cpc",
                r"gclid="
            ],
            LeadSource.INSTAGRAM_ORGANIC: [
                r"instagram\.com",
                r"ig\.com"
            ],
            LeadSource.INSTAGRAM_ADS: [
                r"instagram.*ads",
                r"ig.*ads"
            ],
            LeadSource.ZILLOW: [
                r"zillow\.com",
                r"utm_source=zillow"
            ],
            LeadSource.REALTOR_COM: [
                r"realtor\.com",
                r"utm_source=realtor"
            ],
            LeadSource.TRULIA: [
                r"trulia\.com",
                r"utm_source=trulia"
            ],
            LeadSource.REDFIN: [
                r"redfin\.com",
                r"utm_source=redfin"
            ],
            LeadSource.YOUTUBE: [
                r"youtube\.com",
                r"youtu\.be",
                r"utm_source=youtube"
            ],
            LeadSource.LINKEDIN: [
                r"linkedin\.com",
                r"utm_source=linkedin"
            ]
        }

    def _build_quality_scores(self) -> Dict[LeadSource, float]:
        """Build default quality scores for each source."""
        return {
            # Premium Sources (High conversion, high value)
            LeadSource.AGENT_REFERRAL: 9.5,
            LeadSource.CLIENT_REFERRAL: 9.0,
            LeadSource.DIRECT: 8.5,

            # Real Estate Platforms (Good targeting)
            LeadSource.ZILLOW: 7.8,
            LeadSource.REALTOR_COM: 7.5,
            LeadSource.TRULIA: 7.2,
            LeadSource.REDFIN: 7.0,

            # Paid Digital (Variable quality)
            LeadSource.GOOGLE_ADS: 6.8,
            LeadSource.FACEBOOK_ADS: 6.5,
            LeadSource.INSTAGRAM_ADS: 6.0,

            # Organic Digital (Lower intent)
            LeadSource.GOOGLE_ORGANIC: 5.8,
            LeadSource.FACEBOOK_ORGANIC: 5.0,
            LeadSource.INSTAGRAM_ORGANIC: 4.8,
            LeadSource.YOUTUBE: 4.5,

            # Traditional (Variable)
            LeadSource.PHONE_CALL: 7.0,
            LeadSource.WEBSITE: 6.0,
            LeadSource.EMAIL: 5.5,

            # Events (Good for relationship building)
            LeadSource.OPEN_HOUSE: 6.8,
            LeadSource.NETWORKING_EVENT: 6.5,

            # Default scores
            LeadSource.UNKNOWN: 3.0,
            LeadSource.OTHER: 4.0
        }

    async def analyze_lead_source(
        self,
        contact_data: Dict[str, Any],
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> SourceAttribution:
        """
        Analyze and determine the source attribution for a lead.

        Args:
            contact_data: GHL contact information
            webhook_data: Additional webhook metadata

        Returns:
            SourceAttribution with complete source analysis
        """
        try:
            logger.info(f"Analyzing source attribution for contact")

            attribution = SourceAttribution(
                source=LeadSource.UNKNOWN,
                first_touch=datetime.utcnow(),
                last_touch=datetime.utcnow()
            )

            # Extract available data
            referrer = self._extract_referrer(contact_data, webhook_data)
            utm_params = self._extract_utm_params(contact_data, webhook_data)
            landing_page = self._extract_landing_page(contact_data, webhook_data)
            custom_fields = contact_data.get("custom_fields", {})

            # Populate attribution data
            attribution.referrer = referrer
            attribution.landing_page = landing_page
            attribution.utm_source = utm_params.get("utm_source")
            attribution.utm_medium = utm_params.get("utm_medium")
            attribution.utm_campaign = utm_params.get("utm_campaign")
            attribution.utm_term = utm_params.get("utm_term")
            attribution.utm_content = utm_params.get("utm_content")

            # Determine primary source
            detected_source, confidence = await self._detect_primary_source(
                referrer, utm_params, landing_page, custom_fields
            )

            attribution.source = detected_source
            attribution.confidence_score = confidence

            # Set source details
            attribution.source_detail = self._extract_source_detail(
                detected_source, utm_params, referrer
            )
            attribution.medium = utm_params.get("utm_medium") or self._infer_medium(detected_source)
            attribution.campaign = utm_params.get("utm_campaign")

            # Calculate quality score
            attribution.quality_score = await self._calculate_quality_score(attribution)
            attribution.source_quality = self._classify_source_quality(attribution.quality_score)

            # Load historical performance data
            await self._enrich_with_historical_data(attribution)

            logger.info(
                f"Source attribution completed: {attribution.source} "
                f"(confidence: {attribution.confidence_score:.2f}, "
                f"quality: {attribution.quality_score:.1f})"
            )

            return attribution

        except Exception as e:
            logger.error(f"Error analyzing lead source: {e}", exc_info=True)
            # Return basic attribution on error
            return SourceAttribution(
                source=LeadSource.UNKNOWN,
                confidence_score=0.0,
                first_touch=datetime.utcnow(),
                last_touch=datetime.utcnow()
            )

    def _extract_referrer(
        self,
        contact_data: Dict[str, Any],
        webhook_data: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Extract referrer information from available data."""
        # Check custom fields first
        custom_fields = contact_data.get("custom_fields", {})
        referrer = (
            custom_fields.get("referrer") or
            custom_fields.get("source_url") or
            custom_fields.get("lead_source_url")
        )

        if referrer:
            return referrer

        # Check webhook data
        if webhook_data:
            referrer = (
                webhook_data.get("referrer") or
                webhook_data.get("source") or
                webhook_data.get("original_referrer")
            )

        return referrer

    def _extract_utm_params(
        self,
        contact_data: Dict[str, Any],
        webhook_data: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Extract UTM parameters from contact data."""
        utm_params = {}
        custom_fields = contact_data.get("custom_fields", {})

        # Standard UTM parameter names
        utm_fields = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"]

        for field in utm_fields:
            value = (
                custom_fields.get(field) or
                custom_fields.get(field.upper()) or
                custom_fields.get(field.replace("utm_", ""))
            )
            if value:
                utm_params[field] = value

        # Also check webhook data
        if webhook_data:
            for field in utm_fields:
                if field not in utm_params:
                    value = webhook_data.get(field)
                    if value:
                        utm_params[field] = value

        # Parse from referrer URL if available
        referrer = self._extract_referrer(contact_data, webhook_data)
        if referrer and "?" in referrer:
            try:
                parsed_url = urlparse(referrer)
                query_params = parse_qs(parsed_url.query)

                for field in utm_fields:
                    if field not in utm_params and field in query_params:
                        utm_params[field] = query_params[field][0]
            except Exception:
                pass

        return utm_params

    def _extract_landing_page(
        self,
        contact_data: Dict[str, Any],
        webhook_data: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Extract landing page URL."""
        custom_fields = contact_data.get("custom_fields", {})

        landing_page = (
            custom_fields.get("landing_page") or
            custom_fields.get("original_url") or
            custom_fields.get("source_page")
        )

        if not landing_page and webhook_data:
            landing_page = webhook_data.get("landing_page")

        return landing_page

    async def _detect_primary_source(
        self,
        referrer: Optional[str],
        utm_params: Dict[str, str],
        landing_page: Optional[str],
        custom_fields: Dict[str, Any]
    ) -> Tuple[LeadSource, float]:
        """
        Detect the primary lead source with confidence scoring.

        Returns:
            Tuple of (detected_source, confidence_score)
        """
        confidence_scores = {}

        # Check for explicit source in custom fields
        explicit_source = (
            custom_fields.get("lead_source") or
            custom_fields.get("source") or
            custom_fields.get("original_source")
        )

        if explicit_source:
            mapped_source = self._map_explicit_source(explicit_source)
            if mapped_source != LeadSource.UNKNOWN:
                confidence_scores[mapped_source] = 0.95

        # UTM source analysis (high confidence)
        utm_source = utm_params.get("utm_source", "").lower()
        utm_medium = utm_params.get("utm_medium", "").lower()

        if utm_source:
            mapped_source = self._map_utm_source(utm_source, utm_medium)
            if mapped_source != LeadSource.UNKNOWN:
                confidence_scores[mapped_source] = 0.9

        # Referrer analysis (medium confidence)
        if referrer:
            detected_sources = self._analyze_referrer(referrer)
            for source, score in detected_sources.items():
                confidence_scores[source] = max(
                    confidence_scores.get(source, 0),
                    score * 0.8  # Referrer gets lower base confidence
                )

        # Landing page analysis (low confidence)
        if landing_page:
            detected_sources = self._analyze_landing_page(landing_page)
            for source, score in detected_sources.items():
                confidence_scores[source] = max(
                    confidence_scores.get(source, 0),
                    score * 0.6  # Landing page gets lowest confidence
                )

        # Return highest confidence source
        if confidence_scores:
            best_source = max(confidence_scores.items(), key=lambda x: x[1])
            return best_source[0], best_source[1]

        return LeadSource.UNKNOWN, 0.0

    def _map_explicit_source(self, source: str) -> LeadSource:
        """Map explicit source strings to LeadSource enum."""
        source_lower = source.lower()

        mapping = {
            "zillow": LeadSource.ZILLOW,
            "realtor.com": LeadSource.REALTOR_COM,
            "trulia": LeadSource.TRULIA,
            "redfin": LeadSource.REDFIN,
            "facebook": LeadSource.FACEBOOK_ORGANIC,
            "google": LeadSource.GOOGLE_ORGANIC,
            "instagram": LeadSource.INSTAGRAM_ORGANIC,
            "referral": LeadSource.AGENT_REFERRAL,
            "direct": LeadSource.DIRECT,
            "website": LeadSource.WEBSITE,
            "phone": LeadSource.PHONE_CALL,
            "email": LeadSource.EMAIL,
        }

        for key, value in mapping.items():
            if key in source_lower:
                return value

        return LeadSource.UNKNOWN

    def _map_utm_source(self, utm_source: str, utm_medium: str = "") -> LeadSource:
        """Map UTM source to LeadSource enum."""
        source_mapping = {
            "facebook": LeadSource.FACEBOOK_ADS if "cpc" in utm_medium or "paid" in utm_medium else LeadSource.FACEBOOK_ORGANIC,
            "google": LeadSource.GOOGLE_ADS if "cpc" in utm_medium or "paid" in utm_medium else LeadSource.GOOGLE_ORGANIC,
            "instagram": LeadSource.INSTAGRAM_ADS if "cpc" in utm_medium or "paid" in utm_medium else LeadSource.INSTAGRAM_ORGANIC,
            "zillow": LeadSource.ZILLOW,
            "realtor": LeadSource.REALTOR_COM,
            "trulia": LeadSource.TRULIA,
            "redfin": LeadSource.REDFIN,
            "youtube": LeadSource.YOUTUBE,
            "linkedin": LeadSource.LINKEDIN,
        }

        for key, value in source_mapping.items():
            if key in utm_source:
                return value

        return LeadSource.UNKNOWN

    def _analyze_referrer(self, referrer: str) -> Dict[LeadSource, float]:
        """Analyze referrer URL and return possible sources with confidence scores."""
        detected = {}
        referrer_lower = referrer.lower()

        for source, patterns in self.source_patterns.items():
            for pattern in patterns:
                if re.search(pattern, referrer_lower):
                    detected[source] = 0.8
                    break

        return detected

    def _analyze_landing_page(self, landing_page: str) -> Dict[LeadSource, float]:
        """Analyze landing page URL for source hints."""
        detected = {}
        page_lower = landing_page.lower()

        # Look for campaign indicators in the URL
        if "utm_source=" in page_lower:
            # Extract utm_source from URL
            try:
                parsed = urlparse(landing_page)
                params = parse_qs(parsed.query)
                if "utm_source" in params:
                    utm_source = params["utm_source"][0].lower()
                    utm_medium = params.get("utm_medium", [""])[0].lower()
                    mapped_source = self._map_utm_source(utm_source, utm_medium)
                    if mapped_source != LeadSource.UNKNOWN:
                        detected[mapped_source] = 0.7
            except Exception:
                pass

        return detected

    def _extract_source_detail(
        self,
        source: LeadSource,
        utm_params: Dict[str, str],
        referrer: Optional[str]
    ) -> Optional[str]:
        """Extract detailed source information."""
        campaign = utm_params.get("utm_campaign")
        if campaign:
            return campaign

        content = utm_params.get("utm_content")
        if content:
            return content

        # Extract from referrer for some sources
        if referrer and source in [LeadSource.FACEBOOK_ADS, LeadSource.GOOGLE_ADS]:
            try:
                parsed = urlparse(referrer)
                if parsed.netloc:
                    return f"{source.value}_from_{parsed.netloc}"
            except Exception:
                pass

        return None

    def _infer_medium(self, source: LeadSource) -> Optional[str]:
        """Infer medium from source type."""
        medium_mapping = {
            LeadSource.FACEBOOK_ADS: "cpc",
            LeadSource.GOOGLE_ADS: "cpc",
            LeadSource.INSTAGRAM_ADS: "cpc",
            LeadSource.FACEBOOK_ORGANIC: "organic",
            LeadSource.GOOGLE_ORGANIC: "organic",
            LeadSource.INSTAGRAM_ORGANIC: "organic",
            LeadSource.AGENT_REFERRAL: "referral",
            LeadSource.CLIENT_REFERRAL: "referral",
            LeadSource.DIRECT: "direct",
            LeadSource.PHONE_CALL: "phone",
            LeadSource.EMAIL: "email",
        }

        return medium_mapping.get(source)

    async def _calculate_quality_score(self, attribution: SourceAttribution) -> float:
        """Calculate quality score for the attributed source."""
        base_score = self.source_quality_scores.get(attribution.source, 5.0)

        # Adjust based on confidence
        confidence_factor = attribution.confidence_score

        # Adjust based on UTM parameters (indicates organized campaign)
        utm_factor = 1.0
        if attribution.utm_campaign:
            utm_factor += 0.5
        if attribution.utm_content:
            utm_factor += 0.2

        # Adjust based on historical performance (if available)
        historical_factor = 1.0
        if attribution.historical_conversion_rate > 0:
            # Scale based on conversion rate (assume 10% is average)
            historical_factor = max(0.5, min(2.0, attribution.historical_conversion_rate / 0.1))

        final_score = base_score * confidence_factor * utm_factor * historical_factor
        return min(10.0, max(0.0, final_score))

    def _classify_source_quality(self, quality_score: float) -> SourceQuality:
        """Classify source quality based on score."""
        if quality_score >= 8.0:
            return SourceQuality.PREMIUM
        elif quality_score >= 6.0:
            return SourceQuality.STANDARD
        elif quality_score >= 4.0:
            return SourceQuality.BUDGET
        else:
            return SourceQuality.EXPERIMENTAL

    async def _enrich_with_historical_data(self, attribution: SourceAttribution) -> None:
        """Enrich attribution with historical performance data."""
        try:
            cache_key = f"source_performance:{attribution.source.value}"
            historical_data = await self.cache.get(cache_key)

            if historical_data:
                attribution.historical_conversion_rate = historical_data.get("conversion_rate", 0.0)
                attribution.historical_avg_deal_size = historical_data.get("avg_deal_size", 0.0)
                attribution.historical_time_to_close = historical_data.get("avg_time_to_close")
        except Exception as e:
            logger.warning(f"Could not load historical data for {attribution.source}: {e}")

    async def track_source_performance(
        self,
        source: LeadSource,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track performance events for a lead source.

        Args:
            source: The lead source
            event_type: Type of event (e.g., 'lead_created', 'lead_qualified', 'deal_closed')
            metadata: Additional event data
        """
        try:
            # Store individual event for detailed analysis
            event_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "source": source.value,
                "event_type": event_type,
                "metadata": metadata or {}
            }

            cache_key = f"source_events:{source.value}:{datetime.utcnow().strftime('%Y-%m-%d')}"

            # Get existing events for today
            existing_events = await self.cache.get(cache_key) or []
            existing_events.append(event_data)

            # Store updated events (24-hour TTL)
            await self.cache.set(cache_key, existing_events, ttl=86400)

            # Update aggregated performance metrics
            await self._update_performance_metrics(source, event_type, metadata)

            logger.debug(f"Tracked {event_type} event for source {source.value}")

        except Exception as e:
            logger.error(f"Error tracking source performance: {e}", exc_info=True)

    async def _update_performance_metrics(
        self,
        source: LeadSource,
        event_type: str,
        metadata: Optional[Dict[str, Any]]
    ) -> None:
        """Update aggregated performance metrics for a source."""
        cache_key = f"source_performance:{source.value}"

        # Get current metrics
        current_metrics = await self.cache.get(cache_key) or {
            "total_leads": 0,
            "qualified_leads": 0,
            "hot_leads": 0,
            "closed_deals": 0,
            "total_revenue": 0.0,
            "total_cost": 0.0,
            "response_times": [],
            "qualify_times": [],
            "close_times": [],
            "lead_scores": [],
            "budgets": [],
            "last_updated": datetime.utcnow().isoformat()
        }

        # Update based on event type
        if event_type == "lead_created":
            current_metrics["total_leads"] += 1

            # Track cost if provided
            if metadata and "cost" in metadata:
                current_metrics["total_cost"] += metadata["cost"]

        elif event_type == "lead_qualified":
            current_metrics["qualified_leads"] += 1

            # Track qualification time
            if metadata and "qualify_time_hours" in metadata:
                current_metrics["qualify_times"].append(metadata["qualify_time_hours"])

        elif event_type == "hot_lead":
            current_metrics["hot_leads"] += 1

        elif event_type == "deal_closed":
            current_metrics["closed_deals"] += 1

            # Track revenue and close time
            if metadata:
                if "deal_value" in metadata:
                    current_metrics["total_revenue"] += metadata["deal_value"]
                if "close_time_days" in metadata:
                    current_metrics["close_times"].append(metadata["close_time_days"])

        elif event_type == "lead_scored":
            if metadata and "score" in metadata:
                current_metrics["lead_scores"].append(metadata["score"])

        elif event_type == "budget_identified":
            if metadata and "budget" in metadata:
                current_metrics["budgets"].append(metadata["budget"])

        # Calculate derived metrics
        total_leads = current_metrics["total_leads"]
        if total_leads > 0:
            current_metrics["conversion_rate"] = current_metrics["closed_deals"] / total_leads
            current_metrics["qualification_rate"] = current_metrics["qualified_leads"] / total_leads
            current_metrics["hot_lead_rate"] = current_metrics["hot_leads"] / total_leads

        if current_metrics["closed_deals"] > 0:
            current_metrics["avg_deal_size"] = current_metrics["total_revenue"] / current_metrics["closed_deals"]

        # Calculate averages
        if current_metrics["qualify_times"]:
            current_metrics["avg_time_to_qualify"] = sum(current_metrics["qualify_times"]) / len(current_metrics["qualify_times"])

        if current_metrics["close_times"]:
            current_metrics["avg_time_to_close"] = sum(current_metrics["close_times"]) / len(current_metrics["close_times"])

        if current_metrics["lead_scores"]:
            current_metrics["avg_lead_score"] = sum(current_metrics["lead_scores"]) / len(current_metrics["lead_scores"])

        if current_metrics["budgets"]:
            current_metrics["avg_budget"] = sum(current_metrics["budgets"]) / len(current_metrics["budgets"])

        # Calculate ROI
        if current_metrics["total_cost"] > 0:
            current_metrics["roi"] = (current_metrics["total_revenue"] - current_metrics["total_cost"]) / current_metrics["total_cost"]
            current_metrics["cost_per_lead"] = current_metrics["total_cost"] / total_leads if total_leads > 0 else 0
            current_metrics["cost_per_qualified_lead"] = current_metrics["total_cost"] / current_metrics["qualified_leads"] if current_metrics["qualified_leads"] > 0 else 0

        current_metrics["last_updated"] = datetime.utcnow().isoformat()

        # Store updated metrics (7-day TTL)
        await self.cache.set(cache_key, current_metrics, ttl=604800)

    async def get_source_performance(
        self,
        source: LeadSource,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[SourcePerformance]:
        """
        Get performance metrics for a lead source.

        Args:
            source: The lead source to analyze
            start_date: Start of analysis period (defaults to 30 days ago)
            end_date: End of analysis period (defaults to now)

        Returns:
            SourcePerformance object or None if no data available
        """
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Get aggregated metrics
            cache_key = f"source_performance:{source.value}"
            metrics = await self.cache.get(cache_key)

            if not metrics:
                return None

            # Create performance object
            performance = SourcePerformance(
                source=source,
                period_start=start_date,
                period_end=end_date,
                total_leads=metrics.get("total_leads", 0),
                qualified_leads=metrics.get("qualified_leads", 0),
                hot_leads=metrics.get("hot_leads", 0),
                conversion_rate=metrics.get("conversion_rate", 0.0),
                qualification_rate=metrics.get("qualification_rate", 0.0),
                hot_lead_rate=metrics.get("hot_lead_rate", 0.0),
                total_revenue=metrics.get("total_revenue", 0.0),
                avg_deal_size=metrics.get("avg_deal_size", 0.0),
                cost_per_lead=metrics.get("cost_per_lead", 0.0),
                cost_per_qualified_lead=metrics.get("cost_per_qualified_lead", 0.0),
                roi=metrics.get("roi", 0.0),
                avg_time_to_qualify=metrics.get("avg_time_to_qualify"),
                avg_time_to_close=metrics.get("avg_time_to_close"),
                avg_lead_score=metrics.get("avg_lead_score", 0.0),
                avg_budget=metrics.get("avg_budget", 0.0)
            )

            return performance

        except Exception as e:
            logger.error(f"Error getting source performance for {source}: {e}", exc_info=True)
            return None

    async def get_all_source_performance(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_leads: int = 1
    ) -> List[SourcePerformance]:
        """
        Get performance metrics for all active lead sources.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            min_leads: Minimum leads required to include source

        Returns:
            List of SourcePerformance objects sorted by ROI
        """
        performances = []

        for source in LeadSource:
            performance = await self.get_source_performance(source, start_date, end_date)
            if performance and performance.total_leads >= min_leads:
                performances.append(performance)

        # Sort by ROI (descending)
        performances.sort(key=lambda p: p.roi, reverse=True)
        return performances

    async def get_source_recommendations(self) -> Dict[str, Any]:
        """
        Generate actionable recommendations for source optimization.

        Returns:
            Dictionary containing optimization recommendations
        """
        try:
            performances = await self.get_all_source_performance()

            if not performances:
                return {
                    "status": "insufficient_data",
                    "message": "Not enough data to generate recommendations",
                    "recommendations": []
                }

            recommendations = []

            # Find top performing sources
            top_performers = [p for p in performances[:3] if p.roi > 0]
            if top_performers:
                recommendations.append({
                    "type": "scale_up",
                    "priority": "high",
                    "title": "Scale Top Performing Sources",
                    "description": f"Increase investment in {', '.join([p.source.value for p in top_performers])}",
                    "sources": [p.source.value for p in top_performers],
                    "expected_impact": "Increase overall ROI by focusing on proven sources"
                })

            # Find underperforming sources
            poor_performers = [p for p in performances if p.roi < -0.2 and p.total_leads > 5]
            if poor_performers:
                recommendations.append({
                    "type": "optimize_or_pause",
                    "priority": "high",
                    "title": "Optimize or Pause Underperforming Sources",
                    "description": f"Review and optimize {', '.join([p.source.value for p in poor_performers])}",
                    "sources": [p.source.value for p in poor_performers],
                    "expected_impact": "Reduce wasted ad spend and improve overall ROI"
                })

            # Find high-quality, low-volume sources
            high_quality_low_volume = [
                p for p in performances
                if p.qualification_rate > 0.3 and p.total_leads < 10 and p.roi > 0
            ]
            if high_quality_low_volume:
                recommendations.append({
                    "type": "scale_quality",
                    "priority": "medium",
                    "title": "Scale High-Quality Sources",
                    "description": f"Increase volume from {', '.join([p.source.value for p in high_quality_low_volume])}",
                    "sources": [p.source.value for p in high_quality_low_volume],
                    "expected_impact": "Increase qualified lead volume with maintained quality"
                })

            # Identify attribution gaps
            unknown_performance = next((p for p in performances if p.source == LeadSource.UNKNOWN), None)
            if unknown_performance and unknown_performance.total_leads > 5:
                recommendations.append({
                    "type": "improve_tracking",
                    "priority": "medium",
                    "title": "Improve Source Tracking",
                    "description": f"{unknown_performance.total_leads} leads have unknown source",
                    "expected_impact": "Better attribution enables more informed optimization decisions"
                })

            return {
                "status": "success",
                "generated_at": datetime.utcnow().isoformat(),
                "total_sources_analyzed": len(performances),
                "recommendations": recommendations,
                "top_performers": [
                    {
                        "source": p.source.value,
                        "roi": round(p.roi * 100, 1),
                        "total_leads": p.total_leads,
                        "conversion_rate": round(p.conversion_rate * 100, 1)
                    }
                    for p in performances[:5]
                ]
            }

        except Exception as e:
            logger.error(f"Error generating source recommendations: {e}", exc_info=True)
            return {
                "status": "error",
                "message": "Failed to generate recommendations",
                "recommendations": []
            }

    async def update_ghl_custom_fields(
        self,
        contact_id: str,
        attribution: SourceAttribution,
        ghl_client
    ) -> bool:
        """
        Update GHL custom fields with source attribution data.

        Args:
            contact_id: GHL contact ID
            attribution: Source attribution data
            ghl_client: GHL client instance

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare custom field updates
            custom_fields = {}

            # Core attribution fields
            if hasattr(settings, 'custom_field_lead_source') and settings.custom_field_lead_source:
                custom_fields[settings.custom_field_lead_source] = attribution.source.value

            # Additional fields (check if configured)
            field_mappings = {
                'custom_field_source_medium': attribution.medium,
                'custom_field_source_campaign': attribution.campaign,
                'custom_field_source_quality': attribution.source_quality.value,
                'custom_field_source_confidence': f"{attribution.confidence_score:.2f}",
                'custom_field_utm_source': attribution.utm_source,
                'custom_field_utm_campaign': attribution.utm_campaign,
                'custom_field_referrer': attribution.referrer,
            }

            for setting_name, value in field_mappings.items():
                if hasattr(settings, setting_name):
                    field_name = getattr(settings, setting_name)
                    if field_name and value:
                        custom_fields[field_name] = str(value)

            # Update fields if any are configured
            if custom_fields:
                success = await ghl_client.update_contact_custom_fields(contact_id, custom_fields)

                if success:
                    logger.info(f"Updated source attribution fields for contact {contact_id}")
                    return True
                else:
                    logger.warning(f"Failed to update custom fields for contact {contact_id}")

            return True  # Success if no fields to update

        except Exception as e:
            logger.error(f"Error updating GHL custom fields: {e}", exc_info=True)
            return False

    def to_dict(self, attribution: SourceAttribution) -> Dict[str, Any]:
        """Convert SourceAttribution to dictionary for JSON serialization."""
        data = asdict(attribution)

        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat() if value else None

        return data

    def from_dict(self, data: Dict[str, Any]) -> SourceAttribution:
        """Create SourceAttribution from dictionary."""
        # Convert datetime strings back to datetime objects
        for key in ['first_touch', 'last_touch']:
            if key in data and data[key]:
                data[key] = datetime.fromisoformat(data[key])

        # Convert enums
        if 'source' in data:
            data['source'] = LeadSource(data['source'])
        if 'source_quality' in data:
            data['source_quality'] = SourceQuality(data['source_quality'])

        return SourceAttribution(**data)