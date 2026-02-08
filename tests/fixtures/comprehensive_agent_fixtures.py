#!/usr/bin/env python3
"""
Comprehensive Agent Fixtures for Service 6 Testing
Provides realistic test data and mock configurations for all 25+ agents.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.agents.lead_intelligence_swarm import AgentInsight, AgentType
from ghl_real_estate_ai.services.autonomous_followup_engine import FollowUpRecommendation, FollowUpTask
from ghl_real_estate_ai.services.predictive_lead_routing import RoutingRecommendation


class LeadProfileType(Enum):
    HIGH_INTENT = "high_intent"
    MEDIUM_INTENT = "medium_intent"
    LOW_INTENT = "low_intent"
    INVESTOR = "investor"
    FIRST_TIME_BUYER = "first_time_buyer"
    LUXURY_BUYER = "luxury_buyer"


@dataclass
class LeadProfile:
    """Comprehensive lead profile for testing"""

    lead_id: str
    profile_type: LeadProfileType
    demographics: Dict[str, Any]
    behavioral_data: Dict[str, Any]
    engagement_history: List[Dict[str, Any]]
    expected_agent_insights: Dict[AgentType, Dict[str, Any]]
    expected_follow_up_strategy: Dict[str, Any]
    expected_routing_decision: Dict[str, Any]


class LeadProfileFactory:
    """Factory for creating comprehensive lead test profiles"""

    @staticmethod
    def high_intent_lead() -> LeadProfile:
        """High-intent lead expecting immediate contact"""
        lead_id = f"LEAD_HIGH_{uuid.uuid4().hex[:8]}"

        return LeadProfile(
            lead_id=lead_id,
            profile_type=LeadProfileType.HIGH_INTENT,
            demographics={
                "age": 34,
                "income": 95000,
                "credit_score": 750,
                "down_payment": 25000,
                "employment_status": "employed",
                "family_size": 4,
                "location": "Austin, TX",
                "budget_min": 350000,
                "budget_max": 450000,
                "property_type": "single_family",
                "timeline": "immediate",  # Within 30 days
            },
            behavioral_data={
                "website_sessions": 12,
                "pages_viewed": 45,
                "property_views": 23,
                "calculator_usage": 8,
                "mortgage_calculator_sessions": 5,
                "email_open_rate": 0.85,
                "email_click_rate": 0.34,
                "response_time_minutes": 15,
                "weekend_activity": True,
                "mobile_usage_percent": 0.75,
            },
            engagement_history=[
                {
                    "timestamp": datetime.now() - timedelta(hours=2),
                    "action": "property_search",
                    "details": {"criteria": "3br, 2ba, Austin", "results_viewed": 8},
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=1),
                    "action": "mortgage_calculator",
                    "details": {"amount": 400000, "down_payment": 25000},
                },
                {
                    "timestamp": datetime.now() - timedelta(minutes=30),
                    "action": "contact_form",
                    "details": {"message": "Looking for 3BR home in Cedar Park. Need to move by end of month."},
                },
            ],
            expected_agent_insights={
                AgentType.DEMOGRAPHIC_ANALYZER: {
                    "confidence": 0.92,
                    "opportunity_score": 88.5,
                    "risk_factors": [],
                    "urgency_level": "high",
                },
                AgentType.BEHAVIORAL_PROFILER: {
                    "confidence": 0.89,
                    "opportunity_score": 91.2,
                    "intent_signals": ["immediate_timeline", "mortgage_calc_usage", "high_engagement"],
                    "urgency_level": "urgent",
                },
                AgentType.INTENT_DETECTOR: {
                    "confidence": 0.94,
                    "opportunity_score": 93.8,
                    "intent_score": 94.0,
                    "purchase_probability": 0.87,
                    "timeline_days": 25,
                },
            },
            expected_follow_up_strategy={
                "priority": "urgent",
                "primary_channel": "phone",
                "backup_channel": "sms",
                "response_time_target": 15,  # minutes
                "follow_up_sequence": [
                    {"delay_minutes": 0, "channel": "phone", "message_type": "immediate_response"},
                    {"delay_minutes": 15, "channel": "sms", "message_type": "backup_contact"},
                    {"delay_hours": 2, "channel": "email", "message_type": "property_recommendations"},
                ],
            },
            expected_routing_decision={
                "priority": "urgent",
                "agent_expertise_required": ["luxury_homes", "austin_market"],
                "estimated_response_time": 15,  # minutes
                "predicted_success_rate": 0.82,
                "routing_confidence": 0.91,
            },
        )

    @staticmethod
    def medium_engagement_lead() -> LeadProfile:
        """Medium-engagement lead for standard processing"""
        lead_id = f"LEAD_MED_{uuid.uuid4().hex[:8]}"

        return LeadProfile(
            lead_id=lead_id,
            profile_type=LeadProfileType.MEDIUM_INTENT,
            demographics={
                "age": 28,
                "income": 65000,
                "credit_score": 680,
                "down_payment": 15000,
                "employment_status": "employed",
                "family_size": 2,
                "location": "Dallas, TX",
                "budget_min": 250000,
                "budget_max": 320000,
                "property_type": "townhouse",
                "timeline": "3_to_6_months",
            },
            behavioral_data={
                "website_sessions": 6,
                "pages_viewed": 18,
                "property_views": 8,
                "calculator_usage": 2,
                "email_open_rate": 0.45,
                "email_click_rate": 0.12,
                "response_time_minutes": 120,
                "weekend_activity": False,
                "mobile_usage_percent": 0.55,
            },
            engagement_history=[
                {
                    "timestamp": datetime.now() - timedelta(days=2),
                    "action": "property_search",
                    "details": {"criteria": "2br, Dallas", "results_viewed": 3},
                },
                {
                    "timestamp": datetime.now() - timedelta(days=1),
                    "action": "email_open",
                    "details": {"campaign": "market_update", "clicked": False},
                },
            ],
            expected_agent_insights={
                AgentType.DEMOGRAPHIC_ANALYZER: {
                    "confidence": 0.75,
                    "opportunity_score": 68.3,
                    "risk_factors": ["lower_income", "smaller_down_payment"],
                    "urgency_level": "medium",
                },
                AgentType.BEHAVIORAL_PROFILER: {
                    "confidence": 0.71,
                    "opportunity_score": 65.8,
                    "intent_signals": ["property_searches", "budget_conscious"],
                    "urgency_level": "medium",
                },
            },
            expected_follow_up_strategy={
                "priority": "medium",
                "primary_channel": "email",
                "backup_channel": "sms",
                "response_time_target": 120,  # minutes
                "follow_up_sequence": [
                    {"delay_hours": 1, "channel": "email", "message_type": "market_insights"},
                    {"delay_days": 1, "channel": "sms", "message_type": "check_in"},
                    {"delay_days": 3, "channel": "email", "message_type": "property_recommendations"},
                ],
            },
            expected_routing_decision={
                "priority": "medium",
                "agent_expertise_required": ["first_time_buyers", "dallas_market"],
                "estimated_response_time": 60,  # minutes
                "predicted_success_rate": 0.64,
                "routing_confidence": 0.73,
            },
        )

    @staticmethod
    def low_engagement_lead() -> LeadProfile:
        """Low-engagement lead for nurture sequence"""
        lead_id = f"LEAD_LOW_{uuid.uuid4().hex[:8]}"

        return LeadProfile(
            lead_id=lead_id,
            profile_type=LeadProfileType.LOW_INTENT,
            demographics={
                "age": 45,
                "income": 55000,
                "credit_score": 620,
                "down_payment": 8000,
                "employment_status": "employed",
                "family_size": 3,
                "location": "Houston, TX",
                "budget_min": 180000,
                "budget_max": 250000,
                "property_type": "starter_home",
                "timeline": "12_plus_months",
            },
            behavioral_data={
                "website_sessions": 2,
                "pages_viewed": 5,
                "property_views": 1,
                "calculator_usage": 0,
                "email_open_rate": 0.25,
                "email_click_rate": 0.05,
                "response_time_minutes": 1440,  # 24 hours
                "weekend_activity": False,
                "mobile_usage_percent": 0.30,
            },
            engagement_history=[
                {
                    "timestamp": datetime.now() - timedelta(days=5),
                    "action": "newsletter_signup",
                    "details": {"source": "blog_post", "topic": "first_time_buyer_tips"},
                }
            ],
            expected_agent_insights={
                AgentType.DEMOGRAPHIC_ANALYZER: {
                    "confidence": 0.65,
                    "opportunity_score": 45.2,
                    "risk_factors": ["lower_credit", "limited_down_payment", "long_timeline"],
                    "urgency_level": "low",
                }
            },
            expected_follow_up_strategy={
                "priority": "low",
                "primary_channel": "email",
                "backup_channel": None,
                "response_time_target": 1440,  # 24 hours
                "follow_up_sequence": [
                    {"delay_days": 1, "channel": "email", "message_type": "welcome_series"},
                    {"delay_weeks": 1, "channel": "email", "message_type": "market_education"},
                    {"delay_weeks": 2, "channel": "email", "message_type": "financing_tips"},
                ],
            },
            expected_routing_decision={
                "priority": "low",
                "agent_expertise_required": ["first_time_buyers", "financing_assistance"],
                "estimated_response_time": 240,  # minutes
                "predicted_success_rate": 0.35,
                "routing_confidence": 0.58,
            },
        )

    @staticmethod
    def investor_profile_lead() -> LeadProfile:
        """Investor profile requiring specialized handling"""
        lead_id = f"LEAD_INV_{uuid.uuid4().hex[:8]}"

        return LeadProfile(
            lead_id=lead_id,
            profile_type=LeadProfileType.INVESTOR,
            demographics={
                "age": 52,
                "income": 180000,
                "credit_score": 780,
                "down_payment": 100000,
                "employment_status": "self_employed",
                "family_size": 2,
                "location": "Austin, TX",
                "budget_min": 300000,
                "budget_max": 800000,
                "property_type": "investment",
                "timeline": "immediate",
                "investment_goals": ["cash_flow", "appreciation"],
            },
            behavioral_data={
                "website_sessions": 8,
                "pages_viewed": 32,
                "property_views": 15,
                "calculator_usage": 12,
                "cap_rate_calculations": 8,
                "cash_flow_analysis": 6,
                "email_open_rate": 0.75,
                "email_click_rate": 0.28,
                "response_time_minutes": 45,
                "weekend_activity": True,
                "mobile_usage_percent": 0.40,
            },
            engagement_history=[
                {
                    "timestamp": datetime.now() - timedelta(hours=3),
                    "action": "investment_calculator",
                    "details": {"properties_analyzed": 5, "cap_rate_threshold": 8.5},
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=1),
                    "action": "market_report_download",
                    "details": {"report": "austin_investment_trends_q4_2025"},
                },
            ],
            expected_agent_insights={
                AgentType.DEMOGRAPHIC_ANALYZER: {
                    "confidence": 0.88,
                    "opportunity_score": 85.7,
                    "profile_type": "experienced_investor",
                    "urgency_level": "high",
                },
                AgentType.INTENT_DETECTOR: {
                    "confidence": 0.91,
                    "opportunity_score": 87.3,
                    "investment_signals": ["cap_rate_focus", "cash_flow_analysis", "market_research"],
                    "purchase_probability": 0.79,
                },
            },
            expected_follow_up_strategy={
                "priority": "high",
                "primary_channel": "phone",
                "backup_channel": "email",
                "response_time_target": 30,  # minutes
                "content_type": "investment_focused",
                "follow_up_sequence": [
                    {"delay_minutes": 0, "channel": "phone", "message_type": "investment_consultation"},
                    {"delay_hours": 1, "channel": "email", "message_type": "market_analysis"},
                    {"delay_hours": 4, "channel": "email", "message_type": "property_opportunities"},
                ],
            },
            expected_routing_decision={
                "priority": "high",
                "agent_expertise_required": ["investment_properties", "commercial_real_estate", "cap_rate_analysis"],
                "estimated_response_time": 30,  # minutes
                "predicted_success_rate": 0.78,
                "routing_confidence": 0.87,
            },
        )

    @classmethod
    def random_lead(cls) -> LeadProfile:
        """Generate random lead for performance testing"""
        import random

        profile_types = [
            cls.high_intent_lead,
            cls.medium_engagement_lead,
            cls.low_engagement_lead,
            cls.investor_profile_lead,
        ]

        return random.choice(profile_types)()


class MockAgentInsightFactory:
    """Factory for creating realistic agent insights"""

    @staticmethod
    def create_insight(
        agent_type: AgentType, confidence: float = 0.80, opportunity_score: float = 75.0, urgency: str = "medium"
    ) -> AgentInsight:
        """Create a realistic agent insight for testing"""

        agent_responses = {
            AgentType.DEMOGRAPHIC_ANALYZER: {
                "primary_finding": f"Lead demographics suggest {opportunity_score:.1f}% opportunity score",
                "supporting_evidence": [
                    f"Income level appropriate for target market",
                    f"Credit score within acceptable range",
                    f"Timeline aligns with current inventory",
                ],
                "recommendations": [
                    f"Prioritize based on {urgency} urgency level",
                    f"Focus on demographic strengths in outreach",
                ],
            },
            AgentType.BEHAVIORAL_PROFILER: {
                "primary_finding": f"Behavioral patterns indicate {urgency} intent level",
                "supporting_evidence": [
                    f"Website engagement consistent with {urgency} buyers",
                    f"Response timing indicates {urgency} interest",
                    f"Content consumption suggests serious intent",
                ],
                "recommendations": [
                    f"Tailor communication cadence for {urgency} intent",
                    f"Focus on behavioral triggers in messaging",
                ],
            },
            AgentType.INTENT_DETECTOR: {
                "primary_finding": f"Purchase intent detected at {confidence * 100:.1f}% confidence",
                "supporting_evidence": [
                    f"Multiple intent signals present",
                    f"Timeline analysis suggests immediate need",
                    f"Financial qualification indicators positive",
                ],
                "recommendations": [f"Fast-track for {urgency} follow-up", f"Prepare property recommendations"],
            },
        }

        response_data = agent_responses.get(
            agent_type,
            {
                "primary_finding": f"Analysis complete with {confidence:.1f} confidence",
                "supporting_evidence": [f"Standard analysis for {agent_type.value}"],
                "recommendations": [f"Follow standard protocol for {urgency} leads"],
            },
        )

        return AgentInsight(
            agent_type=agent_type,
            confidence=confidence,
            primary_finding=response_data["primary_finding"],
            supporting_evidence=response_data["supporting_evidence"],
            recommendations=response_data["recommendations"],
            risk_factors=[],
            opportunity_score=opportunity_score,
            urgency_level=urgency,
            processing_time_ms=100.0 + (confidence * 50),  # Realistic processing time
            data_sources=[f"{agent_type.value}_data", "lead_profile", "behavioral_history"],
            metadata={
                "confidence_breakdown": {
                    "data_quality": confidence * 0.9,
                    "pattern_matching": confidence * 1.1,
                    "historical_accuracy": confidence * 0.95,
                },
                "opportunity_breakdown": {
                    "demographic_fit": opportunity_score * 0.4,
                    "behavioral_indicators": opportunity_score * 0.35,
                    "intent_signals": opportunity_score * 0.25,
                },
            },
        )


class MockFollowUpRecommendationFactory:
    """Factory for creating realistic follow-up recommendations"""

    @staticmethod
    def create_recommendation(
        lead_profile: LeadProfile, agent_type: AgentType, confidence: float = 0.80
    ) -> FollowUpRecommendation:
        """Create realistic follow-up recommendation based on lead profile"""

        strategy = lead_profile.expected_follow_up_strategy

        return FollowUpRecommendation(
            agent_type=agent_type,
            confidence=confidence,
            recommended_action=f"{strategy['primary_channel']}_outreach",
            reasoning=f"Based on {lead_profile.profile_type.value} profile analysis",
            optimal_timing=datetime.now() + timedelta(minutes=strategy["response_time_target"]),
            communication_channel=strategy["primary_channel"],
            personalization_data={
                "lead_interests": lead_profile.demographics.get("property_type", "general"),
                "urgency_level": strategy["priority"],
                "budget_range": f"{lead_profile.demographics.get('budget_min', 0)}-{lead_profile.demographics.get('budget_max', 0)}",
                "location": lead_profile.demographics.get("location", "Unknown"),
            },
            expected_response_rate=confidence * 0.9,
            risk_assessment={
                "timing_risk": "low" if strategy["priority"] == "urgent" else "medium",
                "channel_risk": "low",
                "content_risk": "low",
            },
        )


# Export all factories for easy import in tests
__all__ = [
    "LeadProfileType",
    "LeadProfile",
    "LeadProfileFactory",
    "MockAgentInsightFactory",
    "MockFollowUpRecommendationFactory",
]
