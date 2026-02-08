"""
Jorge's Global Market Intelligence System - International Expansion Engine
Multi-market analytics and intelligence for worldwide real estate operations

This module provides:
- Multi-market analytics for international expansion
- Currency conversion and localization services
- Regional regulatory compliance and adaptation
- Cultural adaptation for bot personalities
- International payment processing integration
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MarketRegion(Enum):
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    LATIN_AMERICA = "latin_america"
    MIDDLE_EAST_AFRICA = "middle_east_africa"


class MarketMaturity(Enum):
    EMERGING = "emerging"  # New markets with growth potential
    DEVELOPING = "developing"  # Markets in growth phase
    MATURE = "mature"  # Established markets
    SATURATED = "saturated"  # Highly competitive markets


class CulturalProfile(Enum):
    DIRECT = "direct"  # Direct communication style (US, Germany)
    RELATIONSHIP_FOCUSED = "relationship"  # Relationship-first (Japan, China)
    FORMAL = "formal"  # Formal approach (UK, France)
    COLLABORATIVE = "collaborative"  # Team-oriented (Scandinavia)


@dataclass
class CurrencyConfig:
    """Currency configuration for international markets"""

    currency_code: str
    symbol: str
    decimal_places: int = 2
    exchange_rate: float = 1.0  # Relative to USD
    last_updated: datetime = field(default_factory=datetime.now)
    local_formatting: str = "{symbol}{amount}"


@dataclass
class RegulatoryFramework:
    """Regional regulatory compliance framework"""

    region: MarketRegion
    privacy_laws: List[str]
    real_estate_regulations: Dict[str, Any]
    data_residency_requirements: List[str]
    licensing_requirements: Dict[str, Any]
    commission_regulations: Dict[str, Any]
    marketing_restrictions: List[str]
    consumer_protection_laws: List[str]


@dataclass
class CulturalAdaptation:
    """Cultural adaptation configuration for bots"""

    cultural_profile: CulturalProfile
    communication_style: str
    greeting_preferences: List[str]
    negotiation_approach: str
    time_sensitivity: str  # high, medium, low
    hierarchy_respect: bool
    personal_space_importance: str
    gift_giving_customs: bool
    business_card_protocol: str


@dataclass
class MarketConfig:
    """Complete market configuration for international deployment"""

    market_id: str
    country_code: str
    region: MarketRegion
    market_maturity: MarketMaturity
    currency_config: CurrencyConfig
    regulatory_framework: RegulatoryFramework
    cultural_adaptation: CulturalAdaptation
    local_languages: List[str]
    timezone: str
    business_hours: Dict[str, str]
    market_characteristics: Dict[str, Any]
    competitive_landscape: Dict[str, Any]
    expansion_priority: int = 1  # 1=highest, 5=lowest


@dataclass
class MarketAnalysis:
    """Market analysis results for expansion decisions"""

    market_config: MarketConfig
    market_size: float  # Total addressable market
    competition_intensity: float  # 0-1 scale
    entry_barriers: List[str]
    growth_potential: float  # Expected annual growth
    roi_projection: float  # Expected ROI
    risk_factors: List[str]
    success_probability: float  # 0-1 scale
    recommended_strategy: str
    investment_required: float
    timeline_to_profitability: int  # months


class GlobalMarketIntelligence:
    """
    Jorge's Global Market Intelligence System
    Provides international expansion intelligence and market adaptation
    """

    def __init__(self):
        self.market_configs: Dict[str, MarketConfig] = {}
        self.exchange_rates: Dict[str, float] = {}
        self.market_analyses: Dict[str, MarketAnalysis] = {}
        self._initialize_default_markets()

    def _initialize_default_markets(self):
        """Initialize default market configurations for major regions"""

        # United States (baseline market)
        us_market = MarketConfig(
            market_id="us",
            country_code="US",
            region=MarketRegion.NORTH_AMERICA,
            market_maturity=MarketMaturity.MATURE,
            currency_config=CurrencyConfig(currency_code="USD", symbol="$", decimal_places=2, exchange_rate=1.0),
            regulatory_framework=RegulatoryFramework(
                region=MarketRegion.NORTH_AMERICA,
                privacy_laws=["CCPA", "GLBA"],
                real_estate_regulations={
                    "fair_housing_act": True,
                    "respa_compliance": True,
                    "mls_access_required": True,
                },
                data_residency_requirements=["us-east-1", "us-west-2"],
                licensing_requirements={"real_estate_license": "state_specific", "continuing_education": "required"},
                commission_regulations={
                    "max_commission": None,
                    "disclosure_required": True,
                    "jorge_6_percent_allowed": True,
                },
                marketing_restrictions=["spam_compliance", "do_not_call"],
                consumer_protection_laws=["truth_in_advertising"],
            ),
            cultural_adaptation=CulturalAdaptation(
                cultural_profile=CulturalProfile.DIRECT,
                communication_style="direct_confrontational",  # Jorge's original style
                greeting_preferences=["Hi", "Hello", "Good morning"],
                negotiation_approach="aggressive_value_focused",
                time_sensitivity="high",
                hierarchy_respect=False,
                personal_space_importance="medium",
                gift_giving_customs=False,
                business_card_protocol="informal",
            ),
            local_languages=["en"],
            timezone="America/New_York",
            business_hours={"open": "09:00", "close": "18:00"},
            market_characteristics={
                "avg_home_price": 400000,
                "transaction_volume_annual": 6000000,
                "agent_count": 2000000,
                "mls_penetration": 0.95,
            },
            competitive_landscape={
                "major_players": ["Zillow", "Realtor.com", "Compass"],
                "ai_adoption": 0.25,
                "market_share_available": 0.15,
            },
            expansion_priority=1,
        )
        self.market_configs["us"] = us_market

        # Canada
        canada_market = MarketConfig(
            market_id="ca",
            country_code="CA",
            region=MarketRegion.NORTH_AMERICA,
            market_maturity=MarketMaturity.MATURE,
            currency_config=CurrencyConfig(
                currency_code="CAD",
                symbol="C$",
                decimal_places=2,
                exchange_rate=0.74,  # CAD to USD
            ),
            regulatory_framework=RegulatoryFramework(
                region=MarketRegion.NORTH_AMERICA,
                privacy_laws=["PIPEDA"],
                real_estate_regulations={
                    "provincial_licensing": True,
                    "mls_system": "CREA",
                    "foreign_buyer_tax": "varies_by_province",
                },
                data_residency_requirements=["ca-central-1"],
                licensing_requirements={
                    "real_estate_license": "provincial_specific",
                    "continuing_education": "required",
                },
                commission_regulations={
                    "max_commission": None,
                    "disclosure_required": True,
                    "jorge_6_percent_allowed": True,
                },
                marketing_restrictions=["casl_compliance"],
                consumer_protection_laws=["consumer_protection_act"],
            ),
            cultural_adaptation=CulturalAdaptation(
                cultural_profile=CulturalProfile.COLLABORATIVE,
                communication_style="polite_direct",  # More polite than US
                greeting_preferences=["Hello", "Good morning", "Bonjour"],
                negotiation_approach="collaborative_value_focused",
                time_sensitivity="medium",
                hierarchy_respect=True,
                personal_space_importance="medium",
                gift_giving_customs=False,
                business_card_protocol="polite",
            ),
            local_languages=["en", "fr"],
            timezone="America/Toronto",
            business_hours={"open": "09:00", "close": "17:00"},
            market_characteristics={
                "avg_home_price": 650000,
                "transaction_volume_annual": 500000,
                "agent_count": 120000,
                "mls_penetration": 0.98,
            },
            competitive_landscape={
                "major_players": ["Realtor.ca", "Royal LePage", "RE/MAX"],
                "ai_adoption": 0.15,
                "market_share_available": 0.25,
            },
            expansion_priority=2,
        )
        self.market_configs["ca"] = canada_market

        # United Kingdom
        uk_market = MarketConfig(
            market_id="uk",
            country_code="GB",
            region=MarketRegion.EUROPE,
            market_maturity=MarketMaturity.MATURE,
            currency_config=CurrencyConfig(
                currency_code="GBP",
                symbol="£",
                decimal_places=2,
                exchange_rate=1.27,  # GBP to USD
            ),
            regulatory_framework=RegulatoryFramework(
                region=MarketRegion.EUROPE,
                privacy_laws=["UK_GDPR", "DPA_2018"],
                real_estate_regulations={
                    "estate_agent_licensing": True,
                    "property_portal_regulation": True,
                    "leasehold_regulations": True,
                },
                data_residency_requirements=["eu-west-2"],
                licensing_requirements={
                    "estate_agent_license": "not_required_but_regulated",
                    "professional_indemnity": "required",
                },
                commission_regulations={
                    "typical_commission": "1.0_to_3.5_percent",
                    "no_win_no_fee": "common",
                    "jorge_6_percent_challenging": True,
                },
                marketing_restrictions=["gdpr_consent", "property_misdescriptions_act"],
                consumer_protection_laws=["estate_agents_act"],
            ),
            cultural_adaptation=CulturalAdaptation(
                cultural_profile=CulturalProfile.FORMAL,
                communication_style="polite_reserved",  # Very different from Jorge's style
                greeting_preferences=["Good morning", "Good afternoon", "How do you do"],
                negotiation_approach="understated_professional",
                time_sensitivity="medium",
                hierarchy_respect=True,
                personal_space_importance="high",
                gift_giving_customs=False,
                business_card_protocol="formal",
            ),
            local_languages=["en"],
            timezone="Europe/London",
            business_hours={"open": "09:00", "close": "17:30"},
            market_characteristics={
                "avg_home_price": 280000,  # £
                "transaction_volume_annual": 1200000,
                "agent_count": 40000,
                "mls_penetration": 0.70,  # Different system - property portals
            },
            competitive_landscape={
                "major_players": ["Rightmove", "Zoopla", "OnTheMarket"],
                "ai_adoption": 0.20,
                "market_share_available": 0.18,
            },
            expansion_priority=3,
        )
        self.market_configs["uk"] = uk_market

        # Germany
        germany_market = MarketConfig(
            market_id="de",
            country_code="DE",
            region=MarketRegion.EUROPE,
            market_maturity=MarketMaturity.MATURE,
            currency_config=CurrencyConfig(
                currency_code="EUR",
                symbol="€",
                decimal_places=2,
                exchange_rate=1.09,  # EUR to USD
            ),
            regulatory_framework=RegulatoryFramework(
                region=MarketRegion.EUROPE,
                privacy_laws=["GDPR", "BDSG"],
                real_estate_regulations={
                    "makler_license": "required",
                    "widerruf_right": True,  # Right of withdrawal
                    "energieausweis": "required",  # Energy certificate
                },
                data_residency_requirements=["eu-central-1"],
                licensing_requirements={"makler_license": "required", "liability_insurance": "required"},
                commission_regulations={
                    "commission_split_law": "50_50_buyer_seller",
                    "max_commission": "7.14_percent_including_vat",
                    "jorge_6_percent_acceptable": True,
                },
                marketing_restrictions=["gdpr_strict_consent", "truthful_advertising"],
                consumer_protection_laws=["bgb", "consumer_protection"],
            ),
            cultural_adaptation=CulturalAdaptation(
                cultural_profile=CulturalProfile.DIRECT,
                communication_style="direct_formal",  # Direct but formal
                greeting_preferences=["Guten Tag", "Guten Morgen", "Hallo"],
                negotiation_approach="data_driven_systematic",
                time_sensitivity="high",
                hierarchy_respect=True,
                personal_space_importance="high",
                gift_giving_customs=False,
                business_card_protocol="formal",
            ),
            local_languages=["de"],
            timezone="Europe/Berlin",
            business_hours={"open": "09:00", "close": "18:00"},
            market_characteristics={
                "avg_home_price": 350000,  # €
                "transaction_volume_annual": 650000,
                "agent_count": 35000,
                "mls_penetration": 0.60,  # More fragmented
            },
            competitive_landscape={
                "major_players": ["ImmobilienScout24", "Immonet", "eBay Kleinanzeigen"],
                "ai_adoption": 0.12,
                "market_share_available": 0.22,
            },
            expansion_priority=4,
        )
        self.market_configs["de"] = germany_market

    async def analyze_international_market(self, country_code: str, deep_analysis: bool = True) -> MarketAnalysis:
        """
        Perform comprehensive analysis of international market for expansion
        """
        try:
            market_config = self.market_configs.get(country_code.lower())
            if not market_config:
                raise ValueError(f"Market configuration not found for country: {country_code}")

            # Calculate market metrics
            market_size = await self._calculate_market_size(market_config)
            competition_intensity = await self._assess_competition_intensity(market_config)
            entry_barriers = await self._identify_entry_barriers(market_config)
            growth_potential = await self._calculate_growth_potential(market_config)
            roi_projection = await self._project_roi(market_config)
            risk_factors = await self._identify_risk_factors(market_config)
            success_probability = await self._calculate_success_probability(market_config)

            # Generate strategic recommendations
            strategy = await self._recommend_entry_strategy(market_config, success_probability)
            investment_required = await self._estimate_investment_requirements(market_config)
            profitability_timeline = await self._estimate_profitability_timeline(market_config)

            analysis = MarketAnalysis(
                market_config=market_config,
                market_size=market_size,
                competition_intensity=competition_intensity,
                entry_barriers=entry_barriers,
                growth_potential=growth_potential,
                roi_projection=roi_projection,
                risk_factors=risk_factors,
                success_probability=success_probability,
                recommended_strategy=strategy,
                investment_required=investment_required,
                timeline_to_profitability=profitability_timeline,
            )

            # Store analysis
            self.market_analyses[country_code.lower()] = analysis

            logger.info(f"Completed market analysis for {country_code.upper()}")
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze market {country_code}: {str(e)}")
            raise

    async def _calculate_market_size(self, market_config: MarketConfig) -> float:
        """Calculate total addressable market size"""
        characteristics = market_config.market_characteristics
        avg_price = characteristics.get("avg_home_price", 0)
        annual_volume = characteristics.get("transaction_volume_annual", 0)
        jorge_commission = 0.06  # 6% commission rate

        # Total commission market size
        total_market_value = avg_price * annual_volume
        total_commission_pool = total_market_value * jorge_commission

        return total_commission_pool

    async def _assess_competition_intensity(self, market_config: MarketConfig) -> float:
        """Assess competition intensity in market (0-1 scale)"""
        landscape = market_config.competitive_landscape
        ai_adoption = landscape.get("ai_adoption", 0)
        major_players = len(landscape.get("major_players", []))

        # Higher AI adoption and more players = higher competition
        competition_score = (ai_adoption * 0.6) + (min(major_players / 10, 1) * 0.4)
        return min(competition_score, 1.0)

    async def _identify_entry_barriers(self, market_config: MarketConfig) -> List[str]:
        """Identify key entry barriers for the market"""
        barriers = []

        # Regulatory barriers
        if market_config.regulatory_framework.licensing_requirements.get("real_estate_license") == "required":
            barriers.append("Regulatory licensing requirements")

        # Cultural barriers
        if market_config.cultural_adaptation.cultural_profile != CulturalProfile.DIRECT:
            barriers.append("Cultural adaptation required for Jorge's methodology")

        # Language barriers
        if "en" not in market_config.local_languages:
            barriers.append("Language localization required")

        # Commission barriers
        commission_regs = market_config.regulatory_framework.commission_regulations
        if (
            commission_regs.get("jorge_6_percent_challenging")
            or commission_regs.get("jorge_6_percent_allowed") is False
        ):
            barriers.append("6% commission rate may face resistance")

        # Technology barriers
        if market_config.market_characteristics.get("mls_penetration", 0) < 0.8:
            barriers.append("Limited MLS penetration requires different data strategy")

        return barriers

    async def _calculate_growth_potential(self, market_config: MarketConfig) -> float:
        """Calculate market growth potential"""
        # Base growth on market maturity and AI adoption gap
        if market_config.market_maturity == MarketMaturity.EMERGING:
            base_growth = 0.25
        elif market_config.market_maturity == MarketMaturity.DEVELOPING:
            base_growth = 0.20
        elif market_config.market_maturity == MarketMaturity.MATURE:
            base_growth = 0.10
        else:  # SATURATED
            base_growth = 0.05

        # Factor in AI adoption gap (opportunity)
        ai_adoption = market_config.competitive_landscape.get("ai_adoption", 0)
        ai_opportunity = 1 - ai_adoption

        # Combined growth potential
        growth_potential = base_growth + (ai_opportunity * 0.15)
        return min(growth_potential, 0.40)  # Cap at 40%

    async def _project_roi(self, market_config: MarketConfig) -> float:
        """Project expected ROI for market entry"""
        market_size = await self._calculate_market_size(market_config)
        competition = await self._assess_competition_intensity(market_config)
        market_share_available = market_config.competitive_landscape.get("market_share_available", 0.1)

        # Potential revenue (conservative estimate)
        potential_revenue = market_size * market_share_available * (1 - competition * 0.5)

        # Estimated investment
        investment = await self._estimate_investment_requirements(market_config)

        # ROI calculation (simplified)
        if investment > 0:
            roi = (potential_revenue - investment) / investment
        else:
            roi = 0

        return max(roi, -1.0)  # Cap at -100% loss

    async def _identify_risk_factors(self, market_config: MarketConfig) -> List[str]:
        """Identify key risk factors for market entry"""
        risks = []

        # Regulatory risks
        if "GDPR" in market_config.regulatory_framework.privacy_laws:
            risks.append("Strict GDPR compliance requirements")

        # Currency risks
        if market_config.currency_config.currency_code != "USD":
            risks.append("Foreign exchange rate volatility")

        # Cultural risks
        if market_config.cultural_adaptation.communication_style != "direct_confrontational":
            risks.append("Jorge's confrontational style may not suit local culture")

        # Market risks
        if market_config.market_maturity == MarketMaturity.SATURATED:
            risks.append("Highly saturated market with intense competition")

        # Operational risks
        if market_config.region != MarketRegion.NORTH_AMERICA:
            risks.append("Distance and time zone challenges for support")

        return risks

    async def _calculate_success_probability(self, market_config: MarketConfig) -> float:
        """Calculate probability of successful market entry"""
        # Start with base probability
        success_prob = 0.5

        # Adjust based on market factors
        if market_config.region == MarketRegion.NORTH_AMERICA:
            success_prob += 0.2  # Familiar market

        if "en" in market_config.local_languages:
            success_prob += 0.15  # English language advantage

        if market_config.cultural_adaptation.cultural_profile == CulturalProfile.DIRECT:
            success_prob += 0.1  # Cultural fit

        competition = await self._assess_competition_intensity(market_config)
        success_prob -= competition * 0.3  # Competition penalty

        # Regulatory complexity penalty
        if len(market_config.regulatory_framework.privacy_laws) > 1:
            success_prob -= 0.1

        return max(min(success_prob, 1.0), 0.0)

    async def _recommend_entry_strategy(self, market_config: MarketConfig, success_prob: float) -> str:
        """Recommend market entry strategy"""
        if success_prob > 0.7:
            return "Direct market entry with full platform deployment"
        elif success_prob > 0.5:
            return "Partnership-based entry with local real estate firms"
        elif success_prob > 0.3:
            return "Pilot program with limited feature set"
        else:
            return "Market monitoring - not recommended for immediate entry"

    async def _estimate_investment_requirements(self, market_config: MarketConfig) -> float:
        """Estimate investment required for market entry"""
        base_investment = 500000  # Base platform setup

        # Localization costs
        if "en" not in market_config.local_languages:
            base_investment += 200000  # Translation and localization

        # Regulatory compliance costs
        if "GDPR" in market_config.regulatory_framework.privacy_laws:
            base_investment += 150000  # GDPR compliance

        # Cultural adaptation costs
        if market_config.cultural_adaptation.cultural_profile != CulturalProfile.DIRECT:
            base_investment += 100000  # Bot personality adaptation

        # Market development costs
        if market_config.market_maturity == MarketMaturity.EMERGING:
            base_investment += 300000  # Higher market development needed

        return base_investment

    async def _estimate_profitability_timeline(self, market_config: MarketConfig) -> int:
        """Estimate months to profitability"""
        base_timeline = 18  # 18 months baseline

        # Adjust based on market factors
        if market_config.market_maturity == MarketMaturity.EMERGING:
            base_timeline += 12
        elif market_config.market_maturity == MarketMaturity.SATURATED:
            base_timeline += 6

        if "en" not in market_config.local_languages:
            base_timeline += 6  # Language barrier delay

        competition = await self._assess_competition_intensity(market_config)
        base_timeline += int(competition * 12)  # Competition delay

        return base_timeline

    async def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Convert currency amounts with real-time exchange rates
        """
        try:
            if from_currency == to_currency:
                return amount

            # Get exchange rates (in production, this would connect to real exchange rate API)
            await self._update_exchange_rates()

            from_rate = self.exchange_rates.get(from_currency.upper(), 1.0)
            to_rate = self.exchange_rates.get(to_currency.upper(), 1.0)

            # Convert to USD first, then to target currency
            usd_amount = amount / from_rate
            converted_amount = usd_amount * to_rate

            return float(Decimal(str(converted_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        except Exception as e:
            logger.error(f"Currency conversion failed: {str(e)}")
            return amount

    async def _update_exchange_rates(self):
        """Update exchange rates from external API"""
        # Mock exchange rates - in production, this would fetch from real API
        self.exchange_rates.update(
            {"USD": 1.0, "CAD": 0.74, "GBP": 1.27, "EUR": 1.09, "AUD": 0.66, "JPY": 0.0067, "CHF": 1.08, "SEK": 0.095}
        )

    async def adapt_bot_personality(self, market_id: str, original_message: str) -> str:
        """
        Adapt bot personality and communication for local market
        """
        try:
            market_config = self.market_configs.get(market_id.lower())
            if not market_config:
                return original_message  # No adaptation if market not configured

            adaptation = market_config.cultural_adaptation

            # Apply cultural adaptations based on profile
            if adaptation.cultural_profile == CulturalProfile.FORMAL:
                # Make message more formal and polite
                adapted_message = await self._formalize_message(original_message, adaptation)
            elif adaptation.cultural_profile == CulturalProfile.RELATIONSHIP_FOCUSED:
                # Add relationship-building elements
                adapted_message = await self._relationalize_message(original_message, adaptation)
            elif adaptation.cultural_profile == CulturalProfile.COLLABORATIVE:
                # Make message more collaborative and inclusive
                adapted_message = await self._collaborate_message(original_message, adaptation)
            else:
                # Keep direct style but potentially tone down
                adapted_message = original_message

            return adapted_message

        except Exception as e:
            logger.error(f"Bot personality adaptation failed: {str(e)}")
            return original_message

    async def _formalize_message(self, message: str, adaptation: CulturalAdaptation) -> str:
        """Make message more formal for formal cultures"""
        # Replace casual greetings
        formal_message = message

        # Add polite language
        if "you should" in formal_message.lower():
            formal_message = formal_message.replace("you should", "you might consider")

        if "hey" in formal_message.lower():
            formal_message = formal_message.replace("hey", "hello")

        return formal_message

    async def _relationalize_message(self, message: str, adaptation: CulturalAdaptation) -> str:
        """Add relationship-building elements for relationship-focused cultures"""
        # Add relationship-building prefixes
        relationship_message = message

        if not any(greeting in message.lower() for greeting in ["how are", "hope you", "trust you"]):
            relationship_message = "I hope you're doing well. " + message

        return relationship_message

    async def _collaborate_message(self, message: str, adaptation: CulturalAdaptation) -> str:
        """Make message more collaborative for team-oriented cultures"""
        collaborative_message = message

        # Replace "I" with "we" where appropriate
        if "I recommend" in collaborative_message:
            collaborative_message = collaborative_message.replace("I recommend", "We recommend")

        return collaborative_message

    async def get_market_expansion_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get prioritized market expansion recommendations
        """
        try:
            recommendations = []

            for market_id, market_config in self.market_configs.items():
                if market_id == "us":  # Skip existing market
                    continue

                analysis = await self.analyze_international_market(market_id)

                recommendation = {
                    "market_id": market_id,
                    "country_code": market_config.country_code,
                    "market_name": market_config.market_characteristics.get("market_name", market_id.upper()),
                    "expansion_priority": market_config.expansion_priority,
                    "success_probability": analysis.success_probability,
                    "roi_projection": analysis.roi_projection,
                    "investment_required": analysis.investment_required,
                    "timeline_months": analysis.timeline_to_profitability,
                    "market_size": analysis.market_size,
                    "key_opportunities": self._extract_opportunities(analysis),
                    "main_challenges": analysis.entry_barriers[:3],  # Top 3 barriers
                    "recommended_strategy": analysis.recommended_strategy,
                }

                recommendations.append(recommendation)

            # Sort by priority and success probability
            recommendations.sort(key=lambda x: (x["expansion_priority"], -x["success_probability"]))

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate expansion recommendations: {str(e)}")
            return []

    def _extract_opportunities(self, analysis: MarketAnalysis) -> List[str]:
        """Extract key opportunities from market analysis"""
        opportunities = []

        if analysis.growth_potential > 0.15:
            opportunities.append(f"High growth potential: {analysis.growth_potential:.1%}")

        if analysis.competition_intensity < 0.3:
            opportunities.append("Low AI competition - early mover advantage")

        if analysis.market_config.market_characteristics.get("mls_penetration", 0) > 0.8:
            opportunities.append("High MLS penetration - easy data integration")

        if "en" in analysis.market_config.local_languages:
            opportunities.append("English language market - no localization needed")

        return opportunities[:3]  # Top 3 opportunities

    async def generate_global_dashboard(self) -> Dict[str, Any]:
        """
        Generate comprehensive global market intelligence dashboard
        """
        try:
            # Analyze all configured markets
            market_summaries = {}
            total_market_size = 0
            avg_success_probability = 0

            for market_id in self.market_configs:
                if market_id != "us":  # Skip home market
                    analysis = await self.analyze_international_market(market_id)
                    market_summaries[market_id] = {
                        "market_size": analysis.market_size,
                        "success_probability": analysis.success_probability,
                        "roi_projection": analysis.roi_projection,
                        "investment_required": analysis.investment_required,
                        "priority": analysis.market_config.expansion_priority,
                    }
                    total_market_size += analysis.market_size
                    avg_success_probability += analysis.success_probability

            if len(market_summaries) > 0:
                avg_success_probability /= len(market_summaries)

            # Get expansion recommendations
            expansion_recommendations = await self.get_market_expansion_recommendations()

            dashboard = {
                "global_overview": {
                    "total_international_market_size": total_market_size,
                    "markets_analyzed": len(market_summaries),
                    "average_success_probability": avg_success_probability,
                    "total_investment_required": sum(m["investment_required"] for m in market_summaries.values()),
                },
                "market_summaries": market_summaries,
                "expansion_recommendations": expansion_recommendations[:5],  # Top 5
                "currency_rates": self.exchange_rates,
                "regional_insights": await self._generate_regional_insights(),
                "global_trends": await self._identify_global_trends(),
                "generated_at": datetime.now().isoformat(),
            }

            return dashboard

        except Exception as e:
            logger.error(f"Failed to generate global dashboard: {str(e)}")
            return {}

    async def _generate_regional_insights(self) -> Dict[str, Any]:
        """Generate insights by geographic region"""
        regional_insights = {}

        for region in MarketRegion:
            region_markets = [config for config in self.market_configs.values() if config.region == region]

            if region_markets:
                insights = {
                    "market_count": len(region_markets),
                    "avg_market_maturity": self._calculate_avg_maturity(region_markets),
                    "cultural_complexity": self._assess_cultural_complexity(region_markets),
                    "regulatory_complexity": self._assess_regulatory_complexity(region_markets),
                    "expansion_recommendation": self._get_regional_recommendation(region_markets),
                }
                regional_insights[region.value] = insights

        return regional_insights

    def _calculate_avg_maturity(self, markets: List[MarketConfig]) -> str:
        """Calculate average market maturity for region"""
        maturity_scores = {
            MarketMaturity.EMERGING: 1,
            MarketMaturity.DEVELOPING: 2,
            MarketMaturity.MATURE: 3,
            MarketMaturity.SATURATED: 4,
        }

        if not markets:
            return "unknown"

        avg_score = sum(maturity_scores[m.market_maturity] for m in markets) / len(markets)

        if avg_score < 1.5:
            return "emerging"
        elif avg_score < 2.5:
            return "developing"
        elif avg_score < 3.5:
            return "mature"
        else:
            return "saturated"

    def _assess_cultural_complexity(self, markets: List[MarketConfig]) -> str:
        """Assess cultural adaptation complexity for region"""
        direct_count = sum(1 for m in markets if m.cultural_adaptation.cultural_profile == CulturalProfile.DIRECT)

        if direct_count == len(markets):
            return "low"
        elif direct_count > len(markets) / 2:
            return "medium"
        else:
            return "high"

    def _assess_regulatory_complexity(self, markets: List[MarketConfig]) -> str:
        """Assess regulatory complexity for region"""
        avg_privacy_laws = sum(len(m.regulatory_framework.privacy_laws) for m in markets) / len(markets)

        if avg_privacy_laws < 1.5:
            return "low"
        elif avg_privacy_laws < 2.5:
            return "medium"
        else:
            return "high"

    def _get_regional_recommendation(self, markets: List[MarketConfig]) -> str:
        """Get expansion recommendation for region"""
        avg_priority = sum(m.expansion_priority for m in markets) / len(markets)

        if avg_priority <= 2:
            return "high_priority"
        elif avg_priority <= 3:
            return "medium_priority"
        else:
            return "low_priority"

    async def _identify_global_trends(self) -> List[Dict[str, Any]]:
        """Identify global real estate and AI trends"""
        return [
            {
                "trend": "AI Adoption Acceleration",
                "description": "Real estate AI adoption growing 35% annually worldwide",
                "impact": "high",
                "opportunity": "First-mover advantage in emerging markets",
            },
            {
                "trend": "Remote Work Impact",
                "description": "Sustained impact on residential real estate preferences",
                "impact": "medium",
                "opportunity": "Suburban and rural market expansion",
            },
            {
                "trend": "Regulatory Harmonization",
                "description": "Cross-border real estate regulations becoming more standardized",
                "impact": "medium",
                "opportunity": "Easier international expansion",
            },
            {
                "trend": "PropTech Investment Growth",
                "description": "Global PropTech investment reaching record highs",
                "impact": "high",
                "opportunity": "Partnership and acquisition opportunities",
            },
        ]


# Global market intelligence instance
global_market_intelligence = GlobalMarketIntelligence()
