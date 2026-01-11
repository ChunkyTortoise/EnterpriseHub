"""
Tests for Live Agent Coordinator

Comprehensive test suite covering:
- Agent workload management
- Intelligent lead routing
- Lead handoff orchestration
- Team coordination and alerts
- Claude AI coaching integration
- Performance metrics and analytics
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.services.live_agent_coordinator import (
    LiveAgentCoordinator,
    AgentWorkload,
    AgentStatus,
    LeadHandoff,
    TeamAlert,
    RoutingDecision,
    AlertPriority,
    HandoffStatus,
    get_coordinator
)


# =================== FIXTURES ===================

@pytest.fixture
def coordinator():
    """Create coordinator instance for testing."""
    return LiveAgentCoordinator(tenant_id="test_tenant")


@pytest.fixture
def sample_agent_data():
    """Sample agent data for testing."""
    return {
        'agent_id': 'agent_001',
        'name': 'Test Agent',
        'email': 'test@example.com',
        'role': 'agent',
        'specialties': ['residential', 'first_time_buyers']
    }


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        'name': 'John Doe',
        'budget_range': '$400K-$600K',
        'property_type': 'residential',
        'location': 'Austin, TX',
        'urgency': 'high',
        'complexity': 'moderate',
        'language': 'english',
        'source': 'website',
        'lead_score': 75.0
    }


# =================== WORKLOAD MANAGEMENT TESTS ===================

@pytest.mark.asyncio
async def test_update_agent_workload(coordinator, sample_agent_data):
    """Test updating agent workload information."""
    # Add agent to team manager
    coordinator.team_manager.add_agent(**sample_agent_data)

    # Update workload
    workload = await coordinator.update_agent_workload(
        agent_id='agent_001',
        workload_update={
            'status': 'available',
            'active_leads': 5,
            'capacity_utilization': 0.5
        }
    )

    assert workload is not None
    assert workload.agent_id == 'agent_001'
    assert workload.status == AgentStatus.AVAILABLE
    assert workload.active_leads == 5
    assert workload.capacity_utilization == 0.5


@pytest.mark.asyncio
async def test_get_agent_workload(coordinator, sample_agent_data):
    """Test retrieving agent workload."""
    coordinator.team_manager.add_agent(**sample_agent_data)

    # Initialize workload
    await coordinator.update_agent_workload(
        'agent_001',
        {'active_leads': 3, 'capacity_utilization': 0.3}
    )

    # Get workload
    workload = await coordinator.get_agent_workload('agent_001')

    assert workload is not None
    assert workload.agent_id == 'agent_001'
    assert workload.active_leads == 3


@pytest.mark.asyncio
async def test_get_team_workloads(coordinator, sample_agent_data):
    """Test getting workloads for all team agents."""
    # Add multiple agents
    for i in range(3):
        agent_data = sample_agent_data.copy()
        agent_data['agent_id'] = f'agent_00{i+1}'
        agent_data['name'] = f'Agent {i+1}'
        coordinator.team_manager.add_agent(**agent_data)

        await coordinator.update_agent_workload(
            f'agent_00{i+1}',
            {'active_leads': i+1, 'capacity_utilization': 0.2 * (i+1)}
        )

    # Get team workloads
    workloads = await coordinator.get_team_workloads()

    assert len(workloads) == 3
    assert all(isinstance(w, AgentWorkload) for w in workloads)


@pytest.mark.asyncio
async def test_calculate_workload_balance(coordinator, sample_agent_data):
    """Test workload balance calculation."""
    # Add agents with different workloads
    for i in range(3):
        agent_data = sample_agent_data.copy()
        agent_data['agent_id'] = f'agent_00{i+1}'
        coordinator.team_manager.add_agent(**agent_data)

        # Create balanced workload
        await coordinator.update_agent_workload(
            f'agent_00{i+1}',
            {'capacity_utilization': 0.5}  # All agents at 50%
        )

    balance_score = await coordinator.calculate_workload_balance()

    # Should be highly balanced (close to 1.0)
    assert balance_score >= 0.9
    assert balance_score <= 1.0


@pytest.mark.asyncio
async def test_agent_overload_alert(coordinator, sample_agent_data):
    """Test alert creation when agent is overloaded."""
    coordinator.team_manager.add_agent(**sample_agent_data)

    # Update to overloaded state
    await coordinator.update_agent_workload(
        'agent_001',
        {'capacity_utilization': 0.96}  # Above 95% threshold
    )

    # Check that alert was created
    alerts = [a for a in coordinator._active_alerts.values() if a.alert_type == 'agent_overload']
    assert len(alerts) > 0
    assert alerts[0].priority == AlertPriority.HIGH


# =================== INTELLIGENT ROUTING TESTS ===================

@pytest.mark.asyncio
async def test_route_lead_intelligent(coordinator, sample_agent_data, sample_lead_data):
    """Test intelligent lead routing algorithm."""
    # Add agents
    for i in range(3):
        agent_data = sample_agent_data.copy()
        agent_data['agent_id'] = f'agent_00{i+1}'
        agent_data['name'] = f'Agent {i+1}'
        coordinator.team_manager.add_agent(**agent_data)

        await coordinator.update_agent_workload(
            f'agent_00{i+1}',
            {
                'status': 'available',
                'active_leads': i,
                'capacity_utilization': 0.2 * i
            }
        )

    # Route lead
    decision = await coordinator.route_lead_intelligent(
        lead_id='lead_001',
        lead_data=sample_lead_data,
        priority='high'
    )

    assert decision is not None
    assert isinstance(decision, RoutingDecision)
    assert decision.lead_id == 'lead_001'
    assert decision.selected_agent_id in ['agent_001', 'agent_002', 'agent_003']
    assert decision.match_score > 0
    assert decision.assignment_time_ms > 0


@pytest.mark.asyncio
async def test_routing_with_expertise_match(coordinator, sample_agent_data, sample_lead_data):
    """Test that routing considers expertise match."""
    # Add agents with different specialties
    agent1 = sample_agent_data.copy()
    agent1['agent_id'] = 'agent_001'
    agent1['specialties'] = ['residential', 'first_time_buyers']
    coordinator.team_manager.add_agent(**agent1)

    agent2 = sample_agent_data.copy()
    agent2['agent_id'] = 'agent_002'
    agent2['name'] = 'Luxury Agent'
    agent2['specialties'] = ['luxury', 'investment']
    coordinator.team_manager.add_agent(**agent2)

    # Initialize both agents
    for agent_id in ['agent_001', 'agent_002']:
        await coordinator.update_agent_workload(
            agent_id,
            {'status': 'available', 'capacity_utilization': 0.3}
        )

    # Route residential lead
    residential_lead = sample_lead_data.copy()
    residential_lead['property_type'] = 'residential'

    decision = await coordinator.route_lead_intelligent(
        lead_id='lead_residential',
        lead_data=residential_lead
    )

    # Should route to agent with residential specialty
    assert decision.selected_agent_id == 'agent_001'
    assert decision.routing_factors['expertise'] > 0.2


@pytest.mark.asyncio
async def test_routing_no_available_agents(coordinator, sample_agent_data, sample_lead_data):
    """Test routing when no agents are available."""
    coordinator.team_manager.add_agent(**sample_agent_data)

    # Set agent to full capacity
    await coordinator.update_agent_workload(
        'agent_001',
        {'status': 'busy', 'capacity_utilization': 1.0}
    )

    # Should raise error and create alert
    with pytest.raises(ValueError, match="No available agents"):
        await coordinator.route_lead_intelligent(
            lead_id='lead_001',
            lead_data=sample_lead_data
        )

    # Check alert was created
    alerts = [a for a in coordinator._active_alerts.values() if a.alert_type == 'no_agents_available']
    assert len(alerts) > 0


@pytest.mark.asyncio
async def test_routing_performance_target(coordinator, sample_agent_data, sample_lead_data):
    """Test that routing meets <5 second performance target."""
    coordinator.team_manager.add_agent(**sample_agent_data)

    await coordinator.update_agent_workload(
        'agent_001',
        {'status': 'available', 'capacity_utilization': 0.5}
    )

    decision = await coordinator.route_lead_intelligent(
        lead_id='lead_001',
        lead_data=sample_lead_data
    )

    # Should complete in <5000ms
    assert decision.assignment_time_ms < 5000


# =================== HANDOFF TESTS ===================

@pytest.mark.asyncio
async def test_initiate_lead_handoff(coordinator, sample_agent_data):
    """Test initiating a lead handoff between agents."""
    # Add two agents
    for i in range(2):
        agent_data = sample_agent_data.copy()
        agent_data['agent_id'] = f'agent_00{i+1}'
        coordinator.team_manager.add_agent(**agent_data)

        await coordinator.update_agent_workload(
            f'agent_00{i+1}',
            {'active_leads': 5, 'capacity_utilization': 0.5}
        )

    # Initiate handoff
    handoff = await coordinator.initiate_lead_handoff(
        lead_id='lead_001',
        from_agent_id='agent_001',
        to_agent_id='agent_002',
        reason='Agent 1 going on break',
        priority=AlertPriority.MEDIUM
    )

    assert handoff is not None
    assert isinstance(handoff, LeadHandoff)
    assert handoff.lead_id == 'lead_001'
    assert handoff.from_agent_id == 'agent_001'
    assert handoff.to_agent_id == 'agent_002'
    assert handoff.status == HandoffStatus.PENDING


@pytest.mark.asyncio
async def test_accept_handoff(coordinator, sample_agent_data):
    """Test accepting a lead handoff."""
    # Add agents
    for i in range(2):
        agent_data = sample_agent_data.copy()
        agent_data['agent_id'] = f'agent_00{i+1}'
        coordinator.team_manager.add_agent(**agent_data)

        await coordinator.update_agent_workload(
            f'agent_00{i+1}',
            {'active_leads': 5, 'capacity_utilization': 0.5}
        )

    # Initiate handoff
    handoff = await coordinator.initiate_lead_handoff(
        lead_id='lead_001',
        from_agent_id='agent_001',
        to_agent_id='agent_002',
        reason='Test handoff'
    )

    # Accept handoff
    accepted_handoff = await coordinator.accept_handoff(
        handoff_id=handoff.handoff_id,
        agent_id='agent_002'
    )

    assert accepted_handoff.status == HandoffStatus.ACCEPTED
    assert accepted_handoff.accepted_at is not None


@pytest.mark.asyncio
async def test_complete_handoff(coordinator, sample_agent_data):
    """Test completing a handoff and tracking duration."""
    # Add agents
    for i in range(2):
        agent_data = sample_agent_data.copy()
        agent_data['agent_id'] = f'agent_00{i+1}'
        coordinator.team_manager.add_agent(**agent_data)

        await coordinator.update_agent_workload(
            f'agent_00{i+1}',
            {'active_leads': 5}
        )

    # Initiate and accept handoff
    handoff = await coordinator.initiate_lead_handoff(
        lead_id='lead_001',
        from_agent_id='agent_001',
        to_agent_id='agent_002',
        reason='Test'
    )

    await coordinator.accept_handoff(handoff.handoff_id, 'agent_002')

    # Complete handoff
    completed_handoff = await coordinator.complete_handoff(handoff.handoff_id)

    assert completed_handoff.status == HandoffStatus.COMPLETED
    assert completed_handoff.completed_at is not None
    assert completed_handoff.handoff_duration_seconds is not None


@pytest.mark.asyncio
async def test_handoff_unauthorized_acceptance(coordinator, sample_agent_data):
    """Test that only target agent can accept handoff."""
    # Add agents
    for i in range(3):
        agent_data = sample_agent_data.copy()
        agent_data['agent_id'] = f'agent_00{i+1}'
        coordinator.team_manager.add_agent(**agent_data)

        await coordinator.update_agent_workload(f'agent_00{i+1}', {})

    # Initiate handoff
    handoff = await coordinator.initiate_lead_handoff(
        lead_id='lead_001',
        from_agent_id='agent_001',
        to_agent_id='agent_002',
        reason='Test'
    )

    # Try to accept with wrong agent
    with pytest.raises(ValueError, match="not authorized"):
        await coordinator.accept_handoff(handoff.handoff_id, 'agent_003')


# =================== COACHING INTEGRATION TESTS ===================

@pytest.mark.asyncio
async def test_request_coaching_assistance(coordinator, sample_agent_data):
    """Test requesting real-time coaching from Claude AI."""
    coordinator.team_manager.add_agent(**sample_agent_data)
    await coordinator.update_agent_workload('agent_001', {})

    # Mock Claude service response with proper dataclass
    from ghl_real_estate_ai.services.claude_agent_service import CoachingResponse

    mock_coaching = CoachingResponse(
        coaching_suggestions=["Focus on budget qualification"],
        objection_detected=None,
        recommended_response="Let's discuss your budget range",
        next_question="What's your timeline for moving?",
        conversation_stage="discovery",
        confidence=0.9,
        urgency="medium",
        reasoning="Initial discovery phase"
    )

    with patch('ghl_real_estate_ai.services.live_agent_coordinator.claude_agent_service') as mock_claude:
        mock_claude.get_real_time_coaching = AsyncMock(return_value=mock_coaching)

        response = await coordinator.request_coaching_assistance(
            agent_id='agent_001',
            conversation_context={'lead_id': 'lead_001'},
            prospect_message="I'm interested in buying a home",
            conversation_stage='discovery'
        )

    assert response['success'] is True
    assert response['agent_id'] == 'agent_001'
    assert 'coaching' in response

    # Check metrics updated
    workload = await coordinator.get_agent_workload('agent_001')
    assert workload.coaching_sessions_today == 1


# =================== ANALYTICS TESTS ===================

@pytest.mark.asyncio
async def test_get_coordination_metrics(coordinator, sample_agent_data):
    """Test retrieving coordination performance metrics."""
    coordinator.team_manager.add_agent(**sample_agent_data)
    await coordinator.update_agent_workload('agent_001', {'capacity_utilization': 0.7})

    metrics = await coordinator.get_coordination_metrics()

    assert 'total_assignments' in metrics
    assert 'workload_balance_score' in metrics
    assert 'agent_utilization' in metrics
    assert 'active_agents' in metrics
    assert 'total_agents' in metrics
    assert 'timestamp' in metrics


@pytest.mark.asyncio
async def test_get_agent_performance_summary(coordinator, sample_agent_data, sample_lead_data):
    """Test getting comprehensive agent performance summary."""
    coordinator.team_manager.add_agent(**sample_agent_data)

    await coordinator.update_agent_workload(
        'agent_001',
        {
            'status': 'available',
            'active_leads': 5,
            'capacity_utilization': 0.6
        }
    )

    # Route some leads to create history
    await coordinator.route_lead_intelligent(
        lead_id='lead_001',
        lead_data=sample_lead_data
    )

    # Get performance summary
    summary = await coordinator.get_agent_performance_summary('agent_001')

    assert 'agent_id' in summary
    assert 'agent_name' in summary
    assert 'current_status' in summary
    assert 'workload' in summary
    assert 'performance' in summary
    assert 'assignments_today' in summary


# =================== INTEGRATION TESTS ===================

@pytest.mark.asyncio
async def test_end_to_end_lead_assignment_workflow(coordinator, sample_agent_data, sample_lead_data):
    """Test complete workflow: routing -> coaching -> handoff."""
    # Setup: Add two agents
    for i in range(2):
        agent_data = sample_agent_data.copy()
        agent_data['agent_id'] = f'agent_00{i+1}'
        agent_data['name'] = f'Agent {i+1}'
        coordinator.team_manager.add_agent(**agent_data)

        await coordinator.update_agent_workload(
            f'agent_00{i+1}',
            {'status': 'available', 'active_leads': i, 'capacity_utilization': 0.3 * i}
        )

    # Step 1: Route lead
    routing_decision = await coordinator.route_lead_intelligent(
        lead_id='lead_001',
        lead_data=sample_lead_data,
        priority='high'
    )

    assert routing_decision.selected_agent_id in ['agent_001', 'agent_002']
    assigned_agent = routing_decision.selected_agent_id

    # Step 2: Request coaching (mocked)
    from ghl_real_estate_ai.services.claude_agent_service import CoachingResponse

    mock_coaching = CoachingResponse(
        coaching_suggestions=["Build rapport first"],
        objection_detected=None,
        recommended_response="Let's explore your needs",
        next_question="What brings you to the market today?",
        conversation_stage="discovery",
        confidence=0.85,
        urgency="medium",
        reasoning="Building initial rapport"
    )

    with patch('ghl_real_estate_ai.services.live_agent_coordinator.claude_agent_service') as mock_claude:
        mock_claude.get_real_time_coaching = AsyncMock(return_value=mock_coaching)

        coaching_response = await coordinator.request_coaching_assistance(
            agent_id=assigned_agent,
            conversation_context={'lead_id': 'lead_001'},
            prospect_message="Hi, I'm looking for a home",
            conversation_stage='discovery'
        )

    assert coaching_response['success'] is True

    # Step 3: Initiate handoff
    other_agent = 'agent_002' if assigned_agent == 'agent_001' else 'agent_001'

    handoff = await coordinator.initiate_lead_handoff(
        lead_id='lead_001',
        from_agent_id=assigned_agent,
        to_agent_id=other_agent,
        reason='Agent going on break'
    )

    assert handoff.status == HandoffStatus.PENDING

    # Step 4: Accept and complete handoff
    await coordinator.accept_handoff(handoff.handoff_id, other_agent)
    completed = await coordinator.complete_handoff(handoff.handoff_id)

    assert completed.status == HandoffStatus.COMPLETED

    # Verify final state
    metrics = await coordinator.get_coordination_metrics()
    assert metrics['total_assignments'] == 1
    assert metrics['total_handoffs'] == 1


@pytest.mark.asyncio
async def test_get_coordinator_singleton():
    """Test global coordinator instance retrieval."""
    coordinator1 = get_coordinator("tenant_1")
    coordinator2 = get_coordinator("tenant_1")
    coordinator3 = get_coordinator("tenant_2")

    # Same tenant should return same instance
    assert coordinator1 is coordinator2

    # Different tenant should return different instance
    assert coordinator1 is not coordinator3


# =================== PERFORMANCE TESTS ===================

@pytest.mark.asyncio
async def test_routing_performance_at_scale(coordinator, sample_agent_data, sample_lead_data):
    """Test routing performance with multiple agents and leads."""
    # Add 10 agents
    for i in range(10):
        agent_data = sample_agent_data.copy()
        agent_data['agent_id'] = f'agent_{i:03d}'
        agent_data['name'] = f'Agent {i}'
        coordinator.team_manager.add_agent(**agent_data)

        await coordinator.update_agent_workload(
            f'agent_{i:03d}',
            {'status': 'available', 'capacity_utilization': 0.3}
        )

    # Route 20 leads and measure average time
    total_time = 0
    for i in range(20):
        decision = await coordinator.route_lead_intelligent(
            lead_id=f'lead_{i:03d}',
            lead_data=sample_lead_data
        )
        total_time += decision.assignment_time_ms

    avg_time = total_time / 20

    # Should average <5000ms per assignment
    assert avg_time < 5000


@pytest.mark.asyncio
async def test_workload_balance_optimization(coordinator, sample_agent_data):
    """Test that workload balancing achieves >85% score."""
    # Add agents with similar capacity
    for i in range(5):
        agent_data = sample_agent_data.copy()
        agent_data['agent_id'] = f'agent_{i:03d}'
        coordinator.team_manager.add_agent(**agent_data)

        # Distribute workload evenly
        await coordinator.update_agent_workload(
            f'agent_{i:03d}',
            {'capacity_utilization': 0.5 + (i * 0.02)}  # Small variation
        )

    balance_score = await coordinator.calculate_workload_balance()

    # Should achieve >85% balance
    assert balance_score > 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
