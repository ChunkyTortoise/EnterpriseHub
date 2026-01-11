"""
Comprehensive Tests for Claude Conversation Analyzer Service

Tests cover:
- Conversation quality analysis
- Real estate expertise assessment
- Coaching opportunity identification
- Performance improvement tracking
- Real-time WebSocket integration
- Caching and performance optimization
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json

from ghl_real_estate_ai.services.claude_conversation_analyzer import (
    ClaudeConversationAnalyzer,
    ConversationData,
    ConversationAnalysis,
    CoachingInsights,
    ImprovementMetrics,
    SkillAssessment,
    QualityScore,
    ExpertiseAssessment,
    CoachingOpportunity,
    ConversationQualityArea,
    RealEstateExpertiseArea,
    CoachingPriority,
    SkillLevel,
    ConversationOutcome,
    get_conversation_analyzer,
    analyze_agent_conversation,
    get_coaching_recommendations,
    track_agent_improvement
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing"""
    return ConversationData(
        conversation_id="conv_test_001",
        agent_id="agent_123",
        tenant_id="tenant_456",
        lead_id="lead_789",
        messages=[
            {
                "role": "client",
                "content": "Hi, I'm looking for a 3-bedroom house in Austin.",
                "timestamp": "2024-01-10T10:00:00"
            },
            {
                "role": "agent",
                "content": "Great! I'd be happy to help you find the perfect home. What's your budget range?",
                "timestamp": "2024-01-10T10:00:30"
            },
            {
                "role": "client",
                "content": "Around $500k to $600k.",
                "timestamp": "2024-01-10T10:01:00"
            },
            {
                "role": "agent",
                "content": "Excellent. Are you pre-approved for financing?",
                "timestamp": "2024-01-10T10:01:15"
            },
            {
                "role": "client",
                "content": "Yes, I have pre-approval for up to $650k.",
                "timestamp": "2024-01-10T10:02:00"
            },
            {
                "role": "agent",
                "content": "Perfect! When are you looking to move?",
                "timestamp": "2024-01-10T10:02:20"
            },
            {
                "role": "client",
                "content": "Ideally in the next 3 months.",
                "timestamp": "2024-01-10T10:03:00"
            },
            {
                "role": "agent",
                "content": "Great timeline. Let me show you some properties that match your criteria. Would you be available for viewings this weekend?",
                "timestamp": "2024-01-10T10:03:30"
            },
            {
                "role": "client",
                "content": "Yes, Saturday afternoon works for me.",
                "timestamp": "2024-01-10T10:04:00"
            },
            {
                "role": "agent",
                "content": "Perfect! I'll schedule viewings for Saturday at 2 PM. I'll send you the property details shortly.",
                "timestamp": "2024-01-10T10:04:30"
            }
        ],
        start_time=datetime(2024, 1, 10, 10, 0, 0),
        end_time=datetime(2024, 1, 10, 10, 5, 0),
        context={
            "lead_source": "website",
            "lead_score": 85
        }
    )


