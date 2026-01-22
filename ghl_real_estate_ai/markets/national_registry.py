"""
National Market Registry for Multi-Market Geographic Expansion

Extended registry for managing nationwide market configurations with specialized
corporate headquarters mapping and Fortune 500 relocation program management.
Builds on the existing MarketRegistry with national expansion capabilities.

Key Features:
- Corporate headquarters discovery and mapping
- Fortune 500 relocation program coordination
- Cross-market analytics and intelligence
- Dynamic market discovery for nationwide expansion
- Corporate client onboarding workflows

Author: EnterpriseHub AI
Created: 2026-01-18
"""

import os
import json
import yaml
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .registry import MarketRegistry, get_market_registry
from .base_market_service import BaseMarketService, ConfigDrivenMarketService
from .config_schemas import MarketConfig
from ..services.cache_service import get_cache_service
from ..ghl_utils.logger import get_logger

logger = get_logger(__name__)


class CorporatePartnerTier(Enum):
    """Corporate partnership tiers for Fortune 500 programs"""
    PLATINUM = "platinum"  # Major Fortune 100 with >10K employees
    GOLD = "gold"         # Fortune 500 with 5K-10K employees
    SILVER = "silver"     # Mid-market with 1K-5K employees
    BRONZE = "bronze"     # Growing companies with <1K employees


@dataclass
class CorporateHeadquarters:
    """Corporate headquarters information for relocation programs"""
    company_name: str
    ticker_symbol: Optional[str]
    industry: str
    headquarters_location: Tuple[float, float]  # lat, lng
    headquarters_city: str
    headquarters_state: str
    employee_count: int
    fortune_ranking: Optional[int]
    partnership_tier: CorporatePartnerTier
    preferred_markets: List[str]  # Market IDs where they have operations
    relocation_volume_annual: int  # Annual employee relocations
    average_relocation_budget: float
    contact_info: Dict[str, Any]
    program_start_date: datetime
    last_updated: datetime


@dataclass
class MarketExpansionTarget:
    """Target market for national expansion"""
    market_id: str
    market_name: str
    state: str
    region: str
    expansion_priority: int  # 1-10 (10 = highest priority)
    corporate_headquarters_count: int
    fortune_500_presence: int
    estimated_annual_revenue_potential: float
    market_entry_complexity: str  # low, medium, high
    competitive_landscape: Dict[str, Any]
    expansion_timeline: str  # Q1 2026, etc.
    investment_required: float
    roi_projection: float


@dataclass
class CrossMarketInsights:
    """Cross-market analytics and intelligence"""
    source_market: str
    target_market: str
    migration_volume: int
    average_salary_delta: float
    cost_of_living_comparison: float
    housing_affordability_ratio: float
    corporate_driving_factors: List[str]
    seasonal_patterns: Dict[str, int]
    top_employment_sectors: List[str]
    success_probability: float


