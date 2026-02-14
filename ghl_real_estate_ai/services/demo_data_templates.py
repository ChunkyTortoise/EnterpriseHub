"""
Jorge's Real Estate AI Platform - Professional Demo Data Templates
Realistic lead, property, and conversation templates for client demonstrations
Version: 2.0.0
"""

from enum import Enum
from typing import Any, Dict, List


class DemoScenario(Enum):
    """Professional client demonstration scenarios"""

    LUXURY_AGENT = "luxury_agent"
    MID_MARKET = "mid_market"
    FIRST_TIME_BUYER = "first_time_buyer"
    INVESTOR_FOCUSED = "investor_focused"
    HIGH_VOLUME = "high_volume"


class DemoDataTemplates:
    """Professional demo data templates for realistic client presentations"""

    @staticmethod
    def get_lead_templates(scenario: DemoScenario) -> List[Dict[str, Any]]:
        """Get realistic lead templates based on market scenario"""

        luxury_templates = [
            {
                "name": "Patricia Williams",
                "source": "High-end Referral",
                "budget_min": 2000000,
                "budget_max": 3500000,
                "location": "Beverly Hills / Bel Air",
                "urgency": "high",
                "status": "qualified",
                "temperature": "hot",
                "conversion_prob": 0.85,
                "notes": "Relocating from Manhattan for tax reasons. Needs luxury amenities, ocean view preferred. Timeline: 60 days.",
            },
            {
                "name": "Robert Chen",
                "source": "Luxury Portal",
                "budget_min": 1500000,
                "budget_max": 2200000,
                "location": "Manhattan Beach / Hermosa Beach",
                "urgency": "medium",
                "status": "qualified",
                "temperature": "warm",
                "conversion_prob": 0.72,
                "notes": "Tech executive upgrading from condo to house. Specific requirements for home office and smart home features.",
            },
            {
                "name": "Michael & Sarah Thompson",
                "source": "Past Client Referral",
                "budget_min": 2500000,
                "budget_max": 4000000,
                "location": "Malibu / Pacific Palisades",
                "urgency": "low",
                "status": "pre-qualified",
                "temperature": "warm",
                "conversion_prob": 0.68,
                "notes": "Empty nesters selling $6M estate, downsizing but want luxury. No timeline pressure.",
            },
            {
                "name": "David Martinez",
                "source": "Social Media",
                "budget_min": 1800000,
                "budget_max": 2500000,
                "location": "West Hollywood / Beverly Hills",
                "urgency": "high",
                "status": "qualified",
                "temperature": "hot",
                "conversion_prob": 0.82,
                "notes": "Entertainment industry client. Needs quick close, cash buyer, modern architecture preferred.",
            },
            {
                "name": "Jennifer Lake",
                "source": "Luxury Expo",
                "budget_min": 3000000,
                "budget_max": 5000000,
                "location": "Bel Air / Holmby Hills",
                "urgency": "medium",
                "status": "qualified",
                "temperature": "warm",
                "conversion_prob": 0.75,
                "notes": "Investment banker moving from London. Requires private school districts and security features.",
            },
        ]

        mid_market_templates = [
            {
                "name": "Alex Johnson",
                "source": "Zillow Lead",
                "budget_min": 350000,
                "budget_max": 450000,
                "location": "Upland / Fontana",
                "urgency": "medium",
                "status": "qualified",
                "temperature": "warm",
                "conversion_prob": 0.65,
                "notes": "First-time buyer, pre-approved for $400K. Looking for 3BR/2BA with good schools.",
            },
            {
                "name": "Maria Gonzalez",
                "source": "Facebook Lead",
                "budget_min": 280000,
                "budget_max": 380000,
                "location": "Rancho Cucamonga Metro / Ontario",
                "urgency": "high",
                "status": "qualified",
                "temperature": "hot",
                "conversion_prob": 0.78,
                "notes": "Relocating for work, needs to close within 45 days. Has sold previous home in Dallas.",
            },
            {
                "name": "Tim & Rachel Foster",
                "source": "Open House",
                "budget_min": 480000,
                "budget_max": 600000,
                "location": "Georgetown / Chino",
                "urgency": "low",
                "status": "pre-qualified",
                "temperature": "lukewarm",
                "conversion_prob": 0.45,
                "notes": "Growing family, need larger home. Current lease expires in 8 months.",
            },
            {
                "name": "Kevin Park",
                "source": "Google Ads",
                "budget_min": 320000,
                "budget_max": 420000,
                "location": "East Rancho Cucamonga / Del Valle",
                "urgency": "medium",
                "status": "qualified",
                "temperature": "warm",
                "conversion_prob": 0.62,
                "notes": "Tech worker, wants modern finishes and short commute to downtown Rancho Cucamonga.",
            },
            {
                "name": "Ashley Brown",
                "source": "Referral",
                "budget_min": 390000,
                "budget_max": 520000,
                "location": "North Rancho Cucamonga / Upland",
                "urgency": "high",
                "status": "qualified",
                "temperature": "hot",
                "conversion_prob": 0.71,
                "notes": "Divorce situation, needs to find new home quickly. Strong income, clean credit.",
            },
        ]

        first_time_templates = [
            {
                "name": "Emma Rodriguez",
                "source": "First-Time Buyer Program",
                "budget_min": 250000,
                "budget_max": 320000,
                "location": "Tempe / Chandler",
                "urgency": "medium",
                "status": "pre-qualified",
                "temperature": "warm",
                "conversion_prob": 0.58,
                "notes": "26 years old, teacher. Needs education about process and down payment assistance programs.",
            },
            {
                "name": "Jake & Lisa Mitchell",
                "source": "Mortgage Broker Referral",
                "budget_min": 280000,
                "budget_max": 350000,
                "location": "Gilbert / Mesa",
                "urgency": "low",
                "status": "exploring",
                "temperature": "lukewarm",
                "conversion_prob": 0.42,
                "notes": "Young couple, currently renting. Want to understand buying process before committing.",
            },
            {
                "name": "Carlos Mendoza",
                "source": "HomeReady Program",
                "budget_min": 220000,
                "budget_max": 290000,
                "location": "Phoenix / Glendale",
                "urgency": "high",
                "status": "qualified",
                "temperature": "warm",
                "conversion_prob": 0.65,
                "notes": "Military veteran, using VA loan. Needs move-in ready condition, has timeline pressure.",
            },
            {
                "name": "Samantha White",
                "source": "Online Search",
                "budget_min": 300000,
                "budget_max": 380000,
                "location": "Scottsdale / Paradise Valley",
                "urgency": "medium",
                "status": "pre-qualified",
                "temperature": "warm",
                "conversion_prob": 0.55,
                "notes": "Nurse practitioner, stable income. Wants condo or townhome with low maintenance.",
            },
            {
                "name": "Jordan Taylor",
                "source": "Social Media",
                "budget_min": 260000,
                "budget_max": 330000,
                "location": "North Phoenix / Deer Valley",
                "urgency": "low",
                "status": "exploring",
                "temperature": "lukewarm",
                "conversion_prob": 0.38,
                "notes": "Recent college graduate, good job. Needs extensive education about process and costs.",
            },
        ]

        investor_templates = [
            {
                "name": "Richard Hayes",
                "source": "Investment Network",
                "budget_min": 500000,
                "budget_max": 800000,
                "location": "Dallas Metro / Plano",
                "urgency": "high",
                "status": "qualified",
                "temperature": "hot",
                "conversion_prob": 0.82,
                "notes": "Experienced investor, cash buyer. Looking for rental properties with 8%+ cap rates.",
            },
            {
                "name": "PropertyMax LLC",
                "source": "Commercial Referral",
                "budget_min": 1000000,
                "budget_max": 2000000,
                "location": "Atlanta / Gwinnett County",
                "urgency": "medium",
                "status": "qualified",
                "temperature": "warm",
                "conversion_prob": 0.75,
                "notes": "Portfolio acquisition, looking for 10-20 unit apartment buildings. 1031 exchange buyer.",
            },
            {
                "name": "Susan Kim",
                "source": "REIA Meeting",
                "budget_min": 300000,
                "budget_max": 500000,
                "location": "Rancho Cucamonga / San Antonio Corridor",
                "urgency": "low",
                "status": "exploring",
                "temperature": "lukewarm",
                "conversion_prob": 0.48,
                "notes": "New investor, has capital but needs education on market analysis and property evaluation.",
            },
            {
                "name": "Global Investment Partners",
                "source": "International Referral",
                "budget_min": 2000000,
                "budget_max": 5000000,
                "location": "Miami / Fort Lauderdale",
                "urgency": "medium",
                "status": "qualified",
                "temperature": "warm",
                "conversion_prob": 0.78,
                "notes": "International fund, USD hedge strategy. Needs bulk purchase opportunities.",
            },
            {
                "name": "Mark Stevens",
                "source": "Past Client",
                "budget_min": 600000,
                "budget_max": 900000,
                "location": "Phoenix Metro",
                "urgency": "high",
                "status": "qualified",
                "temperature": "hot",
                "conversion_prob": 0.85,
                "notes": "Repeat investor client, owns 15 properties. Looking to expand portfolio in growth markets.",
            },
        ]

        high_volume_templates = [
            {
                "name": "Multiple Active Leads",
                "source": "Various Sources",
                "budget_min": 200000,
                "budget_max": 600000,
                "location": "Metro Area Wide",
                "urgency": "mixed",
                "status": "various",
                "temperature": "mixed",
                "conversion_prob": 0.22,
                "notes": "High-volume operation with leads in all stages of qualification and nurturing.",
            }
        ]

        templates = {
            DemoScenario.LUXURY_AGENT: luxury_templates,
            DemoScenario.MID_MARKET: mid_market_templates,
            DemoScenario.FIRST_TIME_BUYER: first_time_templates,
            DemoScenario.INVESTOR_FOCUSED: investor_templates,
            DemoScenario.HIGH_VOLUME: high_volume_templates,
        }

        return templates.get(scenario, mid_market_templates)

    @staticmethod
    def get_property_templates(scenario: DemoScenario) -> List[Dict[str, Any]]:
        """Get realistic property templates for demonstrations"""

        luxury_properties = [
            {
                "address": "1247 Benedict Canyon Dr, Beverly Hills, CA",
                "price": 2850000,
                "bedrooms": 5,
                "bathrooms": 6,
                "sqft": 4200,
                "type": "Single Family",
                "neighborhood": "Benedict Canyon",
                "features": ["Ocean view", "Wine cellar", "Home theater", "Pool/Spa", "Smart home"],
                "status": "Active",
                "notes": "Recently renovated, celebrity neighborhood",
            },
            {
                "address": "456 Ocean Avenue, Manhattan Beach, CA",
                "price": 3200000,
                "bedrooms": 4,
                "bathrooms": 4,
                "sqft": 3800,
                "type": "Beach House",
                "neighborhood": "Manhattan Beach",
                "features": ["Ocean front", "Private beach access", "Rooftop deck", "3-car garage"],
                "status": "Active",
                "notes": "Rare beachfront opportunity",
            },
        ]

        mid_market_properties = [
            {
                "address": "123 Oak Hill Drive, Upland, CA",
                "price": 425000,
                "bedrooms": 4,
                "bathrooms": 3,
                "sqft": 2400,
                "type": "Single Family",
                "neighborhood": "Upland",
                "features": ["New construction", "Open floor plan", "2-car garage", "Large yard"],
                "status": "Active",
                "notes": "Excellent schools, move-in ready",
            },
            {
                "address": "789 Maple Street, Fontana, CA",
                "price": 380000,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 2100,
                "type": "Single Family",
                "neighborhood": "Fontana",
                "features": ["Updated kitchen", "Hardwood floors", "Covered patio", "Corner lot"],
                "status": "Active",
                "notes": "Great starter home in desirable area",
            },
        ]

        first_time_properties = [
            {
                "address": "567 Desert Rose Lane, Tempe, AZ",
                "price": 295000,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 1650,
                "type": "Townhome",
                "neighborhood": "Tempe",
                "features": ["HOA amenities", "Attached garage", "Patio", "Low maintenance"],
                "status": "Active",
                "notes": "Perfect for first-time buyers, great schools nearby",
            },
            {
                "address": "234 Sunshine Court, Gilbert, AZ",
                "price": 315000,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 1750,
                "type": "Single Family",
                "neighborhood": "Gilbert",
                "features": ["Newer build", "Energy efficient", "Community pool", "Playground"],
                "status": "Active",
                "notes": "Family-friendly community, excellent value",
            },
        ]

        investor_properties = [
            {
                "address": "Investment Property Portfolio - Dallas Metro",
                "price": 750000,
                "bedrooms": 12,
                "bathrooms": 8,
                "sqft": 8400,
                "type": "4-Unit Building",
                "neighborhood": "Plano",
                "features": ["Fully occupied", "8.2% cap rate", "Recent renovations", "Professional management"],
                "status": "Active",
                "notes": "Strong rental market, excellent cash flow",
            },
            {
                "address": "567 Investment Lane, Atlanta, GA",
                "price": 485000,
                "bedrooms": 6,
                "bathrooms": 4,
                "sqft": 4200,
                "type": "Duplex",
                "neighborhood": "Gwinnett County",
                "features": ["Two 3BR units", "Separate utilities", "Large lots", "Good condition"],
                "status": "Active",
                "notes": "Strong rental demand, both units occupied",
            },
        ]

        templates = {
            DemoScenario.LUXURY_AGENT: luxury_properties,
            DemoScenario.MID_MARKET: mid_market_properties,
            DemoScenario.FIRST_TIME_BUYER: first_time_properties,
            DemoScenario.INVESTOR_FOCUSED: investor_properties,
            DemoScenario.HIGH_VOLUME: mid_market_properties,  # Use mid-market as base
        }

        return templates.get(scenario, mid_market_properties)

    @staticmethod
    def get_conversation_templates(scenario: DemoScenario, status: str) -> Dict[str, Any]:
        """Get realistic Jorge bot conversation templates"""

        # Professional Jorge bot conversations with realistic flow
        luxury_qualified_conversation = {
            "messages": [
                {
                    "timestamp": "2024-01-15T14:32:12Z",
                    "sender": "Jorge",
                    "message": "Hi Patricia! I'm Jorge, your AI real estate specialist. I understand you're looking for luxury properties in Beverly Hills. What brings you to the market right now?",
                },
                {
                    "timestamp": "2024-01-15T14:33:45Z",
                    "sender": "Patricia",
                    "message": "Hi Jorge. We're relocating from Manhattan for tax reasons and need something spectacular. Budget is flexible up to $3.5M.",
                },
                {
                    "timestamp": "2024-01-15T14:34:12Z",
                    "sender": "Jorge",
                    "message": "Excellent! A strategic move. I specialize in luxury relocations. Few quick questions: Are you looking for a primary residence or investment property? Any specific amenities that are non-negotiable?",
                },
                {
                    "timestamp": "2024-01-15T14:35:30Z",
                    "sender": "Patricia",
                    "message": "Primary residence. We need ocean views, wine storage, and modern smart home features. Security is also important.",
                },
                {
                    "timestamp": "2024-01-15T14:36:15Z",
                    "sender": "Jorge",
                    "message": "Perfect. Based on your criteria, I can show you 3 properties today that match exactly: oceanfront in Manhattan Beach at $3.2M, Benedict Canyon estate with wine cellar at $2.85M, and a Malibu smart home at $3.1M. Are you pre-approved or would you prefer cash purchase?",
                },
                {
                    "timestamp": "2024-01-15T14:37:22Z",
                    "sender": "Patricia",
                    "message": "Cash purchase, we can close within 30 days. The Benedict Canyon property sounds interesting.",
                },
                {
                    "timestamp": "2024-01-15T14:38:05Z",
                    "sender": "Jorge",
                    "message": "Excellent! Cash gives you tremendous negotiating power. The Benedict Canyon estate is spectacular - 5BR/6BA, celebrity neighborhood, just renovated. I can arrange a private showing today at 4 PM. Should I also prepare market analysis and negotiation strategy?",
                },
            ],
            "sentiment": "Very Positive - Engaged luxury buyer",
            "frs_score": 95,
            "pcs_score": 88,
            "insights": [
                "Cash buyer with strong financials",
                "Specific luxury requirements",
                "Timeline urgency creates opportunity",
            ],
            "actions": ["Schedule immediate showing", "Prepare luxury market analysis", "Draft initial offer strategy"],
            "engagement": 0.92,
        }

        mid_market_qualified_conversation = {
            "messages": [
                {
                    "timestamp": "2024-01-15T10:15:30Z",
                    "sender": "Jorge",
                    "message": "Hi Alex! I'm Jorge, and I help first-time buyers navigate the Rancho Cucamonga market. I see you're looking in the $350-450K range. What's driving your home search right now?",
                },
                {
                    "timestamp": "2024-01-15T10:17:45Z",
                    "sender": "Alex",
                    "message": "Hi! We're tired of renting and rates seem to be stabilizing. We're pre-approved for $400K and want something in good school districts.",
                },
                {
                    "timestamp": "2024-01-15T10:18:22Z",
                    "sender": "Jorge",
                    "message": "Smart timing! The Rancho Cucamonga market is competitive but stabilizing. Upland and Fontana have excellent schools. Are you looking for move-in ready or okay with some updates?",
                },
                {
                    "timestamp": "2024-01-15T10:19:55Z",
                    "sender": "Alex",
                    "message": "Prefer move-in ready. We both work full time and don't want renovation stress. 3 bedrooms minimum.",
                },
                {
                    "timestamp": "2024-01-15T10:21:12Z",
                    "sender": "Jorge",
                    "message": "Perfect! I have 3 properties that fit exactly: Upland new build at $425K (4BR/3BA), Fontana updated home at $380K (3BR/2BA), and Chino family home at $395K (4BR/2.5BA). All move-in ready with great schools. Want to see them this weekend?",
                },
                {
                    "timestamp": "2024-01-15T10:22:30Z",
                    "sender": "Alex",
                    "message": "Yes! The Upland one sounds good. How's the market for buyers right now?",
                },
                {
                    "timestamp": "2024-01-15T10:23:45Z",
                    "sender": "Jorge",
                    "message": "Good news! Competition has cooled from last year. Average days on market is 25 vs 8 last year, so you have more time to decide. I'll set up showings and prepare a buyer's strategy guide for you.",
                },
            ],
            "sentiment": "Positive - Motivated first-time buyer",
            "frs_score": 82,
            "pcs_score": 75,
            "insights": [
                "Pre-approved and ready to move",
                "Clear criteria and timeline",
                "Needs guidance but qualified",
            ],
            "actions": [
                "Schedule weekend showings",
                "Prepare buyer strategy guide",
                "Send school district information",
            ],
            "engagement": 0.84,
        }

        # Return appropriate template based on scenario and status
        if scenario == DemoScenario.LUXURY_AGENT and status == "qualified":
            return luxury_qualified_conversation
        elif scenario in [DemoScenario.MID_MARKET, DemoScenario.FIRST_TIME_BUYER] and status == "qualified":
            return mid_market_qualified_conversation
        else:
            # Default conversation for other combinations
            return {
                "messages": [
                    {
                        "timestamp": "2024-01-15T12:00:00Z",
                        "sender": "Jorge",
                        "message": "Hi! I'm Jorge, your AI real estate specialist. How can I help you with your real estate needs today?",
                    },
                    {
                        "timestamp": "2024-01-15T12:01:30Z",
                        "sender": "Client",
                        "message": "I'm looking to buy a home but not sure where to start.",
                    },
                    {
                        "timestamp": "2024-01-15T12:02:00Z",
                        "sender": "Jorge",
                        "message": "Great! I'll help you through the entire process. Let's start with your budget and timeline. Are you pre-approved for a mortgage?",
                    },
                ],
                "sentiment": "Neutral - Early stage inquiry",
                "frs_score": 65,
                "pcs_score": 60,
                "insights": ["Early stage buyer", "Needs education and guidance"],
                "actions": ["Qualify financial readiness", "Provide buyer education", "Schedule consultation"],
                "engagement": 0.68,
            }
