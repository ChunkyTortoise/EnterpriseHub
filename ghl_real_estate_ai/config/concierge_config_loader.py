"""ConciergeConfigLoader — Multi-tenant config for the Claude Concierge system.

Each tenant provides a YAML file at concierge_configs/{tenant_id}.yaml.
The loader parses it into ConciergeClientConfig which drives:
  - System prompt template variables (business_model, market_context, client_style)
  - PlatformKnowledgeEngine feature/agent lists
  - Pluggable agent registry invoke_pattern routing

Pattern mirrors JorgeConfigLoader: YAML + typed dataclass, singleton with
in-process cache. New clients drop a YAML file — no code changes required.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# Concierge YAML configs live two levels above this file (project root)
_CONFIGS_DIR = Path(__file__).parent.parent.parent / "concierge_configs"


@dataclass
class AgentDef:
    """Single agent definition loaded from YAML config."""

    name: str
    agent_type: str
    capabilities: List[str]
    specializations: List[str] = field(default_factory=list)
    invoke_pattern: str = ""  # Substring matched against lowercase agent name for routing


@dataclass
class ConciergeClientConfig:
    """Per-tenant Concierge configuration — drives prompts, knowledge engine, and agent routing."""

    tenant_id: str
    domain: str                           # e.g. "real_estate", "dental", "legal"
    client_name: str                      # Used in system prompts
    business_model: str                   # Revenue model description → {business_model} template var
    market_context: str                   # Geographic/market description → {market_context} var
    client_style: str                     # Communication preferences → {client_style} var
    available_agents: List[AgentDef] = field(default_factory=list)
    platform_features: Dict[str, List[str]] = field(default_factory=dict)
    compliance_requirements: List[str] = field(default_factory=list)
    config_path: Optional[Path] = None

    @property
    def agent_summary(self) -> str:
        """Formatted agent list for system prompt injection."""
        return ", ".join(a.name for a in self.available_agents) or "General AI assistant"

    @property
    def compliance_summary(self) -> str:
        """Formatted compliance list for system prompt injection."""
        if not self.compliance_requirements:
            return "Standard professional and ethical guidelines"
        return "; ".join(self.compliance_requirements)


class ConciergeConfigLoader:
    """Loads per-tenant Concierge configs from concierge_configs/{tenant_id}.yaml.

    Follows the JorgeConfigLoader singleton + in-process cache pattern.
    Falls back to hardcoded Jorge defaults when the YAML is missing (e.g. tests).
    """

    def __init__(self, configs_dir: Optional[Path] = None) -> None:
        self.configs_dir = configs_dir or _CONFIGS_DIR
        self._cache: Dict[str, ConciergeClientConfig] = {}

    def load(self, tenant_id: str) -> ConciergeClientConfig:
        """Return cached or freshly parsed config for *tenant_id*."""
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        config_path = self.configs_dir / f"{tenant_id}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(
                f"Concierge config not found: {config_path}. "
                f"Create concierge_configs/{tenant_id}.yaml or call get_default_concierge_config()."
            )

        with open(config_path) as f:
            raw = yaml.safe_load(f)

        config = self._parse(tenant_id, raw, config_path)
        self._cache[tenant_id] = config
        logger.info(f"Loaded concierge config for tenant '{tenant_id}' from {config_path}")
        return config

    def _parse(self, tenant_id: str, raw: Dict[str, Any], config_path: Path) -> ConciergeClientConfig:
        agents = [
            AgentDef(
                name=a["name"],
                agent_type=a.get("agent_type", "general"),
                capabilities=a.get("capabilities", []),
                specializations=a.get("specializations", []),
                invoke_pattern=a.get("invoke_pattern", ""),
            )
            for a in raw.get("agents", [])
        ]
        return ConciergeClientConfig(
            tenant_id=tenant_id,
            domain=raw.get("domain", "general"),
            client_name=raw.get("client_name", "User"),
            business_model=raw.get("business_model", ""),
            market_context=raw.get("market_context", ""),
            client_style=raw.get("client_style", ""),
            available_agents=agents,
            platform_features=raw.get("platform_features", {}),
            compliance_requirements=raw.get("compliance_requirements", []),
            config_path=config_path,
        )

    def get_default(self) -> ConciergeClientConfig:
        """Return Jorge's config; fall back to hardcoded if YAML is missing."""
        try:
            return self.load("jorge")
        except FileNotFoundError:
            logger.warning("concierge_configs/jorge.yaml not found — using hardcoded Jorge defaults")
            return self._jorge_hardcoded()

    def reload(self, tenant_id: str) -> None:
        """Evict cache entry and reload from disk (useful after hot-reloading config)."""
        self._cache.pop(tenant_id, None)
        self.load(tenant_id)

    # ------------------------------------------------------------------
    # Hardcoded fallback — keeps Jorge working even without jorge.yaml
    # ------------------------------------------------------------------

    def _jorge_hardcoded(self) -> ConciergeClientConfig:
        return ConciergeClientConfig(
            tenant_id="jorge",
            domain="real_estate",
            client_name="Jorge Salas",
            business_model=(
                "6% commission on residential home sales. Primary focus on seller "
                "qualification and lead conversion in the Rancho Cucamonga market."
            ),
            market_context=(
                "Rancho Cucamonga, CA — Inland Empire submarket. Median home price $850K, "
                "high demand and low inventory. Target closing timeline: 30-45 days."
            ),
            client_style=(
                "Direct and results-focused. Data-driven decision making. "
                "High-energy, ambitious. Values efficiency and automation. "
                "Prefers actionable insights over theory."
            ),
            available_agents=[
                AgentDef(
                    name="Adaptive Jorge Seller Bot",
                    agent_type="seller_qualification",
                    capabilities=["real_time_questioning", "calendar_integration", "stall_breaking"],
                    specializations=["seller_qualification"],
                    invoke_pattern="seller",
                ),
                AgentDef(
                    name="Predictive Lead Bot",
                    agent_type="lead_nurture",
                    capabilities=["timing_optimization", "personality_adaptation", "multi_channel"],
                    specializations=["behavioral_analysis"],
                    invoke_pattern="lead",
                ),
                AgentDef(
                    name="Real-time Intent Decoder",
                    agent_type="intent_analysis",
                    capabilities=["streaming_analysis", "semantic_understanding", "forecasting"],
                    specializations=["intent_scoring"],
                    invoke_pattern="intent",
                ),
                AgentDef(
                    name="Jorge Buyer Bot",
                    agent_type="buyer_qualification",
                    capabilities=["property_matching", "affordability_assessment", "buyer_nurture"],
                    specializations=["buyer_qualification"],
                    invoke_pattern="buyer",
                ),
                AgentDef(
                    name="Enhanced Bot Orchestrator",
                    agent_type="orchestration",
                    capabilities=["multi_bot_coordination", "fallback_management", "metrics_tracking"],
                    specializations=["bot_coordination"],
                    invoke_pattern="orchestrator",
                ),
            ],
            platform_features={
                "lead_management": [
                    "Jorge Seller Bot (Adaptive)",
                    "Predictive Lead Bot",
                    "Real-time Intent Decoder",
                    "Lead Intelligence Swarm",
                    "Voss Negotiation Agent",
                    "Temperature Prediction",
                    "Behavioral Analytics",
                    "Multi-channel Sequences",
                    "Lead Scoring",
                ],
                "bot_ecosystem": [
                    "40+ Specialized Agents",
                    "Multi-agent Orchestration",
                    "Swarm Intelligence",
                    "Real-time Coordination",
                    "Performance Monitoring",
                    "Adaptive Learning",
                ],
                "property_analysis": [
                    "CMA Generator",
                    "Property Intelligence",
                    "Market Analysis",
                    "Competitive Benchmarking",
                    "Investment Analysis",
                ],
                "analytics_reporting": [
                    "Revenue Attribution",
                    "Performance Dashboards",
                    "Predictive Analytics",
                    "Lead Intelligence Reports",
                    "Agent Performance Metrics",
                ],
            },
            compliance_requirements=[
                "California Department of Real Estate (DRE) licensing",
                "Equal Housing Opportunity Act",
                "California Fair Employment and Housing Act (FEHA)",
                "Natural Hazard Disclosure Statement required",
                "Transfer Disclosure Statement required",
                "CAN-SPAM for email sequences",
                "CCPA for data privacy",
            ],
        )


# ---------------------------------------------------------------------------
# Module-level singleton + factory functions
# ---------------------------------------------------------------------------

_loader = ConciergeConfigLoader()


def get_concierge_config(tenant_id: str) -> ConciergeClientConfig:
    """Load ConciergeClientConfig for the given tenant_id."""
    return _loader.load(tenant_id)


def get_default_concierge_config() -> ConciergeClientConfig:
    """Load the default (Jorge) ConciergeClientConfig."""
    return _loader.get_default()
