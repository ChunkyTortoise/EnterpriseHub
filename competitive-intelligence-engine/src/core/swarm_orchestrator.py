"""
Intelligence Swarm Orchestrator - Phase 5

Coordinates specialized intelligence agents (Supply Chain, M&A, Regulatory)
using the EventBus. Implements the "Sense-Think-Act" loop for autonomous
competitive response.

Author: Claude Code Agent
Date: January 2026
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime

from .event_bus import EventBus, EventHandler, EventType, EventPriority, Event
from .rbac import Role, User, Permission, RBACService
from .ai_client import AIClient

logger = logging.getLogger(__name__)

class IntelligenceSwarmOrchestrator:
    """
    Central orchestrator for the Competitive Intelligence Swarm.
    Manages agent lifecycles, cross-agent delegation, and autonomous decision gates.
    """
    
    def __init__(self, event_bus: EventBus, ai_client: AIClient):
        self.event_bus = event_bus
        self.ai_client = ai_client
        self.agents: Dict[str, EventHandler] = {}
        self.is_autonomous_mode = False
        self.pending_actions: List[Dict[str, Any]] = []
        
        logger.info("Intelligence Swarm Orchestrator Initialized")

    def register_agent(self, agent: EventHandler):
        """Register a specialized agent with the swarm."""
        self.agents[agent.name] = agent
        self.event_bus.register_handler(agent)
        logger.info(f"Swarm Agent Registered: {agent.name}")

    async def start_swarm(self):
        """Activate all registered agents."""
        for agent in self.agents.values():
            await agent.start()
        logger.info(f"Intelligence Swarm Activated with {len(self.agents)} agents")

    async def stop_swarm(self):
        """Deactivate all registered agents."""
        for agent in self.agents.values():
            await agent.stop()
        logger.info("Intelligence Swarm Deactivated")

    def toggle_autonomous_mode(self, enabled: bool):
        """Enable/Disable proactive agent responses without human approval."""
        self.is_autonomous_mode = enabled
        logger.info(f"Swarm Autonomous Mode: {'ENABLED' if enabled else 'DISABLED'}")

    async def propose_action(self, agent_name: str, action_data: Dict[str, Any]):
        """Propose an action for human approval when autonomous mode is OFF."""
        action_id = f"act_{int(datetime.now().timestamp())}_{len(self.pending_actions)}"
        proposal = {
            "id": action_id,
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "data": action_data,
            "status": "pending"
        }
        self.pending_actions.append(proposal)
        logger.info(f"Action Proposed by {agent_name}: {action_id}")
        
        # Publish notification for UI
        await self.event_bus.publish(
            event_type=EventType.MULTI_ENGINE_COORDINATION_REQUIRED,
            data={
                "message": f"New strategic action pending approval from {agent_name}",
                "action_id": action_id
            },
            source_system="swarm_orchestrator",
            priority=EventPriority.HIGH
        )
        return action_id

    async def approve_action(self, action_id: str):
        """Execute a previously proposed action."""
        for action in self.pending_actions:
            if action["id"] == action_id and action["status"] == "pending":
                action["status"] = "approved"
                data = action["data"]
                
                # Publish the actual action event
                await self.event_bus.publish(
                    event_type=data["event_type"],
                    data=data["payload"],
                    source_system=f"approved_{action['agent']}",
                    priority=data.get("priority", EventPriority.CRITICAL)
                )
                logger.info(f"Action Approved: {action_id}")
                return True
        return False

    async def reject_action(self, action_id: str):
        """Discard a proposed action."""
        for action in self.pending_actions:
            if action["id"] == action_id:
                action["status"] = "rejected"
                logger.info(f"Action Rejected: {action_id}")
                return True
        return False

    async def delegate_task(self, from_agent: str, to_agent: str, task_data: Dict[str, Any]):
        """Explicitly delegate a task between agents via the EventBus."""
        await self.event_bus.publish(
            event_type=EventType.MULTI_ENGINE_COORDINATION_REQUIRED,
            data={
                "delegated_from": from_agent,
                "delegated_to": to_agent,
                "task_data": task_data
            },
            source_system=f"swarm_orchestrator_{from_agent}",
            priority=EventPriority.HIGH
        )

class BaseSwarmAgent(EventHandler):
    """Base class for specialized swarm agents with AI capabilities."""
    
    def __init__(self, name: str, event_types: List[EventType], ai_client: AIClient, orchestrator: IntelligenceSwarmOrchestrator):
        super().__init__(name, event_types)
        self.ai_client = ai_client
        self.orchestrator = orchestrator
        self.user_context = User("agent_id", name, Role.CEO) # Agents operate with high internal privilege

    async def think(self, prompt: str) -> str:
        """Process information using the strategic AI engine."""
        return await self.ai_client.generate_strategic_response(prompt)

    async def handle(self, event: Event) -> bool:
        """Standard event handling implementation for swarm agents."""
        try:
            prompt = (
                f"Event Type: {event.type.name}\n"
                f"Source: {event.source_system}\n"
                f"Priority: {event.priority.value}\n"
                f"Data: {event.data}\n"
            )
            insight = await self.think(prompt)

            await self.orchestrator.event_bus.publish(
                event_type=EventType.INTELLIGENCE_INSIGHT_CREATED,
                data={
                    "agent": self.name,
                    "insight": insight,
                    "source_event": event.to_dict(),
                },
                source_system=self.name,
                priority=EventPriority.MEDIUM,
            )
            return True
        except Exception as e:
            logger.error(f"BaseSwarmAgent handle failed: {e}")
            return False
