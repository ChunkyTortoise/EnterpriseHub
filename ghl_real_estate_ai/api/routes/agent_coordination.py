"""
Agent Coordination API Routes

REST API endpoints for live agent coordination, workload management,
lead routing, and team coordination features.

Endpoints:
- Workload management
- Lead routing and assignment
- Lead handoffs
- Team alerts
- Real-time coaching requests
- Performance analytics
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ...services.live_agent_coordinator import (
    LiveAgentCoordinator,
    get_coordinator,
    AgentStatus,
    AlertPriority,
    HandoffStatus
)
from ...services.realtime_websocket_hub import RealtimeWebSocketHub

router = APIRouter(prefix="/api/v1/agent-coordination", tags=["Agent Coordination"])


# =================== REQUEST/RESPONSE MODELS ===================

class WorkloadUpdateRequest(BaseModel):
    """Request to update agent workload."""
    status: Optional[str] = None
    active_leads: Optional[int] = None
    active_conversations: Optional[int] = None
    capacity_utilization: Optional[float] = Field(None, ge=0.0, le=1.0)


class LeadRoutingRequest(BaseModel):
    """Request to route a lead to an agent."""
    lead_id: str
    lead_data: Dict[str, Any]
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")


class HandoffRequest(BaseModel):
    """Request to initiate lead handoff."""
    lead_id: str
    from_agent_id: str
    to_agent_id: str
    reason: str
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical|urgent)$")
    context: Optional[Dict[str, Any]] = None


class HandoffActionRequest(BaseModel):
    """Request to accept/reject/complete handoff."""
    agent_id: str


class CoachingRequest(BaseModel):
    """Request for real-time coaching assistance."""
    agent_id: str
    conversation_context: Dict[str, Any]
    prospect_message: str
    conversation_stage: str = Field(
        pattern="^(discovery|qualification|objection_handling|closing)$"
    )


class AlertAcknowledgement(BaseModel):
    """Acknowledge an alert."""
    agent_id: str


# =================== WORKLOAD MANAGEMENT ENDPOINTS ===================

@router.post("/agents/{agent_id}/workload")
async def update_agent_workload(
    agent_id: str,
    workload_update: WorkloadUpdateRequest,
    tenant_id: str = Query(default="default")
):
    """
    Update agent workload information in real-time.

    Updates current workload metrics including status, active leads,
    conversations, and capacity utilization.
    """
    try:
        coordinator = get_coordinator(tenant_id)

        workload = await coordinator.update_agent_workload(
            agent_id=agent_id,
            workload_update=workload_update.model_dump(exclude_none=True)
        )

        return {
            'success': True,
            'agent_id': agent_id,
            'workload': {
                'status': workload.status.value,
                'active_leads': workload.active_leads,
                'active_conversations': workload.active_conversations,
                'capacity_utilization': workload.capacity_utilization,
                'is_available': workload.is_available,
                'priority_score': workload.priority_score
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/workload")
async def get_agent_workload(
    agent_id: str,
    tenant_id: str = Query(default="default")
):
    """Get current workload information for an agent."""
    try:
        coordinator = get_coordinator(tenant_id)
        workload = await coordinator.get_agent_workload(agent_id)

        if not workload:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        return {
            'success': True,
            'agent_id': agent_id,
            'workload': {
                'agent_name': workload.agent_name,
                'status': workload.status.value,
                'active_leads': workload.active_leads,
                'active_conversations': workload.active_conversations,
                'capacity_utilization': workload.capacity_utilization,
                'is_available': workload.is_available,
                'can_accept_lead': workload.can_accept_lead,
                'performance': {
                    'avg_response_time_minutes': workload.avg_response_time_minutes,
                    'conversion_rate': workload.conversion_rate,
                    'customer_satisfaction': workload.customer_satisfaction
                },
                'last_activity': workload.last_activity.isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/workloads")
async def get_team_workloads(tenant_id: str = Query(default="default")):
    """Get workload information for all agents in the team."""
    try:
        coordinator = get_coordinator(tenant_id)
        workloads = await coordinator.get_team_workloads()

        return {
            'success': True,
            'team_size': len(workloads),
            'workloads': [
                {
                    'agent_id': w.agent_id,
                    'agent_name': w.agent_name,
                    'status': w.status.value,
                    'active_leads': w.active_leads,
                    'capacity_utilization': w.capacity_utilization,
                    'is_available': w.is_available,
                    'priority_score': w.priority_score
                }
                for w in workloads
            ],
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/balance")
async def get_workload_balance(tenant_id: str = Query(default="default")):
    """
    Get team workload balance score.

    Returns a score from 0.0 (perfectly balanced) to 1.0 (completely imbalanced).
    Target: >0.85 for optimal team efficiency.
    """
    try:
        coordinator = get_coordinator(tenant_id)
        balance_score = await coordinator.calculate_workload_balance()

        return {
            'success': True,
            'balance_score': balance_score,
            'status': 'optimal' if balance_score >= 0.85 else 'needs_balancing',
            'target': 0.85,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================== LEAD ROUTING ENDPOINTS ===================

@router.post("/leads/route")
async def route_lead(
    routing_request: LeadRoutingRequest,
    tenant_id: str = Query(default="default")
):
    """
    Route a lead to the optimal agent using intelligent multi-factor routing.

    Considers:
    - Agent availability and workload (35%)
    - Expertise match (30%)
    - Performance metrics (20%)
    - Real-time responsiveness (15%)

    Target: <5 seconds assignment time, >85% routing accuracy
    """
    try:
        coordinator = get_coordinator(tenant_id)

        decision = await coordinator.route_lead_intelligent(
            lead_id=routing_request.lead_id,
            lead_data=routing_request.lead_data,
            priority=routing_request.priority
        )

        return {
            'success': True,
            'lead_id': decision.lead_id,
            'assigned_agent': {
                'agent_id': decision.selected_agent_id,
                'agent_name': decision.selected_agent_name
            },
            'routing_details': {
                'match_score': decision.match_score,
                'confidence': decision.confidence,
                'reasoning': decision.reasoning,
                'assignment_time_ms': decision.assignment_time_ms
            },
            'routing_factors': decision.routing_factors,
            'alternative_agents': decision.alternative_agents,
            'timestamp': datetime.now().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================== HANDOFF ENDPOINTS ===================

@router.post("/handoffs/initiate")
async def initiate_handoff(
    handoff_request: HandoffRequest,
    tenant_id: str = Query(default="default")
):
    """
    Initiate a lead handoff between agents with full context preservation.

    Creates handoff request, sends alert to target agent, and
    preserves all conversation context and lead preferences.
    """
    try:
        coordinator = get_coordinator(tenant_id)

        # Convert priority string to enum
        priority = AlertPriority(handoff_request.priority)

        handoff = await coordinator.initiate_lead_handoff(
            lead_id=handoff_request.lead_id,
            from_agent_id=handoff_request.from_agent_id,
            to_agent_id=handoff_request.to_agent_id,
            reason=handoff_request.reason,
            priority=priority,
            context=handoff_request.context
        )

        return {
            'success': True,
            'handoff_id': handoff.handoff_id,
            'lead_id': handoff.lead_id,
            'from_agent': handoff.from_agent_id,
            'to_agent': handoff.to_agent_id,
            'status': handoff.status.value,
            'priority': handoff.priority.value,
            'initiated_at': handoff.initiated_at.isoformat(),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/handoffs/{handoff_id}/accept")
async def accept_handoff(
    handoff_id: str,
    action_request: HandoffActionRequest,
    tenant_id: str = Query(default="default")
):
    """Accept a lead handoff."""
    try:
        coordinator = get_coordinator(tenant_id)

        handoff = await coordinator.accept_handoff(
            handoff_id=handoff_id,
            agent_id=action_request.agent_id
        )

        return {
            'success': True,
            'handoff_id': handoff.handoff_id,
            'status': handoff.status.value,
            'accepted_at': handoff.accepted_at.isoformat() if handoff.accepted_at else None,
            'timestamp': datetime.now().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/handoffs/{handoff_id}/complete")
async def complete_handoff(
    handoff_id: str,
    tenant_id: str = Query(default="default")
):
    """Mark a handoff as completed."""
    try:
        coordinator = get_coordinator(tenant_id)

        handoff = await coordinator.complete_handoff(handoff_id)

        return {
            'success': True,
            'handoff_id': handoff.handoff_id,
            'status': handoff.status.value,
            'completed_at': handoff.completed_at.isoformat() if handoff.completed_at else None,
            'duration_seconds': handoff.handoff_duration_seconds,
            'timestamp': datetime.now().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================== COACHING ENDPOINTS ===================

@router.post("/coaching/request")
async def request_coaching(
    coaching_request: CoachingRequest,
    tenant_id: str = Query(default="default")
):
    """
    Request real-time coaching assistance from Claude AI.

    Provides:
    - Coaching suggestions
    - Objection detection and handling
    - Recommended responses
    - Next question suggestions

    Target: <30 seconds response time
    """
    try:
        coordinator = get_coordinator(tenant_id)

        coaching_response = await coordinator.request_coaching_assistance(
            agent_id=coaching_request.agent_id,
            conversation_context=coaching_request.conversation_context,
            prospect_message=coaching_request.prospect_message,
            conversation_stage=coaching_request.conversation_stage
        )

        return coaching_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================== ALERT ENDPOINTS ===================

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledgement: AlertAcknowledgement,
    tenant_id: str = Query(default="default")
):
    """Acknowledge a team alert."""
    try:
        coordinator = get_coordinator(tenant_id)

        await coordinator.acknowledge_alert(
            alert_id=alert_id,
            agent_id=acknowledgement.agent_id
        )

        return {
            'success': True,
            'alert_id': alert_id,
            'acknowledged_by': acknowledgement.agent_id,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    tenant_id: str = Query(default="default")
):
    """Mark an alert as resolved."""
    try:
        coordinator = get_coordinator(tenant_id)

        await coordinator.resolve_alert(alert_id)

        return {
            'success': True,
            'alert_id': alert_id,
            'resolved': True,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================== ANALYTICS ENDPOINTS ===================

@router.get("/metrics")
async def get_coordination_metrics(tenant_id: str = Query(default="default")):
    """
    Get comprehensive coordination performance metrics.

    Includes:
    - Assignment metrics (count, avg time)
    - Handoff metrics (count, avg duration)
    - Workload balance score
    - Agent utilization
    - Coaching request count
    - Alert dispatch count
    """
    try:
        coordinator = get_coordinator(tenant_id)
        metrics = await coordinator.get_coordination_metrics()

        return {
            'success': True,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/performance")
async def get_agent_performance(
    agent_id: str,
    tenant_id: str = Query(default="default")
):
    """
    Get comprehensive performance summary for a specific agent.

    Includes:
    - Current workload and status
    - Performance metrics (conversion, satisfaction, response time)
    - Assignment count
    - Handoff statistics
    - Coaching sessions
    """
    try:
        coordinator = get_coordinator(tenant_id)
        performance = await coordinator.get_agent_performance_summary(agent_id)

        return {
            'success': True,
            'performance': performance,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================== HEALTH CHECK ===================

@router.get("/health")
async def health_check():
    """Health check endpoint for agent coordination service."""
    return {
        'status': 'healthy',
        'service': 'agent_coordination',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }
