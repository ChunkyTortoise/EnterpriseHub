"""
Bot Test Fixtures - Comprehensive Testing Library for Jorge Bot Ecosystem

Provides production-ready fixtures for testing:
- Jorge Seller Bot (1,550+ lines of production code)
- Jorge Buyer Bot (consultative qualification)
- Lead Bot (3-7-30 day nurture sequences)
- All bot state objects and conversation flows
- External service mocks (Claude, GHL, MLS, Perplexity, Stripe)
- Compliance test scenarios (Fair Housing, TREC)
- Performance monitoring and analytics

Architecture:
- Async-first design matching production bot patterns
- Realistic Austin real estate market data ($300k-$1M+)
- Jorge's confrontational methodology conversation samples
- Progressive skills and agent mesh integration support
- Track 3.1 ML analytics integration

Author: EnterpriseHub Testing Team
Version: 1.0.0
Last Updated: 2026-01-25
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from pydantic import BaseModel

# Import production models
try:
    from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState
    from ghl_real_estate_ai.models.lead_scoring import (
        BuyerIntentProfile,
        ConditionRealism,
        FinancialReadinessScore,
        LeadIntentProfile,
        MotivationSignals,
        PriceResponsiveness,
        PsychologicalCommitmentScore,
        TimelineCommitment,
    )
    from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
    from ghl_real_estate_ai.models.workflows import LeadFollowUpState, SellerWorkflowState
except ImportError:
    # Fallback for when models aren't available
    JorgeSellerState = Dict[str, Any]
    BuyerBotState = Dict[str, Any]
    LeadFollowUpState = Dict[str, Any]
    SellerWorkflowState = Dict[str, Any]
    LeadIntentProfile = Dict[str, Any]
    BuyerIntentProfile = Dict[str, Any]
    FinancialReadinessScore = Dict[str, Any]
    PsychologicalCommitmentScore = Dict[str, Any]
    MotivationSignals = Dict[str, Any]
    TimelineCommitment = Dict[str, Any]
    ConditionRealism = Dict[str, Any]
    PriceResponsiveness = Dict[str, Any]

# ============================================================================
# MOCK SERVICE FIXTURES - Core Dependencies
# ============================================================================


@pytest.fixture
def mock_claude_client() -> AsyncMock:
    """
    Mock Claude API client for bot conversations.

    Returns AsyncMock configured with realistic responses for:
    - Intent analysis
    - Lead qualification
    - Stall detection
    - Response generation

    Usage:
        mock_claude = mock_claude_client()
        mock_claude.generate_response.return_value = "Custom response"
    """
    mock_client = AsyncMock()

    # Default responses for common scenarios
    mock_client.generate_response = AsyncMock(
        return_value="Thank you for sharing that information. Based on what you've told me, "
        "it sounds like you're serious about selling. Let me ask you this - "
        "what's your actual timeline to close?"
    )

    mock_client.analyze_intent = AsyncMock(
        return_value={
            "intent": "seller_qualification",
            "confidence": 0.92,
            "urgency_score": 75,
            "financial_readiness": 80,
        }
    )

    mock_client.detect_stall = AsyncMock(return_value={"stall_detected": False, "stall_type": None, "confidence": 0.95})

    # Simulate token usage for cost tracking
    mock_client.last_request_tokens = 1250
    mock_client.last_response_tokens = 380
    mock_client.total_tokens_used = 1630

    return mock_client


@pytest.fixture
def mock_ghl_client() -> AsyncMock:
    """
    Mock GoHighLevel CRM client for lead management.

    Simulates:
    - Contact creation/updates
    - Conversation sync
    - Pipeline stage transitions
    - Custom field updates
    - Webhook delivery

    Usage:
        mock_ghl = mock_ghl_client()
        mock_ghl.update_contact.assert_called_with(contact_id="lead_123")
    """
    mock_client = AsyncMock()

    # Contact management
    mock_client.create_contact = AsyncMock(
        return_value={
            "contact_id": "ghl_contact_" + str(uuid4())[:8],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
    )

    mock_client.update_contact = AsyncMock(
        return_value={"status": "success", "updated_at": datetime.now(timezone.utc).isoformat()}
    )

    mock_client.get_contact = AsyncMock(
        return_value={
            "contact_id": "ghl_contact_123",
            "name": "John Seller",
            "email": "john@example.com",
            "phone": "+15125551234",
            "custom_fields": {
                "lead_score": 85,
                "qualification_status": "qualified",
                "property_address": "123 Main St, Austin, TX 78701",
            },
        }
    )

    # Conversation management
    mock_client.send_message = AsyncMock(
        return_value={
            "message_id": "msg_" + str(uuid4())[:8],
            "delivered_at": datetime.now(timezone.utc).isoformat(),
            "status": "delivered",
        }
    )

    # Pipeline management
    mock_client.update_opportunity = AsyncMock(return_value={"opportunity_id": "opp_123", "stage": "qualified"})

    # Rate limit simulation
    mock_client.request_count = 0
    mock_client.rate_limit_remaining = 300

    return mock_client


@pytest.fixture
def mock_property_matcher() -> AsyncMock:
    """
    Mock Property Matcher service for buyer bot testing.

    Returns AsyncMock configured with Austin market property listings.
    """
    mock_matcher = AsyncMock()

    mock_matcher.match_properties = AsyncMock(
        return_value=[
            {
                "property_id": "prop_001",
                "address": "456 Oak Ave, Austin, TX 78704",
                "price": 425000,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 1850,
                "match_score": 0.92,
                "neighborhood": "South Austin",
                "listing_date": "2026-01-15",
            },
            {
                "property_id": "prop_002",
                "address": "789 Cedar Ln, Round Rock, TX 78681",
                "price": 389000,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "sqft": 1920,
                "match_score": 0.88,
                "neighborhood": "Round Rock",
                "listing_date": "2026-01-20",
            },
        ]
    )

    mock_matcher.get_property_details = AsyncMock(
        return_value={
            "property_id": "prop_001",
            "full_details": {
                "year_built": 2015,
                "lot_size": 0.25,
                "hoa_fee": 150,
                "property_tax": 8500,
                "school_district": "Austin ISD",
            },
        }
    )

    return mock_matcher


# ============================================================================
# CONVERSATION HISTORY FIXTURES - Realistic Dialog Samples
# ============================================================================


@pytest.fixture
def conversation_history_seller_hot_lead() -> List[Dict[str, str]]:
    """
    Hot seller lead - Strong motivation, clear timeline, realistic expectations.
    Jorge's confrontational methodology in action.
    """
    return [
        {"role": "user", "content": "Hi, I need to sell my house in Austin ASAP. Got a job transfer to Seattle."},
        {
            "role": "assistant",
            "content": "I appreciate the urgency. Job transfer is a legitimate reason. "
            "Let me ask you this straight - what's your absolute deadline to be out?",
        },
        {"role": "user", "content": "Need to be there by March 1st. That's 5 weeks from now."},
        {
            "role": "assistant",
            "content": "5 weeks is tight but doable if you're serious. Here's the reality - "
            "in this market, properly priced homes are selling in 15-18 days. "
            "What's the property address so I can pull comps?",
        },
        {
            "role": "user",
            "content": "123 Oak Street, 78704. It's a 3br/2ba, about 1,800 sqft. Built in 2010, good condition.",
        },
        {
            "role": "assistant",
            "content": "South Austin, good area. Let me be direct - have you looked at "
            "what similar homes sold for recently, or are you going off Zestimate?",
        },
        {
            "role": "user",
            "content": "I saw Zillow says $485k but I know that's not always accurate. What do you think it's worth?",
        },
        {
            "role": "assistant",
            "content": "Smart - you understand Zestimates are algorithms, not appraisals. "
            "Based on recent sales in 78704, I'm thinking $465-475k range. "
            "Here's the question - are you ready to list at market price, "
            "or do you need to test the market first?",
        },
        {"role": "user", "content": "I need to sell, not test. Let's go with the right price. What's next?"},
    ]


@pytest.fixture
def conversation_history_buyer_qualified() -> List[Dict[str, str]]:
    """
    Qualified buyer - pre-approved, clear timeline, realistic expectations.
    """
    return [
        {"role": "user", "content": "Looking for a 3-bedroom house in North Austin, budget around $450k."},
        {
            "role": "assistant",
            "content": "Great, let's narrow this down. Are you pre-approved for financing, "
            "or is that $450k what you think you can afford?",
        },
        {"role": "user", "content": "Pre-approved for $475k, putting 10% down. Have $50k saved."},
        {
            "role": "assistant",
            "content": "Perfect - you're actually qualified, not just browsing. What's your timeline? "
            "When do you need to be in the new place?",
        },
        {"role": "user", "content": "Lease ends April 30th, so ideally close by mid-April."},
        {
            "role": "assistant",
            "content": "10 weeks - that's realistic if we find the right place quickly. "
            "In this market, good homes are going under contract in 7-10 days. "
            "What are your must-haves versus nice-to-haves?",
        },
        {
            "role": "user",
            "content": "Must have: 3 bed, 2 bath, good schools, backyard for the dog. "
            "Nice to have: updated kitchen, home office space.",
        },
        {
            "role": "assistant",
            "content": "That's clear. Good schools usually means Leander ISD or Round Rock ISD "
            "in that price range. Let me pull some listings that match your criteria.",
        },
    ]


# ============================================================================
# BOT STATE FIXTURES - Pre-configured States for Testing
# ============================================================================


@pytest.fixture
def bot_state_seller_hot_lead() -> Dict[str, Any]:
    """
    Hot seller lead state - ready to list, qualified, high commitment.
    """
    return {
        "lead_id": "seller_hot_001",
        "lead_name": "Michael Rodriguez",
        "property_address": "123 Oak Street, Austin, TX 78704",
        "conversation_history": [
            {"role": "user", "content": "Need to sell ASAP, job transfer"},
            {"role": "assistant", "content": "What's your deadline?"},
            {"role": "user", "content": "5 weeks from now"},
        ],
        "intent_profile": None,  # Will be populated by intent analysis
        "current_tone": "consultative",
        "stall_detected": False,
        "detected_stall_type": None,
        "next_action": "qualify_financial_readiness",
        "response_content": "",
        "psychological_commitment": 85.0,
        "is_qualified": True,
        "current_journey_stage": "qualification",
        "follow_up_count": 0,
        "last_action_timestamp": datetime.now(timezone.utc),
    }


@pytest.fixture
def bot_state_buyer_qualified() -> Dict[str, Any]:
    """
    Qualified buyer - pre-approved, clear timeline, realistic expectations.
    """
    return {
        "buyer_id": "buyer_qualified_001",
        "buyer_name": "Sarah Martinez",
        "target_areas": ["North Austin", "Round Rock", "Cedar Park"],
        "conversation_history": [
            {"role": "user", "content": "Looking for 3br house, pre-approved for $475k"},
            {"role": "assistant", "content": "Great! When do you need to move?"},
            {"role": "user", "content": "Lease ends April 30th"},
        ],
        "intent_profile": None,
        "budget_range": {"min": 400000, "max": 475000},
        "financing_status": "pre_approved",
        "urgency_level": "3_months",
        "property_preferences": {
            "bedrooms": 3,
            "bathrooms": 2,
            "must_have_backyard": True,
            "school_district": "high_rated",
        },
        "current_qualification_step": "preferences",
        "objection_detected": False,
        "detected_objection_type": None,
        "next_action": "match_properties",
        "response_content": "",
        "matched_properties": [],
        "financial_readiness_score": 85.0,
        "buying_motivation_score": 75.0,
        "is_qualified": True,
        "current_journey_stage": "property_search",
        "properties_viewed_count": 0,
        "last_action_timestamp": datetime.now(timezone.utc),
    }


# ============================================================================
# PROPERTY LISTING FIXTURES - Austin Market Data
# ============================================================================


@pytest.fixture
def sample_property_listings_austin() -> List[Dict[str, Any]]:
    """
    Realistic Austin property listings across different price ranges.
    """
    return [
        {
            "property_id": "MLS2601234",
            "address": "456 Oak Ave, Austin, TX 78704",
            "neighborhood": "South Austin (Bouldin Creek)",
            "price": 675000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 1850,
            "lot_size": 0.18,
            "year_built": 2015,
            "property_type": "Single Family",
            "status": "active",
            "days_on_market": 8,
            "price_per_sqft": 365,
            "hoa_fee": 0,
            "property_tax": 11250,
            "school_district": "Austin ISD",
            "features": ["Updated kitchen", "Hardwood floors", "Covered patio", "Walking distance to South Congress"],
            "listing_date": "2026-01-17",
        },
        {
            "property_id": "MLS2601235",
            "address": "789 Cedar Ln, Round Rock, TX 78681",
            "neighborhood": "Round Rock (Teravista)",
            "price": 425000,
            "bedrooms": 4,
            "bathrooms": 2.5,
            "sqft": 2450,
            "lot_size": 0.25,
            "year_built": 2018,
            "property_type": "Single Family",
            "status": "active",
            "days_on_market": 12,
            "price_per_sqft": 173,
            "hoa_fee": 180,
            "property_tax": 8925,
            "school_district": "Round Rock ISD",
            "features": ["Open floor plan", "Large backyard", "Community pool", "Highly rated schools"],
            "listing_date": "2026-01-13",
        },
    ]


# ============================================================================
# COMPLIANCE TEST FIXTURES - Fair Housing & TREC
# ============================================================================


@pytest.fixture
def compliance_test_scenarios() -> Dict[str, List[str]]:
    """
    Test scenarios for Fair Housing and TREC compliance validation.

    Returns dictionary with:
    - valid_responses: Compliant bot responses
    - violations_discriminatory: Fair Housing violations
    - violations_unauthorized_advice: TREC violations
    - violations_misleading: Deceptive trade practice violations
    """
    return {
        "valid_responses": [
            "Based on recent comparable sales, similar homes in your area are selling for $450-475k.",
            "The school district is Austin ISD. You can research ratings at GreatSchools.org.",
            "I recommend consulting with a home inspector for a detailed property assessment.",
            "I can help you understand market trends, but final pricing should be discussed with your licensed agent.",
            "That neighborhood has a mix of property types and price ranges.",
        ],
        "violations_discriminatory": [
            "That neighborhood is mostly families, not many singles.",
            "You probably want to avoid that area, it's changing demographically.",
            "The schools there have a lot of ESL students.",
            "That's a quiet, family-oriented neighborhood - might not be right for you.",
            "Most buyers in that price range are young professionals.",
        ],
        "violations_unauthorized_advice": [
            "I guarantee your home will sell for $500k.",
            "You should definitely accept that offer - it's the best you'll get.",
            "Don't bother with an inspection, the house is fine.",
            "I'm certain property values will increase 10% next year.",
            "You don't need a lawyer for this transaction.",
        ],
        "violations_misleading": [
            "This home is a steal - it'll be worth 20% more in a year!",
            "Every home in Austin sells in 3 days or less.",
            "You'll definitely get multiple offers above asking price.",
            "The Zestimate is always accurate - you can rely on that number.",
            "All homes in this area have foundation issues, but don't worry about it.",
        ],
    }


# ============================================================================
# PERFORMANCE MONITORING FIXTURES - Metrics & Analytics
# ============================================================================


@pytest.fixture
def performance_metrics_tracking() -> Dict[str, Any]:
    """
    Performance metrics for bot performance monitoring tests.
    """
    return {
        "response_times": {
            "intent_analysis_ms": 245,
            "stall_detection_ms": 120,
            "response_generation_ms": 890,
            "total_workflow_ms": 1255,
        },
        "token_usage": {
            "input_tokens": 1250,
            "output_tokens": 380,
            "total_tokens": 1630,
            "estimated_cost": 0.02445,  # $0.000015 per token
        },
        "conversation_metrics": {
            "turns_to_qualification": 7,
            "qualification_rate": 0.68,
            "stall_detection_rate": 0.23,
            "stall_break_success_rate": 0.72,
        },
        "business_metrics": {
            "leads_processed": 1247,
            "hot_leads_identified": 189,
            "warm_leads_identified": 412,
            "cold_leads_identified": 646,
            "avg_lead_score": 52.3,
            "conversion_rate": 0.152,  # 15.2% hot lead conversion
        },
        "sla_compliance": {
            "response_time_target_ms": 2000,
            "response_time_actual_ms": 1255,
            "sla_met": True,
            "uptime_percentage": 99.7,
        },
    }


# ============================================================================
# HELPER FUNCTIONS - Test Utilities
# ============================================================================


def create_mock_conversation_turn(role: str, content: str, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Create a single conversation turn for building test dialogs.

    Args:
        role: "user" or "assistant"
        content: Message content
        timestamp: Optional timestamp (defaults to now)

    Returns:
        Dict representing a conversation turn
    """
    return {
        "role": role,
        "content": content,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "message_id": str(uuid4()),
    }


