"""
Jorge's Rancho Cucamonga Market Configuration

This module contains all Rancho Cucamonga-specific configuration settings,
market data, regulatory compliance, and local expertise for Jorge's bots.
Replaces Rancho Cucamonga, CA market focus with comprehensive Rancho Cucamonga, CA
market intelligence and compliance.

Author: Claude Code Assistant
Created: 2026-01-25
Market Focus: Rancho Cucamonga, California (Inland Empire)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Union


class RanchoNeighborhood(Enum):
    """Rancho Cucamonga neighborhoods and surrounding areas"""

    ALTA_LOMA = "alta_loma"
    CENTRAL_RC = "central_rc"
    ETIWANDA = "etiwanda"
    VICTORIA_GARDENS = "victoria_gardens"
    TERRA_VISTA = "terra_vista"
    DAY_CREEK = "day_creek"
    NORTH_RC = "north_rc"
    SOUTH_RC = "south_rc"


class CaliforniaPriceRange(Enum):
    """California/Inland Empire price ranges"""

    ENTRY_LEVEL = "700k_700k"  # $700k-700k
    MID_MARKET = "700k_1_2m"  # $700k-1.2M
    LUXURY = "1_2m_plus"  # $1.2M+
    INVESTMENT = "multi_unit"  # Multi-unit/investment properties


@dataclass
class RanchoCucamongaMarketConfig:
    """Rancho Cucamonga-specific market configuration"""

    # ========== MARKET IDENTIFICATION ==========
    MARKET_NAME = "Rancho Cucamonga"
    STATE_CODE = "CA"
    COUNTY = "San Bernardino County"
    REGION = "Inland Empire"
    MLS_SYSTEM = "CRMLS"  # California Regional MLS

    # ========== PRICE RANGES (UPDATED FOR CALIFORNIA) ==========
    PRICE_RANGES = {
        "entry_level": {"min": 700000, "max": 700000, "description": "Starter homes and condos"},
        "mid_market": {"min": 700000, "max": 1200000, "description": "Family homes in good neighborhoods"},
        "luxury": {"min": 1200000, "max": 7000000, "description": "Premium homes with views and amenities"},
        "ultra_luxury": {"min": 7000000, "max": 12000000, "description": "Estate homes in Alta Loma foothills"},
    }

    # ========== KEY NEIGHBORHOODS ==========
    NEIGHBORHOODS = {
        "alta_loma": {
            "median_price": 1150000,
            "characteristics": ["Mountain views", "Excellent schools", "Large lots", "Quiet foothills"],
            "buyer_type": "Families, executives",
            "commute": "15 min to Ontario Airport, 45 min to LA",
        },
        "central_rc": {
            "median_price": 850000,
            "characteristics": ["Established community", "Shopping centers", "Good schools", "Family-friendly"],
            "buyer_type": "First-time buyers, families",
            "commute": "10 min to Victoria Gardens, 40 min to LA",
        },
        "etiwanda": {
            "median_price": 925000,
            "characteristics": ["Newer developments", "Award-winning schools", "Modern amenities"],
            "buyer_type": "Young families, professionals",
            "commute": "Close to freeways, 35 min to LA",
        },
        "victoria_gardens": {
            "median_price": 750000,
            "characteristics": ["Walkable lifestyle", "Shopping/dining", "Condos and townhomes"],
            "buyer_type": "Young professionals, downsizers",
            "commute": "Transit-oriented, 40 min to LA",
        },
        "terra_vista": {
            "median_price": 875000,
            "characteristics": ["Newer community", "Family-oriented", "Parks and recreation"],
            "buyer_type": "Growing families, professionals",
            "commute": "20 min to Ontario, 35 min to LA",
        },
        "day_creek": {
            "median_price": 825000,
            "characteristics": ["Master-planned", "Golf course community", "Resort-style amenities"],
            "buyer_type": "Affluent families, golf enthusiasts",
            "commute": "15 min to Victoria Gardens, 40 min to LA",
        },
    }

    # ========== CALIFORNIA REGULATORY COMPLIANCE ==========
    REGULATORY_FRAMEWORK = {
        "license_authority": "DRE",  # Department of Real Estate (not DRE)
        "license_authority_full": "California Department of Real Estate",
        "state_regulations": "California Civil Code",
        "fair_housing": "California Fair Employment and Housing Act (FEHA)",
        "disclosure_requirements": [
            "Natural Hazard Disclosure Statement",
            "Transfer Disclosure Statement",
            "Lead-Based Paint Disclosure",
            "Earthquake Safety Disclosure",
            "Fire Hazard Disclosure",
        ],
        "license_types": {
            "salesperson": "California Real Estate Salesperson License",
            "broker": "California Real Estate Broker License",
        },
    }

    # ========== MARKET DYNAMICS ==========
    MARKET_CHARACTERISTICS = {
        "primary_drivers": [
            "More affordable than Orange County",
            "Family-oriented suburban community",
            "Excellent schools (Alta Loma, Etiwanda districts)",
            "Growing tech/logistics job market",
            "Ontario International Airport proximity",
        ],
        "buyer_demographics": [
            "Young families seeking space and schools",
            "Tech professionals working remotely",
            "Orange County refugees seeking affordability",
            "Logistics/warehouse professionals",
            "Retirees seeking mountain views",
        ],
        "market_trends": {
            "inventory": "Moderate (2.5 months supply)",
            "appreciation": "6.2% annually",
            "days_on_market": "28 days average",
            "buyer_competition": "Moderate to high in desirable areas",
        },
    }

    # ========== LOCAL EXPERTISE TALKING POINTS ==========
    LOCAL_ADVANTAGES = {
        "vs_orange_county": [
            "Get 2x the house for your money",
            "Same mountain views, half the price",
            "Top-rated schools without OC property taxes",
            "15 minutes to Ontario Airport vs LAX traffic",
        ],
        "vs_los_angeles": [
            "Family-friendly suburbs vs urban density",
            "Actual parking and yard space",
            "Safe neighborhoods with community feel",
            "Better air quality in foothills",
        ],
        "investment_advantages": [
            "Strong rental demand from Ontario Airport workers",
            "Amazon/logistics hub employment growth",
            "ADU potential for rental income",
            "Path of progress toward mountain communities",
        ],
    }

    # ========== JORGE'S CALIFORNIA QUESTIONS ==========
    # Updated for California market and regulations
    SELLER_QUESTIONS_CA = {
        1: "What's got you thinking about selling in Rancho Cucamonga? Are you staying in the Inland Empire or heading somewhere else?",
        2: "If we could get your home sold in the next 30-45 days, would that timeline work for you?",
        3: "How's the condition of your home? Would you say it's move-in ready or might need some updates?",
        4: "What price would make you excited to sell and move forward?",
    }

    # ========== CALIFORNIA COMPLIANCE MESSAGING ==========
    COMPLIANCE_LANGUAGE = {
        "licensing_disclosure": "Licensed by the California Department of Real Estate",
        "equal_housing": "Equal Housing Opportunity - We comply with all California Fair Housing laws",
        "property_disclosures": "All California-required property disclosures will be provided",
        "representation": "We represent both buyers and sellers in accordance with California Real Estate Law",
    }


@dataclass
class JorgeRanchoConfig:
    """Enhanced Jorge configuration for Rancho Cucamonga market"""

    # ========== MARKET INTEGRATION ==========
    MARKET_CONFIG = RanchoCucamongaMarketConfig()

    # ========== ACTIVATION/DEACTIVATION TAGS (UNCHANGED) ==========
    ACTIVATION_TAGS = ["Needs Qualifying"]
    DEACTIVATION_TAGS = ["AI-Off", "Qualified", "Stop-Bot", "Seller-Qualified"]

    # ========== CALIFORNIA TEMPERATURE CLASSIFICATION ==========
    # Adjusted for California market dynamics
    HOT_SELLER_THRESHOLD = 1.0  # Still need all 4 questions
    WARM_SELLER_THRESHOLD = 0.75  # 3+ questions
    COLD_SELLER_THRESHOLD = 0.0

    # California-specific qualification criteria
    CA_HOT_SELLER_CRITERIA = {
        "questions_answered": 4,
        "timeline_acceptable": True,
        "price_realistic": True,  # Understands CA market values
        "condition_disclosed": True,
        "motivation_clear": True,
    }

    # ========== CALIFORNIA MESSAGING STYLE ==========
    # More relaxed, California-friendly approach
    CA_MESSAGING_STYLE = {
        "friendly_opener": [
            "Hi! I help folks in Rancho Cucamonga with their home sales.",
            "Hi there! Jorge here - I specialize in the Inland Empire market.",
            "Hello! I work with homeowners throughout Rancho Cucamonga.",
        ],
        "market_expertise": [
            "I know the Inland Empire market really well",
            "I work with homes from Alta Loma to Victoria Gardens",
            "I've helped families throughout San Bernardino County",
        ],
        "value_propositions": [
            "Get you top dollar in this market",
            "We know all the local buyer preferences",
            "Experts in California real estate regulations",
            "Strong connections with Inland Empire buyers",
        ],
    }

    # ========== INITIAL OUTREACH (TAG-ADDED) ==========
    INITIAL_OUTREACH_MESSAGES = [
        "Hi {name}, this is Jorge. I saw your home inquiry and can help you get clear on value and timing. What has you thinking about selling?",
        "Hi {name}, Jorge here. I work with Rancho Cucamonga sellers and can walk you through pricing and timing. What got you considering a move?",
        "Hi {name}, Jorge. I help homeowners in Rancho Cucamonga sell quickly and for strong prices. What would make selling worth it for you?",
    ]

    BUYER_INITIAL_OUTREACH_MESSAGES = [
        "Hi {name}, Jorge here! Looking to buy in Rancho Cucamonga? What's your budget range?",
        "Hey {name}, this is Jorge. I help buyers find homes in Rancho Cucamonga. What price range are you working with?",
        "Hi {name}! Jorge here. Excited to help you find a home in Rancho Cucamonga. What's your budget?",
    ]

    # ========== CALIFORNIA FOLLOW-UP TEMPLATES ==========
    CA_FOLLOW_UP_SEQUENCES = {
        "day_2": "Hi {name}! Just wanted to follow up about your home in {neighborhood}. The Inland Empire market is really active right now.",
        "day_5": "Hey {name}, have you had a chance to think about your home sale timeline? I'm seeing great results for {neighborhood} properties.",
        "day_10": "Hi {name}! The market in Rancho Cucamonga is still strong. Would you like an updated home value estimate?",
        "day_20": "Hey {name}, just checking in. If you're still considering selling in {neighborhood}, I'd love to help when you're ready.",
    }

    # ========== GHL CALIFORNIA INTEGRATION ==========
    CA_CUSTOM_FIELDS = {
        "ca_neighborhood": "rancho_neighborhood_field",
        "ca_price_range": "ca_price_range_field",
        "ca_buyer_type": "ca_buyer_type_field",
        "dre_compliance": "dre_compliance_field",
        "natural_hazards": "natural_hazards_field",
        "school_district": "school_district_field",
        "mountain_views": "mountain_views_field",
        "commute_preference": "commute_preference_field",
    }

    # ========== CALIFORNIA WORKFLOWS ==========
    CA_WORKFLOWS = {
        "hot_seller_ca": "jorge_ca_hot_seller_workflow",
        "warm_seller_ca": "jorge_ca_warm_seller_workflow",
        "dre_compliance": "california_compliance_workflow",
        "disclosure_delivery": "ca_disclosure_workflow",
    }

    # ========== PERFORMANCE METRICS (CA ADJUSTED) ==========
    CA_SUCCESS_METRICS = {
        "qualification_rate": 0.65,  # Slightly higher in CA market
        "hot_lead_rate": 0.18,  # More qualified buyers in CA
        "agent_handoff_rate": 0.22,  # Higher conversion
        "avg_home_value": 950000,  # Rancho Cucamonga median
        "days_to_close": 35,  # California average
    }


# ========== NEIGHBORHOOD-SPECIFIC CONFIGURATIONS ==========


class AltaLomaConfig:
    """Alta Loma specific configuration"""

    PRICE_RANGE = (900000, 2700000)
    KEY_FEATURES = ["Mountain views", "Large lots", "Top schools", "Quiet"]
    BUYER_PROFILE = "Families, executives seeking space and views"
    COMPETITION_LEVEL = "High - premium market"
    JORGE_ADVANTAGES = [
        "Deep knowledge of foothills properties",
        "Network of buyers seeking mountain views",
        "Experience with luxury home marketing",
        "Understanding of Alta Loma school district value",
    ]


class CentralRCConfig:
    """Central Rancho Cucamonga configuration"""

    PRICE_RANGE = (650000, 1100000)
    KEY_FEATURES = ["Established", "Shopping", "Schools", "Family-friendly"]
    BUYER_PROFILE = "First-time buyers, growing families"
    COMPETITION_LEVEL = "Moderate - steady market"
    JORGE_ADVANTAGES = [
        "First-time buyer expertise",
        "Knowledge of family neighborhoods",
        "School district navigation",
        "Move-up buyer network",
    ]


class EtiwandaConfig:
    """Etiwanda area configuration"""

    PRICE_RANGE = (700000, 1700000)
    KEY_FEATURES = ["Newer homes", "Award-winning schools", "Modern amenities"]
    BUYER_PROFILE = "Young families, professionals"
    COMPETITION_LEVEL = "High - desirable schools"
    JORGE_ADVANTAGES = [
        "New construction expertise",
        "Etiwanda school district knowledge",
        "Young family buyer network",
        "Modern home marketing strategies",
    ]


# ========== CALIFORNIA COMPLIANCE HELPERS ==========


class CaliforniaComplianceHelper:
    """Helper functions for California real estate compliance"""

    @staticmethod
    def get_required_disclosures(property_type: str, location: str) -> List[str]:
        """Get required California disclosures"""
        base_disclosures = [
            "Transfer Disclosure Statement",
            "Natural Hazard Disclosure Statement",
            "Lead-Based Paint Disclosure (if built before 1978)",
        ]

        # Rancho Cucamonga specific
        if "rancho" in location.lower():
            base_disclosures.extend(
                [
                    "Earthquake Safety Disclosure",
                    "Fire Hazard Disclosure",
                    "Airport Proximity Disclosure (Ontario Airport)",
                ]
            )

        return base_disclosures

    @staticmethod
    def format_dre_disclaimer() -> str:
        """Standard DRE disclaimer"""
        return "Licensed by the California Department of Real Estate. Equal Housing Opportunity."

    @staticmethod
    def validate_california_price(price: int, neighborhood: str) -> Dict[str, Union[bool, str]]:
        """Validate price against California market data"""
        neighborhood_ranges = {
            "alta_loma": (900000, 2700000),
            "central_rc": (650000, 1100000),
            "etiwanda": (700000, 1700000),
            "victoria_gardens": (600000, 900000),
        }

        range_min, range_max = neighborhood_ranges.get(neighborhood.lower(), (700000, 7000000))

        if range_min <= price <= range_max:
            return {"valid": True, "message": "Price within market range"}
        elif price < range_min:
            return {"valid": False, "message": f"Below market range for {neighborhood}"}
        else:
            return {"valid": False, "message": f"Above typical range for {neighborhood}"}


# ========== EXPORT CONFIGURATION ==========

# Create global configuration instance
rancho_config = JorgeRanchoConfig()

# Export commonly used values
RANCHO_MARKET_NAME = rancho_config.MARKET_CONFIG.MARKET_NAME
RANCHO_STATE = rancho_config.MARKET_CONFIG.STATE_CODE
RANCHO_NEIGHBORHOODS = rancho_config.MARKET_CONFIG.NEIGHBORHOODS
RANCHO_PRICE_RANGES = rancho_config.MARKET_CONFIG.PRICE_RANGES
CALIFORNIA_QUESTIONS = rancho_config.MARKET_CONFIG.SELLER_QUESTIONS_CA
CALIFORNIA_COMPLIANCE = rancho_config.MARKET_CONFIG.REGULATORY_FRAMEWORK

__all__ = [
    "JorgeRanchoConfig",
    "RanchoCucamongaMarketConfig",
    "RanchoNeighborhood",
    "CaliforniaPriceRange",
    "AltaLomaConfig",
    "CentralRCConfig",
    "EtiwandaConfig",
    "CaliforniaComplianceHelper",
    "rancho_config",
    "RANCHO_MARKET_NAME",
    "RANCHO_STATE",
    "RANCHO_NEIGHBORHOODS",
    "RANCHO_PRICE_RANGES",
    "CALIFORNIA_QUESTIONS",
    "CALIFORNIA_COMPLIANCE",
]