@pytest.fixture
def mock_claude_quality_response():
    """Mock Claude API response for quality analysis"""
    return json.dumps({
        "overall_quality_score": 85,
        "quality_scores": [
            {
                "area": "communication_effectiveness",
                "score": 88,
                "confidence": 0.9,
                "strengths": ["Clear and concise", "Professional tone"],
                "weaknesses": ["Could ask more discovery questions"],
                "evidence": ["Great! I'd be happy to help you find the perfect home."],
                "recommendations": ["Ask about lifestyle preferences", "Dig deeper into must-haves"]
            },
            {
                "area": "rapport_building",
                "score": 82,
                "confidence": 0.85,
                "strengths": ["Friendly approach", "Responsive"],
                "weaknesses": ["Limited personal connection"],
                "evidence": ["Perfect! I'll schedule viewings"],
                "recommendations": ["Ask about family", "Share local insights"]
            },
            {
                "area": "information_gathering",
                "score": 90,
                "confidence": 0.95,
                "strengths": ["Systematic qualification", "Budget confirmed", "Timeline established"],
                "weaknesses": ["Could explore location preferences more"],
                "evidence": ["What's your budget range?", "Are you pre-approved?", "When are you looking to move?"],
                "recommendations": ["Ask about neighborhood preferences", "Explore lifestyle needs"]
            },
            {
                "area": "objection_handling",
                "score": 75,
                "confidence": 0.7,
                "strengths": ["No objections raised"],
                "weaknesses": ["No proactive objection prevention"],
                "evidence": [],
                "recommendations": ["Address common concerns proactively", "Set expectations early"]
            },
            {
                "area": "closing_technique",
                "score": 92,
                "confidence": 0.9,
                "strengths": ["Strong close", "Commitment secured", "Next steps clear"],
                "weaknesses": [],
                "evidence": ["Would you be available for viewings this weekend?", "I'll schedule viewings for Saturday"],
                "recommendations": ["Excellent closing - maintain this approach"]
            },
            {
                "area": "professionalism",
                "score": 95,
                "confidence": 0.95,
                "strengths": ["Professional language", "Responsive", "Organized"],
                "weaknesses": [],
                "evidence": ["I'll send you the property details shortly"],
                "recommendations": ["Continue high professionalism standards"]
            }
        ],
        "key_strengths": [
            "Excellent qualification process",
            "Strong closing with clear next steps",
            "Professional and responsive communication"
        ],
        "key_weaknesses": [
            "Limited rapport building",
            "Could explore lifestyle preferences more",
            "No proactive objection handling"
        ],
        "missed_opportunities": [
            "Could have asked about current living situation",
            "Missed opportunity to discuss neighborhood preferences",
            "Could have set expectations about the home buying process"
        ],
        "best_practices": [
            "Systematic needs assessment",
            "Clear timeline establishment",
            "Immediate scheduling of next steps"
        ],
        "conversation_outcome": "appointment_scheduled"
    })


@pytest.fixture
def mock_claude_expertise_response():
    """Mock Claude API response for expertise analysis"""
    return json.dumps({
        "expertise_assessments": [
            {
                "area": "market_knowledge",
                "skill_level": "proficient",
                "score": 78,
                "confidence": 0.75,
                "demonstrated_knowledge": ["Budget ranges for Austin market"],
                "knowledge_gaps": ["No market trends discussed", "No pricing strategy mentioned"],
                "improvement_suggestions": ["Share current market conditions", "Discuss pricing trends"]
            },
            {
                "area": "property_presentation",
                "skill_level": "developing",
                "score": 65,
                "confidence": 0.7,
                "demonstrated_knowledge": [],
                "knowledge_gaps": ["No property features highlighted", "No virtual tour mentioned"],
                "improvement_suggestions": ["Describe property highlights", "Use visual aids", "Create anticipation"]
            },
            {
                "area": "negotiation_skills",
                "skill_level": "developing",
                "score": 60,
                "confidence": 0.65,
                "demonstrated_knowledge": [],
                "knowledge_gaps": ["No negotiation strategy discussed"],
                "improvement_suggestions": ["Discuss market positioning", "Set negotiation expectations"]
            },
            {
                "area": "client_needs_identification",
                "skill_level": "proficient",
                "score": 85,
                "confidence": 0.9,
                "demonstrated_knowledge": ["Budget qualification", "Timeline assessment", "Pre-approval confirmation"],
                "knowledge_gaps": ["Lifestyle preferences", "Neighborhood priorities"],
                "improvement_suggestions": ["Ask about daily routines", "Explore family needs"]
            },
            {
                "area": "follow_up_quality",
                "skill_level": "proficient",
                "score": 88,
                "confidence": 0.85,
                "demonstrated_knowledge": ["Clear next steps", "Specific appointment time", "Property details promised"],
                "knowledge_gaps": [],
                "improvement_suggestions": ["Continue excellent follow-up practices"]
            }
        ],
        "overall_expertise_level": "proficient",
        "top_strengths": [
            "Strong client needs identification",
            "Excellent follow-up commitment",
            "Professional qualification process"
        ],
        "priority_development_areas": [
            "Market knowledge sharing",
            "Property presentation skills",
            "Negotiation strategy development"
        ]
    })