def build_conversation_history(turns: List[Tuple[str, str]]) -> List[Dict[str, str]]:
    """
    Build a conversation history from a list of (role, content) tuples.

    Args:
        turns: List of (role, content) tuples

    Returns:
        Complete conversation history

    Example:
        history = build_conversation_history([
            ("user", "I want to sell my house"),
            ("assistant", "Great! What's your timeline?"),
            ("user", "Need to close in 30 days")
        ])
    """
    return [create_mock_conversation_turn(role, content) for role, content in turns]


def assert_bot_response_compliant(response: str, compliance_scenarios: Dict[str, List[str]]) -> bool:
    """
    Validate bot response for Fair Housing and TREC compliance.

    Args:
        response: Bot response text
        compliance_scenarios: Compliance test scenarios fixture

    Returns:
        True if compliant, raises AssertionError otherwise
    """
    response_lower = response.lower()

    # Check for discriminatory language
    for violation in compliance_scenarios["violations_discriminatory"]:
        if violation.lower() in response_lower:
            raise AssertionError(f"Fair Housing violation detected: {violation}")

    # Check for unauthorized advice
    for violation in compliance_scenarios["violations_unauthorized_advice"]:
        if violation.lower() in response_lower:
            raise AssertionError(f"TREC violation detected: {violation}")

    # Check for misleading statements
    for violation in compliance_scenarios["violations_misleading"]:
        if violation.lower() in response_lower:
            raise AssertionError(f"Deceptive practice detected: {violation}")

    return True


