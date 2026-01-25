"""
Luxury Lead Scoring Engine with Net Worth Integration
Advanced lead qualification system for UHNW clients and luxury property buyers

This engine provides sophisticated lead scoring specifically designed for luxury
real estate markets, focusing on net worth qualification, lifestyle indicators,
and luxury buying signals to justify premium commission rates.

Features:
- Net worth verification and estimation
- Luxury lifestyle indicator analysis
- UHNW buying signal detection
- Investment capacity assessment
- Competitive intelligence integration
- Premium service qualification
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import numpy as np
from decimal import Decimal
import re
import asyncio

from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.optimized_cache_service import cached
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.core.llm_client import LLMClient


class WealthTier(Enum):
    MASS_AFFLUENT = "mass_affluent"      # $100K - $1M net worth
    AFFLUENT = "affluent"                # $1M - $5M net worth
    UHNW = "uhnw"                        # $5M - $25M net worth
    ULTRA_UHNW = "ultra_uhnw"            # $25M - $100M net worth
    BILLIONAIRE = "billionaire"           # $100M+ net worth


class LuxuryBuyingSignal(Enum):
    IMMEDIATE = "immediate"               # Ready to buy now
    ACTIVE = "active"                     # Actively searching
    CONSIDERING = "considering"           # Considering luxury purchase
    FUTURE = "future"                     # Future luxury buyer
    INVESTOR = "investor"                 # Investment focused


@dataclass
class NetWorthIndicators:
    """Indicators for net worth estimation"""
    estimated_net_worth: float = 0.0
    net_worth_confidence: float = 0.0    # Confidence score 0-100
    income_estimates: Dict[str, float] = field(default_factory=dict)  # Multiple income sources
    asset_indicators: List[str] = field(default_factory=list)  # Asset ownership indicators
    investment_sophistication: float = 0.0  # Investment knowledge score 0-100

    # Verification sources
    public_records_match: bool = False
    social_media_indicators: List[str] = field(default_factory=list)
    property_ownership_history: List[Dict] = field(default_factory=list)
    business_ownership: Optional[Dict] = None

    # Risk factors
    debt_indicators: List[str] = field(default_factory=list)
    financial_stress_signals: List[str] = field(default_factory=list)
    liquidity_concerns: List[str] = field(default_factory=list)


@dataclass
class LuxuryLifestyleProfile:
    """Luxury lifestyle indicators and preferences"""
    lifestyle_score: float = 0.0         # Overall luxury lifestyle score 0-100

    # Luxury preferences
    preferred_neighborhoods: List[str] = field(default_factory=list)
    property_type_preferences: List[str] = field(default_factory=list)
    amenity_preferences: List[str] = field(default_factory=list)
    architectural_preferences: List[str] = field(default_factory=list)

    # Lifestyle indicators
    luxury_brand_affinity: float = 0.0   # Luxury brand preference score
    travel_patterns: List[str] = field(default_factory=list)
    dining_preferences: List[str] = field(default_factory=list)
    entertainment_preferences: List[str] = field(default_factory=list)

    # Service expectations
    service_level_expectations: str = "premium"  # standard, premium, white_glove
    communication_preferences: Dict[str, Any] = field(default_factory=dict)
    privacy_requirements: float = 0.0    # Privacy requirement score 0-100
    discretion_importance: float = 0.0   # Discretion importance score 0-100


@dataclass
class InvestmentCapacityAnalysis:
    """Analysis of lead's investment capacity and sophistication"""
    investment_capacity_score: float = 0.0      # Overall investment capacity 0-100

    # Financial capacity
    estimated_buying_budget: float = 0.0
    down_payment_capacity: float = 0.0
    financing_sophistication: float = 0.0       # Understanding of luxury financing

    # Investment experience
    real_estate_experience: float = 0.0         # RE investment experience 0-100
    portfolio_complexity: float = 0.0           # Existing portfolio complexity
    alternative_investments: List[str] = field(default_factory=list)

    # Decision-making patterns
    decision_timeline: str = "moderate"          # fast, moderate, deliberate
    advisor_involvement: List[str] = field(default_factory=list)  # CPAs, lawyers, etc.
    due_diligence_requirements: List[str] = field(default_factory=list)


@dataclass
class CompetitiveIntelligence:
    """Competitive intelligence for luxury lead qualification"""
    competitor_interactions: List[Dict] = field(default_factory=list)
    agent_preferences: List[str] = field(default_factory=list)
    past_transaction_patterns: List[Dict] = field(default_factory=list)

    # Market intelligence
    luxury_market_knowledge: float = 0.0        # Market knowledge score 0-100
    price_sensitivity: float = 0.0              # Price sensitivity 0-100 (lower = less sensitive)
    negotiation_style: str = "collaborative"    # aggressive, collaborative, analytical

    # Referral intelligence
    referral_source_quality: float = 0.0        # Quality of referral source 0-100
    network_influence: float = 0.0              # Network influence score 0-100
    repeat_client_potential: float = 0.0        # Potential for repeat business 0-100