class NationalMarketRegistry:
    """
    Extended registry for national market expansion and corporate relocation programs.

    Manages Fortune 500 partnerships, cross-market analytics, and nationwide
    expansion targeting $1M+ annual revenue enhancement.
    """

    def __init__(self, base_registry: Optional[MarketRegistry] = None):
        """
        Initialize national registry with base market registry integration

        Args:
            base_registry: Existing market registry to extend (defaults to global)
        """
        self.base_registry = base_registry or get_market_registry()
        self.cache = get_cache_service()

        # National expansion data structures
        self.corporate_headquarters: Dict[str, CorporateHeadquarters] = {}
        self.expansion_targets: Dict[str, MarketExpansionTarget] = {}
        self.corporate_partnerships: Dict[str, Dict[str, Any]] = {}

        # Data paths
        self.data_dir = Path(__file__).parent.parent / "data" / "national_expansion"
        self.corporate_data_file = self.data_dir / "corporate_headquarters.json"
        self.expansion_targets_file = self.data_dir / "expansion_targets.json"

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self._load_corporate_headquarters()
        self._load_expansion_targets()

        # Initialize new market services for Denver, Phoenix, Seattle
        self._initialize_national_markets()

        logger.info(f"NationalMarketRegistry initialized with {len(self.corporate_headquarters)} "
                   f"corporate headquarters and {len(self.expansion_targets)} expansion targets")

    def _load_corporate_headquarters(self) -> None:
        """Load corporate headquarters data from JSON file"""
        if not self.corporate_data_file.exists():
            # Create initial Fortune 500 headquarters data
            self._create_initial_corporate_data()
            return

        try:
            with open(self.corporate_data_file, 'r') as f:
                data = json.load(f)

            for corp_id, corp_data in data.items():
                # Convert datetime strings back to datetime objects
                corp_data['program_start_date'] = datetime.fromisoformat(corp_data['program_start_date'])
                corp_data['last_updated'] = datetime.fromisoformat(corp_data['last_updated'])
                corp_data['partnership_tier'] = CorporatePartnerTier(corp_data['partnership_tier'])

                self.corporate_headquarters[corp_id] = CorporateHeadquarters(**corp_data)

            logger.info(f"Loaded {len(self.corporate_headquarters)} corporate headquarters")

        except Exception as e:
            logger.error(f"Failed to load corporate headquarters data: {str(e)}")

    def _load_expansion_targets(self) -> None:
        """Load market expansion targets from JSON file"""
        if not self.expansion_targets_file.exists():
            self._create_initial_expansion_targets()
            return

        try:
            with open(self.expansion_targets_file, 'r') as f:
                data = json.load(f)

            for target_id, target_data in data.items():
                self.expansion_targets[target_id] = MarketExpansionTarget(**target_data)

            logger.info(f"Loaded {len(self.expansion_targets)} expansion targets")

        except Exception as e:
            logger.error(f"Failed to load expansion targets: {str(e)}")

    def _create_initial_corporate_data(self) -> None:
        """Create initial Fortune 500 corporate headquarters data"""
        initial_headquarters = {
            "amazon": CorporateHeadquarters(
                company_name="Amazon",
                ticker_symbol="AMZN",
                industry="Technology/E-commerce",
                headquarters_location=(47.6062, -122.3321),
                headquarters_city="Seattle",
                headquarters_state="WA",
                employee_count=1540000,
                fortune_ranking=2,
                partnership_tier=CorporatePartnerTier.PLATINUM,
                preferred_markets=["seattle", "austin", "denver", "phoenix"],
                relocation_volume_annual=850,
                average_relocation_budget=85000.0,
                contact_info={
                    "hr_director": "corporate-relocations@amazon.com",
                    "phone": "+1-206-266-1000",
                    "program_manager": "Jane Smith"
                },
                program_start_date=datetime(2024, 1, 15),
                last_updated=datetime.now()
            ),

            "microsoft": CorporateHeadquarters(
                company_name="Microsoft Corporation",
                ticker_symbol="MSFT",
                industry="Technology",
                headquarters_location=(47.6740, -122.1215),
                headquarters_city="Redmond",
                headquarters_state="WA",
                employee_count=221000,
                fortune_ranking=14,
                partnership_tier=CorporatePartnerTier.PLATINUM,
                preferred_markets=["seattle", "austin", "denver", "phoenix"],
                relocation_volume_annual=420,
                average_relocation_budget=95000.0,
                contact_info={
                    "hr_director": "relocations@microsoft.com",
                    "phone": "+1-425-882-8080",
                    "program_manager": "David Chen"
                },
                program_start_date=datetime(2024, 3, 1),
                last_updated=datetime.now()
            ),

            "google": CorporateHeadquarters(
                company_name="Alphabet Inc. (Google)",
                ticker_symbol="GOOGL",
                industry="Technology",
                headquarters_location=(37.4220, -122.0841),
                headquarters_city="Mountain View",
                headquarters_state="CA",
                employee_count=190000,
                fortune_ranking=29,
                partnership_tier=CorporatePartnerTier.PLATINUM,
                preferred_markets=["austin", "denver", "seattle"],
                relocation_volume_annual=380,
                average_relocation_budget=125000.0,
                contact_info={
                    "hr_director": "people-ops-relocations@google.com",
                    "phone": "+1-650-253-0000",
                    "program_manager": "Sarah Martinez"
                },
                program_start_date=datetime(2024, 2, 1),
                last_updated=datetime.now()
            ),

            "boeing": CorporateHeadquarters(
                company_name="Boeing Company",
                ticker_symbol="BA",
                industry="Aerospace",
                headquarters_location=(41.8781, -87.6298),
                headquarters_city="Chicago",
                headquarters_state="IL",
                employee_count=156000,
                fortune_ranking=54,
                partnership_tier=CorporatePartnerTier.GOLD,
                preferred_markets=["seattle", "denver", "houston"],
                relocation_volume_annual=285,
                average_relocation_budget=75000.0,
                contact_info={
                    "hr_director": "talent.mobility@boeing.com",
                    "phone": "+1-312-544-2000",
                    "program_manager": "Michael Johnson"
                },
                program_start_date=datetime(2024, 4, 15),
                last_updated=datetime.now()
            ),

            "intel": CorporateHeadquarters(
                company_name="Intel Corporation",
                ticker_symbol="INTC",
                industry="Semiconductors",
                headquarters_location=(37.3861, -121.9644),
                headquarters_city="Santa Clara",
                headquarters_state="CA",
                employee_count=131900,
                fortune_ranking=45,
                partnership_tier=CorporatePartnerTier.GOLD,
                preferred_markets=["phoenix", "austin", "denver"],
                relocation_volume_annual=225,
                average_relocation_budget=82000.0,
                contact_info={
                    "hr_director": "global.mobility@intel.com",
                    "phone": "+1-408-765-8080",
                    "program_manager": "Lisa Wang"
                },
                program_start_date=datetime(2024, 5, 1),
                last_updated=datetime.now()
            )
        }

        # Save to file
        serializable_data = {}
        for corp_id, headquarters in initial_headquarters.items():
            data_dict = headquarters.__dict__.copy()
            data_dict['program_start_date'] = headquarters.program_start_date.isoformat()
            data_dict['last_updated'] = headquarters.last_updated.isoformat()
            data_dict['partnership_tier'] = headquarters.partnership_tier.value
            serializable_data[corp_id] = data_dict

        with open(self.corporate_data_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)

        self.corporate_headquarters = initial_headquarters
        logger.info(f"Created initial corporate headquarters data with {len(initial_headquarters)} companies")

    def _create_initial_expansion_targets(self) -> None:
        """Create initial market expansion targets"""
        initial_targets = {
            "denver": MarketExpansionTarget(
                market_id="denver",
                market_name="Denver Metropolitan Area",
                state="CO",
                region="Rocky Mountain West",
                expansion_priority=10,
                corporate_headquarters_count=8,
                fortune_500_presence=12,
                estimated_annual_revenue_potential=385000.0,
                market_entry_complexity="medium",
                competitive_landscape={
                    "major_competitors": ["Re/Max", "Coldwell Banker", "Kentwood Real Estate"],
                    "market_share_opportunity": 0.15,
                    "differentiation_factors": ["Tech hub expertise", "Corporate relocation specialization"]
                },
                expansion_timeline="Q1 2026",
                investment_required=125000.0,
                roi_projection=3.8
            ),

            "phoenix": MarketExpansionTarget(
                market_id="phoenix",
                market_name="Phoenix Metropolitan Area",
                state="AZ",
                region="Southwest Desert",
                expansion_priority=9,
                corporate_headquarters_count=6,
                fortune_500_presence=8,
                estimated_annual_revenue_potential=425000.0,
                market_entry_complexity="medium",
                competitive_landscape={
                    "major_competitors": ["Long Realty", "Russ Lyon Sotheby's", "HomeSmart"],
                    "market_share_opportunity": 0.18,
                    "differentiation_factors": ["Luxury retirement expertise", "Corporate headquarters focus"]
                },
                expansion_timeline="Q2 2026",
                investment_required=145000.0,
                roi_projection=4.2
            ),

            "seattle": MarketExpansionTarget(
                market_id="seattle",
                market_name="Seattle Metropolitan Area",
                state="WA",
                region="Pacific Northwest",
                expansion_priority=10,
                corporate_headquarters_count=15,
                fortune_500_presence=18,
                estimated_annual_revenue_potential=625000.0,
                market_entry_complexity="high",
                competitive_landscape={
                    "major_competitors": ["Windermere", "John L. Scott", "Redfin"],
                    "market_share_opportunity": 0.12,
                    "differentiation_factors": ["Tech giant specialization", "International corporate transfers"]
                },
                expansion_timeline="Q1 2026",
                investment_required=225000.0,
                roi_projection=4.8
            ),

            "london": MarketExpansionTarget(
                market_id="london",
                market_name="London Metropolitan Area",
                state="London",
                region="EMEA",
                expansion_priority=10,
                corporate_headquarters_count=25,
                fortune_500_presence=35,
                estimated_annual_revenue_potential=1250000.0,
                market_entry_complexity="high",
                competitive_landscape={
                    "major_competitors": ["Savills", "Knight Frank", "Foxtons"],
                    "market_share_opportunity": 0.08,
                    "differentiation_factors": ["US-style proactive service", "AI-powered ROI defense"]
                },
                expansion_timeline="Q3 2026",
                investment_required=450000.0,
                roi_projection=5.2
            ),

            "singapore": MarketExpansionTarget(
                market_id="singapore",
                market_name="Singapore",
                state="Singapore",
                region="APAC",
                expansion_priority=9,
                corporate_headquarters_count=20,
                fortune_500_presence=28,
                estimated_annual_revenue_potential=950000.0,
                market_entry_complexity="high",
                competitive_landscape={
                    "major_competitors": ["PropNex", "ERA", "Huttons"],
                    "market_share_opportunity": 0.10,
                    "differentiation_factors": ["Cross-border relocation", "Advanced data analytics"]
                },
                expansion_timeline="Q4 2026",
                investment_required=350000.0,
                roi_projection=4.5
            )
        }

        # Save to file
        serializable_data = {}
        for target_id, target in initial_targets.items():
            serializable_data[target_id] = target.__dict__

        with open(self.expansion_targets_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)

        self.expansion_targets = initial_targets
        logger.info(f"Created initial expansion targets for {len(initial_targets)} markets")

    def _initialize_national_markets(self) -> None:
        """Initialize new market services for national expansion markets"""
        national_markets = ["denver", "phoenix", "seattle", "london", "singapore"]

        for market_id in national_markets:
            if market_id not in self.base_registry.service_classes:
                # Register new market with ConfigDrivenMarketService
                self.base_registry.service_classes[market_id] = ConfigDrivenMarketService
                logger.info(f"Registered {market_id} market service for national expansion")

    async def get_corporate_relocation_program(self, company_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive corporate relocation program details

        Args:
            company_identifier: Company name, ticker symbol, or internal ID

        Returns:
            Complete relocation program details including preferred markets,
            budget guidelines, and contact information
        """
        cache_key = f"corporate_program:{company_identifier}"

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for corporate program: {company_identifier}")
            return cached

        # Find corporate headquarters
        headquarters = self._find_corporate_headquarters(company_identifier)
        if not headquarters:
            logger.warning(f"Corporate headquarters not found: {company_identifier}")
            return None

        # Build comprehensive program details
        program_details = {
            "company_info": {
                "name": headquarters.company_name,
                "ticker": headquarters.ticker_symbol,
                "industry": headquarters.industry,
                "employee_count": headquarters.employee_count,
                "fortune_ranking": headquarters.fortune_ranking,
                "partnership_tier": headquarters.partnership_tier.value
            },
            "headquarters": {
                "location": headquarters.headquarters_location,
                "city": headquarters.headquarters_city,
                "state": headquarters.headquarters_state
            },
            "relocation_program": {
                "annual_volume": headquarters.relocation_volume_annual,
                "average_budget": headquarters.average_relocation_budget,
                "preferred_markets": headquarters.preferred_markets,
                "program_start_date": headquarters.program_start_date.isoformat(),
                "last_updated": headquarters.last_updated.isoformat()
            },
            "preferred_market_details": [],
            "contact_information": headquarters.contact_info,
            "service_tiers": self._get_service_tiers_for_partnership(headquarters.partnership_tier)
        }

        # Add detailed market information for preferred markets
        for market_id in headquarters.preferred_markets:
            market_service = self.base_registry.get_market_service(market_id)
            if market_service:
                market_config = self.base_registry.get_market_config(market_id)
                if market_config:
                    # Get corporate-specific insights for this market
                    corporate_insights = await market_service.get_corporate_relocation_insights(
                        company_identifier.lower().replace(" ", "_"),
                        "executive"  # Default to executive level
                    )

                    program_details["preferred_market_details"].append({
                        "market_id": market_id,
                        "market_name": market_config.get("market_name", market_id),
                        "median_home_price": market_config.get("median_home_price", 0),
                        "corporate_insights": corporate_insights
                    })

        # Cache for 6 hours
        await self.cache.set(cache_key, program_details, ttl=21600)
        logger.info(f"Generated corporate relocation program for {headquarters.company_name}")

        return program_details

    def _find_corporate_headquarters(self, identifier: str) -> Optional[CorporateHeadquarters]:
        """Find corporate headquarters by name, ticker, or ID"""
        identifier_lower = identifier.lower()

        # Try direct ID match first
        if identifier_lower in self.corporate_headquarters:
            return self.corporate_headquarters[identifier_lower]

        # Try company name match
        for corp_id, headquarters in self.corporate_headquarters.items():
            if headquarters.company_name.lower() == identifier_lower:
                return headquarters

            # Try ticker symbol match
            if headquarters.ticker_symbol and headquarters.ticker_symbol.lower() == identifier_lower:
                return headquarters

            # Try partial name match
            if identifier_lower in headquarters.company_name.lower():
                return headquarters

        return None

    def _get_service_tiers_for_partnership(self, tier: CorporatePartnerTier) -> Dict[str, Any]:
        """Get service tier details based on partnership level"""
        service_tiers = {
            CorporatePartnerTier.PLATINUM: {
                "dedicated_relocation_specialist": True,
                "24_7_support": True,
                "priority_scheduling": True,
                "exclusive_market_insights": True,
                "volume_discounts": 15,
                "quarterly_business_reviews": True,
                "custom_reporting": True
            },
            CorporatePartnerTier.GOLD: {
                "dedicated_relocation_specialist": True,
                "24_7_support": False,
                "priority_scheduling": True,
                "exclusive_market_insights": True,
                "volume_discounts": 10,
                "quarterly_business_reviews": False,
                "custom_reporting": True
            },
            CorporatePartnerTier.SILVER: {
                "dedicated_relocation_specialist": False,
                "24_7_support": False,
                "priority_scheduling": False,
                "exclusive_market_insights": False,
                "volume_discounts": 5,
                "quarterly_business_reviews": False,
                "custom_reporting": False
            },
            CorporatePartnerTier.BRONZE: {
                "dedicated_relocation_specialist": False,
                "24_7_support": False,
                "priority_scheduling": False,
                "exclusive_market_insights": False,
                "volume_discounts": 0,
                "quarterly_business_reviews": False,
                "custom_reporting": False
            }
        }

        return service_tiers.get(tier, service_tiers[CorporatePartnerTier.BRONZE])

    async def get_cross_market_insights(
        self,
        source_market: str,
        target_market: str
    ) -> Optional[CrossMarketInsights]:
        """
        Get cross-market migration and relocation insights

        Args:
            source_market: Source market ID (where employees are coming from)
            target_market: Target market ID (where employees are relocating to)

        Returns:
            Cross-market insights including cost comparisons and migration patterns
        """
        cache_key = f"cross_market:{source_market}:{target_market}"

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return CrossMarketInsights(**cached)

        # Get market configurations
        source_config = self.base_registry.get_market_config(source_market)
        target_config = self.base_registry.get_market_config(target_market)

        if not source_config or not target_config:
            logger.warning(f"Market configs not found: {source_market} -> {target_market}")
            return None

        # Calculate insights
        insights = CrossMarketInsights(
            source_market=source_market,
            target_market=target_market,
            migration_volume=self._estimate_migration_volume(source_market, target_market),
            average_salary_delta=self._calculate_salary_delta(source_config, target_config),
            cost_of_living_comparison=self._calculate_col_comparison(source_config, target_config),
            housing_affordability_ratio=self._calculate_housing_affordability(source_config, target_config),
            corporate_driving_factors=self._identify_corporate_factors(source_market, target_market),
            seasonal_patterns=self._analyze_seasonal_patterns(source_market, target_market),
            top_employment_sectors=self._get_top_sectors(target_config),
            success_probability=self._calculate_success_probability(source_market, target_market)
        )

        # Cache for 24 hours
        await self.cache.set(cache_key, insights.__dict__, ttl=86400)
        logger.info(f"Generated cross-market insights: {source_market} -> {target_market}")

        return insights

    def _estimate_migration_volume(self, source_market: str, target_market: str) -> int:
        """Estimate annual migration volume between markets"""
        # Simplified estimation based on market sizes and corporate presence
        source_config = self.base_registry.get_market_config(source_market)
        target_config = self.base_registry.get_market_config(target_market)

        if not source_config or not target_config:
            return 0

        # Base calculation on population and corporate presence
        source_pop = source_config.get("demographics", {}).get("population", 1000000)
        target_pop = target_config.get("demographics", {}).get("population", 1000000)

        # Estimate as percentage of population with corporate adjustment
        base_migration = min(source_pop, target_pop) * 0.001  # 0.1% base migration

        # Corporate adjustment based on shared employers
        corporate_boost = len(self._find_shared_employers(source_market, target_market)) * 15

        return int(base_migration + corporate_boost)

    def _find_shared_employers(self, market1: str, market2: str) -> List[str]:
        """Find employers operating in both markets"""
        shared = []

        for corp_id, headquarters in self.corporate_headquarters.items():
            if market1 in headquarters.preferred_markets and market2 in headquarters.preferred_markets:
                shared.append(headquarters.company_name)

        return shared

    def _calculate_salary_delta(self, source_config: Dict[str, Any], target_config: Dict[str, Any]) -> float:
        """Calculate average salary difference between markets"""
        source_income = source_config.get("demographics", {}).get("median_household_income", 70000)
        target_income = target_config.get("demographics", {}).get("median_household_income", 70000)

        return ((target_income - source_income) / source_income) * 100

    def _calculate_col_comparison(self, source_config: Dict[str, Any], target_config: Dict[str, Any]) -> float:
        """Calculate cost of living comparison (simplified)"""
        # Use housing prices as primary COL indicator
        source_price = source_config.get("median_home_price", 400000)
        target_price = target_config.get("median_home_price", 400000)

        return ((target_price - source_price) / source_price) * 100

    def _calculate_housing_affordability(self, source_config: Dict[str, Any], target_config: Dict[str, Any]) -> float:
        """Calculate housing affordability ratio"""
        target_price = target_config.get("median_home_price", 400000)
        target_income = target_config.get("demographics", {}).get("median_household_income", 70000)

        return target_price / target_income if target_income > 0 else 10.0

    def _identify_corporate_factors(self, source_market: str, target_market: str) -> List[str]:
        """Identify key corporate driving factors for migration"""
        factors = []

        # Check for major employers in target market
        shared_employers = self._find_shared_employers(source_market, target_market)
        if shared_employers:
            factors.append(f"Shared corporate presence: {', '.join(shared_employers[:3])}")

        # Industry-based factors
        target_config = self.base_registry.get_market_config(target_market)
        if target_config:
            market_type = target_config.get("market_type", "")
            if "tech" in market_type:
                factors.append("Tech industry growth and opportunities")
            elif "finance" in market_type:
                factors.append("Financial services sector expansion")
            elif "energy" in market_type:
                factors.append("Energy sector corporate relocations")

        # Default factors
        if not factors:
            factors = ["Cost of living advantages", "Career advancement opportunities"]

        return factors

    def _analyze_seasonal_patterns(self, source_market: str, target_market: str) -> Dict[str, int]:
        """Analyze seasonal migration patterns"""
        # Simplified seasonal patterns based on market characteristics
        return {
            "Q1": 35,  # High corporate relocation season
            "Q2": 25,  # Moderate
            "Q3": 20,  # Lower (school year considerations)
            "Q4": 20   # Lower (holidays)
        }

    def _get_top_sectors(self, market_config: Dict[str, Any]) -> List[str]:
        """Get top employment sectors for a market"""
        market_type = market_config.get("market_type", "")

        sector_mapping = {
            "tech_hub": ["Technology", "Software Development", "Cybersecurity"],
            "tech_headquarters": ["Technology", "Cloud Computing", "AI/ML"],
            "finance_hub": ["Financial Services", "Banking", "Insurance"],
            "energy_hub": ["Energy", "Oil & Gas", "Renewable Energy"],
            "corporate_hub": ["Corporate Services", "Finance", "Technology"],
            "mixed_economy": ["Healthcare", "Education", "Government"]
        }

        return sector_mapping.get(market_type, ["Professional Services", "Healthcare", "Technology"])

    def _calculate_success_probability(self, source_market: str, target_market: str) -> float:
        """Calculate probability of successful relocation"""
        # Simplified success probability based on market characteristics
        base_probability = 0.75

        # Adjust based on cost of living
        source_config = self.base_registry.get_market_config(source_market)
        target_config = self.base_registry.get_market_config(target_market)

        if source_config and target_config:
            cost_delta = self._calculate_col_comparison(source_config, target_config)

            # Lower success if cost increase is too high
            if cost_delta > 30:
                base_probability -= 0.15
            elif cost_delta < -10:  # Cost decrease is good
                base_probability += 0.1

        # Corporate presence boost
        shared_employers = self._find_shared_employers(source_market, target_market)
        if shared_employers:
            base_probability += len(shared_employers) * 0.05

        return min(0.95, max(0.30, base_probability))

    async def get_expansion_opportunities(self) -> List[MarketExpansionTarget]:
        """Get prioritized list of market expansion opportunities"""
        cache_key = "expansion_opportunities"

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return [MarketExpansionTarget(**target) for target in cached]

        # Sort expansion targets by priority and ROI
        opportunities = list(self.expansion_targets.values())
        opportunities.sort(key=lambda x: (x.expansion_priority, x.roi_projection), reverse=True)

        # Cache for 12 hours
        serializable_opportunities = [target.__dict__ for target in opportunities]
        await self.cache.set(cache_key, serializable_opportunities, ttl=43200)

        logger.info(f"Retrieved {len(opportunities)} expansion opportunities")
        return opportunities

    async def get_national_market_summary(self) -> Dict[str, Any]:
        """Get comprehensive national market summary"""
        cache_key = "national_market_summary"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Aggregate data from all markets
        all_markets = self.base_registry.list_markets()
        total_revenue_potential = sum(
            target.estimated_annual_revenue_potential
            for target in self.expansion_targets.values()
        )

        summary = {
            "total_markets": len(all_markets),
            "expansion_markets": len(self.expansion_targets),
            "corporate_partnerships": len(self.corporate_headquarters),
            "revenue_enhancement_target": total_revenue_potential,
            "investment_required": sum(
                target.investment_required
                for target in self.expansion_targets.values()
            ),
            "average_roi_projection": sum(
                target.roi_projection
                for target in self.expansion_targets.values()
            ) / len(self.expansion_targets) if self.expansion_targets else 0,
            "partnership_tiers": {
                tier.value: len([h for h in self.corporate_headquarters.values()
                               if h.partnership_tier == tier])
                for tier in CorporatePartnerTier
            },
            "markets_by_type": {},
            "last_updated": datetime.now().isoformat()
        }

        # Categorize markets by type
        for market_id in all_markets:
            market_config = self.base_registry.get_market_config(market_id)
            if market_config:
                market_type = market_config.get("market_type", "unknown")
                if market_type not in summary["markets_by_type"]:
                    summary["markets_by_type"][market_type] = []
                summary["markets_by_type"][market_type].append(market_id)

        # Cache for 2 hours
        await self.cache.set(cache_key, summary, ttl=7200)
        logger.info("Generated national market summary")

        return summary

    def register_corporate_partnership(
        self,
        headquarters: CorporateHeadquarters
    ) -> bool:
        """Register a new corporate partnership"""
        try:
            # Generate corporate ID
            corp_id = headquarters.company_name.lower().replace(" ", "_").replace(".", "")

            self.corporate_headquarters[corp_id] = headquarters

            # Save to file
            self._save_corporate_data()

            logger.info(f"Registered corporate partnership: {headquarters.company_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to register corporate partnership: {str(e)}")
            return False

    def _save_corporate_data(self) -> None:
        """Save corporate headquarters data to JSON file"""
        serializable_data = {}
        for corp_id, headquarters in self.corporate_headquarters.items():
            data_dict = headquarters.__dict__.copy()
            data_dict['program_start_date'] = headquarters.program_start_date.isoformat()
            data_dict['last_updated'] = headquarters.last_updated.isoformat()
            data_dict['partnership_tier'] = headquarters.partnership_tier.value
            serializable_data[corp_id] = data_dict

        with open(self.corporate_data_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            base_health = self.base_registry.get_market_summary()

            return {
                "status": "healthy",
                "national_registry": {
                    "corporate_headquarters": len(self.corporate_headquarters),
                    "expansion_targets": len(self.expansion_targets),
                    "data_files_exist": {
                        "corporate_data": self.corporate_data_file.exists(),
                        "expansion_targets": self.expansion_targets_file.exists()
                    }
                },
                "base_registry": base_health,
                "cache_available": self.cache is not None,
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }


# Global registry instance
_national_registry = None


def get_national_market_registry() -> NationalMarketRegistry:
    """Get the global national market registry instance"""
    global _national_registry
    if _national_registry is None:
        _national_registry = NationalMarketRegistry()
    return _national_registry


# Convenience functions
async def get_corporate_program(company: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get corporate relocation program"""
    registry = get_national_market_registry()
    return await registry.get_corporate_relocation_program(company)


async def get_market_migration_insights(source: str, target: str) -> Optional[CrossMarketInsights]:
    """Convenience function to get cross-market insights"""
    registry = get_national_market_registry()
    return await registry.get_cross_market_insights(source, target)