"""
Feature Configuration - Centralized Feature Flag Management

Environment-based configuration for optional Jorge Bot features:
- Progressive Skills (68% token reduction)
- Agent Mesh Integration (enterprise orchestration)
- MCP Protocol Integration (standardized external services)

All features disabled by default for backward compatibility.
Enable via environment variables for progressive rollout.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any


def _env_bool(key: str, default: bool = False) -> bool:
    """Parse boolean environment variable."""
    val = os.getenv(key, "").lower()
    if val in ("true", "1", "yes"):
        return True
    if val in ("false", "0", "no"):
        return False
    return default


@dataclass
class ProgressiveSkillsConfig:
    """Configuration for Progressive Skills Manager (68% token reduction)."""
    enabled: bool = False
    model: str = "claude-sonnet-4"
    skills_path: str = "skills/"
    cache_ttl: int = 3600
    max_discovery_tokens: int = 103
    max_execution_tokens: int = 169
    fallback_to_full: bool = True
    enabled_skills: str = "all"  # comma-separated skill names or "all"


@dataclass
class AgentMeshConfig:
    """Configuration for Agent Mesh Coordinator (enterprise orchestration)."""
    enabled: bool = False
    max_agents: int = 10
    routing_strategy: str = "capability_based"
    max_cost_per_task: float = 5.0
    task_timeout: int = 30
    enable_auto_scaling: bool = False
    load_balance: bool = True
    health_check_interval: int = 30  # seconds


@dataclass
class MCPConfig:
    """Configuration for MCP Protocol Integration (external services)."""
    enabled: bool = False
    protocol_version: str = "2024-11-05"
    config_path: str = "mcp_config.json"
    request_timeout: int = 10
    max_retries: int = 3
    enable_crm_sync: bool = True
    enable_mls_lookup: bool = True


@dataclass
class FeatureConfig:
    """Top-level feature configuration wrapping all sub-configs."""
    progressive_skills: ProgressiveSkillsConfig = field(default_factory=ProgressiveSkillsConfig)
    agent_mesh: AgentMeshConfig = field(default_factory=AgentMeshConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)

    # Shared settings
    enable_adaptive_questioning: bool = False
    enable_track3_intelligence: bool = True
    enable_bot_intelligence: bool = True


def load_feature_config_from_env() -> FeatureConfig:
    """Load feature configuration from environment variables.

    Environment variables:
        ENABLE_PROGRESSIVE_SKILLS  - Enable progressive skills (default: false)
        PROGRESSIVE_SKILLS_MODEL   - Model for skills (default: claude-sonnet-4)
        PROGRESSIVE_SKILLS_PATH    - Skills directory (default: skills/)
        PROGRESSIVE_SKILLS_CACHE_TTL - Cache TTL seconds (default: 3600)
        PROGRESSIVE_SKILLS_FALLBACK_TO_FULL - Fallback to full context on failure (default: true)
        PROGRESSIVE_SKILLS_ENABLED_SKILLS - Comma-separated skill names or "all" (default: all)

        ENABLE_AGENT_MESH          - Enable agent mesh (default: false)
        AGENT_MESH_MAX_AGENTS      - Max concurrent agents (default: 10)
        AGENT_MESH_ROUTING_STRATEGY - Routing strategy (default: capability_based)
        AGENT_MESH_MAX_COST        - Max cost per task (default: 5.0)
        AGENT_MESH_TASK_TIMEOUT    - Task timeout seconds (default: 30)
        AGENT_MESH_LOAD_BALANCE    - Enable load balancing (default: true)
        AGENT_MESH_HEALTH_CHECK_INTERVAL - Health check interval seconds (default: 30)

        ENABLE_MCP_INTEGRATION     - Enable MCP integration (default: false)
        MCP_PROTOCOL_VERSION       - MCP protocol version (default: 2024-11-05)
        MCP_CONFIG_PATH            - MCP config file path (default: mcp_config.json)
        MCP_REQUEST_TIMEOUT        - Request timeout seconds (default: 10)
        MCP_MAX_RETRIES            - Max retries (default: 3)

        ENABLE_ADAPTIVE_QUESTIONING - Enable adaptive questioning (default: false)
        ENABLE_TRACK3_INTELLIGENCE  - Enable Track 3.1 ML (default: true)
        ENABLE_BOT_INTELLIGENCE     - Enable bot intelligence middleware (default: true)
    """
    progressive_skills = ProgressiveSkillsConfig(
        enabled=_env_bool("ENABLE_PROGRESSIVE_SKILLS"),
        model=os.getenv("PROGRESSIVE_SKILLS_MODEL", "claude-sonnet-4"),
        skills_path=os.getenv("PROGRESSIVE_SKILLS_PATH", "skills/"),
        cache_ttl=int(os.getenv("PROGRESSIVE_SKILLS_CACHE_TTL", "3600")),
        fallback_to_full=_env_bool("PROGRESSIVE_SKILLS_FALLBACK_TO_FULL", default=True),
        enabled_skills=os.getenv("PROGRESSIVE_SKILLS_ENABLED_SKILLS", "all"),
    )

    agent_mesh = AgentMeshConfig(
        enabled=_env_bool("ENABLE_AGENT_MESH"),
        max_agents=int(os.getenv("AGENT_MESH_MAX_AGENTS", "10")),
        routing_strategy=os.getenv("AGENT_MESH_ROUTING_STRATEGY", "capability_based"),
        max_cost_per_task=float(os.getenv("AGENT_MESH_MAX_COST", "5.0")),
        task_timeout=int(os.getenv("AGENT_MESH_TASK_TIMEOUT", "30")),
        load_balance=_env_bool("AGENT_MESH_LOAD_BALANCE", default=True),
        health_check_interval=int(os.getenv("AGENT_MESH_HEALTH_CHECK_INTERVAL", "30")),
    )

    mcp = MCPConfig(
        enabled=_env_bool("ENABLE_MCP_INTEGRATION"),
        protocol_version=os.getenv("MCP_PROTOCOL_VERSION", "2024-11-05"),
        config_path=os.getenv("MCP_CONFIG_PATH", "mcp_config.json"),
        request_timeout=int(os.getenv("MCP_REQUEST_TIMEOUT", "10")),
        max_retries=int(os.getenv("MCP_MAX_RETRIES", "3")),
    )

    return FeatureConfig(
        progressive_skills=progressive_skills,
        agent_mesh=agent_mesh,
        mcp=mcp,
        enable_adaptive_questioning=_env_bool("ENABLE_ADAPTIVE_QUESTIONING"),
        enable_track3_intelligence=_env_bool("ENABLE_TRACK3_INTELLIGENCE", default=True),
        enable_bot_intelligence=_env_bool("ENABLE_BOT_INTELLIGENCE", default=True),
    )


def feature_config_to_jorge_kwargs(config: FeatureConfig) -> Dict[str, Any]:
    """Bridge FeatureConfig to JorgeFeatureConfig constructor kwargs.

    Converts centralized config to kwargs compatible with
    JorgeFeatureConfig(**kwargs) without modifying jorge_seller_bot.py.
    """
    return {
        "enable_progressive_skills": config.progressive_skills.enabled,
        "enable_agent_mesh": config.agent_mesh.enabled,
        "enable_mcp_integration": config.mcp.enabled,
        "enable_adaptive_questioning": config.enable_adaptive_questioning,
        "enable_track3_intelligence": config.enable_track3_intelligence,
        "enable_bot_intelligence": config.enable_bot_intelligence,
        "max_concurrent_tasks": config.agent_mesh.max_agents,
    }