@dataclass
class LuxuryLead:
    """Comprehensive luxury lead profile"""
    lead_id: str
    contact_info: Dict[str, Any]
    source: str
    created_date: datetime

    # Core demographics
    estimated_age_range: Tuple[int, int] = (35, 65)
    family_composition: Dict[str, Any] = field(default_factory=dict)
    location_preferences: List[str] = field(default_factory=list)

    # Wealth and capacity analysis
    wealth_tier: WealthTier = WealthTier.AFFLUENT
    net_worth_indicators: NetWorthIndicators = field(default_factory=NetWorthIndicators)
    investment_capacity: InvestmentCapacityAnalysis = field(default_factory=InvestmentCapacityAnalysis)

    # Luxury profile
    lifestyle_profile: LuxuryLifestyleProfile = field(default_factory=LuxuryLifestyleProfile)
    buying_signal: LuxuryBuyingSignal = LuxuryBuyingSignal.CONSIDERING

    # Market intelligence
    competitive_intel: CompetitiveIntelligence = field(default_factory=CompetitiveIntelligence)

    # Scoring results
    overall_luxury_score: float = 0.0           # Master luxury score 0-100
    qualification_status: str = "pending"        # pending, qualified, premium, ultra_premium
    commission_potential: float = 0.0           # Estimated commission potential

    # Service requirements
    recommended_service_level: str = "premium"   # standard, premium, white_glove
    agent_specialization_required: List[str] = field(default_factory=list)

    # Tracking
    last_updated: datetime = field(default_factory=datetime.now)
    next_follow_up: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))


