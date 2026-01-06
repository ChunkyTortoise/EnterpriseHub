"""
Demo Data Library - Centralized Scenarios for High-Ticket Sales Demos
Provides swappable datasets for Real Estate AI, Lead Scoring, and other modules.
"""
from typing import Dict, List, Any
from datetime import datetime, timedelta
import random

# ============================================================================
# SCENARIO DEFINITIONS
# ============================================================================

SCENARIOS = {
    "MIAMI_LUXURY_BUYER": {
        "name": "Miami Luxury Buyer - Sarah Chen",
        "description": "High-net-worth tech executive looking for waterfront property",
        "lead_data": {
            "name": "Sarah Chen",
            "email": "sarah.chen@techcorp.com",
            "phone": "+1 (415) 555-0198",
            "budget_min": 3500000,
            "budget_max": 5500000,
            "location": "Miami Beach, FL",
            "property_type": "Waterfront Condo",
            "bedrooms": "3-4",
            "timeline": "3-6 months",
            "source": "Zillow Premium Listing",
            "engagement_score": 92,
            "sentiment": "Very Positive",
            "ai_insights": [
                "Recently sold SF condo for $4.2M (public records)",
                "LinkedIn shows VP role at Series C SaaS company",
                "Engaged with 8 luxury waterfront listings in past 30 days",
                "High intent: Viewed virtual tours 3x, downloaded floor plans"
            ],
            "recommended_properties": [
                {"address": "1000 S Pointe Dr #2901", "price": 4750000, "match_score": 94},
                {"address": "900 Biscayne Blvd PH5402", "price": 5200000, "match_score": 89},
                {"address": "1200 West Ave #1526", "price": 3900000, "match_score": 86}
            ],
            "conversation_history": [
                {"role": "lead", "message": "I'm interested in waterfront properties with direct ocean views.", "timestamp": "2026-01-02 14:23"},
                {"role": "agent", "message": "Perfect timing! We have 3 exceptional oceanfront listings in your range. Would you prefer South Beach or Brickell?", "timestamp": "2026-01-02 14:24"},
                {"role": "lead", "message": "South Beach preferred. What's available for March viewing?", "timestamp": "2026-01-02 14:28"}
            ],
            "next_actions": [
                "Schedule private showing at 1000 S Pointe (3 units available)",
                "Send comparable sales analysis for waterfront properties",
                "Share neighborhood investment trends report"
            ]
        }
    },
    
    "DISTRESSED_SELLER": {
        "name": "Distressed Seller - Marcus Johnson",
        "description": "Homeowner facing foreclosure, needs quick cash sale",
        "lead_data": {
            "name": "Marcus Johnson",
            "email": "mjohnson.prop@gmail.com",
            "phone": "+1 (786) 555-0142",
            "budget_min": 0,
            "budget_max": 0,
            "location": "Fort Lauderdale, FL",
            "property_type": "Single Family Home",
            "bedrooms": "3",
            "timeline": "URGENT - 30 days",
            "source": "Pre-Foreclosure List",
            "engagement_score": 45,
            "sentiment": "Anxious/Stressed",
            "ai_insights": [
                "⚠️ Pre-foreclosure notice filed 45 days ago",
                "Property equity estimated at $85k",
                "Multiple mortgage payment skips detected",
                "High urgency - needs creative financing solution"
            ],
            "recommended_properties": [],
            "conversation_history": [
                {"role": "lead", "message": "I need to sell fast. Bank gave me 60 days notice.", "timestamp": "2026-01-04 09:15"},
                {"role": "agent", "message": "I understand the pressure. We specialize in quick closings. Can you share your property address so I can run a market analysis?", "timestamp": "2026-01-04 09:17"},
                {"role": "lead", "message": "2340 NW 12th St. I owe $315k, think it's worth $400k.", "timestamp": "2026-01-04 09:22"}
            ],
            "next_actions": [
                "🚨 PRIORITY: Get pre-approved cash buyer list",
                "Schedule urgent property inspection within 48 hours",
                "Prepare short sale negotiation packet for lender",
                "Connect with foreclosure attorney for timeline extension"
            ]
        }
    },
    
    "RE_ENGAGEMENT_COLD": {
        "name": "Cold Lead Re-Engagement - David Park",
        "description": "Previously engaged lead, went silent 4 months ago",
        "lead_data": {
            "name": "David Park",
            "email": "david.park@innovatetech.io",
            "phone": "+1 (305) 555-0891",
            "budget_min": 850000,
            "budget_max": 1200000,
            "location": "Coral Gables, FL",
            "property_type": "Single Family Home",
            "bedrooms": "4",
            "timeline": "Flexible",
            "source": "Open House Sign-In (Sept 2025)",
            "engagement_score": 12,
            "sentiment": "Neutral/Dormant",
            "ai_insights": [
                "Last engagement: 124 days ago (open house visit)",
                "Email open rate dropped to 0% after 6 follow-ups",
                "LinkedIn shows recent job change to VP Engineering",
                "Potential trigger: New role may mean relocation budget"
            ],
            "recommended_properties": [
                {"address": "521 Majorca Ave", "price": 1050000, "match_score": 77},
                {"address": "234 Venetia Ave", "price": 980000, "match_score": 74}
            ],
            "conversation_history": [
                {"role": "lead", "message": "Nice property, but I'm not ready to buy yet. Just browsing.", "timestamp": "2025-09-08 15:45"},
                {"role": "agent", "message": "No pressure! I'll send you market updates so you stay informed when you're ready.", "timestamp": "2025-09-08 15:47"},
                {"role": "agent", "message": "[AUTO] New listings matching your criteria", "timestamp": "2025-09-15 10:00"},
                {"role": "agent", "message": "[AUTO] Price reduction alert", "timestamp": "2025-10-03 09:30"}
            ],
            "next_actions": [
                "🎯 Re-engagement campaign: Congratulate on new VP role",
                "Send personalized video: 'New executive-friendly neighborhoods'",
                "Offer: Private market preview for new inventory",
                "Ask: 'Has your timeline changed with the new position?'"
            ]
        }
    },
    
    "FIRST_TIME_BUYER": {
        "name": "First-Time Buyer - Emily Rodriguez",
        "description": "Young professional, first home purchase, needs education",
        "lead_data": {
            "name": "Emily Rodriguez",
            "email": "emily.rodriguez.md@gmail.com",
            "phone": "+1 (954) 555-0276",
            "budget_min": 425000,
            "budget_max": 550000,
            "location": "Pembroke Pines, FL",
            "property_type": "Townhouse",
            "bedrooms": "2-3",
            "timeline": "6-12 months",
            "source": "Facebook Ad - First-Time Buyer Guide",
            "engagement_score": 68,
            "sentiment": "Eager but Cautious",
            "ai_insights": [
                "Downloaded 'First-Time Buyer Checklist' (high intent)",
                "Asked 12 questions in chatbot (mortgage, inspection, closing)",
                "Credit score estimated at 720+ based on lender pre-qual form",
                "Needs education on down payment assistance programs"
            ],
            "recommended_properties": [
                {"address": "1520 NW 99th Way", "price": 485000, "match_score": 91},
                {"address": "8821 SW 8th St", "price": 520000, "match_score": 87},
                {"address": "3340 Palm Ave", "price": 445000, "match_score": 85}
            ],
            "conversation_history": [
                {"role": "lead", "message": "I'm a doctor finishing residency. How much do I need for a down payment?", "timestamp": "2026-01-05 19:30"},
                {"role": "agent", "message": "Congratulations on finishing residency! Doctors qualify for special physician loan programs with 0% down. Let me explain...", "timestamp": "2026-01-05 19:32"},
                {"role": "lead", "message": "That sounds perfect! What's the next step?", "timestamp": "2026-01-05 19:45"}
            ],
            "next_actions": [
                "Send physician mortgage program comparison guide",
                "Connect with lender partner for pre-approval",
                "Schedule 'First-Time Buyer Workshop' virtual session",
                "Share timeline: Offer → Inspection → Closing"
            ]
        }
    },
    
    "INVESTOR_PORTFOLIO": {
        "name": "Investor - Portfolio Expansion - James Liu",
        "description": "Experienced investor looking for cash-flowing rental properties",
        "lead_data": {
            "name": "James Liu",
            "email": "james@liucapital.ventures",
            "phone": "+1 (561) 555-0334",
            "budget_min": 250000,
            "budget_max": 400000,
            "location": "West Palm Beach, FL",
            "property_type": "Multi-Family",
            "bedrooms": "N/A",
            "timeline": "Continuous",
            "source": "BiggerPockets Referral",
            "engagement_score": 88,
            "sentiment": "Analytical/Data-Driven",
            "ai_insights": [
                "Owns 8 rental properties across FL (public records)",
                "Targets 8%+ cap rate, prefers turnkey",
                "Responds best to ROI data (NOI, cash-on-cash return)",
                "Uses 1031 exchanges - watch for trigger events"
            ],
            "recommended_properties": [
                {"address": "2200 Palm Beach Lakes Blvd (4-plex)", "price": 780000, "match_score": 96, "cap_rate": 8.2},
                {"address": "1450 N Dixie Hwy (Duplex)", "price": 385000, "match_score": 89, "cap_rate": 7.8},
                {"address": "3300 Broadway (Triplex)", "price": 620000, "match_score": 87, "cap_rate": 8.0}
            ],
            "conversation_history": [
                {"role": "lead", "message": "Send me anything with 8%+ cap rate and positive cash flow Day 1.", "timestamp": "2025-12-28 11:20"},
                {"role": "agent", "message": "Got it. I have 2 fourplexes and 1 triplex that meet your criteria. All fully occupied with stable tenants. Sending pro formas now.", "timestamp": "2025-12-28 11:23"},
                {"role": "lead", "message": "Fourplex looks good. Can you get me actual rent rolls?", "timestamp": "2025-12-28 14:15"}
            ],
            "next_actions": [
                "Send rent roll + 2-year income statements for fourplex",
                "Schedule property walkthrough with property manager",
                "Prepare 1031 exchange timeline if applicable",
                "Share market rent analysis (upside potential)"
            ]
        }
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_scenario_list() -> List[str]:
    """Returns list of scenario names for dropdown selection."""
    return [f"{key}: {data['name']}" for key, data in SCENARIOS.items()]

def get_scenario_keys() -> List[str]:
    """Returns list of scenario keys."""
    return list(SCENARIOS.keys())

def get_scenario_data(scenario_key: str) -> Dict[str, Any]:
    """Returns full scenario data for a given key."""
    return SCENARIOS.get(scenario_key, SCENARIOS["MIAMI_LUXURY_BUYER"])

def get_lead_data(scenario_key: str) -> Dict[str, Any]:
    """Returns just the lead data portion of a scenario."""
    scenario = get_scenario_data(scenario_key)
    return scenario.get("lead_data", {})

def format_scenario_selector_options() -> Dict[str, str]:
    """Returns formatted dict for st.selectbox: {display_name: scenario_key}"""
    return {
        f"🎯 {data['name']} - {data['description']}": key
        for key, data in SCENARIOS.items()
    }

# ============================================================================
# CONVERSATION HISTORY GENERATORS
# ============================================================================

def generate_conversation_html(conversation_history: List[Dict]) -> str:
    """Generates styled HTML for conversation history display."""
    html = "<div style='font-family: system-ui; font-size: 0.9rem;'>"
    
    for msg in conversation_history:
        role = msg.get("role", "agent")
        message = msg.get("message", "")
        timestamp = msg.get("timestamp", "")
        
        if role == "lead":
            html += f"""
            <div style='background: #EEF2FF; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid #6366F1;'>
                <strong style='color: #4F46E5;'>👤 Lead:</strong> {message}
                <div style='font-size: 0.75rem; color: #64748B; margin-top: 4px;'>{timestamp}</div>
            </div>
            """
        else:
            html += f"""
            <div style='background: #F0FDF4; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid #10B981;'>
                <strong style='color: #059669;'>🤖 AI Agent:</strong> {message}
                <div style='font-size: 0.75rem; color: #64748B; margin-top: 4px;'>{timestamp}</div>
            </div>
            """
    
    html += "</div>"
    return html

# ============================================================================
# MARKET DATA GENERATORS (for Market Pulse, Analytics modules)
# ============================================================================

def generate_market_trends(location: str = "Miami, FL") -> Dict[str, Any]:
    """Generates realistic market trend data for a location."""
    return {
        "location": location,
        "median_price": random.randint(450000, 850000),
        "yoy_appreciation": round(random.uniform(3.5, 12.5), 1),
        "days_on_market": random.randint(18, 45),
        "inventory_level": random.choice(["Low", "Moderate", "High"]),
        "buyer_demand_index": random.randint(65, 95),
        "price_trends_6mo": [random.randint(420, 880) for _ in range(6)]
    }

def generate_lead_scoring_features(scenario_key: str) -> Dict[str, int]:
    """Generates feature scores for lead scoring visualization."""
    base_scores = {
        "MIAMI_LUXURY_BUYER": {"engagement": 92, "budget_fit": 95, "timeline": 78, "authority": 88},
        "DISTRESSED_SELLER": {"engagement": 45, "budget_fit": 60, "timeline": 98, "authority": 70},
        "RE_ENGAGEMENT_COLD": {"engagement": 12, "budget_fit": 75, "timeline": 30, "authority": 65},
        "FIRST_TIME_BUYER": {"engagement": 68, "budget_fit": 82, "timeline": 55, "authority": 45},
        "INVESTOR_PORTFOLIO": {"engagement": 88, "budget_fit": 90, "timeline": 85, "authority": 95}
    }
    return base_scores.get(scenario_key, {"engagement": 50, "budget_fit": 50, "timeline": 50, "authority": 50})