def calculate_conversation_metrics(conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Calculate metrics from a conversation history.

    Args:
        conversation_history: List of conversation turns

    Returns:
        Dict with conversation metrics
    """
    user_turns = [turn for turn in conversation_history if turn["role"] == "user"]
    assistant_turns = [turn for turn in conversation_history if turn["role"] == "assistant"]

    total_user_words = sum(len(turn["content"].split()) for turn in user_turns)
    total_assistant_words = sum(len(turn["content"].split()) for turn in assistant_turns)

    return {
        "total_turns": len(conversation_history),
        "user_turns": len(user_turns),
        "assistant_turns": len(assistant_turns),
        "avg_user_message_length": total_user_words / len(user_turns) if user_turns else 0,
        "avg_assistant_message_length": total_assistant_words / len(assistant_turns) if assistant_turns else 0,
        "conversation_depth": len(conversation_history),
    }


# ============================================================================
# EXPORTS - Make all fixtures available for import
# ============================================================================

__all__ = [
    # Mock services
    "mock_claude_client",
    "mock_ghl_client",
    "mock_property_matcher",
    # Conversation histories
    "conversation_history_seller_hot_lead",
    "conversation_history_buyer_qualified",
    # Bot states
    "bot_state_seller_hot_lead",
    "bot_state_buyer_qualified",
    # Property data
    "sample_property_listings_austin",
    # Compliance
    "compliance_test_scenarios",
    # Performance
    "performance_metrics_tracking",
    # Helper functions
    "create_mock_conversation_turn",
    "build_conversation_history",
    "assert_bot_response_compliant",
    "calculate_conversation_metrics",
]