class LuxuryLeadScoringEngine:
    """
    Advanced lead scoring engine for luxury real estate market

    Provides sophisticated scoring and qualification specifically for UHNW clients,
    luxury property buyers, and high-commission opportunities.
    """

    def __init__(self):
        self.cache = CacheService()
        self.claude = ClaudeAssistant()
        self.base_scorer = LeadScorer()  # Leverage existing base scorer
        self.llm_client = LLMClient()

        # Scoring weights for luxury factors
        self.scoring_weights = {
            "net_worth_indicators": 0.35,
            "lifestyle_profile": 0.25,
            "investment_capacity": 0.20,
            "buying_signals": 0.15,
            "competitive_intel": 0.05
        }

    async def score_luxury_lead(self, lead_data: Dict[str, Any]) -> LuxuryLead:
        """
        Comprehensive luxury lead scoring and qualification

        Args:
            lead_data: Raw lead data from various sources (GHL, website, referral)

        Returns:
            Fully analyzed and scored luxury lead profile
        """
        # Initialize luxury lead
        luxury_lead = LuxuryLead(
            lead_id=lead_data.get("lead_id", f"LUX-{datetime.now().timestamp()}"),
            contact_info=lead_data.get("contact_info", {}),
            source=lead_data.get("source", "unknown"),
            created_date=datetime.now()
        )

        # Analyze net worth indicators
        luxury_lead.net_worth_indicators = await self._analyze_net_worth_indicators(lead_data)
        luxury_lead.wealth_tier = self._determine_wealth_tier(luxury_lead.net_worth_indicators)

        # Analyze lifestyle profile
        luxury_lead.lifestyle_profile = await self._analyze_luxury_lifestyle(lead_data)

        # Analyze investment capacity
        luxury_lead.investment_capacity = await self._analyze_investment_capacity(lead_data)

        # Detect buying signals
        luxury_lead.buying_signal = await self._detect_luxury_buying_signals(lead_data)

        # Gather competitive intelligence
        luxury_lead.competitive_intel = await self._gather_competitive_intelligence(lead_data)

        # Calculate master luxury score
        luxury_lead.overall_luxury_score = self._calculate_master_luxury_score(luxury_lead)

        # Determine qualification status
        luxury_lead.qualification_status = self._determine_qualification_status(luxury_lead)

        # Estimate commission potential
        luxury_lead.commission_potential = self._estimate_commission_potential(luxury_lead)

        # Recommend service level
        luxury_lead.recommended_service_level = self._recommend_service_level(luxury_lead)

        return luxury_lead

    async def _analyze_net_worth_indicators(self, lead_data: Dict[str, Any]) -> NetWorthIndicators:
        """Analyze and estimate net worth using multiple indicators"""

        indicators = NetWorthIndicators()

        # Extract basic information
        email = lead_data.get("contact_info", {}).get("email", "")
        phone = lead_data.get("contact_info", {}).get("phone", "")
        address = lead_data.get("contact_info", {}).get("address", "")
        profession = lead_data.get("profession", "")
        company = lead_data.get("company", "")

        # Analyze email domain for business/executive indicators
        indicators.asset_indicators.extend(self._analyze_email_domain(email))

        # Analyze address for luxury indicators
        if address:
            luxury_address_score = self._analyze_address_luxury_indicators(address)
            indicators.estimated_net_worth += luxury_address_score * 100_000  # Scale factor

        # Professional analysis
        if profession or company:
            profession_analysis = await self._analyze_professional_indicators(profession, company)
            indicators.income_estimates.update(profession_analysis.get("income_estimates", {}))
            indicators.investment_sophistication = profession_analysis.get("investment_sophistication", 0)
            indicators.estimated_net_worth += profession_analysis.get("net_worth_contribution", 0)

        # Analyze communication patterns for sophistication
        communication_data = lead_data.get("communication_history", [])
        if communication_data:
            sophistication_score = self._analyze_communication_sophistication(communication_data)
            indicators.investment_sophistication = max(indicators.investment_sophistication, sophistication_score)

        # Property search patterns
        search_history = lead_data.get("property_search_history", [])
        if search_history:
            search_analysis = self._analyze_property_search_patterns(search_history)
            indicators.estimated_net_worth = max(indicators.estimated_net_worth, search_analysis.get("min_net_worth_estimate", 0))

        # Calculate confidence score
        confidence_factors = [
            len(indicators.asset_indicators) * 10,
            len(indicators.income_estimates) * 15,
            indicators.investment_sophistication * 0.5,
            (1 if indicators.public_records_match else 0) * 30
        ]
        indicators.net_worth_confidence = min(sum(confidence_factors), 100)

        return indicators

    def _analyze_email_domain(self, email: str) -> List[str]:
        """Analyze email domain for business/executive indicators"""
        if not email:
            return []

        domain = email.split("@")[-1].lower()
        indicators = []

        # Executive email patterns
        executive_domains = [
            "gmail.com", "outlook.com", "icloud.com"  # Personal emails (less indicative)
        ]

        # Corporate/professional domains
        if domain not in executive_domains:
            indicators.append("corporate_email")

            # Check for executive email patterns
            local_part = email.split("@")[0].lower()
            executive_patterns = ["ceo", "president", "founder", "owner", "partner"]
            if any(pattern in local_part for pattern in executive_patterns):
                indicators.append("executive_title_email")

        # Industry-specific domains
        finance_indicators = ["bank", "capital", "investment", "wealth", "fund"]
        if any(indicator in domain for indicator in finance_indicators):
            indicators.append("finance_industry")

        tech_indicators = ["tech", "software", "ai", "data"]
        if any(indicator in domain for indicator in tech_indicators):
            indicators.append("tech_industry")

        return indicators

    def _analyze_address_luxury_indicators(self, address: str) -> float:
        """Analyze address for luxury neighborhood indicators"""
        if not address:
            return 0.0

        address_lower = address.lower()

        # Austin luxury zip codes and neighborhoods
        luxury_indicators = {
            "78746": 8.0,  # West Lake Hills
            "78733": 7.5,  # West Lake
            "78738": 7.0,  # Bee Cave
            "78613": 6.5,  # Cedar Park (luxury areas)
            "78704": 6.0,  # South Austin (trendy areas)
            "west lake": 8.0,
            "tarrytown": 7.5,
            "rollingwood": 8.5,
            "bee cave": 7.0,
            "zilker": 6.0,
            "clarksville": 6.5,
            "hyde park": 5.5
        }

        luxury_score = 0.0
        for indicator, score in luxury_indicators.items():
            if indicator in address_lower:
                luxury_score = max(luxury_score, score)

        return luxury_score

    async def _analyze_professional_indicators(self, profession: str, company: str) -> Dict[str, Any]:
        """Analyze professional indicators for net worth estimation"""

        # High net worth professions
        profession_analysis = {
            "income_estimates": {},
            "investment_sophistication": 0,
            "net_worth_contribution": 0
        }

        if not profession and not company:
            return profession_analysis

        combined_text = f"{profession} {company}".lower()

        # Executive positions
        executive_indicators = {
            "ceo": {"income": 500_000, "sophistication": 85, "net_worth_multiplier": 8},
            "president": {"income": 350_000, "sophistication": 80, "net_worth_multiplier": 6},
            "founder": {"income": 400_000, "sophistication": 90, "net_worth_multiplier": 10},
            "partner": {"income": 300_000, "sophistication": 75, "net_worth_multiplier": 5},
            "owner": {"income": 250_000, "sophistication": 70, "net_worth_multiplier": 4}
        }

        # Professional categories
        high_income_professions = {
            "doctor": {"income": 300_000, "sophistication": 60, "net_worth_multiplier": 4},
            "physician": {"income": 350_000, "sophistication": 60, "net_worth_multiplier": 4},
            "surgeon": {"income": 500_000, "sophistication": 65, "net_worth_multiplier": 5},
            "lawyer": {"income": 200_000, "sophistication": 70, "net_worth_multiplier": 3},
            "attorney": {"income": 200_000, "sophistication": 70, "net_worth_multiplier": 3},
            "investment": {"income": 300_000, "sophistication": 95, "net_worth_multiplier": 6},
            "finance": {"income": 200_000, "sophistication": 85, "net_worth_multiplier": 4},
            "consultant": {"income": 150_000, "sophistication": 75, "net_worth_multiplier": 3}
        }

        # Check for matches
        for indicator, values in {**executive_indicators, **high_income_professions}.items():
            if indicator in combined_text:
                profession_analysis["income_estimates"][indicator] = values["income"]
                profession_analysis["investment_sophistication"] = max(
                    profession_analysis["investment_sophistication"],
                    values["sophistication"]
                )
                profession_analysis["net_worth_contribution"] = max(
                    profession_analysis["net_worth_contribution"],
                    values["income"] * values["net_worth_multiplier"]
                )

        return profession_analysis

    def _analyze_communication_sophistication(self, communication_history: List[Dict]) -> float:
        """Analyze communication sophistication score"""
        if not communication_history:
            return 0.0

        sophistication_score = 0.0

        # Analyze communication patterns
        for comm in communication_history[-10:]:  # Last 10 communications
            content = comm.get("content", "").lower()

            # Investment terminology
            investment_terms = [
                "portfolio", "roi", "cap rate", "irr", "appreciation", "depreciation",
                "1031 exchange", "tax benefits", "cash flow", "equity", "leverage"
            ]
            investment_score = sum(1 for term in investment_terms if term in content) * 5

            # Luxury terminology
            luxury_terms = [
                "luxury", "premium", "executive", "private", "exclusive", "bespoke",
                "white-glove", "concierge", "high-end", "sophisticated"
            ]
            luxury_score = sum(1 for term in luxury_terms if term in content) * 3

            # Professional communication indicators
            professional_score = 0
            if len(content.split()) > 50:  # Detailed communications
                professional_score += 10
            if "?" in content:  # Asks questions (engagement)
                professional_score += 5
            if any(word in content for word in ["appreciate", "thank you", "grateful"]):
                professional_score += 5

            sophistication_score = max(
                sophistication_score,
                min(investment_score + luxury_score + professional_score, 100)
            )

        return sophistication_score

    def _analyze_property_search_patterns(self, search_history: List[Dict]) -> Dict[str, Any]:
        """Analyze property search patterns for wealth indicators"""
        if not search_history:
            return {"min_net_worth_estimate": 0}

        # Analyze search price ranges
        price_searches = [search.get("max_price", 0) for search in search_history if search.get("max_price")]

        if not price_searches:
            return {"min_net_worth_estimate": 0}

        avg_search_price = sum(price_searches) / len(price_searches)
        max_search_price = max(price_searches)

        # Estimate net worth based on property search patterns
        # Typically, people can afford properties worth 3-5x their annual income
        # And have net worth 5-10x their annual income
        estimated_annual_income = avg_search_price * 0.25  # Conservative estimate
        estimated_net_worth = estimated_annual_income * 7   # Conservative multiplier

        return {
            "min_net_worth_estimate": estimated_net_worth,
            "avg_search_price": avg_search_price,
            "max_search_price": max_search_price,
            "search_consistency": len(set(price_searches)) < len(price_searches) * 0.5
        }

    def _determine_wealth_tier(self, indicators: NetWorthIndicators) -> WealthTier:
        """Determine wealth tier based on net worth indicators"""
        estimated_net_worth = indicators.estimated_net_worth

        if estimated_net_worth >= 100_000_000:
            return WealthTier.BILLIONAIRE
        elif estimated_net_worth >= 25_000_000:
            return WealthTier.ULTRA_UHNW
        elif estimated_net_worth >= 5_000_000:
            return WealthTier.UHNW
        elif estimated_net_worth >= 1_000_000:
            return WealthTier.AFFLUENT
        else:
            return WealthTier.MASS_AFFLUENT

    async def _analyze_luxury_lifestyle(self, lead_data: Dict[str, Any]) -> LuxuryLifestyleProfile:
        """Analyze luxury lifestyle indicators and preferences"""

        profile = LuxuryLifestyleProfile()

        # Extract lifestyle data
        preferences = lead_data.get("preferences", {})
        search_history = lead_data.get("property_search_history", [])
        communication = lead_data.get("communication_history", [])

        # Analyze property preferences
        if search_history:
            profile.preferred_neighborhoods = self._extract_neighborhood_preferences(search_history)
            profile.property_type_preferences = self._extract_property_type_preferences(search_history)
            profile.amenity_preferences = self._extract_amenity_preferences(search_history)

        # Analyze communication for lifestyle indicators
        lifestyle_score = 0.0

        for comm in communication:
            content = comm.get("content", "").lower()

            # Luxury lifestyle terms
            luxury_lifestyle_terms = [
                "travel", "vacation home", "wine cellar", "home theater", "spa",
                "gym", "pool", "tennis", "golf", "private", "gourmet", "chef",
                "staff", "housekeeper", "gardener", "security", "art", "collection"
            ]

            lifestyle_score += sum(1 for term in luxury_lifestyle_terms if term in content) * 2

            # Service expectation indicators
            service_terms = [
                "personal", "custom", "exclusive", "private", "concierge",
                "white-glove", "full-service", "premium", "luxury service"
            ]

            if any(term in content for term in service_terms):
                profile.service_level_expectations = "white_glove"

        profile.lifestyle_score = min(lifestyle_score, 100)

        # Privacy and discretion analysis
        privacy_indicators = ["private", "confidential", "discrete", "quiet", "off-market"]
        privacy_score = sum(
            1 for comm in communication
            for indicator in privacy_indicators
            if indicator in comm.get("content", "").lower()
        ) * 10

        profile.privacy_requirements = min(privacy_score, 100)
        profile.discretion_importance = profile.privacy_requirements  # Correlated

        return profile

    def _extract_neighborhood_preferences(self, search_history: List[Dict]) -> List[str]:
        """Extract neighborhood preferences from search history"""
        neighborhoods = []
        for search in search_history:
            location = search.get("location", "")
            if location:
                neighborhoods.append(location)

        # Return most frequent neighborhoods
        from collections import Counter
        neighborhood_counts = Counter(neighborhoods)
        return [neighborhood for neighborhood, count in neighborhood_counts.most_common(5)]

    def _extract_property_type_preferences(self, search_history: List[Dict]) -> List[str]:
        """Extract property type preferences"""
        property_types = []
        for search in search_history:
            prop_type = search.get("property_type", "")
            if prop_type:
                property_types.append(prop_type)

        from collections import Counter
        type_counts = Counter(property_types)
        return [prop_type for prop_type, count in type_counts.most_common(3)]

    def _extract_amenity_preferences(self, search_history: List[Dict]) -> List[str]:
        """Extract amenity preferences from search history"""
        amenities = []
        for search in search_history:
            search_amenities = search.get("amenities", [])
            if isinstance(search_amenities, list):
                amenities.extend(search_amenities)

        from collections import Counter
        amenity_counts = Counter(amenities)
        return [amenity for amenity, count in amenity_counts.most_common(10)]

    async def _analyze_investment_capacity(self, lead_data: Dict[str, Any]) -> InvestmentCapacityAnalysis:
        """Analyze investment capacity and sophistication"""

        capacity = InvestmentCapacityAnalysis()

        # Extract financial indicators
        search_history = lead_data.get("property_search_history", [])
        communication = lead_data.get("communication_history", [])

        # Estimate buying budget from search patterns
        if search_history:
            price_searches = [search.get("max_price", 0) for search in search_history if search.get("max_price")]
            if price_searches:
                capacity.estimated_buying_budget = sum(price_searches) / len(price_searches)
                capacity.down_payment_capacity = capacity.estimated_buying_budget * 0.25  # Conservative estimate

        # Analyze investment sophistication from communication
        investment_terms = [
            "investment", "roi", "cash flow", "cap rate", "appreciation", "depreciation",
            "leverage", "equity", "portfolio", "diversification", "1031", "tax benefits"
        ]

        sophistication_score = 0
        for comm in communication:
            content = comm.get("content", "").lower()
            sophistication_score += sum(1 for term in investment_terms if term in content) * 3

        capacity.financing_sophistication = min(sophistication_score, 100)
        capacity.real_estate_experience = min(sophistication_score * 0.8, 100)

        # Investment capacity score
        capacity_factors = [
            min(capacity.estimated_buying_budget / 1_000_000 * 50, 50),  # Budget factor
            capacity.financing_sophistication * 0.3,                     # Sophistication
            capacity.real_estate_experience * 0.2                       # Experience
        ]

        capacity.investment_capacity_score = min(sum(capacity_factors), 100)

        return capacity

    async def _detect_luxury_buying_signals(self, lead_data: Dict[str, Any]) -> LuxuryBuyingSignal:
        """Detect luxury buying signals and urgency"""

        communication = lead_data.get("communication_history", [])
        search_history = lead_data.get("property_search_history", [])

        if not communication and not search_history:
            return LuxuryBuyingSignal.CONSIDERING

        # Recent activity analysis
        recent_communications = [
            comm for comm in communication
            if datetime.fromisoformat(comm.get("date", datetime.now().isoformat())) > datetime.now() - timedelta(days=30)
        ]

        recent_searches = [
            search for search in search_history
            if datetime.fromisoformat(search.get("date", datetime.now().isoformat())) > datetime.now() - timedelta(days=30)
        ]

        # Immediate buying signals
        immediate_signals = [
            "ready to buy", "make an offer", "close quickly", "cash buyer",
            "need to move fast", "time sensitive", "immediate", "urgent"
        ]

        # Active buying signals
        active_signals = [
            "looking for", "searching for", "want to see", "schedule showing",
            "available to tour", "interested in", "when can we", "appointment"
        ]

        # Future/investment signals
        future_signals = [
            "planning to", "considering", "thinking about", "future", "eventually",
            "investment property", "rental property", "portfolio addition"
        ]

        signal_scores = {
            LuxuryBuyingSignal.IMMEDIATE: 0,
            LuxuryBuyingSignal.ACTIVE: 0,
            LuxuryBuyingSignal.CONSIDERING: 0,
            LuxuryBuyingSignal.FUTURE: 0,
            LuxuryBuyingSignal.INVESTOR: 0
        }

        # Score based on communication content
        for comm in recent_communications:
            content = comm.get("content", "").lower()

            signal_scores[LuxuryBuyingSignal.IMMEDIATE] += sum(1 for signal in immediate_signals if signal in content) * 3
            signal_scores[LuxuryBuyingSignal.ACTIVE] += sum(1 for signal in active_signals if signal in content) * 2
            signal_scores[LuxuryBuyingSignal.CONSIDERING] += len(content.split()) / 20  # Engagement score
            signal_scores[LuxuryBuyingSignal.FUTURE] += sum(1 for signal in future_signals if signal in content)

            # Investment signals
            if any(term in content for term in ["investment", "rental", "portfolio", "cash flow"]):
                signal_scores[LuxuryBuyingSignal.INVESTOR] += 2

        # Activity-based scoring
        if len(recent_searches) > 10:
            signal_scores[LuxuryBuyingSignal.ACTIVE] += 5
        elif len(recent_searches) > 5:
            signal_scores[LuxuryBuyingSignal.CONSIDERING] += 3

        # Return highest scoring signal
        return max(signal_scores.items(), key=lambda x: x[1])[0]

    async def _gather_competitive_intelligence(self, lead_data: Dict[str, Any]) -> CompetitiveIntelligence:
        """Gather competitive intelligence for lead"""

        intel = CompetitiveIntelligence()

        # Analyze referral source
        referral_source = lead_data.get("referral_source", "")
        if referral_source:
            intel.referral_source_quality = self._score_referral_source(referral_source)

        # Analyze past agent interactions
        agent_history = lead_data.get("agent_interaction_history", [])
        if agent_history:
            intel.competitor_interactions = agent_history
            intel.agent_preferences = [interaction.get("agent_type", "") for interaction in agent_history]

        # Price sensitivity analysis
        search_history = lead_data.get("property_search_history", [])
        if search_history:
            price_ranges = [search.get("max_price", 0) - search.get("min_price", 0) for search in search_history]
            avg_range = sum(price_ranges) / len(price_ranges) if price_ranges else 0

            # Lower price range variance = less price sensitive
            intel.price_sensitivity = max(0, 100 - (avg_range / 1_000_000 * 50))

        return intel

    def _score_referral_source(self, referral_source: str) -> float:
        """Score the quality of referral source"""

        high_quality_sources = [
            "past client", "attorney", "cpa", "financial advisor", "wealth manager",
            "luxury agent", "private banker", "trust officer"
        ]

        medium_quality_sources = [
            "friend", "family", "colleague", "business partner", "realtor"
        ]

        referral_lower = referral_source.lower()

        if any(source in referral_lower for source in high_quality_sources):
            return 90.0
        elif any(source in referral_lower for source in medium_quality_sources):
            return 70.0
        else:
            return 50.0

    def _calculate_master_luxury_score(self, luxury_lead: LuxuryLead) -> float:
        """Calculate master luxury score using weighted factors"""

        # Component scores
        net_worth_score = min(luxury_lead.net_worth_indicators.net_worth_confidence, 100)
        lifestyle_score = luxury_lead.lifestyle_profile.lifestyle_score
        investment_score = luxury_lead.investment_capacity.investment_capacity_score

        # Buying signal score
        buying_signal_scores = {
            LuxuryBuyingSignal.IMMEDIATE: 100,
            LuxuryBuyingSignal.ACTIVE: 80,
            LuxuryBuyingSignal.CONSIDERING: 60,
            LuxuryBuyingSignal.INVESTOR: 70,
            LuxuryBuyingSignal.FUTURE: 40
        }
        buying_score = buying_signal_scores.get(luxury_lead.buying_signal, 50)

        # Competitive intelligence score
        competitive_score = min(
            luxury_lead.competitive_intel.referral_source_quality +
            (100 - luxury_lead.competitive_intel.price_sensitivity) * 0.5,
            100
        )

        # Weighted final score
        master_score = (
            net_worth_score * self.scoring_weights["net_worth_indicators"] +
            lifestyle_score * self.scoring_weights["lifestyle_profile"] +
            investment_score * self.scoring_weights["investment_capacity"] +
            buying_score * self.scoring_weights["buying_signals"] +
            competitive_score * self.scoring_weights["competitive_intel"]
        )

        return min(master_score, 100)

    def _determine_qualification_status(self, luxury_lead: LuxuryLead) -> str:
        """Determine lead qualification status"""

        score = luxury_lead.overall_luxury_score
        wealth_tier = luxury_lead.wealth_tier

        if score >= 85 and wealth_tier in [WealthTier.ULTRA_UHNW, WealthTier.BILLIONAIRE]:
            return "ultra_premium"
        elif score >= 75 and wealth_tier in [WealthTier.UHNW, WealthTier.ULTRA_UHNW, WealthTier.BILLIONAIRE]:
            return "premium"
        elif score >= 65 and wealth_tier in [WealthTier.AFFLUENT, WealthTier.UHNW]:
            return "qualified"
        else:
            return "pending"

    def _estimate_commission_potential(self, luxury_lead: LuxuryLead) -> float:
        """Estimate commission potential for lead"""

        # Base commission estimate from buying budget
        estimated_budget = luxury_lead.investment_capacity.estimated_buying_budget
        if estimated_budget == 0:
            # Estimate from wealth tier
            wealth_tier_budgets = {
                WealthTier.MASS_AFFLUENT: 200_000,
                WealthTier.AFFLUENT: 800_000,
                WealthTier.UHNW: 2_500_000,
                WealthTier.ULTRA_UHNW: 8_000_000,
                WealthTier.BILLIONAIRE: 20_000_000
            }
            estimated_budget = wealth_tier_budgets.get(luxury_lead.wealth_tier, 500_000)

        # Commission rate based on service level and qualification
        commission_rates = {
            "ultra_premium": 0.040,  # 4.0%
            "premium": 0.038,        # 3.8%
            "qualified": 0.035,      # 3.5%
            "pending": 0.030         # 3.0%
        }

        commission_rate = commission_rates.get(luxury_lead.qualification_status, 0.030)

        # Adjust for buying signal urgency
        signal_multipliers = {
            LuxuryBuyingSignal.IMMEDIATE: 1.0,
            LuxuryBuyingSignal.ACTIVE: 0.8,
            LuxuryBuyingSignal.CONSIDERING: 0.5,
            LuxuryBuyingSignal.INVESTOR: 0.7,
            LuxuryBuyingSignal.FUTURE: 0.3
        }

        probability_multiplier = signal_multipliers.get(luxury_lead.buying_signal, 0.5)

        return estimated_budget * commission_rate * probability_multiplier

    def _recommend_service_level(self, luxury_lead: LuxuryLead) -> str:
        """Recommend appropriate service level"""

        score = luxury_lead.overall_luxury_score
        wealth_tier = luxury_lead.wealth_tier
        lifestyle_expectations = luxury_lead.lifestyle_profile.service_level_expectations

        if (score >= 80 and wealth_tier in [WealthTier.ULTRA_UHNW, WealthTier.BILLIONAIRE] or
            lifestyle_expectations == "white_glove"):
            return "white_glove"
        elif score >= 65 and wealth_tier in [WealthTier.UHNW, WealthTier.ULTRA_UHNW]:
            return "premium"
        else:
            return "standard"

    @cached(ttl=1800, key_prefix="luxury_lead_batch")
    async def score_lead_batch(self, leads_data: List[Dict[str, Any]]) -> List[LuxuryLead]:
        """Score multiple leads efficiently"""

        scored_leads = []

        # Process leads in batches for efficiency
        batch_size = 10
        for i in range(0, len(leads_data), batch_size):
            batch = leads_data[i:i + batch_size]

            # Process batch concurrently
            tasks = [self.score_luxury_lead(lead_data) for lead_data in batch]
            batch_results = await asyncio.gather(*tasks)

            scored_leads.extend(batch_results)

        return scored_leads

    def generate_lead_insights_summary(self, luxury_leads: List[LuxuryLead]) -> Dict[str, Any]:
        """Generate summary insights from luxury lead analysis"""

        if not luxury_leads:
            return {}

        # Qualification distribution
        qualification_dist = {}
        for lead in luxury_leads:
            qual = lead.qualification_status
            qualification_dist[qual] = qualification_dist.get(qual, 0) + 1

        # Wealth tier distribution
        wealth_dist = {}
        for lead in luxury_leads:
            tier = lead.wealth_tier.value
            wealth_dist[tier] = wealth_dist.get(tier, 0) + 1

        # Average scores
        avg_luxury_score = sum(lead.overall_luxury_score for lead in luxury_leads) / len(luxury_leads)
        total_commission_potential = sum(lead.commission_potential for lead in luxury_leads)

        # Top leads
        top_leads = sorted(luxury_leads, key=lambda x: x.overall_luxury_score, reverse=True)[:5]

        return {
            "total_leads_analyzed": len(luxury_leads),
            "qualification_distribution": qualification_dist,
            "wealth_tier_distribution": wealth_dist,
            "average_luxury_score": avg_luxury_score,
            "total_commission_potential": total_commission_potential,
            "top_leads": [
                {
                    "lead_id": lead.lead_id,
                    "score": lead.overall_luxury_score,
                    "qualification": lead.qualification_status,
                    "commission_potential": lead.commission_potential
                }
                for lead in top_leads
            ]
        }


