"""
Agent Mesh Registry for EnterpriseHub
Auto-discovery and registration of Jorge bots and other agents

Provides seamless integration of existing bot ecosystem into agent mesh
with progressive skills and MCP protocol support.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.agent_mesh_coordinator import (
    AgentCapability,
    AgentMetrics,
    AgentStatus,
    MeshAgent,
    get_mesh_coordinator,
)
from ghl_real_estate_ai.services.mcp_client import get_mcp_client
from ghl_real_estate_ai.services.progressive_skills_manager import ProgressiveSkillsManager

logger = get_logger(__name__)


class MeshAgentRegistry:
    """
    Agent Registry for automatic discovery and registration

    Features:
    - Auto-discovery of Jorge bots and services
    - Progressive skills integration
    - MCP server registration
    - Health monitoring and metrics collection
    - Dynamic configuration loading
    """

    def __init__(self, config_path: str = ".claude/agent-mesh/mesh-config.json"):
        self.config_path = Path(config_path)
        self.mesh_coordinator = get_mesh_coordinator()
        self.skills_manager = ProgressiveSkillsManager()
        self.mcp_client = get_mcp_client()

        self.registered_agents: Dict[str, MeshAgent] = {}
        self.config = {}

    async def initialize(self) -> bool:
        """Initialize the agent registry and register all agents"""
        try:
            # Load configuration
            await self._load_configuration()

            # Register agents from configuration
            await self._register_configured_agents()

            # Auto-discover additional agents
            await self._auto_discover_agents()

            # Validate all registrations
            await self._validate_registrations()

            logger.info(f"Agent registry initialized with {len(self.registered_agents)} agents")
            return True

        except Exception as e:
            logger.error(f"Agent registry initialization failed: {e}")
            return False

    async def _load_configuration(self):
        """Load mesh configuration from file"""
        try:
            if not self.config_path.exists():
                logger.error(f"Configuration file not found: {self.config_path}")
                raise FileNotFoundError(f"Config file missing: {self.config_path}")

            with open(self.config_path, "r") as f:
                self.config = json.load(f)

            logger.info("Mesh configuration loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    async def _register_configured_agents(self):
        """Register agents from configuration file"""
        registered_agents = self.config.get("registered_agents", [])

        for agent_config in registered_agents:
            try:
                agent = await self._create_agent_from_config(agent_config)

                if await self.mesh_coordinator.register_agent(agent):
                    self.registered_agents[agent.agent_id] = agent
                    logger.info(f"Registered agent from config: {agent.name}")
                else:
                    logger.error(f"Failed to register agent: {agent_config['name']}")

            except Exception as e:
                logger.error(f"Error registering agent {agent_config.get('name', 'unknown')}: {e}")

    async def _create_agent_from_config(self, config: Dict[str, Any]) -> MeshAgent:
        """Create MeshAgent from configuration"""

        # Parse capabilities
        capabilities = [AgentCapability(cap) for cap in config.get("capabilities", [])]

        # Create metrics
        metrics = AgentMetrics()

        # Create agent
        agent = MeshAgent(
            agent_id=config["agent_id"],
            name=config["name"],
            capabilities=capabilities,
            status=AgentStatus(config.get("status", "idle")),
            max_concurrent_tasks=config.get("max_concurrent_tasks", 5),
            current_tasks=0,
            priority_level=config.get("priority_level", 1),
            cost_per_token=config.get("cost_per_token", 0.00001),
            sla_response_time=config.get("sla_response_time_seconds", 30),
            metrics=metrics,
            endpoint=config["endpoint"],
            health_check_url=config.get("health_check_url", "/health"),
            last_heartbeat=datetime.now(),
        )

        return agent

    async def _auto_discover_agents(self):
        """Auto-discover agents from the codebase"""

        # Discover Jorge bots
        await self._discover_jorge_bots()

        # Discover services
        await self._discover_services()

        # Discover MCP servers
        await self._discover_mcp_servers()

        logger.info("Agent auto-discovery completed")

    async def _discover_jorge_bots(self):
        """Discover Jorge bot agents"""
        jorge_bots = [
            {
                "file": "ghl_real_estate_ai/agents/jorge_seller_bot.py",
                "class": "JorgeSellerBot",
                "capabilities": [AgentCapability.LEAD_QUALIFICATION, AgentCapability.CONVERSATION_ANALYSIS],
                "name": "Jorge Seller Bot",
            },
            {
                "file": "ghl_real_estate_ai/agents/lead_bot.py",
                "class": "LeadBot",
                "capabilities": [AgentCapability.FOLLOWUP_AUTOMATION, AgentCapability.VOICE_INTERACTION],
                "name": "Lead Lifecycle Bot",
            },
            {
                "file": "ghl_real_estate_ai/agents/intent_decoder.py",
                "class": "IntentDecoder",
                "capabilities": [AgentCapability.CONVERSATION_ANALYSIS],
                "name": "Intent Decoder",
            },
        ]

        for bot_info in jorge_bots:
            try:
                # Check if file exists
                bot_file = Path(bot_info["file"])
                if not bot_file.exists():
                    logger.warning(f"Bot file not found: {bot_file}")
                    continue

                # Create auto-discovered agent
                agent_id = f"auto_{bot_info['class'].lower()}"

                # Skip if already registered from config
                if agent_id in self.registered_agents:
                    continue

                agent = MeshAgent(
                    agent_id=agent_id,
                    name=bot_info["name"],
                    capabilities=bot_info["capabilities"],
                    status=AgentStatus.IDLE,
                    max_concurrent_tasks=3,  # Conservative default
                    current_tasks=0,
                    priority_level=2,  # Lower priority than configured agents
                    cost_per_token=0.000015,  # Default Jorge bot cost
                    sla_response_time=30,
                    metrics=AgentMetrics(),
                    endpoint=f"internal:{bot_info['class']}",
                    health_check_url="/health",
                    last_heartbeat=datetime.now(),
                )

                if await self.mesh_coordinator.register_agent(agent):
                    self.registered_agents[agent_id] = agent
                    logger.info(f"Auto-discovered and registered: {bot_info['name']}")

            except Exception as e:
                logger.error(f"Error discovering bot {bot_info['name']}: {e}")

    async def _discover_services(self):
        """Discover service-based agents"""
        services = [
            {
                "file": "ghl_real_estate_ai/services/claude_conversation_intelligence.py",
                "name": "Conversation Intelligence Service",
                "capabilities": [AgentCapability.CONVERSATION_ANALYSIS, AgentCapability.MARKET_INTELLIGENCE],
                "cost_per_token": 0.000008,
            },
            {
                "file": "ghl_real_estate_ai/services/enhanced_property_matcher.py",
                "name": "Enhanced Property Matcher",
                "capabilities": [AgentCapability.PROPERTY_MATCHING, AgentCapability.MARKET_INTELLIGENCE],
                "cost_per_token": 0.00001,
            },
            {
                "file": "ghl_real_estate_ai/services/ghost_followup_engine.py",
                "name": "Ghost Followup Engine",
                "capabilities": [AgentCapability.FOLLOWUP_AUTOMATION],
                "cost_per_token": 0.000005,
            },
            {
                "file": "bots/shared/ml_analytics_engine.py",
                "name": "ML Analytics Engine",
                "capabilities": [AgentCapability.CONVERSATION_ANALYSIS, AgentCapability.MARKET_INTELLIGENCE],
                "cost_per_token": 0.000003,
            },
        ]

        for service_info in services:
            try:
                service_file = Path(service_info["file"])
                if not service_file.exists():
                    logger.warning(f"Service file not found: {service_file}")
                    continue

                agent_id = f"auto_service_{service_info['name'].lower().replace(' ', '_')}"

                # Skip if already registered
                if agent_id in self.registered_agents:
                    continue

                agent = MeshAgent(
                    agent_id=agent_id,
                    name=service_info["name"],
                    capabilities=service_info["capabilities"],
                    status=AgentStatus.IDLE,
                    max_concurrent_tasks=10,  # Services can handle more load
                    current_tasks=0,
                    priority_level=2,
                    cost_per_token=service_info["cost_per_token"],
                    sla_response_time=15,
                    metrics=AgentMetrics(),
                    endpoint=f"internal:service_{service_info['name'].lower().replace(' ', '_')}",
                    health_check_url="/health",
                    last_heartbeat=datetime.now(),
                )

                if await self.mesh_coordinator.register_agent(agent):
                    self.registered_agents[agent_id] = agent
                    logger.info(f"Auto-discovered service: {service_info['name']}")

            except Exception as e:
                logger.error(f"Error discovering service {service_info['name']}: {e}")

    async def _discover_mcp_servers(self):
        """Discover and register MCP servers as agents"""
        try:
            # Load MCP servers configuration
            mcp_config_path = Path(".claude/mcp-servers.json")
            if not mcp_config_path.exists():
                logger.warning("MCP servers configuration not found")
                return

            with open(mcp_config_path, "r") as f:
                mcp_config = json.load(f)

            for server_config in mcp_config.get("servers", []):
                try:
                    agent_id = f"mcp_{server_config['name']}"

                    # Skip if already registered
                    if agent_id in self.registered_agents:
                        continue

                    # Map MCP capabilities to agent capabilities
                    mcp_capabilities = server_config.get("capabilities", [])
                    agent_capabilities = await self._map_mcp_capabilities(mcp_capabilities)

                    agent = MeshAgent(
                        agent_id=agent_id,
                        name=f"MCP {server_config['name'].title()}",
                        capabilities=agent_capabilities,
                        status=AgentStatus.IDLE,
                        max_concurrent_tasks=20,  # MCP servers are typically high throughput
                        current_tasks=0,
                        priority_level=server_config.get("priority", 2),
                        cost_per_token=0.000005,  # MCP operations are typically cheaper
                        sla_response_time=server_config.get("health_check_interval", 60),
                        metrics=AgentMetrics(),
                        endpoint=f"mcp:{server_config['name']}",
                        health_check_url="mcp:health",
                        last_heartbeat=datetime.now(),
                    )

                    if await self.mesh_coordinator.register_agent(agent):
                        self.registered_agents[agent_id] = agent
                        logger.info(f"Registered MCP server: {server_config['name']}")

                except Exception as e:
                    logger.error(f"Error registering MCP server {server_config['name']}: {e}")

        except Exception as e:
            logger.error(f"Error discovering MCP servers: {e}")

    async def _map_mcp_capabilities(self, mcp_capabilities: List[str]) -> List[AgentCapability]:
        """Map MCP server capabilities to agent capabilities"""
        capability_mapping = {
            "contacts": AgentCapability.FOLLOWUP_AUTOMATION,
            "workflows": AgentCapability.FOLLOWUP_AUTOMATION,
            "property_search": AgentCapability.PROPERTY_MATCHING,
            "listing_details": AgentCapability.PROPERTY_MATCHING,
            "comparable_sales": AgentCapability.MARKET_INTELLIGENCE,
            "market_statistics": AgentCapability.MARKET_INTELLIGENCE,
            "document_storage": AgentCapability.DOCUMENT_PROCESSING,
            "e_signature": AgentCapability.DOCUMENT_PROCESSING,
            "automated_valuation": AgentCapability.MARKET_INTELLIGENCE,
            "investment_analysis": AgentCapability.MARKET_INTELLIGENCE,
        }

        mapped_capabilities = []
        for mcp_cap in mcp_capabilities:
            if mcp_cap in capability_mapping:
                mapped_capabilities.append(capability_mapping[mcp_cap])

        # Default capability if no mapping found
        if not mapped_capabilities:
            mapped_capabilities = [AgentCapability.DOCUMENT_PROCESSING]

        return list(set(mapped_capabilities))  # Remove duplicates

    async def _validate_registrations(self):
        """Validate all agent registrations"""
        validation_results = {}

        for agent_id, agent in self.registered_agents.items():
            try:
                # Basic validation
                is_valid = await self._validate_agent_basic(agent)

                # Health check
                is_healthy = await self._validate_agent_health(agent)

                # Capability validation
                capabilities_valid = await self._validate_agent_capabilities(agent)

                validation_results[agent_id] = {
                    "basic_valid": is_valid,
                    "health_check": is_healthy,
                    "capabilities_valid": capabilities_valid,
                    "overall_valid": is_valid and is_healthy and capabilities_valid,
                }

                if not validation_results[agent_id]["overall_valid"]:
                    logger.warning(f"Agent validation issues: {agent.name} - {validation_results[agent_id]}")

            except Exception as e:
                logger.error(f"Validation error for agent {agent_id}: {e}")
                validation_results[agent_id] = {"error": str(e), "overall_valid": False}

        valid_agents = sum(1 for r in validation_results.values() if r.get("overall_valid", False))
        logger.info(f"Agent validation completed: {valid_agents}/{len(self.registered_agents)} agents valid")

        return validation_results

    async def _validate_agent_basic(self, agent: MeshAgent) -> bool:
        """Basic agent validation"""
        required_fields = [agent.agent_id, agent.name, agent.capabilities, agent.endpoint]
        return all(field for field in required_fields)

    async def _validate_agent_health(self, agent: MeshAgent) -> bool:
        """Agent health validation"""
        try:
            # For now, assume all agents are healthy
            # In production, this would make actual health check calls
            agent.last_heartbeat = datetime.now()
            return True
        except Exception:
            return False

    async def _validate_agent_capabilities(self, agent: MeshAgent) -> bool:
        """Validate agent capabilities"""
        try:
            # Ensure capabilities are valid enums
            return all(isinstance(cap, AgentCapability) for cap in agent.capabilities)
        except Exception:
            return False

    async def get_registry_status(self) -> Dict[str, Any]:
        """Get comprehensive registry status"""
        return {
            "total_agents": len(self.registered_agents),
            "agents_by_status": {
                status.value: len([a for a in self.registered_agents.values() if a.status == status])
                for status in AgentStatus
            },
            "agents_by_capability": {
                cap.value: len([a for a in self.registered_agents.values() if cap in a.capabilities])
                for cap in AgentCapability
            },
            "total_capacity": sum(a.max_concurrent_tasks for a in self.registered_agents.values()),
            "current_load": sum(a.current_tasks for a in self.registered_agents.values()),
            "average_cost_per_token": sum(a.cost_per_token for a in self.registered_agents.values())
            / len(self.registered_agents)
            if self.registered_agents
            else 0,
            "configuration_loaded": bool(self.config),
            "last_update": datetime.now().isoformat(),
        }

    async def register_dynamic_agent(self, agent_config: Dict[str, Any]) -> bool:
        """Register a new agent dynamically"""
        try:
            agent = await self._create_agent_from_config(agent_config)

            if await self.mesh_coordinator.register_agent(agent):
                self.registered_agents[agent.agent_id] = agent
                logger.info(f"Dynamically registered agent: {agent.name}")
                return True
            else:
                logger.error(f"Failed to register dynamic agent: {agent_config['name']}")
                return False

        except Exception as e:
            logger.error(f"Dynamic agent registration failed: {e}")
            return False

    async def deregister_agent(self, agent_id: str) -> bool:
        """Deregister an agent"""
        try:
            if agent_id in self.registered_agents:
                # Set agent to maintenance mode
                agent = self.registered_agents[agent_id]
                agent.status = AgentStatus.MAINTENANCE
                agent.current_tasks = 0

                # Remove from registry
                del self.registered_agents[agent_id]
                logger.info(f"Deregistered agent: {agent.name}")
                return True
            else:
                logger.warning(f"Agent not found for deregistration: {agent_id}")
                return False

        except Exception as e:
            logger.error(f"Agent deregistration failed: {e}")
            return False


# Global registry instance
_agent_registry = None


def get_agent_registry() -> MeshAgentRegistry:
    """Get singleton agent registry instance"""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = MeshAgentRegistry()
    return _agent_registry