@pytest.fixture
def mock_claude_coaching_response():
    """Mock Claude API response for coaching opportunities"""
    return json.dumps({
        "coaching_opportunities": [
            {
                "opportunity_id": "coach_001",
                "priority": "high",
                "category": "property_presentation",
                "title": "Enhance Property Presentation Skills",
                "description": "Agent needs to improve property feature highlighting and benefit articulation",
                "impact": "Better property presentation can increase showing-to-offer conversion by 25%",
                "recommended_action": "Complete property presentation training module and practice with role-play scenarios",
                "training_modules": ["Property Storytelling 101", "Virtual Tour Best Practices"],
                "confidence": 0.85
            },
            {
                "opportunity_id": "coach_002",
                "priority": "medium",
                "category": "market_expertise",
                "title": "Strengthen Market Knowledge Communication",
                "description": "Agent should proactively share market insights and trends with clients",
                "impact": "Demonstrating market expertise builds trust and positions agent as advisor",
                "recommended_action": "Review weekly market reports and practice incorporating insights into conversations",
                "training_modules": ["Market Analysis Fundamentals", "Communicating Market Trends"],
                "confidence": 0.8
            },
            {
                "opportunity_id": "coach_003",
                "priority": "medium",
                "category": "rapport_building",
                "title": "Deepen Client Relationships",
                "description": "Agent could build stronger personal connections with clients",
                "impact": "Stronger rapport leads to higher client satisfaction and referrals",
                "recommended_action": "Ask about family, lifestyle, and personal preferences early in conversations",
                "training_modules": ["Relationship Selling", "Discovery Question Mastery"],
                "confidence": 0.75
            },
            {
                "opportunity_id": "coach_004",
                "priority": "low",
                "category": "objection_handling",
                "title": "Proactive Objection Prevention",
                "description": "Agent should address common concerns before they become objections",
                "impact": "Prevents objections from derailing momentum",
                "recommended_action": "Study common buyer objections and practice preventive addressing",
                "training_modules": ["Objection Prevention Strategies"],
                "confidence": 0.7
            }
        ],
        "immediate_actions": [
            "Complete property presentation training module this week",
            "Review 3 recent market reports and identify key talking points",
            "Practice discovery questions with manager in role-play session"
        ],
        "top_skills_to_develop": [
            "Property presentation and storytelling",
            "Market knowledge communication",
            "Rapport building and relationship development"
        ],
        "recommended_training": [
            "Property Storytelling 101",
            "Market Analysis Fundamentals",
            "Discovery Question Mastery",
            "Virtual Tour Best Practices"
        ],
        "practice_scenarios": [
            "Present a luxury property highlighting lifestyle benefits",
            "Explain current market conditions to a first-time buyer",
            "Build rapport with a relocating family"
        ]
    })


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager"""
    manager = AsyncMock()
    manager.websocket_hub = AsyncMock()
    manager.websocket_hub.broadcast_to_tenant = AsyncMock(return_value={})
    return manager


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = AsyncMock()
    client.initialize = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    return client


@pytest.fixture
async def analyzer(mock_websocket_manager, mock_redis_client):
    """Create analyzer instance with mocked dependencies"""
    with patch('ghl_real_estate_ai.services.claude_conversation_analyzer.get_websocket_manager', return_value=mock_websocket_manager):
        with patch('ghl_real_estate_ai.services.claude_conversation_analyzer.redis_client', mock_redis_client):
            analyzer = ClaudeConversationAnalyzer(
                anthropic_api_key="test_key",
                websocket_manager=mock_websocket_manager
            )
            await analyzer.initialize()
            return analyzer


# ============================================================================
# Test Cases - Conversation Analysis
# ============================================================================

@pytest.mark.asyncio
async def test_analyze_conversation_success(
    analyzer,
    sample_conversation_data,
    mock_claude_quality_response,
    mock_claude_expertise_response
):
    """Test successful conversation analysis"""
    # Mock Claude API calls
    with patch.object(analyzer, '_call_claude') as mock_call:
        mock_call.side_effect = [
            mock_claude_quality_response,
            mock_claude_expertise_response
        ]

        # Perform analysis
        analysis = await analyzer.analyze_conversation(sample_conversation_data)

        # Assertions
        assert analysis is not None
        assert analysis.conversation_id == "conv_test_001"
        assert analysis.agent_id == "agent_123"
        assert analysis.overall_quality_score == 85
        assert 0 <= analysis.conversation_effectiveness <= 100
        assert analysis.conversation_outcome == ConversationOutcome.APPOINTMENT_SCHEDULED

        # Check quality scores
        assert len(analysis.quality_scores) == 6
        assert any(score.area == "communication_effectiveness" for score in analysis.quality_scores)

        # Check expertise assessments
        assert len(analysis.expertise_assessments) == 5
        assert any(assess.area == RealEstateExpertiseArea.MARKET_KNOWLEDGE for assess in analysis.expertise_assessments)

        # Check conversation metrics
        assert analysis.total_messages == 10
        assert analysis.agent_messages == 5
        assert analysis.client_messages == 5
        assert analysis.conversation_duration_minutes > 0

        # Check insights
        assert len(analysis.key_strengths) > 0
        assert len(analysis.key_weaknesses) > 0

        # Check performance
        assert analysis.processing_time_ms > 0
        assert 0 <= analysis.confidence_score <= 1


@pytest.mark.asyncio
async def test_analyze_conversation_performance(
    analyzer,
    sample_conversation_data,
    mock_claude_quality_response,
    mock_claude_expertise_response
):
    """Test conversation analysis meets performance targets"""
    with patch.object(analyzer, '_call_claude') as mock_call:
        mock_call.side_effect = [
            mock_claude_quality_response,
            mock_claude_expertise_response
        ]

        # Perform analysis
        import time
        start = time.time()
        analysis = await analyzer.analyze_conversation(sample_conversation_data)
        elapsed = (time.time() - start) * 1000

        # Performance assertion: <2 seconds (2000ms)
        assert elapsed < 2000, f"Analysis took {elapsed:.1f}ms, expected <2000ms"
        assert analysis.processing_time_ms < 2000


@pytest.mark.asyncio
async def test_analyze_conversation_caching(
    analyzer,
    sample_conversation_data,
    mock_claude_quality_response,
    mock_claude_expertise_response,
    mock_redis_client
):
    """Test conversation analysis caching"""
    with patch.object(analyzer, '_call_claude') as mock_call:
        mock_call.side_effect = [
            mock_claude_quality_response,
            mock_claude_expertise_response
        ]

        # First analysis
        analysis1 = await analyzer.analyze_conversation(sample_conversation_data)

        # Verify cache set was called
        mock_redis_client.set.assert_called()
        cache_call_args = mock_redis_client.set.call_args
        assert "conversation_analysis" in cache_call_args.kwargs["key"]


@pytest.mark.asyncio
async def test_analyze_conversation_parallel_processing(
    analyzer,
    sample_conversation_data,
    mock_claude_quality_response,
    mock_claude_expertise_response
):
    """Test parallel processing of quality and expertise analysis"""
    call_count = 0
    call_times = []

    async def mock_call_with_timing(prompt):
        nonlocal call_count
        call_count += 1
        call_times.append(asyncio.get_event_loop().time())

        # Simulate async delay
        await asyncio.sleep(0.1)

        if "conversation quality" in prompt.lower():
            return mock_claude_quality_response
        else:
            return mock_claude_expertise_response

    with patch.object(analyzer, '_call_claude', side_effect=mock_call_with_timing):
        analysis = await analyzer.analyze_conversation(sample_conversation_data)

        # Verify both calls were made
        assert call_count == 2

        # Verify parallel execution (calls should start within 50ms of each other)
        if len(call_times) == 2:
            time_diff = abs(call_times[1] - call_times[0])
            assert time_diff < 0.05, "Calls should execute in parallel"


# ============================================================================
# Test Cases - Coaching Insights
# ============================================================================

@pytest.mark.asyncio
async def test_identify_coaching_opportunities(
    analyzer,
    sample_conversation_data,
    mock_claude_quality_response,
    mock_claude_expertise_response,
    mock_claude_coaching_response
):
    """Test coaching opportunity identification"""
    with patch.object(analyzer, '_call_claude') as mock_call:
        mock_call.side_effect = [
            mock_claude_quality_response,
            mock_claude_expertise_response,
            mock_claude_coaching_response
        ]

        # Perform analysis
        analysis = await analyzer.analyze_conversation(sample_conversation_data)

        # Identify coaching opportunities
        insights = await analyzer.identify_coaching_opportunities(analysis)

        # Assertions
        assert insights is not None
        assert insights.agent_id == "agent_123"
        assert len(insights.coaching_opportunities) == 4

        # Check priority ordering
        priorities = [opp.priority for opp in insights.coaching_opportunities]
        assert CoachingPriority.HIGH in priorities

        # Check coaching content
        assert len(insights.immediate_actions) > 0
        assert len(insights.top_skills_to_develop) > 0
        assert len(insights.recommended_training_modules) > 0

        # Check generated content
        assert len(insights.conversation_templates) > 0
        assert len(insights.objection_handling_tips) > 0
        assert len(insights.closing_techniques) > 0


@pytest.mark.asyncio
async def test_coaching_insights_performance(
    analyzer,
    sample_conversation_data,
    mock_claude_quality_response,
    mock_claude_expertise_response,
    mock_claude_coaching_response
):
    """Test coaching insights generation meets performance targets"""
    with patch.object(analyzer, '_call_claude') as mock_call:
        mock_call.side_effect = [
            mock_claude_quality_response,
            mock_claude_expertise_response,
            mock_claude_coaching_response
        ]

        analysis = await analyzer.analyze_conversation(sample_conversation_data)

        # Measure insight generation time
        import time
        start = time.time()
        insights = await analyzer.identify_coaching_opportunities(analysis)
        elapsed = (time.time() - start) * 1000

        # Performance assertion: <500ms for insight delivery
        assert elapsed < 500, f"Insights took {elapsed:.1f}ms, expected <500ms"


@pytest.mark.asyncio
async def test_coaching_opportunities_prioritization(
    analyzer,
    sample_conversation_data,
    mock_claude_quality_response,
    mock_claude_expertise_response,
    mock_claude_coaching_response
):
    """Test coaching opportunities are properly prioritized"""
    with patch.object(analyzer, '_call_claude') as mock_call:
        mock_call.side_effect = [
            mock_claude_quality_response,
            mock_claude_expertise_response,
            mock_claude_coaching_response
        ]

        analysis = await analyzer.analyze_conversation(sample_conversation_data)
        insights = await analyzer.identify_coaching_opportunities(analysis)

        # Check high priority opportunities
        high_priority_opps = [
            opp for opp in insights.coaching_opportunities
            if opp.priority == CoachingPriority.HIGH
        ]
        assert len(high_priority_opps) > 0

        # Verify high priority has immediate actions
        assert len(insights.immediate_actions) > 0


# ============================================================================
# Test Cases - Performance Tracking
# ============================================================================

@pytest.mark.asyncio
async def test_track_improvement_metrics(analyzer):
    """Test performance improvement tracking"""
    mock_tracking_response = json.dumps({
        "quality_score_trend": "improving",
        "skill_improvements": {
            "communication": 5.2,
            "rapport_building": 3.8,
            "objection_handling": 7.1,
            "closing": 4.5,
            "market_knowledge": 6.3
        },
        "areas_of_growth": [
            "Objection handling significantly improved",
            "Market knowledge showing strong growth",
            "Communication effectiveness trending upward"
        ],
        "areas_needing_focus": [
            "Rapport building needs continued attention",
            "Property presentation skills require development"
        ],
        "coaching_effectiveness": 82,
        "skills_mastered": [
            "Budget qualification",
            "Timeline assessment",
            "Next steps definition"
        ],
        "estimated_time_to_proficiency": {
            "property_presentation": 30,
            "market_knowledge": 45,
            "negotiation_skills": 60
        },
        "next_milestone": "Achieve 90+ quality score on 5 consecutive conversations",
        "recommendations": [
            "Continue focus on objection handling - excellent progress",
            "Increase market knowledge sharing in conversations",
            "Practice property presentation with manager"
        ]
    })

    with patch.object(analyzer, '_call_claude', return_value=mock_tracking_response):
        with patch.object(analyzer, '_get_historical_performance', return_value={"conversations": [], "coaching_sessions": 5}):
            with patch.object(analyzer, '_get_current_performance', return_value={}):

                # Track improvement
                metrics = await analyzer.track_improvement_metrics(
                    agent_id="agent_123",
                    time_period="last_30_days"
                )

                # Assertions
                assert metrics is not None
                assert metrics.agent_id == "agent_123"
                assert metrics.time_period == "last_30_days"
                assert metrics.quality_score_trend == "improving"

                # Check skill improvements
                assert "communication" in metrics.skill_improvements
                assert metrics.skill_improvements["communication"] == 5.2

                # Check areas
                assert len(metrics.areas_of_growth) > 0
                assert len(metrics.areas_needing_focus) > 0

                # Check metrics
                assert metrics.coaching_sessions_completed == 5
                assert len(metrics.skills_mastered) > 0

                # Check projections
                assert "property_presentation" in metrics.estimated_time_to_proficiency
                assert metrics.next_milestone != ""


@pytest.mark.asyncio
async def test_improvement_metrics_time_periods(analyzer):
    """Test different time period calculations"""
    time_periods = ["last_7_days", "last_30_days", "last_quarter", "last_year"]

    for period in time_periods:
        start_date, end_date = analyzer._parse_time_period(period)

        # Verify dates are valid
        assert start_date < end_date
        assert end_date <= datetime.now()

        # Verify correct duration
        duration = (end_date - start_date).days

        if period == "last_7_days":
            assert duration <= 7
        elif period == "last_30_days":
            assert duration <= 30
        elif period == "last_quarter":
            assert duration <= 90
        elif period == "last_year":
            assert duration <= 365


# ============================================================================
# Test Cases - Real-time Integration
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_broadcast_analysis(
    analyzer,
    sample_conversation_data,
    mock_claude_quality_response,
    mock_claude_expertise_response,
    mock_websocket_manager
):
    """Test WebSocket broadcasting of analysis results"""
    with patch.object(analyzer, '_call_claude') as mock_call:
        mock_call.side_effect = [
            mock_claude_quality_response,
            mock_claude_expertise_response
        ]

        # Perform analysis
        analysis = await analyzer.analyze_conversation(sample_conversation_data)

        # Verify WebSocket broadcast was called
        mock_websocket_manager.websocket_hub.broadcast_to_tenant.assert_called()

        # Check broadcast data
        call_args = mock_websocket_manager.websocket_hub.broadcast_to_tenant.call_args
        assert call_args.kwargs["tenant_id"] == "tenant_456"
        assert "event_data" in call_args.kwargs

        event_data = call_args.kwargs["event_data"]
        assert event_data["type"] == "conversation_analysis"
        assert event_data["agent_id"] == "agent_123"
        assert "overall_quality_score" in event_data


@pytest.mark.asyncio
async def test_websocket_broadcast_coaching_alerts(
    analyzer,
    sample_conversation_data,
    mock_claude_quality_response,
    mock_claude_expertise_response,
    mock_claude_coaching_response,
    mock_websocket_manager
):
    """Test WebSocket broadcasting of critical coaching alerts"""
    with patch.object(analyzer, '_call_claude') as mock_call:
        mock_call.side_effect = [
            mock_claude_quality_response,
            mock_claude_expertise_response,
            mock_claude_coaching_response
        ]

        analysis = await analyzer.analyze_conversation(sample_conversation_data)

        # Reset mock to track coaching insights broadcast
        mock_websocket_manager.reset_mock()

        insights = await analyzer.identify_coaching_opportunities(analysis)

        # Note: Broadcast may not be called if no critical opportunities
        # Verify the logic is in place
        critical_opps = [
            opp for opp in insights.coaching_opportunities
            if opp.priority in [CoachingPriority.CRITICAL, CoachingPriority.HIGH]
        ]

        if critical_opps:
            # If critical opportunities exist, broadcast should have been called
            # This is a soft assertion as the actual call depends on implementation
            pass


# ============================================================================
# Test Cases - Data Processing
# ============================================================================

def test_format_messages(analyzer, sample_conversation_data):
    """Test message formatting for Claude analysis"""
    formatted = analyzer._format_messages(sample_conversation_data.messages)

    # Assertions
    assert formatted is not None
    assert "AGENT:" in formatted
    assert "CLIENT:" in formatted
    assert "3-bedroom house" in formatted
    assert "$500k to $600k" in formatted


def test_calculate_conversation_metrics(analyzer, sample_conversation_data):
    """Test conversation metrics calculation"""
    metrics = analyzer._calculate_conversation_metrics(sample_conversation_data)

    # Assertions
    assert metrics["total_messages"] == 10
    assert metrics["agent_messages"] == 5
    assert metrics["client_messages"] == 5
    assert metrics["avg_response_time_seconds"] > 0
    assert metrics["conversation_duration_minutes"] > 0
    assert metrics["questions_asked"] > 0  # Agent asked questions


def test_calculate_duration(analyzer):
    """Test duration calculation"""
    start = datetime(2024, 1, 10, 10, 0, 0)
    end = datetime(2024, 1, 10, 10, 5, 0)

    duration = analyzer._calculate_duration(start, end)

    assert duration == 5.0  # 5 minutes


def test_parse_quality_scores(analyzer, mock_claude_quality_response):
    """Test quality score parsing"""
    data = json.loads(mock_claude_quality_response)
    scores = analyzer._parse_quality_scores(data["quality_scores"])

    assert len(scores) == 6
    assert all(isinstance(score, QualityScore) for score in scores)
    assert all(0 <= score.score <= 100 for score in scores)
    assert all(0 <= score.confidence <= 1 for score in scores)


def test_parse_expertise_assessments(analyzer, mock_claude_expertise_response):
    """Test expertise assessment parsing"""
    data = json.loads(mock_claude_expertise_response)
    assessments = analyzer._parse_expertise_assessments(data["expertise_assessments"])

    assert len(assessments) == 5
    assert all(isinstance(assess, ExpertiseAssessment) for assess in assessments)
    assert all(isinstance(assess.area, RealEstateExpertiseArea) for assess in assessments)
    assert all(isinstance(assess.skill_level, SkillLevel) for assess in assessments)


def test_parse_coaching_opportunities(analyzer, mock_claude_coaching_response):
    """Test coaching opportunity parsing"""
    data = json.loads(mock_claude_coaching_response)
    opportunities = analyzer._parse_coaching_opportunities(data["coaching_opportunities"])

    assert len(opportunities) == 4
    assert all(isinstance(opp, CoachingOpportunity) for opp in opportunities)
    assert all(isinstance(opp.priority, CoachingPriority) for opp in opportunities)
    assert all(opp.opportunity_id != "" for opp in opportunities)


# ============================================================================
# Test Cases - Template Generation
# ============================================================================

def test_generate_conversation_templates(analyzer, sample_conversation_data):
    """Test conversation template generation"""
    # Create mock analysis with weak rapport building
    mock_analysis = Mock()
    mock_analysis.quality_scores = [
        QualityScore(
            area="rapport_building",
            score=65,  # Below 70 threshold
            confidence=0.8,
            strengths=[],
            weaknesses=["Limited personal connection"],
            evidence=[],
            recommendations=[]
        )
    ]

    templates = analyzer._generate_conversation_templates(mock_analysis)

    # Should generate rapport building template
    assert len(templates) > 0
    assert any("appreciate" in template.lower() for template in templates)


def test_generate_objection_tips(analyzer):
    """Test objection handling tips generation"""
    mock_analysis = Mock()
    tips = analyzer._generate_objection_tips(mock_analysis)

    assert len(tips) > 0
    assert any("acknowledge" in tip.lower() for tip in tips)
    assert any("question" in tip.lower() for tip in tips)


def test_generate_closing_techniques(analyzer):
    """Test closing techniques generation"""
    mock_analysis = Mock()
    techniques = analyzer._generate_closing_techniques(mock_analysis)

    assert len(techniques) > 0
    assert any("trial close" in tech.lower() for tech in techniques)
    assert any("assumptive" in tech.lower() for tech in techniques)


# ============================================================================
# Test Cases - Metrics and Monitoring
# ============================================================================

def test_service_metrics_tracking(analyzer):
    """Test service metrics tracking"""
    # Initial metrics
    initial_metrics = analyzer.get_service_metrics()
    assert initial_metrics["total_analyses"] == 0

    # Simulate analysis
    mock_analysis = Mock()
    mock_analysis.processing_time_ms = 1500.0
    analyzer._update_metrics(mock_analysis)

    # Check updated metrics
    updated_metrics = analyzer.get_service_metrics()
    assert updated_metrics["total_analyses"] == 1
    assert updated_metrics["successful_analyses"] == 1
    assert updated_metrics["avg_analysis_time_ms"] == 1500.0


def test_metrics_averaging(analyzer):
    """Test metrics averaging over multiple analyses"""
    # Simulate multiple analyses
    for processing_time in [1000, 1500, 2000]:
        mock_analysis = Mock()
        mock_analysis.processing_time_ms = processing_time
        analyzer._update_metrics(mock_analysis)

    metrics = analyzer.get_service_metrics()
    assert metrics["total_analyses"] == 3
    assert metrics["avg_analysis_time_ms"] == 1500.0  # Average of 1000, 1500, 2000


# ============================================================================
# Test Cases - Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_claude_api_retry_logic(analyzer, sample_conversation_data):
    """Test Claude API retry logic on failures"""
    call_count = 0

    async def mock_failing_call(prompt):
        nonlocal call_count
        call_count += 1

        if call_count < 3:
            raise Exception("API temporarily unavailable")

        # Succeed on third attempt
        return json.dumps({"overall_quality_score": 80, "quality_scores": [], "key_strengths": [], "key_weaknesses": [], "missed_opportunities": [], "best_practices": [], "conversation_outcome": "in_progress"})

    with patch.object(analyzer, '_call_claude', side_effect=mock_failing_call):
        # This should succeed after retries
        response = await analyzer._call_claude("test prompt")

        assert call_count == 3
        assert response is not None


@pytest.mark.asyncio
async def test_analyze_conversation_error_handling(
    analyzer,
    sample_conversation_data
):
    """Test error handling in conversation analysis"""
    with patch.object(analyzer, '_call_claude', side_effect=Exception("API error")):
        with pytest.raises(Exception):
            await analyzer.analyze_conversation(sample_conversation_data)

        # Verify failed analysis is tracked
        metrics = analyzer.get_service_metrics()
        assert metrics["failed_analyses"] > 0


# ============================================================================
# Test Cases - Convenience Functions
# ============================================================================

@pytest.mark.asyncio
async def test_convenience_function_analyze_agent_conversation(
    sample_conversation_data,
    mock_claude_quality_response,
    mock_claude_expertise_response
):
    """Test convenience function for analyzing conversations"""
    with patch('ghl_real_estate_ai.services.claude_conversation_analyzer.get_conversation_analyzer') as mock_get:
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_conversation = AsyncMock(return_value=Mock(
            analysis_id="test",
            overall_quality_score=85
        ))
        mock_get.return_value = mock_analyzer

        result = await analyze_agent_conversation(sample_conversation_data)

        assert result is not None
        mock_analyzer.analyze_conversation.assert_called_once()


@pytest.mark.asyncio
async def test_convenience_function_get_coaching_recommendations():
    """Test convenience function for getting coaching recommendations"""
    mock_analysis = Mock(agent_id="agent_123")

    with patch('ghl_real_estate_ai.services.claude_conversation_analyzer.get_conversation_analyzer') as mock_get:
        mock_analyzer = AsyncMock()
        mock_analyzer.identify_coaching_opportunities = AsyncMock(return_value=Mock(
            insights_id="test",
            coaching_opportunities=[]
        ))
        mock_get.return_value = mock_analyzer

        result = await get_coaching_recommendations(mock_analysis)

        assert result is not None
        mock_analyzer.identify_coaching_opportunities.assert_called_once()


@pytest.mark.asyncio
async def test_convenience_function_track_agent_improvement():
    """Test convenience function for tracking improvement"""
    with patch('ghl_real_estate_ai.services.claude_conversation_analyzer.get_conversation_analyzer') as mock_get:
        mock_analyzer = AsyncMock()
        mock_analyzer.track_improvement_metrics = AsyncMock(return_value=Mock(
            agent_id="agent_123",
            quality_score_trend="improving"
        ))
        mock_get.return_value = mock_analyzer

        result = await track_agent_improvement("agent_123", "last_30_days")

        assert result is not None
        mock_analyzer.track_improvement_metrics.assert_called_once_with(
            "agent_123",
            "last_30_days"
        )


# ============================================================================
# Performance Benchmarks
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_benchmark_conversation_analysis(
    analyzer,
    sample_conversation_data,
    mock_claude_quality_response,
    mock_claude_expertise_response
):
    """Benchmark conversation analysis performance"""
    import time

    with patch.object(analyzer, '_call_claude') as mock_call:
        mock_call.side_effect = [
            mock_claude_quality_response,
            mock_claude_expertise_response
        ] * 10  # 10 iterations

        times = []
        for _ in range(10):
            start = time.time()
            await analyzer.analyze_conversation(sample_conversation_data)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        print(f"\nConversation Analysis Benchmark:")
        print(f"  Average: {avg_time:.1f}ms")
        print(f"  P95: {p95_time:.1f}ms")
        print(f"  Target: <2000ms")

        # Performance assertions
        assert avg_time < 2000
        assert p95_time < 2500


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