# Example usage and testing functions

def create_sample_luxury_lead_data() -> Dict[str, Any]:
    """Create sample luxury lead data for testing"""
    return {
        "lead_id": "LUX-TEST-001",
        "contact_info": {
            "email": "ceo@techcorp.com",
            "phone": "+1-512-555-0123",
            "address": "123 West Lake Hills Dr, Austin, TX 78746"
        },
        "source": "luxury_website",
        "profession": "CEO",
        "company": "Tech Corporation",
        "property_search_history": [
            {
                "date": datetime.now().isoformat(),
                "min_price": 1_500_000,
                "max_price": 3_500_000,
                "location": "West Lake Hills",
                "property_type": "luxury_home",
                "amenities": ["pool", "wine_cellar", "home_theater", "guest_house"]
            },
            {
                "date": (datetime.now() - timedelta(days=2)).isoformat(),
                "min_price": 2_000_000,
                "max_price": 4_000_000,
                "location": "Tarrytown",
                "property_type": "estate",
                "amenities": ["waterfront", "tennis_court", "spa", "private_dock"]
            }
        ],
        "communication_history": [
            {
                "date": datetime.now().isoformat(),
                "content": "I'm looking for a luxury property in West Lake Hills with good investment potential. We're interested in properties with strong appreciation potential and tax benefits. Budget is flexible for the right opportunity.",
                "type": "email"
            },
            {
                "date": (datetime.now() - timedelta(days=1)).isoformat(),
                "content": "Can you provide a detailed analysis of the luxury market trends and cap rates for investment properties in the area? We're also interested in 1031 exchange opportunities.",
                "type": "phone"
            }
        ]
    }


async def test_luxury_scoring_engine():
    """Test the luxury lead scoring engine"""

    # Initialize engine
    engine = LuxuryLeadScoringEngine()

    # Create sample lead data
    sample_lead = create_sample_luxury_lead_data()

    # Score the lead
    luxury_lead = await engine.score_luxury_lead(sample_lead)

    print(f"Luxury Lead Analysis Results:")
    print(f"Lead ID: {luxury_lead.lead_id}")
    print(f"Wealth Tier: {luxury_lead.wealth_tier.value}")
    print(f"Overall Luxury Score: {luxury_lead.overall_luxury_score:.1f}/100")
    print(f"Qualification Status: {luxury_lead.qualification_status}")
    print(f"Commission Potential: ${luxury_lead.commission_potential:,.0f}")
    print(f"Recommended Service Level: {luxury_lead.recommended_service_level}")
    print(f"Estimated Net Worth: ${luxury_lead.net_worth_indicators.estimated_net_worth:,.0f}")
    print(f"Investment Capacity Score: {luxury_lead.investment_capacity.investment_capacity_score:.1f}/100")
    print(f"Lifestyle Score: {luxury_lead.lifestyle_profile.lifestyle_score:.1f}/100")

    return luxury_lead


if __name__ == "__main__":
    asyncio.run(test_luxury_scoring_engine())